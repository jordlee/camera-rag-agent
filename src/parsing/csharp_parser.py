"""
C# Parser for Camera Remote SDK V2.00.00

Extracts C# code examples including:
- Classes and interfaces
- Methods (including event handlers and SDK callbacks)
- Comments and documentation

Output format matches C++ parser for consistent chunking.
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Any, Optional

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSHARP_SOURCE_DIR = os.path.join(PROJECT_ROOT, "data/raw_sdk_docs/sdk_source/V2.00.00-C#")
PARSED_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data/parsed_data/csharp/V2.00.00")

# SDK version
SDK_VERSION = "V2.00.00"

def extract_namespace(content: str) -> Optional[str]:
    """Extract namespace from C# file."""
    match = re.search(r'^\s*namespace\s+(\w+)', content, re.MULTILINE)
    return match.group(1) if match else None

def extract_class_info(content: str) -> List[Dict[str, Any]]:
    """Extract class definitions with interfaces."""
    classes = []

    # Pattern: public (partial) class ClassName (: interfaces)
    pattern = r'^\s*public\s+(?:partial\s+)?class\s+(\w+)(?:\s*:\s*([^{]+))?'

    for match in re.finditer(pattern, content, re.MULTILINE):
        class_name = match.group(1)
        interfaces = match.group(2).strip() if match.group(2) else None

        classes.append({
            "name": class_name,
            "implements": interfaces,
            "start_pos": match.start()
        })

    return classes

def extract_methods(content: str, class_name: str) -> List[Dict[str, Any]]:
    """Extract method definitions with full implementation."""
    methods = []

    # Pattern for methods (including override, async, event handlers)
    # Captures: visibility, modifiers, return type, method name, parameters
    pattern = r'^\s*(public|private|protected)\s+(override\s+)?(async\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)'

    lines = content.split('\n')

    for i, line in enumerate(lines):
        match = re.match(pattern, line)
        if match:
            visibility = match.group(1)
            is_override = match.group(2) is not None
            is_async = match.group(3) is not None
            return_type = match.group(4)
            method_name = match.group(5)
            parameters = match.group(6)

            # Extract method body using brace matching
            method_start = i
            implementation, method_end = extract_method_body(lines, i)

            # Get comments before method (up to 3 lines)
            comments = extract_preceding_comments(lines, method_start)

            # Detect SDK types used
            sdk_types = extract_sdk_types(implementation)

            # Detect if it's an event handler
            is_event_handler = method_name.endswith('_Click') or method_name.endswith('_Load') or method_name.endswith('_Closing')
            ui_control = method_name.replace('_Click', '').replace('_Load', '').replace('_Closing', '') if is_event_handler else None

            # Extract function calls within method
            function_calls = extract_function_calls(implementation)

            methods.append({
                "name": method_name,
                "signature": line.strip(),
                "visibility": visibility,
                "is_override": is_override,
                "is_async": is_async,
                "is_event_handler": is_event_handler,
                "ui_control": ui_control,
                "return_type": return_type,
                "parameters": parameters,
                "implementation": implementation,
                "start_line": method_start + 1,
                "end_line": method_end + 1,
                "comments": comments,
                "sdk_types_used": sdk_types,
                "function_calls": function_calls,
                "class_name": class_name
            })

    return methods

def extract_method_body(lines: List[str], start_index: int) -> tuple[str, int]:
    """Extract method body using brace matching."""
    # Find opening brace
    open_brace_index = start_index
    for i in range(start_index, len(lines)):
        if '{' in lines[i]:
            open_brace_index = i
            break

    # Match braces
    brace_count = 0
    body_lines = []
    end_index = open_brace_index

    for i in range(open_brace_index, len(lines)):
        line = lines[i]
        brace_count += line.count('{') - line.count('}')
        body_lines.append(line)

        if brace_count == 0:
            end_index = i
            break

    return '\n'.join(body_lines), end_index

def extract_preceding_comments(lines: List[str], method_index: int) -> str:
    """Extract comments above method (up to 3 lines)."""
    comments = []

    for i in range(max(0, method_index - 3), method_index):
        line = lines[i].strip()
        if line.startswith('//'):
            comments.append(line[2:].strip())
        elif line.startswith('/*') or line.startswith('*'):
            comments.append(line.strip('/*').strip())

    return ' '.join(comments) if comments else ""

