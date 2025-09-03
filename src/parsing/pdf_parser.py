# src/parsing/pdf_parser.py

import pdfplumber
import pandas as pd
import os
import json
import re

# Get the absolute path to the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- Configuration for PDF Documentation Parsing ---
SDK_PDF_SOURCE_BASE_DIR = os.path.join(PROJECT_ROOT, "data/raw_sdk_docs/docs")
PARSED_PDF_OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/pdf")

def extract_from_pdf(pdf_path, output_dir, sdk_version):
    """
    Extracts text and tables from a PDF document.
    Saves extracted text and tables as JSON files.
    This version includes robust handling for multi-level and complex table headers.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    file_name_raw = os.path.basename(pdf_path)
    file_name = os.path.splitext(file_name_raw)[0]

    all_text = ""
    extracted_tables_data = []

    print(f"Processing PDF: {pdf_path} for SDK version {sdk_version}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    all_text += f"\n--- Page {i+1} ---\n{page_text}\n"

                # Use find_tables to get bounding box information
                tables = page.find_tables()
                if not tables:
                    continue

                print(f"  Found {len(tables)} tables on page {i+1}")
                for table_index, table in enumerate(tables):
                    raw_table = table.extract()
                    if not raw_table or not raw_table[0]:
                        continue

                    # --- ADVANCED: Find text immediately following the table ---
                    table_bbox = table.bbox
                    # Bounding box format: (x0, top, x1, bottom)
                    notes_text = ""
                    # Find words that are below the table
                    words_below_table = [word for word in page.extract_words() if word['top'] > table_bbox[3]]
                    
                    # Heuristically capture the first paragraph of text after the table
                    if words_below_table:
                        first_word_y = words_below_table[0]['top']
                        notes_words = []
                        for word in words_below_table:
                            # Stop if we hit a significant vertical gap (likely a new section)
                            if word['top'] > first_word_y + 20: # 20 points gap
                                break
                            notes_words.append(word['text'])
                        notes_text = " ".join(notes_words)
                    # --- END ADVANCED NOTE FINDING ---

                    # Heuristic to find where the header ends and data begins
                    header_row_count = 0
                    for row_idx, row in enumerate(raw_table):
                        first_cell = str(row[0]).strip() if row and row[0] is not None else ""
                        if first_cell.isdigit():
                            header_row_count = row_idx
                            break
                    
                    if header_row_count == 0 and len(raw_table) > 1:
                        header_row_count = 1
                    
                    header_rows = raw_table[:header_row_count]
                    data_rows = raw_table[header_row_count:]
                    
                    if not header_rows:
                        continue
                    
                    num_cols = len(raw_table[0])

                    # --- ADVANCED HEADER PROCESSING ---
                    # 1. Horizontally propagate headers that span multiple columns
                    propagated_headers = []
                    for h_row in header_rows:
                        # Ensure row is padded to the full table width before processing
                        filled_row = h_row[:] + [None] * (num_cols - len(h_row))
                        last_val = ""
                        for col_idx in range(num_cols):
                            cell_val = filled_row[col_idx]
                            if cell_val is not None and cell_val.strip() != "":
                                last_val = cell_val
                            else:
                                filled_row[col_idx] = last_val
                        propagated_headers.append(filled_row)
                    
                    # 2. Vertically combine the propagated headers
                    final_headers = []
                    for col_idx in range(num_cols):
                        parts = []
                        for row in propagated_headers:
                            if col_idx < len(row) and row[col_idx]:
                                cleaned_part = str(row[col_idx]).replace('\n', ' ').strip()
                                if cleaned_part not in parts: # Avoid duplicating parent headers
                                    parts.append(cleaned_part)
                        
                        full_header = " ".join(parts)
                        # Normalize names like "ILX- LR1" to "ILX-LR1"
                        full_header = re.sub(r'\s+', '', full_header)
                        final_headers.append(full_header)
                    # --- END ADVANCED HEADER PROCESSING ---

                    df = pd.DataFrame(data_rows, columns=final_headers)
                    df.dropna(axis=1, how='all', inplace=True)
                    df.fillna('', inplace=True)
                    
                    extracted_tables_data.append({
                        "page": i + 1,
                        "table_number_on_page": table_index + 1,
                        "data": df.values.tolist(),
                        "headers": df.columns.tolist(),
                        "notes": notes_text # Add the extracted notes here
                    })

        # --- Saving Logic ---
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', file_name)
        version_tag = sdk_version.replace('.', '_')

        text_output_filename = f"{clean_name}_v{version_tag}_text.json"
        text_output_path = os.path.join(output_dir, text_output_filename)
        text_data = {
            "source_file": pdf_path, "file_type": "pdf_text", "content": all_text.strip(),
            "metadata": {"title": file_name, "sdk_version": sdk_version, "extracted_type": "text"}
        }
        with open(text_output_path, "w", encoding="utf-8") as f:
            json.dump(text_data, f, indent=4, ensure_ascii=False)
        print(f"Extracted PDF text saved to: {text_output_path}")

        if extracted_tables_data:
            tables_output_filename = f"{clean_name}_v{version_tag}_tables.json"
            tables_output_path = os.path.join(output_dir, tables_output_filename)
            tables_data = {
                "source_file": pdf_path, "file_type": "pdf_tables", "content": extracted_tables_data,
                "metadata": {"title": file_name, "sdk_version": sdk_version, "extracted_type": "tables", "num_tables": len(extracted_tables_data)}
            }
            with open(tables_output_path, "w", encoding="utf-8") as f:
                json.dump(tables_data, f, indent=4, ensure_ascii=False)
            print(f"Extracted tables saved to: {tables_output_path}")

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

# --- Main execution logic ---
if __name__ == "__main__":
    sdk_versions_to_parse = ["V1.14.00", "V2.00.00"] 

    for version in sdk_versions_to_parse:
        print(f"\n--- Processing PDF Docs for SDK Version: {version} ---")
        current_sdk_pdfs_dir = os.path.join(SDK_PDF_SOURCE_BASE_DIR, version)
        current_parsed_pdf_output_dir = os.path.join(PARSED_PDF_OUTPUT_BASE_DIR, version)
        os.makedirs(current_parsed_pdf_output_dir, exist_ok=True)

        if not os.path.exists(current_sdk_pdfs_dir):
            print(f"Error: PDF source directory '{current_sdk_pdfs_dir}' for version {version} not found. Skipping.")
            continue

        pdf_files_found = False
        processed_count = 0
        for root, _, files in os.walk(current_sdk_pdfs_dir):
            for file_name in files:
                if file_name.lower().endswith(".pdf"):
                    pdf_files_found = True
                    pdf_path = os.path.join(root, file_name)
                    extract_from_pdf(pdf_path, current_parsed_pdf_output_dir, version)
                    processed_count += 1
                    print("=" * 50)
        
        if not pdf_files_found:
            print(f"No PDF files found in '{current_sdk_pdfs_dir}'.")
        else:
            print(f"Finished processing {processed_count} PDF files for SDK Version: {version}.")

    print("\nAll specified SDK PDF versions processed.")