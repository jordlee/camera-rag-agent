#!/usr/bin/env python3
"""
PTP SDK C++ source code parser.
Extracts functions and code from .cpp and .h files without Doxygen.
"""

import os
import json
import re
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
SDK_SOURCE_BASE_DIR = PROJECT_ROOT / "data/raw_sdk_docs/sdk_source"
PARSED_CPP_OUTPUT_BASE_DIR = PROJECT_ROOT / "data/parsed_data/cpp"


def extract_functions_from_cpp(content):
    """
    Extract function definitions from C++ source code.
    Handles both class methods (ClassName::methodName) and standalone functions.

    Returns:
        list: List of dict with function name, signature, and body
    """
    functions = []
    lines = content.split('\n')

    # Keywords to skip (control flow, not functions)
    skip_keywords = {'if', 'for', 'while', 'switch', 'else', 'catch', 'try'}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Pattern for class methods: ReturnType ClassName::methodName(params)
        # Opening brace may be on same line or next line
        method_pattern = r'^(void|int|BOOL|bool|HRESULT|DWORD|HANDLE|HWND|BYTE\s*\*|unsigned\s+\w+|static\s+\w+|[A-Z][a-zA-Z_0-9]*)\s+([A-Z][a-zA-Z_0-9]+::)([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        # Pattern for standalone functions
        standalone_pattern = r'^(void|int|BOOL|bool|HRESULT|DWORD|HANDLE|HWND|unsigned\s+\w+|static\s+\w+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('

        method_match = re.match(method_pattern, line)
        standalone_match = re.match(standalone_pattern, line)

        if method_match:
            # Extract class method name
            func_name = method_match.group(3)

            # Skip control flow keywords
            if func_name in skip_keywords:
                i += 1
                continue

            # Collect signature lines until we find opening brace
            start_line = i
            sig_lines = [line]
            j = i + 1

            # Look ahead for opening brace (max 10 lines for multi-line signatures)
            while j < len(lines) and j < i + 10:
                # Check if we already have opening brace before adding more lines
                if '{' in '\n'.join(sig_lines):
                    break
                sig_lines.append(lines[j].strip())
                if '{' in lines[j]:
                    break
                j += 1

            # If no opening brace found, skip
            if '{' not in '\n'.join(sig_lines):
                i += 1
                continue

            # Now extract full function body with brace matching
            func_lines = sig_lines.copy()
            brace_count = '\n'.join(sig_lines).count('{') - '\n'.join(sig_lines).count('}')

            # Continue reading lines until braces balance
            while j < len(lines) and brace_count > 0:
                j += 1
                if j < len(lines):
                    func_lines.append(lines[j])
                    brace_count += lines[j].count('{') - lines[j].count('}')

            func_text = '\n'.join(func_lines)

            # Extract signature (everything before first {)
            sig_match = re.match(r'^(.+?)\s*\{', func_text, re.DOTALL)
            if sig_match:
                signature = sig_match.group(1).strip()
                body = func_text[sig_match.end():].strip()

                # Remove closing brace
                if body.endswith('}'):
                    body = body[:-1].strip()

                # Keep all functions regardless of size
                functions.append({
                    "function_name": func_name,
                    "return_type": method_match.group(1).strip(),
                    "parameters": "",
                    "signature": signature,
                    "body": body[:2000]  # Truncate very long bodies only
                })

            # Move to next line after function end
            i = j + 1

        elif standalone_match:
            func_name = standalone_match.group(2)

            # Skip control flow keywords
            if func_name in skip_keywords:
                i += 1
                continue

            # Collect signature lines until we find opening brace
            sig_lines = [line]
            j = i + 1

            # Look ahead for opening brace
            while j < len(lines) and j < i + 10:
                # Check if we already have opening brace before adding more lines
                if '{' in '\n'.join(sig_lines):
                    break
                sig_lines.append(lines[j].strip())
                if '{' in lines[j]:
                    break
                j += 1

            # If no opening brace found, skip
            if '{' not in '\n'.join(sig_lines):
                i += 1
                continue

            # Extract full function body
            func_lines = sig_lines.copy()
            brace_count = '\n'.join(sig_lines).count('{') - '\n'.join(sig_lines).count('}')

            # Continue reading lines until braces balance
            while j < len(lines) and brace_count > 0:
                j += 1
                if j < len(lines):
                    func_lines.append(lines[j])
                    brace_count += lines[j].count('{') - lines[j].count('}')

            func_text = '\n'.join(func_lines)

            # Extract signature
            sig_match = re.match(r'^(.+?)\s*\{', func_text, re.DOTALL)
            if sig_match:
                signature = sig_match.group(1).strip()
                body = func_text[sig_match.end():].strip()

                # Remove closing brace
                if body.endswith('}'):
                    body = body[:-1].strip()

                # Keep all functions regardless of size
                functions.append({
                    "function_name": func_name,
                    "return_type": standalone_match.group(1).strip(),
                    "parameters": "",
                    "signature": signature,
                    "body": body[:2000]  # Truncate very long bodies only
                })

            # Move to next line after function end
            i = j + 1
        else:
            i += 1

    return functions