def extract_sdk_types(code: str) -> List[str]:
    """Extract SDK types used in code (SCRSDK namespace, Cr* types)."""
    sdk_types = set()

    # Pattern for Cr* types and SCRSDK namespace
    patterns = [
        r'\b(Cr\w+)',  # CrCameraObjectInfo, CrSdkControlMode, etc.
        r'SCRSDK\.(\w+)',  # SCRSDK.SomeType
        r'SCRSDK::\w+'  # C++ style (in comments)
    ]

    for pattern in patterns:
        matches = re.findall(pattern, code)
        sdk_types.update(matches)

    return sorted(list(sdk_types))

def extract_function_calls(code: str) -> List[str]:
    """Extract function/method calls within code."""
    # Pattern: word followed by opening parenthesis
    pattern = r'(\w+)\s*\('
    calls = set(re.findall(pattern, code))

    # Filter out keywords and common control structures
    keywords = {'if', 'for', 'foreach', 'while', 'switch', 'catch', 'using', 'new', 'return'}
    calls = [c for c in calls if c not in keywords]

    return sorted(list(calls))

def extract_fields(content: str, class_name: str) -> List[Dict[str, Any]]:
    """Extract class-level field declarations."""
    fields = []
    lines = content.split('\n')

    # Pattern for field declarations (handles generics and arrays)
    # Matches: private/public/protected [static] [readonly] Type fieldName = initializer;
    pattern = r'^\s*(public|private|protected|internal)\s+(static\s+)?(readonly\s+)?([\w<>,\s\[\]]+)\s+(\w+)\s*(=\s*(.+?))?;'

    for i, line in enumerate(lines):
        match = re.match(pattern, line)
        if match:
            visibility = match.group(1)
            is_static = match.group(2) is not None
            is_readonly = match.group(3) is not None
            data_type = match.group(4).strip()
            field_name = match.group(5)
            initializer = match.group(7).strip() if match.group(7) else None

            # Check if it's an array type
            is_array = '[]' in data_type

            # Extract SDK types used in field declaration
            sdk_types = extract_sdk_types(line)

            fields.append({
                "name": field_name,
                "visibility": visibility,
                "is_static": is_static,
                "is_readonly": is_readonly,
                "data_type": data_type,
                "is_array": is_array,
                "initializer": initializer,
                "line_number": i + 1,
                "sdk_types_used": sdk_types,
                "class_name": class_name
            })

    return fields

def extract_delegates(content: str, class_name: str) -> List[Dict[str, Any]]:
    """Extract delegate declarations."""
    delegates = []
    lines = content.split('\n')

    # Pattern for delegate declarations
    # Matches: private/public delegate ReturnType DelegateName(params);
    pattern = r'^\s*(public|private|protected)\s+delegate\s+(\w+)\s+(\w+)\s*\(([^)]*)\);'

    for i, line in enumerate(lines):
        match = re.match(pattern, line)
        if match:
            visibility = match.group(1)
            return_type = match.group(2)
            delegate_name = match.group(3)
            parameters = match.group(4)

            delegates.append({
                "name": delegate_name,
                "visibility": visibility,
                "return_type": return_type,
                "parameters": parameters,
                "line_number": i + 1,
                "class_name": class_name
            })

    return delegates

def extract_constants(content: str, class_name: str) -> List[Dict[str, Any]]:
    """Extract constant declarations."""
    constants = []
    lines = content.split('\n')

    # Pattern for const declarations
    # Matches: private/public const Type NAME = value; // comment
    pattern = r'^\s*(public|private|protected)\s+const\s+(\w+)\s+(\w+)\s*=\s*(.+?);(?:\s*//(.+))?'

    for i, line in enumerate(lines):
        match = re.match(pattern, line)
        if match:
            visibility = match.group(1)
            data_type = match.group(2)
            const_name = match.group(3)
            value = match.group(4).strip()
            comment = match.group(5).strip() if match.group(5) else None

            constants.append({
                "name": const_name,
                "visibility": visibility,
                "data_type": data_type,
                "value": value,
                "comment": comment,
                "line_number": i + 1,
                "class_name": class_name
            })

    return constants

