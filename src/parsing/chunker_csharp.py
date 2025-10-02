"""
C# Chunker for Camera Remote SDK V2.00.00

Converts parsed C# methods into chunks matching the C++ format.
Outputs to separate chunks_csharp_v2.json file.
"""

import os
import json
import hashlib
from typing import List, Dict, Any

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PARSED_CSHARP_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/csharp/V2.00.00")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data/chunks_csharp_v2.json")

def generate_chunk_id(content: str, prefix: str = "csharp_method") -> str:
    """Generate unique chunk ID using hash."""
    hash_obj = hashlib.md5(content.encode('utf-8'))
    return f"{prefix}_{hash_obj.hexdigest()[:16]}"

def split_large_content(content: str, max_size: int = 7500) -> List[str]:
    """Split content into chunks at logical boundaries (line breaks)."""
    if len(content) <= max_size:
        return [content]

    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0

    for line in lines:
        line_size = len(line) + 1  # +1 for newline

        if current_size + line_size > max_size and current_chunk:
            # Save current chunk
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size

    # Add last chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks

def create_chunk_from_method(method: Dict[str, Any], file_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert parsed method to chunk(s). Returns list to handle splits."""

    # Build content: signature + implementation
    full_content = method['signature'] + '\n' + method['implementation']

    # Determine original_type
    if method['is_event_handler']:
        original_type = "event_handler"
    elif method['is_override'] and method.get('implements'):
        original_type = "interface_method"
    elif method['visibility'] == "private":
        original_type = "helper_method"
    else:
        original_type = "class_method"

    # Check if splitting is needed
    content_parts = split_large_content(full_content, max_size=7500)

    # Generate group ID if split
    group_id = None
    if len(content_parts) > 1:
        group_id = generate_chunk_id(full_content, prefix="csharp_group")

    chunks = []
    total_parts = len(content_parts)

    for part_num, content_part in enumerate(content_parts, 1):
        # Build metadata matching C++ format
        metadata = {
            "type": "example_code",
            "source_file": file_data['filename'],
            "sdk_version": "V2.00.00",
            "member_name": method['name'],
            "return_type": method['return_type'],
            "start_line": method['start_line'],
            "end_line": method['end_line'],
            "language": "csharp",
            "original_type": original_type,
            "function_name": method['function_calls'],
            "class_name": method.get('class_name'),
        }

        # Add split metadata if applicable
        if group_id:
            metadata['chunk_group_id'] = group_id
            metadata['chunk_part'] = part_num
            metadata['chunk_total_parts'] = total_parts

            # Calculate approximate line ranges for split chunks
            lines_in_part = len(content_part.split('\n'))
            if part_num == 1:
                metadata['split_start_line'] = method['start_line']
                metadata['split_end_line'] = method['start_line'] + lines_in_part - 1
            else:
                # Approximate line numbers for continuation chunks
                prev_lines = sum(len(content_parts[i].split('\n')) for i in range(part_num - 1))
                metadata['split_start_line'] = method['start_line'] + prev_lines
                metadata['split_end_line'] = metadata['split_start_line'] + lines_in_part - 1

        # Add optional fields
        if method.get('implements'):
            metadata['implements'] = method['implements']

        if method.get('ui_control'):
            metadata['ui_control'] = method['ui_control']

        if method.get('sdk_types_used'):
            metadata['sdk_types_used'] = method['sdk_types_used']

        if method.get('comments'):
            metadata['comments'] = method['comments']

        # Generate chunk ID
        chunk_id = generate_chunk_id(content_part + str(part_num))

        chunks.append({
            "id": chunk_id,
            "content": content_part,
            "metadata": metadata
        })

    return chunks

def create_chunk_from_field(field: Dict[str, Any], file_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert field declaration to chunk."""
    # Build content: full field declaration
    content = f"{field['visibility']} "
    if field['is_static']:
        content += "static "
    if field['is_readonly']:
        content += "readonly "
    content += f"{field['data_type']} {field['name']}"
    if field['initializer']:
        content += f" = {field['initializer']}"
    content += ";"

    # Build metadata (consistent with method chunks)
    metadata = {
        "type": "example_code",
        "original_type": "class_field",
        "member_name": field['name'],
        "field_type": field['data_type'],
        "is_array": field['is_array'],
        "is_static": field['is_static'],
        "is_readonly": field['is_readonly'],
        "visibility": field['visibility'],
        "line_number": field['line_number'],
        "class_name": field['class_name'],
        "source_file": file_data['filename'],
        "sdk_version": "V2.00.00",
        "language": "csharp"
    }

    # Add SDK types if present
    if field.get('sdk_types_used'):
        metadata['sdk_types_used'] = field['sdk_types_used']

    # Generate chunk ID
    chunk_id = generate_chunk_id(content, prefix="csharp_field")

    return {
        "id": chunk_id,
        "content": content,
        "metadata": metadata
    }

def create_chunk_from_delegate(delegate: Dict[str, Any], file_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert delegate declaration to chunk."""
    # Build content: full delegate declaration
    content = f"{delegate['visibility']} delegate {delegate['return_type']} {delegate['name']}({delegate['parameters']});"

    # Build metadata (consistent with method chunks)
    metadata = {
        "type": "example_code",
        "original_type": "delegate_declaration",
        "member_name": delegate['name'],
        "return_type": delegate['return_type'],
        "parameters": delegate['parameters'],
        "visibility": delegate['visibility'],
        "line_number": delegate['line_number'],
        "class_name": delegate['class_name'],
        "source_file": file_data['filename'],
        "sdk_version": "V2.00.00",
        "language": "csharp"
    }

    # Generate chunk ID
    chunk_id = generate_chunk_id(content, prefix="csharp_delegate")

    return {
        "id": chunk_id,
        "content": content,
        "metadata": metadata
    }

def create_chunk_from_constant(constant: Dict[str, Any], file_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert constant declaration to chunk."""
    # Build content: full constant declaration with comment
    content = f"{constant['visibility']} const {constant['data_type']} {constant['name']} = {constant['value']};"
    if constant.get('comment'):
        content += f" // {constant['comment']}"

    # Build metadata (consistent with method chunks)
    metadata = {
        "type": "example_code",
        "original_type": "constant",
        "member_name": constant['name'],
        "data_type": constant['data_type'],
        "value": constant['value'],
        "visibility": constant['visibility'],
        "line_number": constant['line_number'],
        "class_name": constant['class_name'],
        "source_file": file_data['filename'],
        "sdk_version": "V2.00.00",
        "language": "csharp"
    }

    if constant.get('comment'):
        metadata['comment'] = constant['comment']

    # Generate chunk ID
    chunk_id = generate_chunk_id(content, prefix="csharp_const")

    return {
        "id": chunk_id,
        "content": content,
        "metadata": metadata
    }

def load_parsed_csharp_files() -> List[Dict[str, Any]]:
    """Load all parsed C# JSON files."""
    parsed_files = []

    if not os.path.exists(PARSED_CSHARP_DIR):
        print(f"ERROR: Parsed C# directory not found: {PARSED_CSHARP_DIR}")
        return []

    json_files = [f for f in os.listdir(PARSED_CSHARP_DIR) if f.endswith('_parsed.json')]

    print(f"Found {len(json_files)} parsed C# files")

    for filename in json_files:
        filepath = os.path.join(PARSED_CSHARP_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            parsed_files.append(json.load(f))

    return parsed_files

def chunk_csharp_code() -> List[Dict[str, Any]]:
    """Convert all parsed C# content (methods, fields, delegates, constants) to chunks."""
    chunks = []
    split_count = 0

    parsed_files = load_parsed_csharp_files()

    for file_data in parsed_files:
        filename = file_data['filename']
        methods = file_data.get('methods', [])
        fields = file_data.get('fields', [])
        delegates = file_data.get('delegates', [])
        constants = file_data.get('constants', [])

        print(f"Processing {filename}: {len(methods)} methods, {len(fields)} fields, {len(delegates)} delegates, {len(constants)} constants")

        # Process methods
        for method in methods:
            method_chunks = create_chunk_from_method(method, file_data)
            chunks.extend(method_chunks)

            if len(method_chunks) > 1:
                split_count += 1
                print(f"  Split {method['name']}: {len(method_chunks)} parts")

        # Process fields
        for field in fields:
            chunks.append(create_chunk_from_field(field, file_data))

        # Process delegates
        for delegate in delegates:
            chunks.append(create_chunk_from_delegate(delegate, file_data))

        # Process constants
        for constant in constants:
            chunks.append(create_chunk_from_constant(constant, file_data))

    if split_count > 0:
        print(f"\nTotal methods split: {split_count}")

    return chunks

def save_chunks(chunks: List[Dict[str, Any]]):
    """Save chunks to JSON file."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(chunks)} chunks to: {OUTPUT_FILE}")

def print_chunk_stats(chunks: List[Dict[str, Any]]):
    """Print statistics about chunks."""
    # Count by type (methods use 'original_type', others use 'type')
    type_counts = {}
    for chunk in chunks:
        metadata = chunk['metadata']
        chunk_type = metadata.get('type', 'unknown')

        # For example_code chunks, use original_type for more detail
        if chunk_type == 'example_code':
            chunk_type = metadata.get('original_type', 'example_code')

        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1

    # Count by file
    file_counts = {}
    for chunk in chunks:
        source_file = chunk['metadata'].get('source_file', 'unknown')
        file_counts[source_file] = file_counts.get(source_file, 0) + 1

    print("\n" + "=" * 60)
    print("CHUNK STATISTICS")
    print("=" * 60)
    print(f"Total chunks: {len(chunks)}")
    print("\nBy type:")
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name}: {count}")
    print("\nBy source file:")
    for filename, count in sorted(file_counts.items()):
        print(f"  {filename}: {count}")

def main():
    """Main entry point."""
    print("=" * 60)
    print("C# Chunker for Camera Remote SDK V2.00.00")
    print("=" * 60)

    chunks = chunk_csharp_code()

    if chunks:
        save_chunks(chunks)
        print_chunk_stats(chunks)
    else:
        print("\nNo chunks generated.")

if __name__ == "__main__":
    main()