def extract_classes_from_cpp(content):
    """
    Extract class definitions from C++ code.

    Returns:
        list: List of class names found
    """
    # Pattern: class ClassName
    class_pattern = r'class\s+([A-Z][a-zA-Z0-9_]*)'
    classes = re.findall(class_pattern, content)
    return list(set(classes))  # Unique classes


def extract_defines_from_cpp(content):
    """
    Extract #define macros from C++ code.

    Returns:
        list: List of dict with name and value
    """
    defines = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        # Pattern: #define NAME VALUE
        if line.startswith('#define'):
            # Skip header guards and include guards
            if any(keyword in line for keyword in ['ifndef', 'endif', 'ifdef', 'PTPTDEF']):
                continue

            parts = line.split(None, 2)  # Split on whitespace, max 3 parts
            if len(parts) >= 2:
                name = parts[1]
                value = parts[2] if len(parts) > 2 else ""
                defines.append({
                    "name": name,
                    "value": value.strip()
                })

    return defines


def extract_enums_from_cpp(content):
    """
    Extract enum definitions from C++ code.

    Returns:
        list: List of dict with enum name and members
    """
    enums = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Pattern: enum EnumName {
        enum_match = re.match(r'^enum\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{', line)
        if enum_match:
            enum_name = enum_match.group(1)
            enum_members = []

            # Collect enum members until closing brace
            i += 1
            while i < len(lines):
                member_line = lines[i].strip()

                # End of enum
                if member_line.startswith('}'):
                    break

                # Skip empty lines and comments
                if not member_line or member_line.startswith('//'):
                    i += 1
                    continue

                # Extract member (handle comments and values)
                # Pattern: MEMBER_NAME = 0x1234, or just MEMBER_NAME,
                member_match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*([^,]+))?,?', member_line)
                if member_match:
                    member_name = member_match.group(1)
                    member_value = member_match.group(2).strip() if member_match.group(2) else None
                    enum_members.append({
                        "name": member_name,
                        "value": member_value
                    })

                i += 1

            if enum_members:  # Only add if we found members
                enums.append({
                    "enum_name": enum_name,
                    "members": enum_members
                })

        i += 1

    return enums


