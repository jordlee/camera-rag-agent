"""
Hierarchical PDF Parser for Camera Help Guide PDFs

This parser extracts hierarchical structure from Sony camera help guide PDFs:
- Topic headers (largest font, bold)
- Section headers (medium font, bold/black)
- Subheaders (smaller font, bold)
- Body text, footnotes, hints, related topics

Output format matches the structure specified in data/html-source.md
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import pdfplumber


class HelpGuidePDFParser:
    """Parse Sony camera help guide PDFs with hierarchical structure extraction"""

    # Camera-specific font threshold profiles
    # Based on font distribution analysis of each camera's PDF
    FONT_THRESHOLD_PROFILES = {
        'ILME-FR7': {
            # FR7 uses smaller fonts (max 12.7pt, median 9.7pt)
            'topic': 11.0,       # Catches 12.7pt and 11.x headers
            'section': 9.8,      # 75th percentile, most sections
            'subheader': 8.6,    # Above footnotes, catches 9.7-9.8pt body-level headers
            'footnote': 8.4      # 10th percentile
        },
        'ILCE': {
            # Alpha series (ILCE-1M2 baseline)
            'topic': 12.0,
            'section': 10.5,
            'subheader': 9.5,
            'footnote': 8.5
        },
        'ILME': {
            # Cinema Line default (FX series)
            'topic': 11.5,
            'section': 10.0,
            'subheader': 9.0,
            'footnote': 8.5
        },
        'default': {
            # Conservative fallback for other cameras
            'topic': 11.5,
            'section': 10.0,
            'subheader': 9.0,
            'footnote': 8.5
        }
    }

    def __init__(self, pdf_path: str, camera_model: str, help_guide_url: str):
        self.pdf_path = Path(pdf_path)
        self.camera_model = camera_model
        self.help_guide_url = help_guide_url

        # Select appropriate font threshold profile based on camera model
        profile = self._select_threshold_profile(camera_model)

        # Font size thresholds
        self.TOPIC_MIN_SIZE = profile['topic']
        self.SECTION_MIN_SIZE = profile['section']
        self.SUBHEADER_MIN_SIZE = profile['subheader']
        self.FOOTNOTE_MAX_SIZE = profile['footnote']

        # Font name patterns
        self.BOLD_PATTERN = re.compile(r'(Bold|Black)', re.IGNORECASE)

    def _select_threshold_profile(self, camera_model: str) -> Dict:
        """
        Select appropriate font threshold profile based on camera model

        Args:
            camera_model: Camera model identifier (e.g., 'ILME-FR7', 'ILCE-1M2')

        Returns:
            Dictionary with font size thresholds
        """
        # Check for exact model match first (e.g., ILME-FR7)
        if camera_model.startswith('ILME-FR7'):
            return self.FONT_THRESHOLD_PROFILES['ILME-FR7']

        # Check for series prefix
        elif camera_model.startswith('ILCE'):
            return self.FONT_THRESHOLD_PROFILES['ILCE']

        elif camera_model.startswith('ILME'):
            return self.FONT_THRESHOLD_PROFILES['ILME']

        # Default fallback
        else:
            return self.FONT_THRESHOLD_PROFILES['default']

    def extract_font_lines(self, page) -> List[Dict]:
        """
        Extract lines of text with font metadata

        Returns:
            List of dicts with 'text', 'font', 'size', 'y0' (vertical position)
        """
        chars = page.chars
        if not chars:
            return []

        # Group characters into lines based on y-coordinate
        lines = defaultdict(list)
        for char in chars:
            y = round(char.get('top', 0), 1)
            lines[y].append(char)

        # Build line objects with font info
        line_objects = []
        for y, line_chars in sorted(lines.items()):
            # Determine dominant font for this line
            font_counts = defaultdict(int)
            for char in line_chars:
                font_key = (char.get('fontname', ''), round(char.get('size', 0), 1))
                font_counts[font_key] += 1

            if not font_counts:
                continue

            dominant_font, dominant_size = max(font_counts.items(), key=lambda x: x[1])[0]
            line_text = ''.join([c.get('text', '') for c in line_chars]).strip()

            if line_text:
                line_objects.append({
                    'text': line_text,
                    'font': dominant_font,
                    'size': dominant_size,
                    'y0': y
                })

        return line_objects

    def classify_line_type(self, line: Dict) -> str:
        """
        Classify a line as topic, section, subheader, footnote, hint, related, or body

        Args:
            line: Dict with 'text', 'font', 'size'

        Returns:
            One of: 'topic', 'section', 'subheader', 'footnote', 'hint', 'related', 'body', 'ignore'
        """
        text = line['text']
        font = line['font']
        size = line['size']

        # Ignore page numbers, headers, camera model references, document IDs
        if re.match(r'^\d+$', text):  # Just a number
            return 'ignore'
        if text in ['Help Guide', self.camera_model]:
            return 'ignore'
        # Ignore model name variations (e.g., "ILME-FX2/ILME-FX2B", "ILME-FR7 / ILME-FR7K")
        model_base = self.camera_model.split('/')[0].split(',')[0].strip()
        if model_base in text and len(text) < 30:
            return 'ignore'
        if text.startswith('Interchangeable Lens'):
            return 'ignore'
        if re.match(r'^TP\d+$', text):  # Document ID like TP1001920799
            return 'ignore'
        if text.startswith('Copyright') or 'Sony Corporation' in text:
            return 'ignore'

        # Check for special standalone headers
        if text.strip() == 'Hint':
            return 'hint'
        if text.strip() == 'Related Topic':
            return 'related'

        # Check for footnotes (small font, often starts with asterisk or superscript)
        if size < self.FOOTNOTE_MAX_SIZE or text.startswith('*'):
            return 'footnote'

        # Check font size and boldness for hierarchy
        is_bold = self.BOLD_PATTERN.search(font) is not None

        if size >= self.TOPIC_MIN_SIZE and is_bold:
            return 'topic'
        elif size >= self.SECTION_MIN_SIZE and is_bold:
            return 'section'
        elif size >= self.SUBHEADER_MIN_SIZE and is_bold:
            return 'subheader'
        else:
            return 'body'

    def extract_footnotes(self, lines: List[Dict], start_idx: int) -> Tuple[List[str], int]:
        """
        Extract consecutive footnotes starting from start_idx

        Returns:
            (list of footnote texts, index after last footnote)
        """
        footnotes = []
        idx = start_idx

        while idx < len(lines):
            line_type = self.classify_line_type(lines[idx])
            if line_type == 'footnote':
                footnotes.append(lines[idx]['text'])
                idx += 1
            else:
                break

        return footnotes, idx

    def parse_page(self, page, page_num: int) -> List[Dict]:
        """
        Parse a single page and return structured chunks

        Returns:
            List of chunk dicts with hierarchical structure
        """
        lines = self.extract_font_lines(page)
        if not lines:
            return []

        chunks = []
        current_chunk = {
            'product_id': self.camera_model,
            'web_help_guide_url': self.help_guide_url,
            'page_start': page_num,
            'page_end': page_num,
            'topic_title': '',
            'topic_body': '',
            'section_title': '',
            'section_body': '',
            'subheader_title': '',
            'subheader_body': '',
            'footnotes': [],
            'hints': [],
            'related_topics': []
        }

        i = 0
        while i < len(lines):
            line = lines[i]
            line_type = self.classify_line_type(line)

            if line_type == 'ignore':
                i += 1
                continue

            if line_type == 'topic':
                # Save previous chunk if it has content
                if current_chunk['subheader_title'] or current_chunk['topic_title']:
                    chunks.append(current_chunk.copy())

                # Start new topic
                current_chunk = {
                    'product_id': self.camera_model,
                    'web_help_guide_url': self.help_guide_url,
                    'page_start': page_num,
                    'page_end': page_num,
                    'topic_title': line['text'],
                    'topic_body': '',
                    'section_title': '',
                    'section_body': '',
                    'subheader_title': '',
                    'subheader_body': '',
                    'footnotes': [],
                    'hints': [],
                    'related_topics': []
                }
                i += 1

            elif line_type == 'section':
                # Save previous chunk if it has any content
                if (current_chunk['subheader_title'] or
                    current_chunk['section_title'] or
                    current_chunk.get('_has_orphan_content')):
                    # Clean up tracking flag before saving
                    if '_has_orphan_content' in current_chunk:
                        del current_chunk['_has_orphan_content']
                    chunks.append(current_chunk.copy())

                # Start new section (keep topic context)
                current_chunk['section_title'] = line['text']
                current_chunk['section_body'] = ''
                current_chunk['subheader_title'] = ''
                current_chunk['subheader_body'] = ''
                current_chunk['footnotes'] = []
                current_chunk['hints'] = []
                current_chunk['page_start'] = page_num
                current_chunk['page_end'] = page_num
                i += 1

            elif line_type == 'subheader':
                # Save previous subheader chunk if exists
                if current_chunk['subheader_title']:
                    chunks.append(current_chunk.copy())

                # Start new subheader
                current_chunk['subheader_title'] = line['text']
                current_chunk['subheader_body'] = ''
                current_chunk['footnotes'] = []
                current_chunk['hints'] = []
                current_chunk['page_start'] = page_num
                current_chunk['page_end'] = page_num
                i += 1

            elif line_type == 'footnote':
                footnotes, next_idx = self.extract_footnotes(lines, i)
                current_chunk['footnotes'].extend(footnotes)
                i = next_idx

            elif line_type == 'hint':
                # Collect hint text from following body lines
                i += 1
                hint_text = ''
                while i < len(lines):
                    next_type = self.classify_line_type(lines[i])
                    if next_type == 'body':
                        hint_text += ' ' + lines[i]['text']
                        i += 1
                    else:
                        break
                if hint_text:
                    current_chunk['hints'].append(hint_text.strip())

            elif line_type == 'related':
                # Extract related topics from following lines
                i += 1
                while i < len(lines):
                    next_type = self.classify_line_type(lines[i])
                    if next_type == 'body':
                        # Each line is typically one related topic
                        topic = lines[i]['text'].strip()
                        if topic and not topic.startswith('TP') and 'Copyright' not in topic:
                            current_chunk['related_topics'].append(topic)
                        i += 1
                    else:
                        break

            elif line_type == 'body':
                text = line['text']
                # Regular body text
                if current_chunk['subheader_title']:
                    current_chunk['subheader_body'] += ' ' + text
                elif current_chunk['section_title']:
                    current_chunk['section_body'] += ' ' + text
                elif current_chunk['topic_title']:
                    current_chunk['topic_body'] += ' ' + text
                else:
                    # No header exists - create default chunk for orphan body text
                    # Skip very short text (likely diagram labels like "POWER lamp", "Air inlet")
                    if len(text.strip()) < 20:
                        i += 1
                        continue

                    # Use first sentence or first 50 chars as title
                    if not current_chunk.get('subheader_title') and not current_chunk.get('_has_orphan_content'):
                        first_sentence = text.split('.')[0] if '.' in text else text
                        title = first_sentence[:50].strip()
                        current_chunk['subheader_title'] = title + ('...' if len(first_sentence) > 50 else '')

                        # Rest goes to body
                        remaining = text[len(first_sentence):].strip() if '.' in text and len(text) > len(first_sentence) else ''
                        current_chunk['subheader_body'] = remaining
                        current_chunk['_has_orphan_content'] = True
                    else:
                        # Continue accumulating orphan body text
                        current_chunk['subheader_body'] += ' ' + text
                i += 1

        # Save final chunk (including orphan content and section-only chunks)
        if (current_chunk['subheader_title'] or
            current_chunk['section_title'] or
            current_chunk['topic_title'] or
            current_chunk.get('_has_orphan_content')):
            # Clean up internal tracking flag before saving
            if '_has_orphan_content' in current_chunk:
                del current_chunk['_has_orphan_content']
            chunks.append(current_chunk)

        return chunks

    def parse(self) -> List[Dict]:
        """
        Parse entire PDF and return all structured chunks

        Returns:
            List of chunk dictionaries
        """
        all_chunks = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_chunks = self.parse_page(page, page_num)
                all_chunks.extend(page_chunks)

        # Clean up whitespace in all text fields
        for chunk in all_chunks:
            for key in ['topic_body', 'section_body', 'subheader_body']:
                if chunk[key]:
                    chunk[key] = ' '.join(chunk[key].split())

        return all_chunks

    def save_json(self, output_path: str):
        """Parse PDF and save structured output as JSON"""
        chunks = self.parse()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        return len(chunks)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Parse camera help guide PDF with hierarchical structure')
    parser.add_argument('--pdf', type=str, required=True, help='Path to PDF file')
    parser.add_argument('--model', type=str, required=True, help='Camera model (e.g., ILCE-1M2)')
    parser.add_argument('--url', type=str, required=True, help='Help guide URL')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file path')

    args = parser.parse_args()

    parser_obj = HelpGuidePDFParser(args.pdf, args.model, args.url)
    num_chunks = parser_obj.save_json(args.output)

    print(f"✓ Parsed {num_chunks} chunks from {args.pdf}")
    print(f"✓ Saved to {args.output}")


if __name__ == "__main__":
    main()
