import os
import re
import json
from bs4 import BeautifulSoup
import pandas as pd # Make sure you have pandas installed: pip install pandas
# You'll also likely need tabulate for df.to_markdown(): pip install tabulate

# Get the absolute path to the project root (where this script is likely run from)
# Assuming html_parser.py is in src/parsing/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- Configuration for HTML Documentation Parsing ---
# Define the SDK version for which HTML documentation exists
CURRENT_SDK_VERSION = "V2.00.00"

# HTML documentation source directory, now version-specific
# Assuming the structure is data/raw_sdk_docs/api_docs_html/V2.00.00/
HTML_SOURCE_DIR = os.path.join(PROJECT_ROOT, "data/raw_sdk_docs/api_docs_html", CURRENT_SDK_VERSION)

# Output directory for parsed HTML JSONs, now version-specific
PARSED_DATA_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/html", CURRENT_SDK_VERSION)


def format_version_tag(sdk_version):
    """Convert SDK version to friendly format: V2.00.00 -> V2"""
    if sdk_version.startswith('V'):
        major = sdk_version.split('.')[0]  # "V2.00.00" -> "V2"
        return major
    return sdk_version


def parse_html_file(file_path):
    """
    Parses an HTML file, extracting main text content separately from tables.
    Tables are saved as structured data in a separate JSON file.

    Args:
        file_path (str): The path to the HTML file.

    Returns:
        dict: A dictionary containing the extracted text content and metadata,
              or None if parsing fails.
    """
    print(f"Parsing HTML file: {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # --- 1. Remove script and style elements ---
        for script_or_style in soup(['script', 'style']):
            script_or_style.extract()

        # --- 2. Extract ALL tables as structured data ---
        extracted_tables = []
        tables_in_soup = soup.find_all('table')

        for i, table in enumerate(tables_in_soup):
            # Extract table caption (look for preceding headings)
            caption = ""
            caption_tag = table.find_previous(['h2', 'h3', 'h4'])
            if caption_tag:
                caption = caption_tag.get_text(strip=True)

            # Extract notes/legends that follow the table (look for content until next section)
            notes = ""
            notes_parts = []

            # Get the parent section of this table
            current_section = table.find_parent('section')

            if current_section:
                # Find all elements after the table but within the same section
                for sibling in table.find_all_next():
                    # Stop if we've left the current section
                    if sibling.find_parent('section') != current_section:
                        break

                    # Stop if we hit another table or major heading within the section
                    if sibling.name in ['table', 'h2', 'h3']:
                        break

                    # Collect text from paragraphs, divs, list items that might contain notes
                    if sibling.name in ['p', 'div', 'li', 'blockquote']:
                        text = sibling.get_text(strip=True)
                        if text and ('*' in text or 'Note:' in text or 'note:' in text or 'refers' in text.lower()):
                            notes_parts.append(text)

            notes = "\n".join(notes_parts) if notes_parts else ""

            # Parse table with pandas
            try:
                df_list = pd.read_html(table.prettify())
                if df_list:
                    df = df_list[0]

                    # Handle multi-level headers (pandas returns them as tuples)
                    if isinstance(df.columns, pd.MultiIndex):
                        # Flatten multi-level headers: ('USB', 'USB', 'R') -> 'USB R'
                        headers = []
                        for col_tuple in df.columns:
                            # Join non-empty unique parts
                            parts = []
                            seen = set()
                            for part in col_tuple:
                                if part and str(part) not in seen:
                                    parts.append(str(part))
                                    seen.add(str(part))
                            headers.append(' '.join(parts) if parts else str(col_tuple[-1]))
                    else:
                        headers = df.columns.tolist()

                    # Check if pandas used numeric indices as headers (0, 1, 2, ...)
                    if all(isinstance(col, int) for col in headers):
                        # Use first row as headers and remaining rows as data
                        headers = df.iloc[0].tolist()
                        data = df.iloc[1:].values.tolist()
                    else:
                        # Normal case: use extracted headers
                        data = df.values.tolist()

                    extracted_tables.append({
                        "table_index": i,
                        "headers": headers,
                        "data": data,
                        "notes": notes,
                        "table_caption": caption
                    })
            except Exception as e:
                print(f"  Warning: Could not parse table {i}: {e}")

            # REMOVE table from soup (don't include in text)
            table.extract()

        # --- 3. Extract remaining text (without tables) from main content only ---
        # Find the main content container to avoid extracting navigation menus
        main_content = soup.find(role="main") or soup.find('div', class_='document') or soup

        text_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div'])

        main_text_parts = []
        for element in text_elements:
            # Get text, strip whitespace, and ignore if empty
            text = element.get_text(separator=" ", strip=True)
            if text:
                main_text_parts.append(text)

        combined_content = "\n\n".join(main_text_parts)

        # --- 4. Extract Metadata ---
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else os.path.basename(file_path)

        # --- 5. Save text output with friendly version ---
        version_tag = format_version_tag(CURRENT_SDK_VERSION)
        filename = os.path.basename(file_path).replace('.html', '').replace('.htm', '').replace('.', '_')

        text_output_filename = f"{filename}_{version_tag}.json"
        text_output_path = os.path.join(PARSED_DATA_DIR, text_output_filename)

        text_output = {
            "source_file": file_path,
            "file_type": "html",
            "content": combined_content.strip(),
            "metadata": {
                "title": title,
                "sdk_version": CURRENT_SDK_VERSION
            }
        }

        with open(text_output_path, 'w', encoding='utf-8') as f:
            json.dump(text_output, f, indent=4, ensure_ascii=False)

        print(f"  Successfully extracted text to {text_output_path}")

        # --- 6. Save table output separately if tables exist ---
        if extracted_tables:
            table_output_filename = f"{filename}_tables_{version_tag}.json"
            table_output_path = os.path.join(PARSED_DATA_DIR, table_output_filename)

            table_output = {
                "source_file": file_path,
                "file_type": "html_tables",
                "content": extracted_tables,
                "metadata": {
                    "title": title,
                    "sdk_version": CURRENT_SDK_VERSION,
                    "extracted_type": "tables",
                    "num_tables": len(extracted_tables)
                }
            }

            with open(table_output_path, 'w', encoding='utf-8') as f:
                json.dump(table_output, f, indent=4, ensure_ascii=False)

            print(f"  Extracted {len(extracted_tables)} tables to {table_output_path}")

        return text_output

    except Exception as e:
        print(f"Error parsing HTML file {file_path}: {e}")
        return None

# --- Main execution logic ---
def main():
    os.makedirs(PARSED_DATA_DIR, exist_ok=True)
    print(f"Starting HTML parsing for SDK Version: {CURRENT_SDK_VERSION}")
    print(f"Scanning HTML files in: {HTML_SOURCE_DIR}")
    print(f"Outputting parsed JSONs to: {PARSED_DATA_DIR}")

    if not os.path.exists(HTML_SOURCE_DIR):
        print(f"Error: HTML source directory '{HTML_SOURCE_DIR}' for version {CURRENT_SDK_VERSION} not found. Skipping HTML parsing.")
        return # Exit if the source directory doesn't exist

    processed_count = 0
    tables_count = 0
    for root, _, files in os.walk(HTML_SOURCE_DIR):
        for file in files:
            if file.endswith(('.html', '.htm')):
                file_path = os.path.join(root, file)
                parsed_data = parse_html_file(file_path)

                if parsed_data:
                    processed_count += 1
                    # Count tables extracted (check if _tables file was created)
                    filename = os.path.basename(file_path).replace('.html', '').replace('.htm', '').replace('.', '_')
                    version_tag = format_version_tag(CURRENT_SDK_VERSION)
                    table_file = os.path.join(PARSED_DATA_DIR, f"{filename}_tables_{version_tag}.json")
                    if os.path.exists(table_file):
                        tables_count += 1
                else:
                    print(f"  Skipped saving data for {file_path} due to parsing error.")

    print(f"\nFinished HTML parsing for SDK Version: {CURRENT_SDK_VERSION}.")
    print(f"Total HTML files processed and saved: {processed_count}")
    print(f"Total files with tables extracted: {tables_count}")

if __name__ == "__main__":
    main()
