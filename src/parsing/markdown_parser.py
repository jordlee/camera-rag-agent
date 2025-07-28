# src/parsing/markdown_parser.py

import os
import json
import re

# Get the absolute path to the project root (where this script is likely run from)
# Assuming markdown_parser.py is in src/parsing/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- Configuration for Markdown Documentation Parsing ---
# Base directory where different SDK versions' Markdown docs are located
SDK_MARKDOWN_SOURCE_BASE_DIR = os.path.join(PROJECT_ROOT, "data/raw_sdk_docs/docs")

# Base directory for parsed Markdown output
PARSED_MARKDOWN_OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/markdown")


def extract_from_markdown(md_path, output_dir, sdk_version):
    """
    Extracts text content from a Markdown (.md) file and saves it as a JSON.

    Args:
        md_path (str): The path to the input Markdown file.
        output_dir (str): The directory to save the extracted data (version-specific).
        sdk_version (str): The SDK version associated with this Markdown file.

    Returns:
        dict: A dictionary containing the extracted text content and metadata.
              Returns None if parsing fails.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the base name of the Markdown file without extension
    file_name_raw = os.path.basename(md_path)
    file_name = os.path.splitext(file_name_raw)[0] # "README.md" -> "README"

    full_text = ""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        # Markdown is already largely plain text. For RAG, often the raw markdown is good
        # as it preserves formatting (headings, lists, code blocks) that LLMs can interpret.
        # You could use a library like 'markdown' or 'mistune' to render to plain text
        # if you want, but for baseline RAG, just reading the raw text is usually enough.

        # Create a clean filename from the original filename and include version
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', file_name)
        version_tag = sdk_version.replace('.', '_')
        output_json_filename = f"{clean_name}_md_v{version_tag}_parsed.json"

        output_path = os.path.join(output_dir, output_json_filename)

        parsed_data = {
            "source_file": md_path,
            "file_type": "markdown",
            "content": full_text.strip(),
            "metadata": {
                "title": file_name, # Use filename as a default title
                "sdk_version": sdk_version
            }
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=4, ensure_ascii=False)
        
        print(f"Extracted Markdown data saved to: {output_path}")
        return parsed_data # Return the dict for main loop tracking if needed
    
    except Exception as e:
        print(f"Error extracting Markdown from {md_path}: {e}")
        return None

# --- Main execution logic ---
if __name__ == "__main__":
    # Define the SDK versions to process
    sdk_versions_to_parse = ["V1.14.00", "V2.00.00"] # Adjust this list based on your actual data

    for version in sdk_versions_to_parse:
        print(f"\n--- Processing Markdown Docs for SDK Version: {version} ---")

        # Dynamically set version-specific input and output directories
        current_markdown_source_dir = os.path.join(SDK_MARKDOWN_SOURCE_BASE_DIR, version)
        current_parsed_md_output_dir = os.path.join(PARSED_MARKDOWN_OUTPUT_BASE_DIR, version)

        os.makedirs(current_parsed_md_output_dir, exist_ok=True) # Ensure versioned output directory exists

        if not os.path.exists(current_markdown_source_dir):
            print(f"Error: Markdown source directory '{current_markdown_source_dir}' for version {version} not found. Skipping this version.")
            continue # Skip to the next version

        md_files_found_in_version = False
        processed_count = 0
        # Use os.walk to find all .md files in the directory and its subdirectories
        for root, _, files in os.walk(current_markdown_source_dir):
            for file_name in files:
                if file_name.lower().endswith((".md", ".txt")): # Include .txt as well if needed for generic text docs
                    md_files_found_in_version = True
                    file_path = os.path.join(root, file_name)
                    print(f"Parsing Markdown file: {file_path}...")
                    
                    # Call the extraction function for each Markdown/text file found
                    # Pass the current version to be included in metadata and filename
                    parsed_item = extract_from_markdown(file_path, current_parsed_md_output_dir, version)
                    if parsed_item:
                        processed_count += 1
                    print("=" * 50) # Separator for clearer output between files
        
        if not md_files_found_in_version:
            print(f"No Markdown/text files found in '{current_markdown_source_dir}' or its subdirectories for version {version}.")
        else:
            print(f"Finished processing {processed_count} Markdown/text files for SDK Version: {version}.")

    print("\nAll specified SDK Markdown versions processed.")