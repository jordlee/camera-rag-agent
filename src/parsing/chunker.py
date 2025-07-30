# src/parsing/chunker.py

import os
import json
from pathlib import Path
import hashlib
import textwrap

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
PARSED_DATA_DIR = PROJECT_ROOT / "data/parsed_data"
OUTPUT_FILE = PROJECT_ROOT / "data/chunks.json"

# Set a character limit to avoid exceeding model token limits.
# 1 token is ~4 chars. Model limit is 3072 tokens. We use a safe character limit.
MAX_CHAR_LENGTH = 500

def create_chunk_id(content: str, parent_id: str, index: int) -> str:
    """Creates a unique, repeatable ID for a chunk."""
    # Use a hash of the content plus an index to ensure uniqueness
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{parent_id}_{index}_{content_hash}"

def split_content(text: str, parent_id: str) -> list[dict]:
    """
    Splits content if it's too long, returning a list of dictionaries 
    with id and content keys.
    """
    if len(text) <= MAX_CHAR_LENGTH:
        return [{"id": create_chunk_id(text, parent_id, 0), "content": text}]

    print(f"  [INFO] Splitting oversized chunk from parent {parent_id}...")
    # Use textwrap to split the text into smaller chunks at word boundaries
    wrapper = textwrap.TextWrapper(width=MAX_CHAR_LENGTH, break_long_words=True, replace_whitespace=False)
    wrapped_text = wrapper.wrap(text)
    
    return [{"id": create_chunk_id(chunk, parent_id, i), "content": chunk} for i, chunk in enumerate(wrapped_text)]

def _sanitize_metadata_value(value):
    """
    Sanitizes a metadata value to ensure it's a type acceptable by ChromaDB:
    str, int, float, or bool. Converts problematic types or None to appropriate defaults.
    """
    if value is None:
        return "" # Default None to empty string
    elif isinstance(value, (bool, int, float, str)):
        return value # Already an acceptable type
    elif isinstance(value, (list, dict)):
        # For lists/dicts, convert to JSON string. Adjust if you have a specific desired string representation.
        try:
            return json.dumps(value)
        except TypeError:
            # Fallback if list/dict contains non-serializable elements
            return str(value) 
    else:
        # For any other unexpected type, convert to string
        return str(value)

