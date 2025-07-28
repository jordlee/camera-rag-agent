# src/parsing/rst_parser.py

import os
import json
import re

# Get the absolute path to the project root (where this script is likely run from)
# Assuming rst_parser.py is in src/parsing/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- Configuration for reStructuredText Documentation Parsing ---
# Base directory where different SDK versions' RST docs are located.
# Assuming RSTs are in '_sources' subfolder within the HTML documentation base directory.
SDK_RST_SOURCE_BASE_DIR = os.path.join(PROJECT_ROOT, "data/raw_sdk_docs/api_docs_html")

# Base directory for parsed RST output
PARSED_RST_OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/rst")


def extract_from_rst(rst_path, output_dir, sdk_version):
    """
    Extracts raw text content from a reStructuredText (.rst or .rst.txt) file.
    For RAG, the raw reStructuredText format often preserves valuable semantic
    information (like headings, code blocks, lists) that LLMs can interpret.

    Args:
        rst_path (str): The path to the input reStructuredText file.
        output_dir (str): The directory to save the extracted data (version-specific).
        sdk_version (str): The SDK version associated with this RST file.

    Returns:
        dict: A dictionary containing the extracted text content and metadata.
              Returns None if parsing fails.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the base name of the RST file, removing both .rst.txt and .rst extensions
    file_name_raw = os.path.basename(rst_path)
    file_name_base = file_name_raw.replace(".rst.txt", "").replace(".rst", "")

    full_text = ""
    try:
        with open(rst_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        # Create a clean filename from the base name and include version
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', file_name_base)
        version_tag = sdk_version.replace('.', '_')
        output_json_filename = f"{clean_name}_rst_v{version_tag}_parsed.json"

        output_path = os.path.join(output_dir, output_json_filename)

        parsed_data = {
            "source_file": rst_path,
            "file_type": "rst",
            "content": full_text.strip(),
            "metadata": {
                "title": file_name_base, # Use base filename as a default title
                "sdk_version": sdk_version
            }
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=4, ensure_ascii=False)
        
        print(f"Extracted reStructuredText content saved to: {output_path}")
        return parsed_data
    
    except Exception as e:
        print(f"Error extracting RST from {rst_path}: {e}")
        return None

# --- Main execution logic ---
if __name__ == "__main__":
    # Define the SDK versions to process for RST.
    # As per your request, this applies ONLY to V2.00.00 and future versions.
    sdk_versions_to_parse = ["V2.00.00"] 

    for version in sdk_versions_to_parse:
        print(f"\n--- Processing RST Docs for SDK Version: {version} ---")

        # Dynamically set version-specific input and output directories
        # Assuming RST sources are in a '_sources' subfolder within the HTML docs for that version.
        current_rst_source_dir = os.path.join(SDK_RST_SOURCE_BASE_DIR, version, "_sources")
        current_parsed_rst_output_dir = os.path.join(PARSED_RST_OUTPUT_BASE_DIR, version)

        os.makedirs(current_parsed_rst_output_dir, exist_ok=True) # Ensure versioned output directory exists

        if not os.path.exists(current_rst_source_dir):
            print(f"Error: RST source directory '{current_rst_source_dir}' for version {version} not found. Skipping this version.")
            continue # Skip to the next version

        rst_files_found_in_version = False
        processed_count = 0
        # Use os.walk to find all .rst and .rst.txt files in the directory and its subdirectories
        for root, _, files in os.walk(current_rst_source_dir):
            for file_name in files:
                if file_name.lower().endswith((".rst", ".rst.txt")):
                    rst_files_found_in_version = True
                    file_path = os.path.join(root, file_name)
                    print(f"Parsing RST file: {file_path}...")
                    
                    # Call the extraction function for each RST file found
                    # Pass the current version
                    parsed_item = extract_from_rst(file_path, current_parsed_rst_output_dir, version)
                    if parsed_item:
                        processed_count += 1
                    print("=" * 50) # Separator for clearer output between files
        
        if not rst_files_found_in_version:
            print(f"No RST files found in '{current_rst_source_dir}' or its subdirectories for version {version}.")
        else:
            print(f"Finished processing {processed_count} RST files for SDK Version: {version}.")

    print("\nAll specified SDK RST versions processed.")