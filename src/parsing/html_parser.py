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


def parse_html_file(file_path):
    """
    Parses an HTML file, extracting main text content and converting tables to Markdown.

    Args:
        file_path (str): The path to the HTML file.

    Returns:
        dict: A dictionary containing the extracted content and metadata,
              or None if parsing fails.
    """
    print(f"Parsing HTML file: {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # --- 1. Extract Main Text Content (excluding tables and scripts/styles initially) ---
        # Remove script and style elements to clean up text
        for script_or_style in soup(['script', 'style']):
            script_or_style.extract()

        # Find all table elements and temporarily remove them from the soup
        # so they don't get processed by the general text extraction below.
        # We will re-add their content later as Markdown tables.
        tables_in_soup = soup.find_all('table')
        for table in tables_in_soup:
            table.extract() # Remove table from the main soup for now

        # Extract text from common content tags from the remaining HTML
        # You can adjust these tags based on the structure of your HTML documentation.
        # Common content tags might include 'p', 'h1', 'h2', 'h3', 'li', 'div' (with specific classes)
        # We'll focus on block-level elements that typically contain readable text.
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'span'])
        
        main_text_parts = []
        for element in text_elements:
            # Get text, strip whitespace, and ignore if empty
            text = element.get_text(separator=" ", strip=True)
            if text:
                main_text_parts.append(text)
        
        combined_content = "\n\n".join(main_text_parts)


        # --- 2. Convert Tables to Markdown and re-insert into content ---
        # This assumes you want tables integrated into the main content.
        # If you prefer them separate, modify this logic.
        tables_markdown = []
        for i, table in enumerate(tables_in_soup):
            try:
                # pandas read_html can parse tables directly into DataFrames
                # It returns a list of DataFrames, even if there's only one table
                df_list = pd.read_html(table.prettify()) 
                if df_list:
                    df = df_list[0]
                    # Convert DataFrame to Markdown table format
                    markdown_table = df.to_markdown(index=False)
                    tables_markdown.append(f"\n\nTable {i+1}:\n{markdown_table}\n\n")
            except Exception as e:
                print(f"  Warning: Could not convert table to Markdown in {file_path}: {e}")
                # Fallback to plain text if conversion fails
                tables_markdown.append(f"\n\n[Table content fallback (could not convert to Markdown)]\n{table.get_text(separator=' ', strip=True)}\n\n")

        # Combine text content with markdown tables
        # This is a simplified integration. You might need more sophisticated logic
        # if the precise position of tables relative to text is critical.
        if tables_markdown:
            combined_content += "\n\n" + "\n\n".join(tables_markdown)

        # --- 3. Extract Metadata ---
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else os.path.basename(file_path)

        # Optional: Extract description from meta tag
        # description_tag = soup.find('meta', attrs={'name': 'description'})
        # description = description_tag['content'].strip() if description_tag else "No description"

        extracted_info = {
            "source_file": file_path,
            "file_type": "html",
            "content": combined_content.strip(), # Final cleaned content
            "metadata": {
                "title": title,
                "sdk_version": CURRENT_SDK_VERSION # Explicitly add SDK version to metadata
                # "description": description,
                # You can add more metadata extraction here
            }
        }
        print(f"  Successfully extracted content from {file_path}")
        return extracted_info

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
    for root, _, files in os.walk(HTML_SOURCE_DIR):
        for file in files:
            if file.endswith(('.html', '.htm')):
                file_path = os.path.join(root, file)
                parsed_data = parse_html_file(file_path)

                if parsed_data:
                    # Sanitize filename and append version for uniqueness
                    base_filename = os.path.basename(file_path).replace('.', '_')
                    # Replace '.' in version with '_' for filename safety
                    version_tag = CURRENT_SDK_VERSION.replace('.', '_')
                    output_filename = f"{base_filename}_v{version_tag}_parsed.json"
                    
                    output_filepath = os.path.join(PARSED_DATA_DIR, output_filename)
                    with open(output_filepath, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, f, indent=4, ensure_ascii=False)
                    print(f"  Saved parsed data to {output_filepath}")
                    processed_count += 1
                else:
                    print(f"  Skipped saving data for {file_path} due to parsing error.")
    
    print(f"\nFinished HTML parsing for SDK Version: {CURRENT_SDK_VERSION}.")
    print(f"Total HTML files processed and saved: {processed_count}")

if __name__ == "__main__":
    main()