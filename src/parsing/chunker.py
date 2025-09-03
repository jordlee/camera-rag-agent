# src/parsing/chunker.py

import os
import json
from pathlib import Path
import hashlib
import re

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
PARSED_DATA_DIR = PROJECT_ROOT / "data/parsed_data"
OUTPUT_FILE = PROJECT_ROOT / "data/context.json"

# --- Chunking Strategy Configuration ---
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100 

# Define common boilerplate strings to remove
BOILERPLATE_PATTERNS = [
    r"Information EditSDKInfo Contents Transfer GetDateFolderList GetContentsHandleList GetContentsDetailInfo ReleaseDateFolderList ReleaseContentsHandleList PullContentsFile GetContentsThumbnailImage Contents Transfer with remote control GetRemoteTransferCapturedDateList GetRemoteTransferContentsInfoList GetRemoteTransferContentsData GetRemoteTransferContentsDataFile ControlGetRemoteTransferContentsDataFile GetRemoteTransferContentsCompressedData GetRemoteTransferContentsCompressedDataFile",
    r"Camera Remote SDK API Reference \d+\.\d+\.\d+ documentation",
    r"1\.13\.00, added new openMode parameter “RemoteTransfer”",
]


def create_chunk_id(content: str, parent_id: str, index: int) -> str:
    """Creates a unique, repeatable ID for a chunk."""
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{parent_id}_{index}_{content_hash}"

def _sanitize_metadata_value(value):
    """
    Sanitizes a metadata value to ensure it's a type acceptable by ChromaDB:
    str, int, float, or bool.
    """
    if value is None:
        return ""
    elif isinstance(value, (bool, int, float, str)):
        return value
    else:
        return str(value)

def split_content(text: str, parent_id: str) -> list[dict]:
    """
    Splits content using a sliding window with overlap.
    """
    cleaned_text = text
    for pattern in BOILERPLATE_PATTERNS:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE).strip()
    
    if not cleaned_text or len(cleaned_text) < 50:
        return []

    chunks = []
    start = 0
    while start < len(cleaned_text):
        end = start + CHUNK_SIZE
        chunk_content = cleaned_text[start:end]
        
        chunks.append({"id": create_chunk_id(chunk_content, parent_id, len(chunks)), "content": chunk_content})
        
        start += CHUNK_SIZE - CHUNK_OVERLAP
        
    return chunks

