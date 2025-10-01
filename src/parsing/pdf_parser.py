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


def format_version_tag(sdk_version):
    """Convert SDK version to friendly format: V2.00.00 -> V2"""
    if sdk_version.startswith('V'):
        major = sdk_version.split('.')[0]  # "V2.00.00" -> "V2"
        return major
    return sdk_version


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
                    # Special handling for multi-line camera model headers
                    # These appear as separate cells but are actually one camera name split across lines
                    final_headers = []

                    # First, reconstruct camera names from multi-line cells in header rows
                    if header_row_count > 0:
                        # Combine all header rows to reconstruct full names
                        for col_idx in range(num_cols):
                            header_parts = []
                            for h_row in header_rows:
                                if col_idx < len(h_row) and h_row[col_idx] is not None:
                                    part = str(h_row[col_idx]).strip()
                                    if part:
                                        header_parts.append(part)

                            if header_parts:
                                # Join parts and clean up newlines
                                full_header = "".join(header_parts).replace('\n', '')
                                # Clean up spaces in camera model names
                                if any(model in full_header for model in ['ILX', 'ILCE', 'ILME', 'ZV', 'HXR', 'PXW', 'MPC']):
                                    full_header = full_header.replace(' ', '')
                            else:
                                full_header = ""

                            final_headers.append(full_header)

                    # Extract only the actual data columns, preserving real values
                    # Camera data appears every 3rd column starting from position 5: 5, 8, 11, 14, etc.
                    # Positions 6, 7, 9, 10, 12, 13, etc. are None artifacts from multi-line header splitting

                    merged_headers = []
                    merged_data_rows = []

                    # Build correct headers: first 4 columns (No., APIs, Outline, Mode)
                    for i in range(min(4, len(final_headers))):
                        merged_headers.append(final_headers[i])

                    # Detect column pattern: consecutive vs every-3rd
                    camera_positions = []
                    camera_headers_found = []

                    # Check if cameras are in consecutive positions starting from 4
                    # Allow for gaps but stop after a significant gap (more than 3 empty columns)
                    consecutive_cameras = []
                    last_camera_pos = -1
                    gap_count = 0

                    for pos in range(4, len(final_headers)):
                        header = final_headers[pos]
                        if header and header.strip() and any(model in header for model in ['ILX', 'ILCE', 'ILME', 'ZV', 'HXR', 'PXW', 'MPC', 'DSC']):
                            consecutive_cameras.append((pos, header))
                            last_camera_pos = pos
                            gap_count = 0  # Reset gap counter
                        elif len(consecutive_cameras) > 0:
                            gap_count += 1
                            # Stop if we hit a significant gap (more than 3 positions) after finding cameras
                            if gap_count > 3:
                                break

                    # Check if cameras are in every-3rd positions - try different starting positions
                    every_third_cameras = []

                    # Try starting from positions 5, 6, 7, 8 to find the best every-3rd pattern
                    best_every_third = []
                    for start_pos in range(5, 9):
                        current_pattern = []
                        for pos in range(start_pos, len(final_headers), 3):
                            if pos < len(final_headers):
                                header = final_headers[pos]
                                if header and header.strip() and any(model in header for model in ['ILX', 'ILCE', 'ILME', 'ZV', 'HXR', 'PXW', 'MPC', 'DSC']):
                                    current_pattern.append((pos, header))

                        # Keep the pattern that finds the most cameras
                        if len(current_pattern) > len(best_every_third):
                            best_every_third = current_pattern

                    every_third_cameras = best_every_third

                    # Choose the pattern that found more cameras
                    if len(consecutive_cameras) > len(every_third_cameras):
                        camera_headers_found = consecutive_cameras
                        print(f"  Using consecutive column pattern: found {len(consecutive_cameras)} cameras")
                    else:
                        camera_headers_found = every_third_cameras
                        print(f"  Using every-3rd column pattern: found {len(every_third_cameras)} cameras")

                    # Add camera headers and positions
                    for pos, header in camera_headers_found:
                        merged_headers.append(header)
                        camera_positions.append(pos)

                    # Determine which pattern to use for data extraction
                    using_consecutive_pattern = len(consecutive_cameras) > len(every_third_cameras)

                    # Extract data using the same pattern
                    for row in data_rows:
                        merged_row = []

                        # First 4 columns (No., APIs, Outline, Mode)
                        for i in range(min(4, len(row))):
                            merged_row.append(row[i] if row[i] is not None else "")

                        # Camera column data extraction - pattern depends on how headers were found
                        for header_pos in camera_positions:
                            # For consecutive pattern, data is at the same position as header
                            # For every-3rd pattern, data is one position before the header
                            if using_consecutive_pattern:
                                # Consecutive pattern: data at same position as header
                                data_pos = header_pos
                            else:
                                # Every-3rd pattern: data one position before header
                                data_pos = header_pos - 1

                            if data_pos < len(row):
                                value = row[data_pos]
                                # Preserve the actual value: "" for compatible, "-" for incompatible, None becomes ""
                                if value is None:
                                    merged_row.append("")
                                else:
                                    merged_row.append(value)
                            else:
                                merged_row.append("")

                        merged_data_rows.append(merged_row)

                    final_headers = merged_headers
                    data_rows = merged_data_rows
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
        version_tag = format_version_tag(sdk_version)

        text_output_filename = f"{clean_name}_{version_tag}_text.json"
        text_output_path = os.path.join(output_dir, text_output_filename)
        text_data = {
            "source_file": pdf_path, "file_type": "pdf_text", "content": all_text.strip(),
            "metadata": {"title": file_name, "sdk_version": sdk_version, "extracted_type": "text"}
        }
        with open(text_output_path, "w", encoding="utf-8") as f:
            json.dump(text_data, f, indent=4, ensure_ascii=False)
        print(f"Extracted PDF text saved to: {text_output_path}")

        if extracted_tables_data:
            tables_output_filename = f"{clean_name}_{version_tag}_tables.json"
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