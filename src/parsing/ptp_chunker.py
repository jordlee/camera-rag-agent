#!/usr/bin/env python3
"""
PTP SDK Chunker - Combines parsed PTP data (PDFs, C++, shell scripts) for embedding
"""

import os
import json
import hashlib
import re
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
PARSED_DATA_DIR = PROJECT_ROOT / "data/parsed_data"
OUTPUT_FILE = PROJECT_ROOT / "data/chunks_ptp_v2.json"

# Chunking strategy
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def create_chunk_id(content: str, parent_id: str, index: int) -> str:
    """Creates a unique, repeatable ID for a chunk."""
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{parent_id}_{index}_{content_hash}"


def _sanitize_metadata_value(value):
    """Sanitizes metadata values for Pinecone compatibility."""
    if value is None:
        return ""
    elif isinstance(value, (bool, int, float, str)):
        return value
    elif isinstance(value, list):
        return value  # Keep arrays for filtering
    else:
        return str(value)


def split_content(text: str, parent_id: str) -> list[dict]:
    """Splits content using sliding window with overlap."""
    if not text or len(text.strip()) < 20:
        return []

    chunks = []
    start = 0
    cleaned_text = text.strip()

    while start < len(cleaned_text):
        end = start + CHUNK_SIZE
        chunk_content = cleaned_text[start:end].strip()

        if len(chunk_content) > 20:  # Minimum quality threshold
            chunks.append({
                "id": create_chunk_id(chunk_content, parent_id, len(chunks)),
                "content": chunk_content
            })

        start += CHUNK_SIZE - CHUNK_OVERLAP

        if start >= len(cleaned_text):
            break

    return chunks


def chunk_ptp_pdf_text(data: dict) -> list:
    """Chunk PTP PDF text files."""
    chunks = []
    parent_metadata = data.get("metadata", {})
    source_file = data.get("source_file", "")
    parent_id_base = hashlib.md5(source_file.encode()).hexdigest()

    full_content = data.get("content", "").strip()
    if not full_content:
        return chunks

    split_chunks = split_content(full_content, parent_id_base)

    for chunk_data in split_chunks:
        chunk_metadata = {
            **parent_metadata,
            "type": "documentation_text",
            "source_file": Path(source_file).name
        }
        chunks.append({
            "id": chunk_data["id"],
            "content": chunk_data["content"],
            "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
        })

    return chunks


def chunk_ptp_pdf_tables(data: dict) -> list:
    """Chunk PTP PDF tables row-by-row."""
    chunks = []
    parent_metadata = data.get("metadata", {})
    source_file = data.get("source_file", "")
    parent_id_base = hashlib.md5(source_file.encode()).hexdigest()

    for i, table in enumerate(data.get("content", [])):
        headers = table.get("headers", [])
        table_data = table.get("data", [])
        notes = table.get("notes", "")

        header_str = " | ".join(str(h) for h in headers if h)

        for row_index, row in enumerate(table_data):
            row_str = " | ".join(str(cell) if cell else "" for cell in row)

            content = (
                f"Table from: {parent_metadata.get('title', 'N/A')}\n"
                f"Headers: {header_str}\n"
                f"Row: {row_str}"
            )

            if notes:
                content += f"\n---\nNotes: {notes}"

            chunk_id = create_chunk_id(content, f"{parent_id_base}_table_{i}", row_index)

            chunk_metadata = {
                **parent_metadata,
                "type": "documentation_table",
                "source_file": Path(source_file).name,
                "page": table.get("page", 0)
            }

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    return chunks