def chunk_api_file(data: dict) -> list:
    """Chunks a JSON file from cpp_parser.py (classes, namespaces, etc.)."""
    chunks = []
    parent_metadata = data.get("metadata", {}) 
    parent_id_base = hashlib.md5(data.get("name", "").encode()).hexdigest()
    
    # Create a chunk for the main description of the class/struct itself
    main_description = (
        f"API Definition: {data.get('name', '')} ({data.get('kind', '')})\n\n"
        f"Description: {data.get('brief_description', '')}\n\n"
        f"Details: {data.get('detailed_description', '')}"
    ).strip()
    
    if len(main_description) > 50:
        split_chunks = split_content(main_description, f"{parent_id_base}_summary")
        for chunk_data in split_chunks:
            # Sanitize metadata for this chunk
            chunk_metadata = {
                **parent_metadata,
                "source_file": data.get("source_file", ""),
                "type": "summary",
                "parent_name": data.get('name', '')
            }
            sanitized_chunk_metadata = {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            chunks.append({
                "id": chunk_data["id"],
                "content": chunk_data["content"],
                "metadata": sanitized_chunk_metadata
            })

    # Create a chunk for each member (function, enum, etc.)
    for i, member in enumerate(data.get("members", [])):
        content = (
            f"API Member: {member.get('name', '')} in {data.get('name', '')}\n"
            f"Kind: {member.get('kind', '')}\n"
            f"Visibility: {member.get('visibility', '')}\n"
            f"Definition: {member.get('definition', '')}{member.get('argsstring', '')}\n\n"
            f"Description: {member.get('brief_description', '')}\n\n"
            f"Details: {member.get('detailed_description', '')}"
        ).strip()

        split_chunks = split_content(content, f"{parent_id_base}_member_{i}")
        for chunk_data in split_chunks:
            # Sanitize metadata for this chunk
            chunk_metadata = {
                **parent_metadata,
                "source_file": member.get("location", data.get("source_file", "")),
                "type": member.get("kind", "member"),
                "member_name": member.get("name", ""),
                "parent_name": data.get('name', '')
            }
            sanitized_chunk_metadata = {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            chunks.append({
                "id": chunk_data["id"],
                "content": chunk_data["content"],
                "metadata": sanitized_chunk_metadata
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
            # Sanitize metadata for this chunk
            chunk_metadata = {
                **parent_metadata,
                "source_file": snippet.get("source_file", ""),
                "start_line": snippet.get("start_line", 0),
                "type": "example_code",
                "snippet_name": snippet.get("name", "")
            }
            sanitized_chunk_metadata = {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            chunks.append({
                "id": chunk_data["id"],
                "content": chunk_data["content"],
                "metadata": sanitized_chunk_metadata
            })
        
    return chunks

def chunk_text_file(data: dict) -> list:
    """Chunks text-based documents (MD, RST, HTML, CSV, Text) by splitting into paragraphs."""
    chunks = []
    parent_metadata = data.get("metadata", {}) 
    source_file = data.get("source_file", "")
    parent_id_base = hashlib.md5(source_file.encode()).hexdigest()
    
    text_blocks = data.get("content", "").split('\n\n')
    
    for i, block in enumerate(text_blocks):
        clean_block = block.strip()
        if len(clean_block) < 50:
            continue

        split_chunks = split_content(clean_block, f"{parent_id_base}_block_{i}")
        for chunk_data in split_chunks:
            # Sanitize metadata for this chunk
            chunk_metadata = {
                **parent_metadata,
                "source_file": source_file,
                "type": "documentation_text"
            }
            sanitized_chunk_metadata = {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            chunks.append({
                "id": chunk_data["id"],
                "content": chunk_data["content"],
                "metadata": sanitized_chunk_metadata
            })
        
    return chunks

def chunk_pdf_tables_file(data: dict) -> list:
    """Chunks PDF table data by formatting each table into a readable string."""
    chunks = []
    parent_metadata = data.get("metadata", {}) 
    source_file = data.get("source_file", "")
    parent_id_base = hashlib.md5(source_file.encode()).hexdigest()
    
    for i, table in enumerate(data.get("content", [])):
        headers = table.get("headers", [])
        table_data = table.get("data", [])
        
        # Ensure headers and table_data elements are strings, not None
        header_str = " | ".join(str(h) for h in headers if h is not None)
        rows_str = [" | ".join(str(cell) for cell in row if cell is not None) for row in table_data]
            
        content = f"Table from: {parent_metadata.get('title', 'N/A')}\n"
        if header_str:
            content += f"Headers: {header_str}\n"
        content += "\n".join(rows_str)
        content = content.strip()
        
        if not content:
            continue

        split_chunks = split_content(content, f"{parent_id_base}_table_{i}")
        for chunk_data in split_chunks:
            # Use the existing page value logic, but then pass through sanitizer
            page_value = table.get("page")
            if page_value is None:
                page_value = 0 # Default to 0 or some other appropriate integer
            elif not isinstance(page_value, (int, float)):
                try:
                    page_value = int(page_value) # Try to convert to int if it's a string number
                except (ValueError, TypeError):
                    page_value = 0 # Fallback if conversion fails
            
            # Sanitize metadata for this chunk
            chunk_metadata = {
                **parent_metadata,
                "source_file": source_file,
                "page": page_value, 
                "type": "documentation_table"
            }
            sanitized_chunk_metadata = {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            chunks.append({
                "id": chunk_data["id"],
                "content": chunk_data["content"],
                "metadata": sanitized_chunk_metadata
            })
        
    return chunks

def main():
    """Main function to find, process, and chunk all parsed JSON files."""
    all_chunks = []
    json_files = list(PARSED_DATA_DIR.rglob("*.json"))
    
    print(f"Found {len(json_files)} JSON files to process in {PARSED_DATA_DIR}.")

    for file_path in json_files:
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # --- Clean parent_metadata before passing it to chunking functions ---
            # Apply the sanitizer to all parent metadata values
            raw_parent_metadata = data.get("metadata", {})
            cleaned_parent_metadata = {k: _sanitize_metadata_value(v) for k, v in raw_parent_metadata.items()}
            
            # Pass the cleaned_parent_metadata to chunking functions by updating the 'data' dict
            data["metadata"] = cleaned_parent_metadata 

            # --- Routing Logic ---
            file_type = data.get("file_type")
            
            if "members" in data and data.get("kind") in ["namespace", "class", "struct", "file"]:
                chunks = chunk_api_file(data)
                print(f"  [API] Chunked '{file_path.name}' into {len(chunks)} chunks.")
            elif "functions" in data or "other_snippets" in data:
                chunks = chunk_example_file(data)
                print(f"  [Example] Chunked '{file_path.name}' into {len(chunks)} chunks.")
            elif file_type in ["html", "markdown", "rst", "csv", "text", "pdf_text"]:
                chunks = chunk_text_file(data)
                print(f"  [Doc - Text] Chunked '{file_path.name}' into {len(chunks)} chunks.")
            elif file_type == "pdf_tables":
                chunks = chunk_pdf_tables_file(data)
                print(f"  [Doc - Table] Chunked '{file_path.name}' into {len(chunks)} chunks.")
            else:
                print(f"  [WARN] Skipping '{file_path.name}', unknown format.")
                continue
            
            all_chunks.extend(chunks)
            
        except json.JSONDecodeError:
            print(f"  [ERROR] Could not decode JSON from {file_path}. Skipping.")
        except Exception as e:
            print(f"  [ERROR] An unexpected error occurred with {file_path}: {e}")

    print(f"\nTotal chunks created: {len(all_chunks)}")

    # Save the consolidated list of chunks to a single file
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)
        
    print(f"Successfully saved all chunks to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()