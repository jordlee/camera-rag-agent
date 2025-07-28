# src/parsing/text_parser.py

import os
import json
import pandas as pd
import numpy as np # Import numpy for potential NaN handling
import re

# Get the absolute path to the project root (where this script is likely run from)
# Assuming text_parser.py is in src/parsing/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- Configuration for Text/CSV Documentation Parsing ---
# Base directory where different SDK versions' text/CSV docs are located.
# Assuming these are found in '_static' subfolder within the HTML documentation base directory.
SDK_TEXT_SOURCE_BASE_DIR = os.path.join(PROJECT_ROOT, "data/raw_sdk_docs/api_docs_html")

# Base directory for parsed Text/CSV output
PARSED_TEXT_OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/text")


def extract_from_text(filepath, output_dir, sdk_version):
    """
    Extracts content from plain text (.txt) and CSV (.csv) files.
    CSV files are converted to a Markdown table string for better readability by LLMs.

    Args:
        filepath (str): The path to the input text or CSV file.
        output_dir (str): The directory to save the extracted data (version-specific).
        sdk_version (str): The SDK version associated with this text/CSV file.

    Returns:
        dict: A dictionary containing the extracted content and metadata.
              Returns None if parsing fails.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    file_name_base = os.path.basename(filepath).split('.')[0]

    extracted_content = {
        "source_file": filepath,
        "file_type": "", # Will be 'text' or 'csv'
        "content": "",
        "metadata": {
            "title": file_name_base,
            "sdk_version": sdk_version
        }
    }
    try:
        if filepath.lower().endswith('.csv'):
            extracted_content["file_type"] = "csv"
            print(f"  Attempting to parse CSV: {filepath}")
            df = None
            
            # --- Try parsing with different delimiters and engines ---
            try:
                # 1. Try comma-separated (default)
                df = pd.read_csv(filepath)
            except pd.errors.ParserError as e_comma:
                print(f"    CSV parsing with comma failed for {filepath}: {e_comma}")
                try:
                    # 2. Try tab-separated (TSV) with python engine for robustness
                    df = pd.read_csv(filepath, sep='\t', engine='python')
                    print(f"    Successfully parsed as TSV.")
                except pd.errors.ParserError as e_tab:
                    print(f"    CSV parsing with tab failed for {filepath}: {e_tab}")
                    # Fallback if both fail, try reading as plain text
                    print(f"    Falling back to reading {filepath} as plain text.")
                    with open(filepath, 'r', encoding='utf-8') as f:
                        extracted_content["content"] = f.read().strip()
                    df = None # Ensure df is None if not successfully parsed as CSV
            
            if df is not None:
                # Replace NaN with empty string for cleaner Markdown output
                df = df.replace(np.nan, '', regex=True)
                # Convert DataFrame to Markdown table string
                extracted_content["content"] = df.to_markdown(index=False)
                extracted_content["metadata"]["num_rows"] = len(df)
                extracted_content["metadata"]["num_columns"] = len(df.columns)
        
        elif filepath.lower().endswith('.txt'):
            extracted_content["file_type"] = "text"
            with open(filepath, 'r', encoding='utf-8') as f:
                extracted_content["content"] = f.read().strip()
        else:
            print(f"Skipping unsupported file type: {filepath}")
            return None

        # Create a clean filename from the base name and include version
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', file_name_base)
        version_tag = sdk_version.replace('.', '_')
        output_json_filename = f"{clean_name}_v{version_tag}_parsed.json"
        
        output_path = os.path.join(output_dir, output_json_filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(extracted_content, f, indent=4, ensure_ascii=False)
        print(f"Extracted content saved to: {output_path}")

        return extracted_content
    except Exception as e:
        print(f"Error parsing text/csv {filepath}: {e}")
        return None

# --- Main execution logic ---
if __name__ == "__main__":
    # Define the SDK versions to process for Text/CSV.
    # As per your request, this applies ONLY to V2.00.00 and future versions.
    sdk_versions_to_parse = ["V2.00.00"] 

    for version in sdk_versions_to_parse:
        print(f"\n--- Processing Text/CSV Docs for SDK Version: {version} ---")

        # Dynamically set version-specific input and output directories
        # Assuming Text/CSV files are in a '_static' subfolder within the HTML docs for that version.
        current_text_source_dir = os.path.join(SDK_TEXT_SOURCE_BASE_DIR, version, "_static")
        current_parsed_text_output_dir = os.path.join(PARSED_TEXT_OUTPUT_BASE_DIR, version)

        os.makedirs(current_parsed_text_output_dir, exist_ok=True) # Ensure versioned output directory exists

        if not os.path.exists(current_text_source_dir):
            print(f"Error: Text/CSV source directory '{current_text_source_dir}' for version {version} not found. Skipping this version.")
            continue # Skip to the next version

        text_files_found_in_version = False
        processed_count = 0
        # Use os.walk to find all .txt and .csv files in the directory and its subdirectories
        for root, _, files in os.walk(current_text_source_dir):
            for file_name in files:
                # Exclude Doxygen's .inv (inventory) files which are binary/special
                if file_name.lower().endswith((".txt", ".csv")) and not file_name.lower().endswith(".inv"):
                    text_files_found_in_version = True
                    file_path = os.path.join(root, file_name)
                    print(f"Processing file: {file_path}...")
                    
                    # Call the extraction function for each file found
                    # Pass the current version
                    parsed_item = extract_from_text(file_path, current_parsed_text_output_dir, version)
                    if parsed_item:
                        processed_count += 1
                    print("=" * 50) # Separator for clearer output between files
        
        if not text_files_found_in_version:
            print(f"No .txt or .csv files found (excluding .inv files) in '{current_text_source_dir}' or its subdirectories for version {version}.")
        else:
            print(f"Finished processing {processed_count} text/csv files for SDK Version: {version}.")

    print("\nAll specified SDK text/csv versions processed.")