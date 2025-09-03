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
    CSV files are parsed into a structured format (headers and data lists).
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
            
            # Use pandas to read the CSV, trying different separators if needed
            try:
                df = pd.read_csv(filepath)
            except pd.errors.ParserError:
                df = pd.read_csv(filepath, sep='\t', engine='python')
            
            # Handle NaN values first
            df.fillna('not-compatible', inplace=True)
            
            # Comprehensive replacement for all compatibility indicators
            replacements = {
                '': 'not-compatible',        # Empty strings
                '\\-': 'not-compatible',    # Escaped dashes (not applicable)
                '\-': 'not-compatible',      # Simple dashes (not applicable)
                '-': 'not-compatible',       # Plain dashes
                '✔': 'is-compatible',        # Checkmarks
                'YES': 'is-compatible',      # Explicit YES
                'Yes': 'is-compatible',      # Capitalized Yes
                'yes': 'is-compatible',      # Lowercase yes
                'NO': 'not-compatible',      # Explicit NO
                'No': 'not-compatible',      # Capitalized No
                'no': 'not-compatible'       # Lowercase no
            }
            
            # Apply all replacements
            df.replace(replacements, inplace=True)

            # Save the headers and data rows into the 'content' field as a list containing one table object
            extracted_content["content"] = [{
                "page": 1, # Default page 1 for CSVs
                "data": df.values.tolist(),
                "headers": df.columns.tolist()
            }]
            extracted_content["metadata"]["num_rows"] = len(df)
            extracted_content["metadata"]["num_columns"] = len(df.columns)
        
        elif filepath.lower().endswith('.txt'):
            extracted_content["file_type"] = "text"
            extracted_content["content"] = open(filepath, 'r', encoding='utf-8').read().strip()
        else:
            return None

        # Create a clean filename and save the JSON output
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
    sdk_versions_to_parse = ["V2.00.00"] 

    for version in sdk_versions_to_parse:
        print(f"\n--- Processing Text/CSV Docs for SDK Version: {version} ---")

        # Dynamically set version-specific input and output directories
        current_text_source_dir = os.path.join(SDK_TEXT_SOURCE_BASE_DIR, version, "_static")
        current_parsed_text_output_dir = os.path.join(PARSED_TEXT_OUTPUT_BASE_DIR, version)

        os.makedirs(current_parsed_text_output_dir, exist_ok=True)

        if not os.path.exists(current_text_source_dir):
            print(f"Error: Text/CSV source directory '{current_text_source_dir}' for version {version} not found. Skipping this version.")
            continue

        text_files_found_in_version = False
        processed_count = 0
        for root, _, files in os.walk(current_text_source_dir):
            for file_name in files:
                if file_name.lower().endswith((".txt", ".csv")) and not file_name.lower().endswith(".inv"):
                    text_files_found_in_version = True
                    file_path = os.path.join(root, file_name)
                    print(f"Processing file: {file_path}...")
                    
                    parsed_item = extract_from_text(file_path, current_parsed_text_output_dir, version)
                    if parsed_item:
                        processed_count += 1
                    print("=" * 50)
        
        if not text_files_found_in_version:
            print(f"No .txt or .csv files found (excluding .inv files) in '{current_text_source_dir}' or its subdirectories for version {version}.")
        else:
            print(f"Finished processing {processed_count} text/csv files for SDK Version: {version}.")

    print("\nAll specified SDK text/csv versions processed.")