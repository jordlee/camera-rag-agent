# src/parsing/chunker.py

import os
import json
from pathlib import Path
import hashlib
import re

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
PARSED_DATA_DIR = PROJECT_ROOT / "data/parsed_data"
OUTPUT_FILE = PROJECT_ROOT / "data/chunks.json"

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

def should_split_chunk(metadata: dict, content_size: int) -> bool:
    """
    Determine if a chunk should be split based on content type and function count.
    Only targets problematic multi-function example_code chunks.
    """
    # Only target example_code chunks
    if metadata.get('type') != 'example_code':
        return False
    
    # Check function names - they might be a list or a JSON string
    function_names = metadata.get('function_name', [])
    
    # If it's a JSON string, parse it
    if isinstance(function_names, str) and function_names.startswith('['):
        try:
            function_names = json.loads(function_names)
        except:
            return False
    
    # Only if they have multiple function names (>3 APIs)
    if not isinstance(function_names, list) or len(function_names) <= 3:
        return False
        
    # And only if content is actually large enough to warrant splitting
    return content_size > 2000

def split_cpp_by_functions(content: str, chunk_id: str, metadata: dict) -> list:
    """
    Split C++ code chunks by individual function boundaries.
    Each resulting chunk contains 1-2 related functions maximum.
    """
    lines = content.split('\n')
    chunks = []
    current_function = []
    current_function_names = []
    function_start = 0
    brace_count = 0
    in_function = False
    part_num = 1
    
    for i, line in enumerate(lines):
        current_function.append(line)
        
        # Count braces to track function boundaries
        brace_count += line.count('{') - line.count('}')
        
        # Detect function start (simplified pattern matching)
        if not in_function and ('::' in line or re.match(r'^\w+\s+\w+\s*\(', line.strip())):
            if '{' in line or (i + 1 < len(lines) and '{' in lines[i + 1]):
                in_function = True
                function_start = i
                
                # Extract function name from line
                func_match = re.search(r'(\w+::\w+|\w+)\s*\(', line)
                if func_match:
                    current_function_names.append(func_match.group(1))
        
        # Function end detected (braces balanced and we were in a function)
        if in_function and brace_count == 0 and any('{' in prev_line for prev_line in lines[function_start:i+1]):
            # Create chunk for this function
            function_content = '\n'.join(current_function).strip()
            
            if function_content and len(function_content) > 50:  # Skip tiny fragments
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_part'] = part_num
                chunk_metadata['total_parts'] = None  # Updated later
                chunk_metadata['function_name'] = current_function_names.copy()
                chunk_metadata['start_line'] = function_start + 1
                chunk_metadata['end_line'] = i + 1
                
                chunks.append({
                    "id": f"{chunk_id}_func{part_num}",
                    "content": function_content,
                    "metadata": chunk_metadata
                })
                part_num += 1
            
            # Reset for next function
            current_function = []
            current_function_names = []
            in_function = False
            brace_count = 0
    
    # Handle any remaining content
    if current_function:
        remaining_content = '\n'.join(current_function).strip()
        if remaining_content and len(remaining_content) > 50:
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_part'] = part_num
            chunk_metadata['total_parts'] = None
            chunk_metadata['function_name'] = current_function_names
            
            chunks.append({
                "id": f"{chunk_id}_func{part_num}",
                "content": remaining_content,
                "metadata": chunk_metadata
            })
    
    # If no functions found, return original chunk
    if not chunks:
        return [{"id": chunk_id, "content": content, "metadata": metadata}]
    
    # Update total_parts for all chunks
    for chunk in chunks:
        chunk['metadata']['total_parts'] = len(chunks)
    
    return chunks


def _sanitize_metadata_value(value):
    """
    Sanitizes a metadata value for Pinecone compatibility.
    Preserves native arrays for proper metadata filtering.
    """
    if value is None:
        return ""
    elif isinstance(value, (bool, int, float, str)):
        return value
    elif isinstance(value, list):
        # Keep native arrays for Pinecone metadata filtering
        return value
    else:
        return str(value)