def parse_csharp_file(filepath: str) -> Dict[str, Any]:
    """Parse a single C# file."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    filename = os.path.basename(filepath)
    namespace = extract_namespace(content)
    classes = extract_class_info(content)

    # Extract methods, fields, delegates, and constants for each class
    all_methods = []
    all_fields = []
    all_delegates = []
    all_constants = []

    for cls in classes:
        # Methods
        methods = extract_methods(content, cls["name"])
        for method in methods:
            method["implements"] = cls.get("implements")
        all_methods.extend(methods)

        # Fields
        fields = extract_fields(content, cls["name"])
        all_fields.extend(fields)

        # Delegates
        delegates = extract_delegates(content, cls["name"])
        all_delegates.extend(delegates)

        # Constants
        constants = extract_constants(content, cls["name"])
        all_constants.extend(constants)

    return {
        "filename": filename,
        "source_file": filepath,
        "namespace": namespace,
        "classes": classes,
        "methods": all_methods,
        "fields": all_fields,
        "delegates": all_delegates,
        "constants": all_constants,
        "sdk_version": SDK_VERSION,
        "language": "csharp"
    }

def should_skip_file(filename: str) -> bool:
    """Determine if file should be skipped."""
    # Skip auto-generated Designer files
    return filename.endswith('.Designer.cs')

def parse_all_csharp_files() -> List[Dict[str, Any]]:
    """Parse all C# files in the source directory."""
    parsed_files = []

    if not os.path.exists(CSHARP_SOURCE_DIR):
        print(f"ERROR: C# source directory not found: {CSHARP_SOURCE_DIR}")
        return []

    cs_files = [f for f in os.listdir(CSHARP_SOURCE_DIR) if f.endswith('.cs')]

    print(f"Found {len(cs_files)} C# files in {CSHARP_SOURCE_DIR}")

    for filename in cs_files:
        if should_skip_file(filename):
            print(f"Skipping {filename} (auto-generated Designer file)")
            continue

        filepath = os.path.join(CSHARP_SOURCE_DIR, filename)
        print(f"Parsing {filename}...")

        try:
            parsed_data = parse_csharp_file(filepath)
            parsed_files.append(parsed_data)

            # Print stats
            num_methods = len(parsed_data['methods'])
            num_fields = len(parsed_data['fields'])
            num_delegates = len(parsed_data['delegates'])
            num_constants = len(parsed_data['constants'])
            num_classes = len(parsed_data['classes'])
            print(f"  Found {num_classes} classes, {num_methods} methods, {num_fields} fields, {num_delegates} delegates, {num_constants} constants")

        except Exception as e:
            print(f"  ERROR parsing {filename}: {e}")

    return parsed_files

def save_parsed_data(parsed_files: List[Dict[str, Any]]):
    """Save parsed data to JSON files."""
    os.makedirs(PARSED_OUTPUT_DIR, exist_ok=True)

    for parsed_file in parsed_files:
        filename = parsed_file['filename'].replace('.cs', '_parsed.json')
        output_path = os.path.join(PARSED_OUTPUT_DIR, filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_file, f, indent=2, ensure_ascii=False)

        print(f"Saved: {output_path}")

def main():
    """Main entry point."""
    print("=" * 60)
    print("C# Parser for Camera Remote SDK V2.00.00")
    print("=" * 60)

    parsed_files = parse_all_csharp_files()

    if parsed_files:
        save_parsed_data(parsed_files)

        # Print summary
        total_methods = sum(len(f['methods']) for f in parsed_files)
        total_fields = sum(len(f['fields']) for f in parsed_files)
        total_delegates = sum(len(f['delegates']) for f in parsed_files)
        total_constants = sum(len(f['constants']) for f in parsed_files)
        total_classes = sum(len(f['classes']) for f in parsed_files)

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Files parsed: {len(parsed_files)}")
        print(f"Total classes: {total_classes}")
        print(f"Total methods: {total_methods}")
        print(f"Total fields: {total_fields}")
        print(f"Total delegates: {total_delegates}")
        print(f"Total constants: {total_constants}")
        print(f"Output directory: {PARSED_OUTPUT_DIR}")
    else:
        print("\nNo files parsed.")

if __name__ == "__main__":
    main()