def chunk_ptp_cpp_file(data: dict) -> list:
    """Chunk PTP C++ source files (from cpp_source_parser_ptp.py)."""
    chunks = []
    parent_metadata = data.get("metadata", {})
    source_file = data.get("source_file", "")
    parent_id_base = hashlib.md5(source_file.encode()).hexdigest()

    # 1. Chunk functions (class methods + standalone)
    for i, func in enumerate(data.get("functions", [])):
        func_name = func.get("function_name", "")
        signature = func.get("signature", "")
        body = func.get("body", "")

        content = f"{signature} {{\n{body}\n}}"

        if len(content.strip()) > 0:
            chunk_id = create_chunk_id(content, f"{parent_id_base}_func_{i}", 0)

            chunk_metadata = {
                **parent_metadata,
                "type": "example_code",
                "source_file": Path(source_file).name,
                "function_name": func_name,
                "return_type": func.get("return_type", "")
            }

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    # 2. Chunk defines
    for i, define in enumerate(data.get("defines", [])):
        name = define.get("name", "")
        value = define.get("value", "")

        content = f"#define {name} {value}"

        if len(content.strip()) > 0:
            chunk_id = create_chunk_id(content, f"{parent_id_base}_define_{i}", 0)

            chunk_metadata = {
                **parent_metadata,
                "type": "define",
                "source_file": Path(source_file).name,
                "define_name": name
            }

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    # 3. Chunk enum members individually
    for i, enum in enumerate(data.get("enums", [])):
        enum_name = enum.get("enum_name", "")

        for j, member in enumerate(enum.get("members", [])):
            member_name = member.get("name", "")
            member_value = member.get("value", "")

            if member_value:
                content = f"enum {enum_name}: {member_name} = {member_value}"
            else:
                content = f"enum {enum_name}: {member_name}"

            if len(content.strip()) > 0:
                chunk_id = create_chunk_id(content, f"{parent_id_base}_enum_{i}_{j}", 0)

                chunk_metadata = {
                    **parent_metadata,
                    "type": "enum",
                    "source_file": Path(source_file).name,
                    "enum_name": enum_name,
                    "member_name": member_name
                }

                chunks.append({
                    "id": chunk_id,
                    "content": content,
                    "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
                })

    # 4. Chunk typedefs
    for i, typedef in enumerate(data.get("typedefs", [])):
        typedef_name = typedef.get("typedef_name", "")
        definition = typedef.get("definition", "")

        content = definition

        if len(content.strip()) > 0:
            chunk_id = create_chunk_id(content, f"{parent_id_base}_typedef_{i}", 0)

            chunk_metadata = {
                **parent_metadata,
                "type": "typedef",
                "source_file": Path(source_file).name,
                "typedef_name": typedef_name
            }

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    # 5. Chunk structs
    for i, struct in enumerate(data.get("structs", [])):
        struct_name = struct.get("struct_name", "")
        definition = struct.get("definition", "")

        content = definition

        if len(content.strip()) > 0:
            chunk_id = create_chunk_id(content, f"{parent_id_base}_struct_{i}", 0)

            chunk_metadata = {
                **parent_metadata,
                "type": "struct",
                "source_file": Path(source_file).name,
                "struct_name": struct_name
            }

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    # 6. Chunk constants
    for i, const in enumerate(data.get("constants", [])):
        const_type = const.get("type", "")
        const_name = const.get("name", "")
        const_value = const.get("value", "")

        content = f"const {const_type} {const_name} = {const_value};"

        if len(content.strip()) > 0:
            chunk_id = create_chunk_id(content, f"{parent_id_base}_const_{i}", 0)

            chunk_metadata = {
                **parent_metadata,
                "type": "constant",
                "source_file": Path(source_file).name,
                "constant_name": const_name
            }

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    # 7. Chunk externs
    for i, ext in enumerate(data.get("externs", [])):
        ext_type = ext.get("type", "")
        ext_name = ext.get("name", "")

        content = f"extern {ext_type} {ext_name};"

        if len(content.strip()) > 0:
            chunk_id = create_chunk_id(content, f"{parent_id_base}_extern_{i}", 0)

            chunk_metadata = {
                **parent_metadata,
                "type": "extern",
                "source_file": Path(source_file).name,
                "extern_name": ext_name
            }

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    return chunks


