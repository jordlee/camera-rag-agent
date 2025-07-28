# src/parsing/pdf_parser.py

import pdfplumber
import pandas as pd
import os
import json
import re

# Get the absolute path to the project root (where this script is likely run from)
# Assuming pdf_parser.py is in src/parsing/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- Configuration for PDF Documentation Parsing ---
# Base directory where different SDK versions' PDF docs are located
SDK_PDF_SOURCE_BASE_DIR = os.path.join(PROJECT_ROOT, "data/raw_sdk_docs/docs")

# Base directory for parsed PDF output
PARSED_PDF_OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/pdf")

def extract_from_pdf(pdf_path, output_dir, sdk_version):
    """
    Extracts text and tables from a PDF document.
    Saves extracted text and tables as JSON files.

    Args:
        pdf_path (str): The path to the input PDF file.
        output_dir (str): The directory to save the extracted data (version-specific).
        sdk_version (str): The SDK version associated with this PDF file.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the base name of the PDF file (e.g., "startup_guide" from "startup_guide.pdf")
    file_name_raw = os.path.basename(pdf_path)
    file_name = os.path.splitext(file_name_raw)[0]

    all_text = ""
    extracted_tables_data = []

    print(f"Processing PDF: {pdf_path} for SDK version {sdk_version}")
    try:
        # Open the PDF using pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            # Iterate through each page of the PDF
            for i, page in enumerate(pdf.pages):
                # --- Extract Text ---
                page_text = page.extract_text()
                if page_text:
                    # Add page number to help identify text origin
                    all_text += f"\n--- Page {i+1} ---\n"
                    all_text += page_text + "\n"

                # --- Extract Tables ---
                tables = page.extract_tables()
                if tables:
                    print(f"  Found {len(tables)} tables on page {i+1}")
                    for j, table in enumerate(tables):
                        # Convert table to DataFrame and then to a list of lists (for JSON compatibility)
                        df = pd.DataFrame(table[1:], columns=table[0]) # Assuming first row is header
                        extracted_tables_data.append({
                            "page": i + 1,
                            "table_number_on_page": j + 1,
                            "data": df.values.tolist(), # Convert to list of lists for JSON
                            "headers": df.columns.tolist() # Store headers separately
                        })

        # Sanitize filename and append version for uniqueness
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', file_name)
        version_tag = sdk_version.replace('.', '_')

        # Save extracted text
        text_output_filename = f"{clean_name}_v{version_tag}_text.json"
        text_output_path = os.path.join(output_dir, text_output_filename)
        text_data = {
            "source_file": pdf_path,
            "file_type": "pdf_text",
            "content": all_text.strip(),
            "metadata": {
                "title": file_name,
                "sdk_version": sdk_version,
                "extracted_type": "text"
            }
        }
        with open(text_output_path, "w", encoding="utf-8") as f:
            json.dump(text_data, f, indent=4, ensure_ascii=False)
        print(f"Extracted PDF text saved to: {text_output_path}")

        # Save extracted tables if any
        if extracted_tables_data:
            tables_output_filename = f"{clean_name}_v{version_tag}_tables.json"
            tables_output_path = os.path.join(output_dir, tables_output_filename)
            tables_data = {
                "source_file": pdf_path,
                "file_type": "pdf_tables",
                "content": extracted_tables_data, # List of table dicts
                "metadata": {
                    "title": file_name,
                    "sdk_version": sdk_version,
                    "extracted_type": "tables",
                    "num_tables": len(extracted_tables_data)
                }
            }
            with open(tables_output_path, "w", encoding="utf-8") as f:
                json.dump(tables_data, f, indent=4, ensure_ascii=False)
            print(f"Extracted tables saved to: {tables_output_path}")

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

# --- Main execution logic ---
if __name__ == "__main__":
    # Define the SDK versions to process
    # Include all versions that might have PDF documentation
    sdk_versions_to_parse = ["V1.14.00", "V2.00.00"] 

    for version in sdk_versions_to_parse:
        print(f"\n--- Processing PDF Docs for SDK Version: {version} ---")

        # Dynamically set version-specific input and output directories
        current_sdk_pdfs_dir = os.path.join(SDK_PDF_SOURCE_BASE_DIR, version)
        current_parsed_pdf_output_dir = os.path.join(PARSED_PDF_OUTPUT_BASE_DIR, version)

        os.makedirs(current_parsed_pdf_output_dir, exist_ok=True) # Ensure versioned output directory exists

        if not os.path.exists(current_sdk_pdfs_dir):
            print(f"Error: PDF source directory '{current_sdk_pdfs_dir}' for version {version} not found. Skipping this version.")
            continue # Skip to the next version

        pdf_files_found_in_version = False
        processed_count = 0
        # Use os.walk to find all .pdf files in the directory and its subdirectories
        for root, _, files in os.walk(current_sdk_pdfs_dir):
            for file_name in files:
                if file_name.lower().endswith(".pdf"):
                    pdf_files_found_in_version = True
                    pdf_path = os.path.join(root, file_name)
                    
                    # Call the extraction function for each PDF file found
                    # Pass the current version
                    extract_from_pdf(pdf_path, current_parsed_pdf_output_dir, version)
                    processed_count += 1
                    print("=" * 50) # Separator for clearer output between files
        
        if not pdf_files_found_in_version:
            print(f"No PDF files found in '{current_sdk_pdfs_dir}' or its subdirectories for version {version}.")
        else:
            print(f"Finished processing {processed_count} PDF files for SDK Version: {version}.")

    print("\nAll specified SDK PDF versions processed.")