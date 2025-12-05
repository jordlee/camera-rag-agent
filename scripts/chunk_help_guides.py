#!/usr/bin/env python3
"""
Help Guide Chunker for Camera Documentation

Converts hierarchical PDF chunks into 500-token semantic chunks for embedding.
Processes all camera help guides in data/help-guides/*/parsed/hierarchical_chunks.json

Usage:
    python scripts/chunk_help_guides.py
    python scripts/chunk_help_guides.py --camera ILME-FR7
    python scripts/chunk_help_guides.py --output custom_chunks.json
"""

import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict
from collections import defaultdict


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
HELP_GUIDES_DIR = PROJECT_ROOT / "data/help-guides"
DEFAULT_OUTPUT = PROJECT_ROOT / "data/help-guides-chunks.json"
HTML_SOURCE_FILE = PROJECT_ROOT / "data/html-source.md"

CHUNK_SIZE = 500  # Target tokens per chunk
CHUNK_OVERLAP = 100  # Token overlap between chunks
MIN_CONTENT_LENGTH = 20  # Minimum characters for valid content


class HelpGuideChunker:
    """Convert hierarchical help guide chunks into semantic chunks for embedding"""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.stats = defaultdict(int)
        self.camera_urls = self._load_camera_urls()

    def _load_camera_urls(self) -> Dict[str, str]:
        """
        Load camera model to help guide URL mapping from html-source.md

        Returns:
            Dictionary mapping camera model to help guide URL
        """
        camera_urls = {}

        if not HTML_SOURCE_FILE.exists():
            print(f"⚠️  Warning: {HTML_SOURCE_FILE} not found, help_guide_url will not be populated")
            return camera_urls

        with open(HTML_SOURCE_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_model = None
        for line in lines:
            line = line.strip()

            # Skip empty lines and instruction lines
            if not line or line.startswith('instructions:') or line.startswith('example'):
                continue

            # Check if line is a URL
            if line.startswith('http'):
                if current_model:
                    camera_urls[current_model] = line
                    current_model = None
            else:
                # This is a camera model name
                # Clean up version info in parentheses
                import re
                model = re.sub(r'\(.*?\)', '', line).strip()
                # Handle models with slashes (e.g., "ILME-FX6V/ILME-FX6T")
                if '/' in model:
                    # Take first model as primary, but also store both
                    models = [m.strip() for m in model.split('/')]
                    current_model = models[0]
                    # Store URL for all variants when URL comes
                else:
                    # Handle comma-separated models
                    if ',' in model:
                        models = [m.strip() for m in model.split(',')]
                        current_model = models[0]
                    else:
                        current_model = model

        return camera_urls

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters for English text)
        More accurate than word count for camera documentation
        """
        return len(text) // 4

    def create_chunk_id(self, product_id: str, page: int, index: int, content: str) -> str:
        """Create unique chunk ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{product_id}_p{page}_c{index}_{content_hash}"

    def is_quality_content(self, text: str) -> bool:
        """Validate content quality"""
        if not text or len(text.strip()) < MIN_CONTENT_LENGTH:
            return False

        stripped = text.strip()

        # Skip if mostly non-alphanumeric (broken fragments)
        alphanumeric = sum(1 for c in stripped if c.isalnum())
        if len(stripped) > 0 and alphanumeric / len(stripped) < 0.3:
            return False

        # Skip pure boilerplate
        boilerplate_phrases = [
            'Help Guide',
            'Copyright',
            'Sony Corporation',
            'All rights reserved'
        ]
        if any(phrase in stripped for phrase in boilerplate_phrases) and len(stripped) < 100:
            return False

        return True

    def build_hierarchical_context(self, chunk_data: Dict) -> str:
        """
        Build full context string from hierarchical chunk data
        Format: Topic > Section > Subheader
                Body text
                Hints/Related topics
        """
        parts = []

        # Add hierarchical breadcrumb
        breadcrumb = []
        if chunk_data.get('topic_title'):
            breadcrumb.append(chunk_data['topic_title'])
        if chunk_data.get('section_title'):
            breadcrumb.append(chunk_data['section_title'])
        if chunk_data.get('subheader_title'):
            breadcrumb.append(chunk_data['subheader_title'])

        if breadcrumb:
            parts.append(" > ".join(breadcrumb))

        # Add body content
        bodies = []
        for key in ['topic_body', 'section_body', 'subheader_body']:
            body = chunk_data.get(key, '').strip()
            if body:
                bodies.append(body)

        if bodies:
            parts.append("\n\n".join(bodies))

        # Add hints
        hints = chunk_data.get('hints', [])
        if hints:
            hints_text = "\n".join([f"Hint: {hint}" for hint in hints])
            parts.append(hints_text)

        # Add related topics
        related = chunk_data.get('related_topics', [])
        if related:
            related_text = "Related Topics: " + ", ".join(related)
            parts.append(related_text)

        # Add footnotes
        footnotes = chunk_data.get('footnotes', [])
        if footnotes:
            footnotes_text = "\n".join([f"Note: {note}" for note in footnotes])
            parts.append(footnotes_text)

        return "\n\n".join(parts)

    def split_into_chunks(self, full_content: str, metadata: Dict) -> List[Dict]:
        """
        Split content into ~500 token chunks with overlap
        """
        tokens_estimate = self.estimate_tokens(full_content)

        # If content fits in one chunk, return as-is
        if tokens_estimate <= self.chunk_size:
            return [{
                'content': full_content,
                'metadata': metadata,
                'token_estimate': tokens_estimate
            }]

        # Split by paragraphs first
        paragraphs = full_content.split('\n\n')
        chunks = []
        current_chunk = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.estimate_tokens(para)

            # If adding this paragraph exceeds chunk size, save current chunk
            if current_tokens + para_tokens > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'metadata': metadata.copy(),
                    'token_estimate': current_tokens
                })

                # Start new chunk with overlap (keep last paragraph)
                overlap_tokens = self.estimate_tokens(current_chunk[-1])
                if overlap_tokens < self.chunk_overlap:
                    current_chunk = [current_chunk[-1]]
                    current_tokens = overlap_tokens
                else:
                    current_chunk = []
                    current_tokens = 0

            current_chunk.append(para)
            current_tokens += para_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'content': chunk_text,
                'metadata': metadata.copy(),
                'token_estimate': current_tokens
            })

        return chunks

    def process_hierarchical_chunk(self, chunk_data: Dict, chunk_index: int) -> List[Dict]:
        """Process a single hierarchical chunk into semantic chunks"""
        # Build full content
        full_content = self.build_hierarchical_context(chunk_data)

        if not self.is_quality_content(full_content):
            self.stats['skipped_low_quality'] += 1
            return []

        # Get product_id and look up help_guide_url
        product_id = chunk_data.get('product_id', 'unknown')
        help_guide_url = chunk_data.get('web_help_guide_url', '')

        # If URL is empty, try to load from camera_urls mapping
        if not help_guide_url and product_id in self.camera_urls:
            help_guide_url = self.camera_urls[product_id]

        # Build metadata - preserve all hierarchical fields
        base_metadata = {
            'product_id': product_id,
            'help_guide_url': help_guide_url,
            'page_start': chunk_data.get('page_start', 0),
            'page_end': chunk_data.get('page_end', 0),
            'topic_title': chunk_data.get('topic_title', ''),
            'topic_body': chunk_data.get('topic_body', ''),
            'section_title': chunk_data.get('section_title', ''),
            'section_body': chunk_data.get('section_body', ''),
            'subheader_title': chunk_data.get('subheader_title', ''),
            'subheader_body': chunk_data.get('subheader_body', ''),
            'hints': chunk_data.get('hints', []),
            'related_topics': chunk_data.get('related_topics', []),
            'footnotes': chunk_data.get('footnotes', []),
            'type': 'help_guide',
            'source': 'camera_help_guide_pdf'
        }

        # Split into semantic chunks
        semantic_chunks = self.split_into_chunks(full_content, base_metadata)

        # Create final chunk objects
        output_chunks = []
        for i, chunk in enumerate(semantic_chunks):
            chunk_id = self.create_chunk_id(
                base_metadata['product_id'],
                base_metadata['page_start'],
                chunk_index + i,
                chunk['content']
            )

            output_chunks.append({
                'id': chunk_id,
                'content': chunk['content'],
                'metadata': chunk['metadata']
            })

        self.stats['chunks_created'] += len(output_chunks)
        return output_chunks

    def process_camera(self, camera_model: str) -> List[Dict]:
        """Process all chunks for a specific camera model"""
        camera_dir = HELP_GUIDES_DIR / camera_model
        chunks_file = camera_dir / "parsed/hierarchical_chunks.json"

        if not chunks_file.exists():
            print(f"⚠️  No parsed chunks found for {camera_model}: {chunks_file}")
            return []

        print(f"Processing {camera_model}...")

        with open(chunks_file, 'r', encoding='utf-8') as f:
            hierarchical_chunks = json.load(f)

        print(f"  Loaded {len(hierarchical_chunks)} hierarchical chunks")

        # Process each hierarchical chunk
        all_semantic_chunks = []
        for i, hier_chunk in enumerate(hierarchical_chunks):
            semantic_chunks = self.process_hierarchical_chunk(hier_chunk, i)
            all_semantic_chunks.extend(semantic_chunks)

        print(f"  ✓ Created {len(all_semantic_chunks)} semantic chunks")
        self.stats['cameras_processed'] += 1

        return all_semantic_chunks

    def process_all_cameras(self, specific_camera: str = None) -> List[Dict]:
        """Process all camera help guides or a specific one"""
        all_chunks = []

        if specific_camera:
            # Process only the specified camera
            chunks = self.process_camera(specific_camera)
            all_chunks.extend(chunks)
        else:
            # Find all camera directories with parsed chunks
            camera_dirs = [d for d in HELP_GUIDES_DIR.iterdir() if d.is_dir()]

            for camera_dir in sorted(camera_dirs):
                if camera_dir.name.startswith('.'):
                    continue

                chunks_file = camera_dir / "parsed/hierarchical_chunks.json"
                if chunks_file.exists():
                    chunks = self.process_camera(camera_dir.name)
                    all_chunks.extend(chunks)

        return all_chunks

    def print_stats(self):
        """Print processing statistics"""
        print("\n" + "=" * 70)
        print("CHUNKING STATISTICS")
        print("=" * 70)
        print(f"Cameras processed: {self.stats['cameras_processed']}")
        print(f"Chunks created: {self.stats['chunks_created']}")
        print(f"Skipped (low quality): {self.stats['skipped_low_quality']}")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Chunk camera help guides for embedding')
    parser.add_argument('--camera', type=str, help='Process specific camera model only')
    parser.add_argument('--output', type=str, default=str(DEFAULT_OUTPUT),
                        help='Output JSON file path')
    parser.add_argument('--chunk-size', type=int, default=CHUNK_SIZE,
                        help='Target tokens per chunk')
    parser.add_argument('--chunk-overlap', type=int, default=CHUNK_OVERLAP,
                        help='Token overlap between chunks')

    args = parser.parse_args()

    print("=" * 70)
    print("HELP GUIDE CHUNKER")
    print("=" * 70)
    print(f"Chunk size: {args.chunk_size} tokens")
    print(f"Chunk overlap: {args.chunk_overlap} tokens")
    print(f"Output: {args.output}")
    print("=" * 70)

    # Initialize chunker
    chunker = HelpGuideChunker(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )

    # Process cameras
    chunks = chunker.process_all_cameras(specific_camera=args.camera)

    # Save chunks
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved {len(chunks)} chunks to: {output_path}")

    # Print statistics
    chunker.print_stats()


if __name__ == "__main__":
    main()