def chunk_shell_script(data: dict) -> list:
    """Chunk shell scripts (from shell_parser.py)."""
    chunks = []
    parent_metadata = data.get("metadata", {})
    source_file = data.get("source_file", "")
    parent_id_base = hashlib.md5(source_file.encode()).hexdigest()

    # Chunk workflow sections
    for i, section in enumerate(data.get("workflow_sections", [])):
        section_name = section.get("section_name", "")
        commands = section.get("commands", "")

        content = f"Workflow: {section_name}\n\n{commands}"

        if len(content) > 20:
            chunk_id = create_chunk_id(content, f"{parent_id_base}_section_{i}", 0)

            chunk_metadata = {
                **parent_metadata,
                "type": "example_code",
                "source_file": Path(source_file).name,
                "workflow_section": section_name
            }

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    # Chunk functions
    for i, func in enumerate(data.get("functions", [])):
        func_name = func.get("function_name", "")
        func_body = func.get("function_body", "")

        content = f"function {func_name}() {{\n{func_body}\n}}"

        if len(content) > 20:
            chunk_id = create_chunk_id(content, f"{parent_id_base}_func_{i}", 0)

            chunk_metadata = {
                **parent_metadata,
                "type": "example_code",
                "source_file": Path(source_file).name,
                "function_name": func_name
            }

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {k: _sanitize_metadata_value(v) for k, v in chunk_metadata.items()}
            })

    return chunks


def main():
    """Main execution: Find and chunk all PTP parsed data."""
    print("=" * 60)
    print("PTP SDK Chunker")
    print("=" * 60)

    all_chunks = []

    # Define paths for PTP parsed data
    ptp_version = "V2.00.00-PTP"
    ptp_parsed_dirs = [
        PARSED_DATA_DIR / "pdf" / ptp_version,
        PARSED_DATA_DIR / "cpp" / ptp_version,
        PARSED_DATA_DIR / "shell" / ptp_version
    ]

    # Process each directory
    for parsed_dir in ptp_parsed_dirs:
        if not parsed_dir.exists():
            print(f"Directory not found: {parsed_dir}")
            continue

        json_files = list(parsed_dir.glob("*.json"))
        print(f"\nProcessing {len(json_files)} files from {parsed_dir.name}/")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                file_type = data.get("file_type", "")
                chunks = []

                if file_type == "pdf_text":
                    chunks = chunk_ptp_pdf_text(data)
                    print(f"  [PDF Text] {json_file.name} → {len(chunks)} chunks")

                elif file_type == "pdf_tables":
                    chunks = chunk_ptp_pdf_tables(data)
                    print(f"  [PDF Tables] {json_file.name} → {len(chunks)} chunks")

                elif file_type == "cpp_source":
                    chunks = chunk_ptp_cpp_file(data)
                    print(f"  [C++ Source] {json_file.name} → {len(chunks)} chunks")

                elif file_type == "shell_script":
                    chunks = chunk_shell_script(data)
                    print(f"  [Shell Script] {json_file.name} → {len(chunks)} chunks")

                else:
                    print(f"  [SKIP] Unknown file type '{file_type}' in {json_file.name}")
                    continue

                all_chunks.extend(chunks)

            except Exception as e:
                print(f"  [ERROR] Failed to process {json_file.name}: {e}")

    print()
    print("=" * 60)
    print(f"Total PTP chunks created: {len(all_chunks)}")
    print(f"Output file: {OUTPUT_FILE}")
    print("=" * 60)

    # Save chunks
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully saved {len(all_chunks)} chunks to {OUTPUT_FILE}")

    # Print metadata summary
    print("\nMetadata Summary:")
    sdk_types = set()
    sdk_subtypes = set()
    sdk_oses = set()
    sdk_languages = set()
    chunk_types = set()

    for chunk in all_chunks:
        metadata = chunk.get("metadata", {})
        sdk_types.add(metadata.get("sdk_type", "unknown"))
        sdk_subtypes.add(metadata.get("sdk_subtype", "unknown"))
        sdk_oses.add(metadata.get("sdk_os", "unknown"))
        sdk_languages.add(metadata.get("sdk_language", "unknown"))
        chunk_types.add(metadata.get("type", "unknown"))

    print(f"  SDK Types: {sorted(sdk_types)}")
    print(f"  SDK Subtypes: {sorted(sdk_subtypes)}")
    print(f"  SDK OSes: {sorted(sdk_oses)}")
    print(f"  SDK Languages: {sorted(sdk_languages)}")
    print(f"  Chunk Types: {sorted(chunk_types)}")


if __name__ == "__main__":
    main()