def extract_api_names_from_content(content: str) -> list:
    """Extract all API/function names from content."""
    api_names = set()
    
    # Pattern 1: Table API column (e.g., "| SetSaveInfo |")
    table_pattern = r'\|\s*([A-Z][a-zA-Z0-9_]+)\s*\|'
    api_names.update(re.findall(table_pattern, content))
    
    # Pattern 2: SDK-specific device properties
    device_props = re.findall(r'CrDeviceProperty_\w+', content)
    api_names.update(device_props)
    
    # Pattern 3: Common SDK API patterns
    api_patterns = [
        r'\b(Set[A-Z][a-zA-Z0-9_]+)\b',  # SetSaveInfo, SetDeviceProperty
        r'\b(Get[A-Z][a-zA-Z0-9_]+)\b',  # GetDeviceProperties, GetContentsList
        r'\b(Release[A-Z][a-zA-Z0-9_]+)\b',  # ReleaseDevice
        r'\b(Connect|Disconnect|EnumCameraObjects)\b',  # Specific APIs
        r'\b(Download[A-Z][a-zA-Z0-9_]+)\b',  # DownloadContents
    ]
    for pattern in api_patterns:
        api_names.update(re.findall(pattern, content))
    
    # Pattern 4: Function definitions
    func_def_pattern = r'\b([A-Z][a-zA-Z0-9_]+)\s*\('
    api_names.update(re.findall(func_def_pattern, content))
    
    # Remove false positives and error/warning codes (handled separately)
    exclude = {'The', 'This', 'For', 'When', 'Row', 'Headers', 'Table', 'Note'}
    api_names = [name for name in api_names 
                 if name not in exclude 
                 and not name.startswith('CrError_')
                 and not name.startswith('CrWarning')]
    
    return list(api_names)

def extract_error_codes(content: str) -> list:
    """Extract CrError_ codes from content."""
    errors = re.findall(r'CrError_\w+', content)
    return list(set(errors)) if errors else []

def extract_warning_codes(content: str) -> list:
    """Extract CrWarning_ codes from content."""
    warnings = re.findall(r'CrWarning_\w+', content)
    return list(set(warnings)) if warnings else []

def extract_warning_ext_codes(content: str) -> list:
    """Extract CrWarningExt codes from content."""
    ext_warnings = re.findall(r'CrWarningExt\w*', content)
    return list(set(ext_warnings)) if ext_warnings else []

