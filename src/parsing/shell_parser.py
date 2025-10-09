#!/usr/bin/env python3
"""
Shell script parser for PTP SDK example scripts.
Extracts workflow examples, functions, and PTP operation sequences from .sh files.
"""

import os
import json
import re
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
SDK_SOURCE_BASE_DIR = PROJECT_ROOT / "data/raw_sdk_docs/sdk_source"
PARSED_SHELL_OUTPUT_BASE_DIR = PROJECT_ROOT / "data/parsed_data/shell"


def extract_script_metadata(file_path, content):
    """
    Extract metadata from shell script filename and content.

    Returns:
        dict: Metadata including workflow type, PTP operations, etc.
    """
    filename = os.path.basename(file_path)

    # Extract workflow type from filename
    workflow_type = None
    if "authentication" in filename.lower():
        workflow_type = "authentication"
    elif "shoot" in filename.lower() or "image" in filename.lower():
        workflow_type = "image_capture"
    elif "liveview" in filename.lower():
        workflow_type = "liveview"
    elif "settings" in filename.lower():
        workflow_type = "camera_settings"
    elif "zoom" in filename.lower():
        workflow_type = "zoom_control"
    elif "expmode" in filename.lower():
        workflow_type = "exposure_mode"
    else:
        workflow_type = "general"

    # Extract PTP operation codes mentioned in script
    ptp_operations = re.findall(r'0x[0-9A-Fa-f]{4}', content)
    ptp_operations = list(set(ptp_operations))  # Unique operations

    # Extract property codes
    property_codes = re.findall(r'0x[0-9A-Fa-f]{4,8}', content)
    property_codes = list(set(property_codes))  # Unique properties

    return {
        "workflow_type": workflow_type,
        "ptp_operations": ptp_operations[:20],  # Limit to avoid metadata bloat
        "property_codes": property_codes[:20],
        "script_name": filename
    }


def extract_functions(content):
    """
    Extract bash function definitions from script.

    Returns:
        list: List of dict with function name, definition, and usage
    """
    functions = []

    # Pattern: function_name() { ... }
    function_pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)\s*\{([^}]*)\}'

    matches = re.finditer(function_pattern, content, re.MULTILINE | re.DOTALL)

    for match in matches:
        func_name = match.group(1)
        func_body = match.group(2).strip()

        # Skip trivial signal handlers
        if func_name.startswith("handler_"):
            continue

        functions.append({
            "function_name": func_name,
            "function_body": func_body[:500],  # Limit length
            "full_definition": match.group(0)[:600]
        })

    return functions


def extract_workflow_sections(content):
    """
    Extract major workflow sections based on echo comments.

    Returns:
        list: List of dict with section name and commands
    """
    sections = []

    # Split by echo statements (section markers)
    echo_pattern = r'echo\s+"([^"]+)"'
    lines = content.split('\n')

    current_section = None
    current_commands = []

    for line in lines:
        echo_match = re.search(echo_pattern, line)

        if echo_match:
            # Save previous section
            if current_section and current_commands:
                sections.append({
                    "section_name": current_section,
                    "commands": '\n'.join(current_commands[:10])  # Limit commands
                })

            # Start new section
            current_section = echo_match.group(1)
            current_commands = []
        elif current_section:
            # Add command to current section
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith('#'):
                current_commands.append(stripped_line)

    # Save last section
    if current_section and current_commands:
        sections.append({
            "section_name": current_section,
            "commands": '\n'.join(current_commands[:10])
        })

    return sections


def detect_sdk_subtype_and_os(file_path):
    """
    Detect SDK subtype (PTP-2 or PTP-3) and OS from file path.

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

    # Detect OS (shell scripts are Linux only)
    if "Linux" in path_str or "/scripts/" in path_str:
        sdk_os = "linux"
    else:
        sdk_os = "unknown"

    return sdk_subtype, sdk_os


def parse_shell_script(file_path, sdk_version="V2.00.00"):
    """
    Parse a shell script file and extract structured data.

    Args:
        file_path: Path to the .sh file
        sdk_version: SDK version (default: V2.00.00)

    Returns:
        dict: Parsed script data with metadata
    """
    print(f"Parsing shell script: {file_path}")

    # Read script content
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    # Detect SDK subtype and OS from path
    sdk_subtype, sdk_os = detect_sdk_subtype_and_os(file_path)

    # Extract metadata
    script_metadata = extract_script_metadata(file_path, content)

    # Extract functions
    functions = extract_functions(content)

    # Extract workflow sections
    workflow_sections = extract_workflow_sections(content)

    # Build parsed data structure
    parsed_data = {
        "source_file": str(file_path),
        "file_type": "shell_script",
        "content": content,  # Full script for context
        "metadata": {
            "title": os.path.basename(file_path),
            "sdk_version": sdk_version,
            "sdk_type": "ptp",
            "sdk_language": "bash",
            "sdk_subtype": sdk_subtype,
            "sdk_os": sdk_os,
            "type": "example_code",  # For Pinecone filtering
            **script_metadata
        },
        "functions": functions,
        "workflow_sections": workflow_sections
    }

    return parsed_data


def save_parsed_shell_data(parsed_data, output_dir):
    """
    Save parsed shell script data to JSON file.

    Args:
        parsed_data: Parsed script dictionary
        output_dir: Output directory path
    """
    if not parsed_data:
        return

    os.makedirs(output_dir, exist_ok=True)

    # Create filename
    script_name = parsed_data['metadata']['script_name']
    sdk_subtype = parsed_data['metadata']['sdk_subtype']
    clean_name = script_name.replace('.sh', '').replace('.', '_').replace(' ', '_')
    filename = f"{clean_name}_{sdk_subtype}_parsed.json"
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
    Main execution: Find and parse all PTP shell scripts.
    """
    print("=" * 60)
    print("PTP SDK Shell Script Parser")
    print("=" * 60)

    # Find all shell scripts in PTP SDK
    ptp_base_dir = SDK_SOURCE_BASE_DIR / "V2.00.00-PTP"

    if not ptp_base_dir.exists():
        print(f"Error: PTP SDK directory not found: {ptp_base_dir}")
        return

    # Search for .sh files
    shell_scripts = list(ptp_base_dir.rglob("*.sh"))

    print(f"\nFound {len(shell_scripts)} shell scripts")
    print()

    if len(shell_scripts) == 0:
        print("No shell scripts found. Exiting.")
        return

    # Create output directory
    output_dir = PARSED_SHELL_OUTPUT_BASE_DIR / "V2.00.00-PTP"
    os.makedirs(output_dir, exist_ok=True)

    # Parse each script
    parsed_count = 0
    for script_path in shell_scripts:
        parsed_data = parse_shell_script(script_path, sdk_version="V2.00.00")

        if parsed_data:
            save_parsed_shell_data(parsed_data, output_dir)
            parsed_count += 1

    print()
    print("=" * 60)
    print(f"Shell script parsing complete!")
    print(f"Parsed {parsed_count} scripts")
    print(f"Output directory: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