def chunk_api_file(data: dict) -> list:
    """Chunks a JSON file from cpp_parser.py (classes, namespaces, etc.)."""
    chunks = []
    parent_metadata = data.get("metadata", {}) 
    
    source_file = data.get("source_file", "")
    entity_name = data.get("name", "")
    unique_identifier = f"{source_file}_{entity_name}"
    parent_id_base = hashlib.md5(unique_identifier.encode()).hexdigest()
    
    main_description = (
        f"API Definition: {data.get('name', '')} ({data.get('kind', '')})\n\n"
        f"Description: {data.get('brief_description', '')}\n\n"
        f"Details: {data.get('detailed_description', '')}"
    ).strip()
    
    if len(main_description) > 50:
        split_chunks = split_content(main_description, f"{parent_id_base}_summary")
        for chunk_data in split_chunks:
            chunk_metadata = {
                **parent_metadata, "source_file": data.get("source_file", ""),
                "type": "summary", "parent_name": data.get('name', '')
            }
            chunks.append({
                "id": chunk_data["id"], "content": chunk_data["content"],
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    for i, member in enumerate(data.get("members", [])):
        content = (
            f"API Member: {member.get('name', '')} in {data.get('name', '')}\n"
            f"Kind: {member.get('kind', '')}\n"
            f"Definition: {member.get('definition', '')}{member.get('argsstring', '')}\n\n"
            f"Description: {member.get('brief_description', '')}\n\n"
            f"Details: {member.get('detailed_description', '')}"
        ).strip()

        split_chunks = split_content(content, f"{parent_id_base}_member_{i}")
        for chunk_data in split_chunks:
            chunk_metadata = {
                **parent_metadata, "source_file": member.get("location", data.get("source_file", "")),
                "type": member.get("kind", "member"), "member_name": member.get("name", ""),
                "parent_name": data.get('name', '')
            }
            chunks.append({
                "id": chunk_data["id"], "content": chunk_data["content"],
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })
        
    return chunks

def chunk_example_file(data: dict) -> list:
    """Chunks a JSON file from example_parser.py."""
    chunks = []
    parent_metadata = data.get("metadata", {}) 
    parent_id_base = hashlib.md5(data.get("name", "").encode()).hexdigest()
    all_snippets = data.get("functions", []) + data.get("other_snippets", [])
    
    for i, snippet in enumerate(all_snippets):
        content = (
            f"Example Snippet: {snippet.get('name', '')}\n"
            f"From Example: {data.get('name')}\n"
            f"Source File: {snippet.get('source_file', '')}\n\n"
            f"// {snippet.get('brief_comment', '')}\n"
            f"{snippet.get('code', '')}"
        ).strip()

        split_chunks = split_content(content, f"{parent_id_base}_snippet_{i}")
        for chunk_data in split_chunks:
            chunk_metadata = {
                **parent_metadata, "source_file": snippet.get("source_file", ""),
                "start_line": snippet.get("start_line", 0), "type": "example_code",
                "snippet_name": snippet.get("name", "")
            }
            chunks.append({
                "id": chunk_data["id"], "content": chunk_data["content"],
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })
        
    return chunks

def extract_page_number(content: str) -> int:
    """Extract page number from content containing '--- Page N ---' markers."""
    import re
    match = re.search(r'--- Page (\d+) ---', content)
    if match:
        return int(match.group(1))
    return 0

def chunk_text_file(data: dict) -> list:
    """Chunks plain text-based documents by splitting into paragraphs."""
    chunks = []
    parent_metadata = data.get("metadata", {}) 
    source_file = data.get("source_file", "")
    source_filename = Path(source_file).name if source_file else ""
    parent_id_base = hashlib.md5(source_file.encode()).hexdigest()
    
    text_blocks = data.get("content", "").split('\n\n')
    
    for i, block in enumerate(text_blocks):
        clean_block = block.strip()
        if not clean_block:
            continue
            
        # Extract page number from the block content
        page_number = extract_page_number(clean_block)
        
        split_chunks = split_content(clean_block, f"{parent_id_base}_block_{i}")
        for chunk_data in split_chunks:
            chunk_metadata = {
                **parent_metadata, "source_file": source_filename,
                "type": "documentation_text",
                "page": page_number
            }
            chunks.append({
                "id": chunk_data["id"], "content": chunk_data["content"],
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })
    return chunks

def chunk_example_file(data: dict) -> list:
    """Chunks an example file containing code snippets."""
    chunks = []
    parent_metadata = data.get("metadata", {})
    
    source_file = data.get("filepath", data.get("name", ""))
    parent_id_base = hashlib.md5(source_file.encode()).hexdigest()
    
    # Process functions with examples
    for func in data.get("functions", []):
        func_name = func.get("name", "unknown")
        for i, example in enumerate(func.get("examples", [])):
            code = example.get("code", "")
            if code and len(code) > 50:
                split_chunks = split_content(code, f"{parent_id_base}_func_{func_name}_{i}")
                for chunk_data in split_chunks:
                    chunk_metadata = {
                        **parent_metadata,
                        "source_file": source_file,
                        "type": "example_code",
                        "function_name": func_name
                    }
                    chunks.append({
                        "id": chunk_data["id"],
                        "content": chunk_data["content"],
                        "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
                    })
    
    # Process other code snippets
    for i, snippet in enumerate(data.get("other_snippets", [])):
        code = snippet.get("code", "")
        if code and len(code) > 50:
            split_chunks = split_content(code, f"{parent_id_base}_snippet_{i}")
            for chunk_data in split_chunks:
                chunk_metadata = {
                    **parent_metadata,
                    "source_file": source_file,
                    "type": "example_code"
                }
                chunks.append({
                    "id": chunk_data["id"],
                    "content": chunk_data["content"],
                    "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
                })
    
    return chunks

def chunk_structured_table_file(data: dict) -> list:
    """
    Chunks structured table data (from PDFs, CSVs) by creating a separate chunk
    for each row and appending any associated notes/footnotes.
    """
    chunks = []
    parent_metadata = data.get("metadata", {}) 
    source_file = data.get("source_file", "")
    source_filename = Path(source_file).name if source_file else ""
    parent_id_base = hashlib.md5(source_file.encode()).hexdigest()
    
    for i, table in enumerate(data.get("content", [])):
        headers = table.get("headers", [])
        table_data = table.get("data", [])
        notes = table.get("notes", "") # Get the notes for this table, if they exist
        
        header_str = " | ".join(str(h) for h in headers if h is not None)
        
        for row_index, row in enumerate(table_data):
            # Replace YES/NO and other indicators with context-aware semantic equivalents
            processed_row = []
            for col_index, cell in enumerate(row):
                cell_str = str(cell).strip()
                
                # Get column header to determine context
                col_header = headers[col_index] if col_index < len(headers) else ""
                
                # Context-aware replacements
                if cell_str in ['', '✔']:  # Empty or checkmark
                    if col_header == 'Mode':
                        processed_row.append('not-applicable')  # For Mode column
                    else:
                        processed_row.append('is-compatible')  # For camera model columns
                elif cell_str in ['\\-', '\\\\-', '-']:  # Various dash formats
                    if col_header == 'Mode':
                        processed_row.append('not-applicable')  # For Mode column
                    else:
                        processed_row.append('not-compatible')  # For camera model columns
                elif cell_str.upper() in ['YES', 'Y']:
                    processed_row.append('is-compatible')
                elif cell_str.upper() in ['NO', 'N']:
                    processed_row.append('not-compatible')
                elif cell_str in ['nan', 'NaN', 'None']:  # Handle stringified NaN values
                    if col_header == 'Mode':
                        processed_row.append('not-applicable')
                    else:
                        processed_row.append('not-compatible')
                else:
                    processed_row.append(cell_str)
            row_str = " | ".join(processed_row)
            
            content = (
                f"Table from: {parent_metadata.get('title', 'N/A')}\n"
                f"Headers: {header_str}\n"
                f"Row: {row_str}"
            ).strip()

            # Append the notes to the chunk content if they exist
            if notes:
                content += f"\n---\nNotes for this table:\n{notes}"

            chunk_id = create_chunk_id(content, f"{parent_id_base}_table_{i}", row_index)
            
            page_value = table.get("page", 0)
            if not isinstance(page_value, (int, float)):
                page_value = 0
            
            chunk_metadata = {
                **parent_metadata,
                "source_file": source_filename,
                "page": int(page_value), 
                "type": "documentation_table"
            }
            chunks.append({
                "id": chunk_id, "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })
            
    return chunks

def main():
    """Main function to find, process, and chunk files."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Chunk parsed SDK documentation')
    parser.add_argument('--version', type=str, default=None, 
                       help='SDK version to process (e.g., V1.14.00, V2.00.00). If not specified, processes all versions.')
    parser.add_argument('--output', type=str, default='context.json',
                       help='Output filename (default: context.json)')
    args = parser.parse_args()
    
    output_file = PROJECT_ROOT / "data" / args.output
    
    all_chunks = []
    json_files = list(PARSED_DATA_DIR.rglob("*.json"))
    
    processed_entities = set()
    
    print(f"Found {len(json_files)} JSON files to process in {PARSED_DATA_DIR}.")
    if args.version:
        print(f"Filtering for version {args.version} only.")
    else:
        print("Processing all versions.")

    for file_path in json_files:
        try:
            # Filter by version if specified
            if args.version and args.version not in str(file_path):
                continue
                
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            data["metadata"] = {k: _sanitize_metadata_value(v) for k, v in data.get("metadata", {}).items()}
            
            entity_name = data.get("name")
            # Extract version from file path
            sdk_version = None
            if "V1.14.00" in str(file_path):
                sdk_version = "1.14.00"
            elif "V2.00.00" in str(file_path):
                sdk_version = "2.00.00"
            
            if entity_name and sdk_version:
                unique_entity_key = (entity_name, sdk_version)
                if unique_entity_key in processed_entities:
                    print(f"  [INFO] Skipping '{file_path.name}', entity '{entity_name}' for v{sdk_version} already processed.")
                    continue
            
            file_type = data.get("file_type")
            chunks = []
            
            # Process different file types
            if file_type in ["html", "markdown", "rst", "text", "pdf_text"]:
                chunks = chunk_text_file(data)
                print(f"  [Text] Chunked '{file_path.name}' into {len(chunks)} chunks.")
            elif file_type in ["pdf_tables", "csv"]:
                chunks = chunk_structured_table_file(data)
                print(f"  [Table] Chunked '{file_path.name}' into {len(chunks)} chunks.")
            elif data.get("kind") in ["class", "struct", "namespace", "file"]:
                # Process C++ API files
                chunks = chunk_api_file(data)
                print(f"  [API] Chunked '{file_path.name}' into {len(chunks)} chunks.")
            elif "examples" in str(file_path) and ("functions" in data or "other_snippets" in data):
                # Process example files
                chunks = chunk_example_file(data)
                print(f"  [Examples] Chunked '{file_path.name}' into {len(chunks)} chunks.")
            else:
                # Skip unrecognized file types
                continue

            if entity_name and sdk_version and chunks:
                processed_entities.add(unique_entity_key)
            
            all_chunks.extend(chunks)
            
        except json.JSONDecodeError:
            print(f"  [ERROR] Could not decode JSON from {file_path}. Skipping.")
        except Exception as e:
            print(f"  [ERROR] An unexpected error occurred with {file_path}: {e}")

    print(f"\nTotal chunks created: {len(all_chunks)}")

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)
        
    print(f"Successfully saved {len(all_chunks)} chunks to {output_file}")

if __name__ == "__main__":
    main()