def add_sdk_metadata(chunk_metadata: dict, content: str, member_name: str = None) -> dict:
    """Add SDK-specific metadata to any chunk."""
    
    # Extract API/function names
    api_names = extract_api_names_from_content(content)
    if member_name and member_name not in api_names:
        api_names.append(member_name)
    if api_names:
        chunk_metadata["function_name"] = api_names
    
    # Extract error codes
    error_codes = extract_error_codes(content)
    if error_codes:
        chunk_metadata["error_codes"] = error_codes
    
    # Extract warning codes
    warning_codes = extract_warning_codes(content)
    if warning_codes:
        chunk_metadata["warning_codes"] = warning_codes
    
    # Extract warning ext codes
    warning_ext_codes = extract_warning_ext_codes(content)
    if warning_ext_codes:
        chunk_metadata["warning_ext_codes"] = warning_ext_codes
    
    return chunk_metadata

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
            # Add SDK-specific metadata
            chunk_metadata = add_sdk_metadata(chunk_metadata, chunk_data["content"], data.get('name', ''))
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
            # Add SDK-specific metadata
            chunk_metadata = add_sdk_metadata(chunk_metadata, chunk_data["content"], member.get("name", ""))
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
            # Add SDK-specific metadata
            chunk_metadata = add_sdk_metadata(chunk_metadata, chunk_data["content"])
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
                        "type": "example_code"
                    }
                    # Add SDK-specific metadata with function name
                    chunk_metadata = add_sdk_metadata(chunk_metadata, chunk_data["content"], func_name)
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
                # Add SDK-specific metadata
                chunk_metadata = add_sdk_metadata(chunk_metadata, chunk_data["content"])
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
            # Add SDK-specific metadata - this will capture SetSaveInfo and other APIs
            chunk_metadata = add_sdk_metadata(chunk_metadata, content)
            chunks.append({
                "id": chunk_id, "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })
            
    return chunks

# === C++ Source File Processing Functions ===

def extract_class_methods(content: str, filename: str, sdk_version: str) -> list:
    """Extract class methods with full implementation."""
    chunks = []
    
    # Pattern for C++ class methods: ClassName::methodName(...)
    method_pattern = r'^([a-zA-Z_][a-zA-Z0-9_\s\*&]*\s+)?([a-zA-Z_][a-zA-Z0-9_]*::[a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        
        # Skip indented lines (inside function bodies)
        if raw_line and raw_line[0] in ' \t':
            i += 1
            continue
            
        method_match = re.match(method_pattern, line)
        
        if method_match:
            method_name = method_match.group(2)
            start_line = i
            
            # Extract complete function by matching braces
            brace_count = 0
            function_lines = []
            j = i
            
            max_lines = min(i + 1000, len(lines))
            while j < max_lines:
                current_line = lines[j]
                function_lines.append(current_line)
                
                for char in current_line:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                
                if brace_count == 0 and '{' in '\n'.join(function_lines):
                    break
                j += 1
            
            if brace_count == 0:
                complete_code = '\n'.join(function_lines)
                chunk_id = hashlib.md5(f"{filename}_{method_name}_{start_line}".encode()).hexdigest()[:16]
                
                chunk_metadata = {
                    "type": "example_code",
                    "source_file": filename,
                    "sdk_version": sdk_version,
                    "member_name": method_name.split("::")[-1],  # Just the method name
                    "start_line": start_line + 1,
                    "end_line": j + 1,
                    "language": "cpp",
                    "original_type": "class_method"
                }
                
                # Apply SDK metadata extraction
                chunk_metadata = add_sdk_metadata(chunk_metadata, complete_code, method_name)
                
                chunks.append({
                    "id": f"cpp_method_{chunk_id}",
                    "content": complete_code,
                    "metadata": chunk_metadata
                })
            
            i = j + 1
        else:
            i += 1
    
    return chunks

def extract_standalone_functions(content: str, filename: str, sdk_version: str) -> list:
    """Extract standalone functions (non-class methods)."""
    chunks = []
    
    # Patterns for standalone functions with various return types
    patterns = [
        r'^static\s+(std::string|CrInt32|void|bool|int)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        r'^(std::string|std::vector[^)]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        r'^(SCRSDK::[a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        r'^(CrInt32|void|bool|int|float|double)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
    ]
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        
        # Skip indented lines
        if raw_line and raw_line[0] in ' \t':
            i += 1
            continue
        
        # Skip class methods
        if re.search(r'[a-zA-Z_][a-zA-Z0-9_]*::[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line):
            i += 1
            continue
            
        func_match = None
        for pattern in patterns:
            func_match = re.match(pattern, line)
            if func_match:
                break
        
        if func_match:
            # Check for opening brace
            has_opening_brace = '{' in line
            if not has_opening_brace and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                has_opening_brace = next_line.startswith('{')
            
            if has_opening_brace:
                return_type = func_match.group(1).strip()
                func_name = func_match.group(2)
                start_line = i
                
                # Extract complete function
                brace_count = 0
                function_lines = []
                j = i
                
                max_lines = min(i + 1000, len(lines))
                while j < max_lines:
                    current_line = lines[j]
                    function_lines.append(current_line)
                    
                    for char in current_line:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                    
                    if brace_count == 0 and '{' in '\n'.join(function_lines):
                        break
                    j += 1
                
                if brace_count == 0:
                    complete_code = '\n'.join(function_lines)
                    chunk_id = hashlib.md5(f"{filename}_{func_name}_{start_line}".encode()).hexdigest()[:16]
                    
                    chunk_metadata = {
                        "type": "example_code",
                        "source_file": filename,
                        "sdk_version": sdk_version,
                        "member_name": func_name,
                        "return_type": return_type,
                        "start_line": start_line + 1,
                        "end_line": j + 1,
                        "language": "cpp",
                        "original_type": "standalone_function"
                    }
                    
                    # Apply SDK metadata extraction
                    chunk_metadata = add_sdk_metadata(chunk_metadata, complete_code, func_name)
                    
                    chunks.append({
                        "id": f"cpp_func_{chunk_id}",
                        "content": complete_code,
                        "metadata": chunk_metadata
                    })
                
                i = j + 1
            else:
                i += 1
        else:
            i += 1
    
    return chunks

def extract_static_maps(content: str, filename: str, sdk_version: str) -> list:
    """Extract static data maps (unordered_map, map definitions)."""
    chunks = []
    
    # Patterns for map definitions
    map_patterns = [
        r'^const\s+std::unordered_map<[^>]+>\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$',
        r'^static\s+const\s+std::unordered_map<[^>]+>\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$',
        r'^std::unordered_map<[^>]+>\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$',
    ]
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        for pattern in map_patterns:
            map_match = re.match(pattern, line)
            if map_match:
                map_name = map_match.group(1)
                start_line = i
                
                # Check if opening brace is on the next line
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('{'):
                    # Extract complete map definition
                    brace_count = 0
                    map_lines = [lines[i]]
                    j = i + 1
                    
                    while j < len(lines):
                        current_line = lines[j]
                        map_lines.append(current_line)
                        
                        for char in current_line:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                        
                        if brace_count == 0 and '{' in '\n'.join(map_lines):
                            # Look for terminating semicolon
                            if ';' in current_line or (j + 1 < len(lines) and ';' in lines[j + 1]):
                                if j + 1 < len(lines) and ';' in lines[j + 1]:
                                    map_lines.append(lines[j + 1])
                                    j += 1
                                break
                        j += 1
                    
                    if brace_count == 0:
                        complete_code = '\n'.join(map_lines)
                        chunk_id = hashlib.md5(f"{filename}_{map_name}_{start_line}".encode()).hexdigest()[:16]
                        
                        chunk_metadata = {
                            "type": "example_code",
                            "source_file": filename,
                            "sdk_version": sdk_version,
                            "member_name": map_name,
                            "start_line": start_line + 1,
                            "end_line": j + 1,
                            "language": "cpp",
                            "original_type": "static_map"
                        }
                        
                        # Filter out debug utility maps that we don't need for RAG
                        debug_maps_to_exclude = [
                            'map_CrDeviceProperty',
                            'map_CrCommandId', 
                            'map_CrError',
                            'map_CrWarning'
                        ]
                        
                        if map_name not in debug_maps_to_exclude:
                            # Apply SDK metadata extraction
                            chunk_metadata = add_sdk_metadata(chunk_metadata, complete_code, map_name)
                            
                            chunks.append({
                                "id": f"cpp_map_{chunk_id}",
                                "content": complete_code,
                                "metadata": chunk_metadata
                            })
                        else:
                            print(f"  Excluding debug map: {map_name} ({len(complete_code):,} chars)")
                    
                    i = j + 1
                    break
        else:
            i += 1
    
    return chunks

def chunk_cpp_source_file(file_path: Path, version_filter: str) -> list:
    """Process raw C++ source files directly."""
    try:
        content = file_path.read_text(encoding='utf-8-sig')  # Handle BOM
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding='latin1')
        except Exception as e:
            print(f"  [ERROR] Could not read {file_path.name}: {e}")
            return []
    
    filename = file_path.name
    chunks = []
    
    # Extract different types of C++ structures
    chunks.extend(extract_class_methods(content, filename, version_filter))
    chunks.extend(extract_standalone_functions(content, filename, version_filter))
    chunks.extend(extract_static_maps(content, filename, version_filter))
    
    # Sanitize metadata for all C++ chunks
    for chunk in chunks:
        if 'metadata' in chunk:
            chunk['metadata'] = {k: _sanitize_metadata_value(v) for k, v in chunk['metadata'].items()}
    
    return chunks

def validate_version(version: str) -> str:
    """Validate and normalize version string."""
    valid_versions = ['V1.14.00', 'V2.00.00']
    if version not in valid_versions:
        raise ValueError(f"Invalid version '{version}'. Valid options: {valid_versions}")
    return version

def should_process_file(file_path: Path, target_version: str) -> bool:
    """Check if file should be processed based on version."""
    path_str = str(file_path).lower()
    target_lower = target_version.lower()
    
    # Check for version in path (case insensitive)
    return target_lower in path_str

def main():
    """Main function to find, process, and chunk files."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Chunk parsed SDK documentation')
    parser.add_argument('--version', type=str, default='V1.14.00',
                       help='SDK version to process (default: V1.14.00, options: V1.14.00, V2.00.00)')
    parser.add_argument('--output', type=str, default='chunks.json',
                       help='Output filename (default: chunks.json)')
    args = parser.parse_args()
    
    # Validate version
    args.version = validate_version(args.version)
    
    output_file = PROJECT_ROOT / "data" / args.output
    
    all_chunks = []
    json_files = list(PARSED_DATA_DIR.rglob("*.json"))
    
    processed_entities = set()
    
    print(f"Found {len(json_files)} JSON files to process in {PARSED_DATA_DIR}.")
    print(f"Processing version: {args.version}")
    if args.version != 'V1.14.00':
        print(f"⚠️  Using non-default version: {args.version}")

    # Process C++ source files first
    cpp_source_dir = PROJECT_ROOT / "data/raw_sdk_docs/sdk_source" / args.version
    if cpp_source_dir.exists():
        cpp_files = list(cpp_source_dir.glob("*.cpp"))
        if cpp_files:
            print(f"\nProcessing {len(cpp_files)} C++ source files...")
            for cpp_file in cpp_files:
                cpp_chunks = chunk_cpp_source_file(cpp_file, args.version)
                all_chunks.extend(cpp_chunks)
                if cpp_chunks:
                    print(f"  [C++] Chunked '{cpp_file.name}' into {len(cpp_chunks)} chunks.")
    else:
        print(f"Note: C++ source directory not found: {cpp_source_dir}")

    # Process parsed JSON files
    for file_path in json_files:
        try:
            # Filter by version (always specified now with default)
            if not should_process_file(file_path, args.version):
                continue
                
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            data["metadata"] = {k: _sanitize_metadata_value(v) for k, v in data.get("metadata", {}).items()}
            
            entity_name = data.get("name")
            # Extract version from file path (consistent format)
            sdk_version = None
            path_str = str(file_path)
            if "V1.14.00" in path_str or "v1.14.00" in path_str.lower():
                sdk_version = "V1.14.00"
            elif "V2.00.00" in path_str or "v2.00.00" in path_str.lower():
                sdk_version = "V2.00.00"
            
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

    # Post-process: Split multi-function example_code chunks
    print("\nPost-processing: Splitting multi-function chunks...")
    final_chunks = []
    split_count = 0
    
    for chunk in all_chunks:
        content_size = len(chunk['content'])
        
        if should_split_chunk(chunk['metadata'], content_size):
            print(f"  Splitting chunk {chunk['id']} ({content_size:,} chars, {len(chunk['metadata'].get('function_name', []))} functions)")
            split_chunks = split_cpp_by_functions(chunk['content'], chunk['id'], chunk['metadata'])
            # Sanitize metadata for split chunks
            for split_chunk in split_chunks:
                if 'metadata' in split_chunk:
                    split_chunk['metadata'] = {k: _sanitize_metadata_value(v) for k, v in split_chunk['metadata'].items()}
            final_chunks.extend(split_chunks)
            split_count += 1
        else:
            final_chunks.append(chunk)
    
    print(f"Split {split_count} multi-function chunks into {len(final_chunks) - len(all_chunks) + split_count} individual function chunks")
    print(f"Final total: {len(final_chunks)} chunks")

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(final_chunks, f, indent=2)
        
    print(f"Successfully saved {len(final_chunks)} chunks to {output_file}")

if __name__ == "__main__":
    main()