def extract_typedefs_from_cpp(content):
    """
    Extract typedef statements from C++ code.

    Returns:
        list: List of dict with typedef info
    """
    typedefs = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Pattern: typedef struct _Name {
        struct_match = re.match(r'^typedef\s+struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{', line)
        if struct_match:
            struct_name = struct_match.group(1)

            # Collect struct body until closing brace
            struct_lines = [line]
            brace_count = 1
            i += 1

            while i < len(lines) and brace_count > 0:
                struct_line = lines[i]
                struct_lines.append(struct_line)
                brace_count += struct_line.count('{') - struct_line.count('}')
                i += 1

            # Extract alias name after closing brace
            full_typedef = '\n'.join(struct_lines)
            # Pattern: } TypedefName, *PTypedefName;
            alias_match = re.search(r'\}\s*([A-Za-z_][A-Za-z0-9_]*)', full_typedef)

            if alias_match:
                typedef_name = alias_match.group(1)
                typedefs.append({
                    "original_name": struct_name,
                    "typedef_name": typedef_name,
                    "definition": full_typedef[:500]  # Truncate very long definitions
                })

            continue

        # Pattern: typedef existing_type new_name;
        simple_match = re.match(r'^typedef\s+(.+?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;', line)
        if simple_match:
            original = simple_match.group(1).strip()
            new_name = simple_match.group(2)
            typedefs.append({
                "original_name": original,
                "typedef_name": new_name,
                "definition": line
            })

        i += 1

    return typedefs


def extract_structs_from_cpp(content):
    """
    Extract struct definitions (non-typedef) from C++ code.

    Returns:
        list: List of dict with struct info
    """
    structs = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Pattern: struct StructName {
        # Exclude typedef structs (handled by extract_typedefs)
        struct_match = re.match(r'^struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{', line)
        if struct_match and not line.startswith('typedef'):
            struct_name = struct_match.group(1)

            # Collect struct body
            struct_lines = [line]
            brace_count = 1
            i += 1

            while i < len(lines) and brace_count > 0:
                struct_line = lines[i]
                struct_lines.append(struct_line)
                brace_count += struct_line.count('{') - struct_line.count('}')
                i += 1

            structs.append({
                "struct_name": struct_name,
                "definition": '\n'.join(struct_lines)[:500]
            })
            continue

        i += 1

    return structs


def extract_constants_from_cpp(content):
    """
    Extract const variable declarations from C++ code.

    Returns:
        list: List of dict with constant info
    """
    constants = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()

        # Pattern: const TYPE NAME = VALUE;
        const_match = re.match(r'^const\s+(\w+(?:\s*\*)?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;]+);', line)
        if const_match:
            const_type = const_match.group(1).strip()
            const_name = const_match.group(2)
            const_value = const_match.group(3).strip()

            constants.append({
                "type": const_type,
                "name": const_name,
                "value": const_value
            })

    return constants


def extract_externs_from_cpp(content):
    """
    Extract extern variable declarations from C++ code.

    Returns:
        list: List of dict with extern info
    """
    externs = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()

        # Pattern: extern TYPE variable_name;
        extern_match = re.match(r'^extern\s+(\w+(?:\s*\*)?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;', line)
        if extern_match:
            extern_type = extern_match.group(1).strip()
            extern_name = extern_match.group(2)

            externs.append({
                "type": extern_type,
                "name": extern_name
            })

    return externs


def detect_sdk_context_from_path(file_path):
    """
    Detect SDK subtype and OS from file path.

    Returns:
        tuple: (sdk_subtype, sdk_os)
    """
    path_str = str(file_path)

    # Detect subtype
    if "PTP-2" in path_str:
        sdk_subtype = "ptp-2"
    elif "PTP-3" in path_str:
        sdk_subtype = "ptp-3"
    else:
        sdk_subtype = "unknown"

    # Detect OS
    if "/Linux/" in path_str or "\\Linux\\" in path_str:
        sdk_os = "linux"
    elif "/Windows/" in path_str or "\\Windows\\" in path_str:
        sdk_os = "windows"
    else:
        sdk_os = "unknown"

    return sdk_subtype, sdk_os


def parse_cpp_file(file_path, sdk_version="V2.00.00"):
    """
    Parse a C++ source file (.cpp or .h).

    Args:
        file_path: Path to the C++ file
        sdk_version: SDK version (default: V2.00.00)

    Returns:
        dict: Parsed file data with metadata
    """
    print(f"Parsing C++ file: {file_path}")

    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
        return None

    # Detect SDK context from path
    sdk_subtype, sdk_os = detect_sdk_context_from_path(file_path)

    # Extract all C++ elements
    functions = extract_functions_from_cpp(content)
    classes = extract_classes_from_cpp(content)
    defines = extract_defines_from_cpp(content)
    enums = extract_enums_from_cpp(content)
    typedefs = extract_typedefs_from_cpp(content)
    structs = extract_structs_from_cpp(content)
    constants = extract_constants_from_cpp(content)
    externs = extract_externs_from_cpp(content)

    # Build parsed data structure
    parsed_data = {
        "source_file": str(file_path),
        "file_type": "cpp_source",
        "content": content,  # Full file for context
        "metadata": {
            "title": os.path.basename(file_path),
            "sdk_version": sdk_version,
            "sdk_type": "ptp",
            "sdk_language": "cpp",
            "sdk_subtype": sdk_subtype,
            "sdk_os": sdk_os,
            "type": "example_code",  # For Pinecone filtering
            "source_file": os.path.basename(file_path),
            "function_count": len(functions),
            "class_count": len(classes),
            "define_count": len(defines),
            "enum_count": len(enums),
            "typedef_count": len(typedefs),
            "struct_count": len(structs),
            "constant_count": len(constants),
            "extern_count": len(externs)
        },
        "functions": functions,
        "classes": classes,
        "defines": defines,
        "enums": enums,
        "typedefs": typedefs,
        "structs": structs,
        "constants": constants,
        "externs": externs
    }

    return parsed_data


def save_parsed_cpp_data(parsed_data, output_dir):
    """
    Save parsed C++ data to JSON file.

    Args:
        parsed_data: Parsed C++ dictionary
        output_dir: Output directory path
    """
    if not parsed_data:
        return

    os.makedirs(output_dir, exist_ok=True)

    # Create filename - keep extension to avoid .h/.cpp collisions
    source_file = parsed_data['metadata']['source_file']
    sdk_subtype = parsed_data['metadata']['sdk_subtype']
    sdk_os = parsed_data['metadata']['sdk_os']

    # Extract file extension and base name separately
    file_path = Path(source_file)
    file_ext = file_path.suffix  # .cpp or .h
    base_name = file_path.stem    # filename without extension

    clean_name = base_name.replace('.', '_').replace(' ', '_')
    filename = f"{clean_name}{file_ext}_{sdk_subtype}_{sdk_os}_parsed.json"
    filepath = os.path.join(output_dir, filename)

    # Save JSON
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=4, ensure_ascii=False)
        print(f"  Saved: {filepath}")
    except Exception as e:
        print(f"  Error saving {filepath}: {e}")


def main():
    """
    Main execution: Find and parse all PTP C++ source files.
    """
    print("=" * 60)
    print("PTP SDK C++ Source Parser")
    print("=" * 60)

    # Find all C++ files in PTP SDK
    ptp_base_dir = SDK_SOURCE_BASE_DIR / "V2.00.00-PTP"

    if not ptp_base_dir.exists():
        print(f"Error: PTP SDK directory not found: {ptp_base_dir}")
        return

    # Search for .cpp and .h files (excluding system headers)
    cpp_files = []
    for pattern in ["**/*.cpp", "**/*.h"]:
        cpp_files.extend(ptp_base_dir.glob(pattern))

    # Filter out system/framework files
    cpp_files = [
        f for f in cpp_files
        if not any(exclude in str(f) for exclude in [
            'stdafx', 'targetver', 'resource.h', 'afxres.h'
        ])
    ]

    print(f"\nFound {len(cpp_files)} C++ source files")
    print()

    if len(cpp_files) == 0:
        print("No C++ files found. Exiting.")
        return

    # Create output directory
    output_dir = PARSED_CPP_OUTPUT_BASE_DIR / "V2.00.00-PTP"
    os.makedirs(output_dir, exist_ok=True)

    # Parse each file
    parsed_count = 0
    for cpp_path in cpp_files:
        parsed_data = parse_cpp_file(cpp_path, sdk_version="V2.00.00")

        if parsed_data:
            # Save files with ANY content (functions, defines, enums, etc.)
            has_content = (
                parsed_data['functions'] or
                parsed_data['defines'] or
                parsed_data['enums'] or
                parsed_data['typedefs'] or
                parsed_data['structs'] or
                parsed_data['constants'] or
                parsed_data['externs'] or
                parsed_data['classes']
            )

            if has_content:
                save_parsed_cpp_data(parsed_data, output_dir)
                parsed_count += 1
            else:
                print(f"  Skipped (no content): {cpp_path.name}")

    print()
    print("=" * 60)
    print(f"C++ source parsing complete!")
    print(f"Parsed {parsed_count} files with functions")
    print(f"Output directory: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
