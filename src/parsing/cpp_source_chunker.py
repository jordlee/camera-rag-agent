# src/parsing/cpp_source_chunker.py

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
CPP_SOURCE_DIR = PROJECT_ROOT / "data/raw_sdk_docs/sdk_source/V1.14.00"
OUTPUT_FILE = PROJECT_ROOT / "data/cpp_source_chunks.json"

# Function removed - no longer adding context bloat to chunks

def extract_class_methods(content: str, filename: str) -> List[Dict[str, Any]]:
    """Extract class methods with full implementation."""
    chunks = []
    
    # More flexible pattern for C++ class methods
    # Handles: bool ClassName::methodName(...) or ClassName::ClassName(...)
    method_pattern = r'^([a-zA-Z_][a-zA-Z0-9_\s\*&]*\s+)?([a-zA-Z_][a-zA-Z0-9_]*::[a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        
        # Skip indented lines (these are inside function bodies, not function definitions)
        if raw_line and raw_line[0] in ' \t':
            i += 1
            continue
            
        method_match = re.match(method_pattern, line)
        
        if method_match:
            method_name = method_match.group(2)  # Updated to group 2
            start_line = i
            
            # Find the complete function by matching braces
            brace_count = 0
            function_lines = []
            j = i
            
            # Collect lines until we find the opening brace and complete function
            max_lines = min(i + 1000, len(lines))
            while j < max_lines:
                current_line = lines[j]
                function_lines.append(current_line)
                
                # Count braces
                for char in current_line:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                
                # If we've found the complete function (opened and closed)
                if brace_count == 0 and any('{' in line for line in function_lines):
                    break
                    
                j += 1
            
            if brace_count == 0 and any('{' in line for line in function_lines):  # Complete function found
                function_code = '\n'.join(function_lines)
                
                # Store only pure function implementation
                complete_code = function_code
                
                chunk_id = hashlib.md5(f"{filename}_{method_name}_{start_line}".encode()).hexdigest()[:16]
                
                chunks.append({
                    "id": f"cpp_method_{chunk_id}",
                    "content": complete_code,
                    "metadata": {
                        "type": "complete_function",
                        "file": filename,
                        "function_name": method_name,
                        "start_line": start_line + 1,
                        "end_line": j + 1,
                        "sdk_version": "V1.14.00",
                        "language": "cpp"
                    }
                })
            
            i = j + 1
        else:
            i += 1
    
    return chunks

def extract_standalone_functions(content: str, filename: str) -> List[Dict[str, Any]]:
    """Extract standalone functions (not class methods)."""
    chunks = []
    
    # Patterns for various standalone function signatures
    patterns = [
        # Static functions with common return types
        r'^static\s+(std::string|CrInt32|void|bool|int)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        # Non-static functions with std:: return types
        r'^(std::string|std::vector[^)]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        # Functions with SDK types
        r'^(SCRSDK::[a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        # Functions with primitive return types
        r'^(CrInt32|void|bool|int|float|double)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        # Generic pattern for other return types (fallback)
        r'^([a-zA-Z_][a-zA-Z0-9_\s\*&]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*$'
    ]
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        
        # Skip indented lines (these are inside function bodies, not function definitions)
        if raw_line and raw_line[0] in ' \t':
            i += 1
            continue
        
        # Skip class methods (already handled) - but not functions with SCRSDK:: return types
        # Class methods have ClassName::methodName pattern
        if re.search(r'[a-zA-Z_][a-zA-Z0-9_]*::[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line):
            i += 1
            continue
            
        func_match = None
        for pattern in patterns:
            func_match = re.match(pattern, line)
            if func_match:
                break
        
        # Check if next non-empty line starts with '{' (allowing for same-line braces)
        if func_match:
            # Check for opening brace on same line or next line
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
                function_lines = [lines[i]]  # Function signature
                j = i + 1
                
                # Add safety limit to prevent infinite loops
                max_lines = min(i + 1000, len(lines))
                while j < max_lines:
                    current_line = lines[j]
                    function_lines.append(current_line)
                    
                    for char in current_line:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                    
                    # Found complete function
                    if brace_count == 0 and '{' in '\n'.join(function_lines):
                        break
                    j += 1
                
                if brace_count == 0 and '{' in '\n'.join(function_lines):  # Complete function found
                    function_code = '\n'.join(function_lines)
                    
                    # Store only pure function implementation
                    complete_code = function_code
                    
                    chunk_id = hashlib.md5(f"{filename}_{func_name}_{start_line}".encode()).hexdigest()[:16]
                    
                    chunks.append({
                        "id": f"cpp_func_{chunk_id}",
                        "content": complete_code,
                        "metadata": {
                            "type": "complete_function",
                            "file": filename,
                            "function_name": func_name,
                            "return_type": return_type,
                            "start_line": start_line + 1,
                            "end_line": j + 1,
                            "sdk_version": "V1.14.00",
                            "language": "cpp"
                        }
                    })
                
                i = j + 1
            else:
                i += 1
        else:
            i += 1
    
    return chunks

def extract_static_maps(content: str, filename: str) -> List[Dict[str, Any]]:
    """Extract static data maps (unordered_map, map definitions)."""
    chunks = []
    
    # Pattern for static/const map definitions (may have brace on next line)
    map_patterns = [
        r'^const\s+std::unordered_map<[^>]+>\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$',
        r'^static\s+const\s+std::unordered_map<[^>]+>\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$',
        r'^std::unordered_map<[^>]+>\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$',
        r'^const\s+std::map<[^>]+>\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$'
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
                    # Find complete map definition (matching braces)
                    brace_count = 0
                    map_lines = [lines[i]]  # Include declaration line
                    j = i + 1
                    
                    while j < len(lines):
                        current_line = lines[j]
                        map_lines.append(current_line)
                        
                        for char in current_line:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                        
                        # Check for semicolon after closing brace
                        if brace_count == 0 and '{' in '\n'.join(map_lines):
                            # Look for terminating semicolon
                            if ';' in current_line or (j + 1 < len(lines) and ';' in lines[j + 1]):
                                if j + 1 < len(lines) and ';' in lines[j + 1]:
                                    map_lines.append(lines[j + 1])
                                    j += 1
                                break
                        j += 1
                    
                    if brace_count == 0:
                        map_code = '\n'.join(map_lines)
                        chunk_id = hashlib.md5(f"{filename}_{map_name}".encode()).hexdigest()[:16]
                        
                        chunks.append({
                            "id": f"cpp_map_{chunk_id}",
                            "content": map_code,
                            "metadata": {
                                "type": "static_map",
                                "file": filename,
                                "map_name": map_name,
                                "start_line": start_line + 1,
                                "end_line": j + 1,
                                "sdk_version": "V1.14.00",
                                "language": "cpp"
                            }
                        })
                        i = j + 1
                        break
        else:
            i += 1
    
    return chunks

def extract_data_structures(content: str, filename: str) -> List[Dict[str, Any]]:
    """Extract enums, structs, and other data structures."""
    chunks = []
    
    # Extract enum definitions
    enum_pattern = r'enum\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{'
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        enum_match = re.search(enum_pattern, line)
        
        if enum_match:
            enum_name = enum_match.group(1)
            start_line = i
            
            # Find closing brace
            brace_count = 0
            enum_lines = []
            j = i
            
            while j < len(lines):
                current_line = lines[j]
                enum_lines.append(current_line)
                
                for char in current_line:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                
                if brace_count == 0 and '{' in '\n'.join(enum_lines):
                    break
                j += 1
            
            if brace_count == 0:
                enum_code = '\n'.join(enum_lines)
                # Store only pure enum definition
                complete_code = enum_code
                
                chunk_id = hashlib.md5(f"{filename}_{enum_name}".encode()).hexdigest()[:16]
                
                chunks.append({
                    "id": f"cpp_enum_{chunk_id}",
                    "content": complete_code,
                    "metadata": {
                        "type": "data_structure",
                        "subtype": "enum",
                        "file": filename,
                        "name": enum_name,
                        "start_line": start_line + 1,
                        "end_line": j + 1,
                        "sdk_version": "V1.14.00",
                        "language": "cpp"
                    }
                })
            
            i = j + 1
        else:
            i += 1
    
    return chunks

def chunk_main_function(content: str, filename: str) -> List[Dict[str, Any]]:
    """Special handling for main() function - split into logical sections."""
    chunks = []
    
    if 'int main(' not in content:
        return chunks
    
    lines = content.split('\n')
    main_start = None
    
    # Find main function
    for i, line in enumerate(lines):
        if 'int main(' in line:
            main_start = i
            break
    
    if main_start is None:
        return chunks
    
    # Extract the complete main function
    brace_count = 0
    main_lines = []
    i = main_start
    
    while i < len(lines):
        current_line = lines[i]
        main_lines.append(current_line)
        
        for char in current_line:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
        
        if brace_count == 0 and '{' in '\n'.join(main_lines):
            break
        i += 1
    
    if brace_count == 0:
        main_code = '\n'.join(main_lines)
        # Store only pure main function
        complete_code = main_code
        
        # For large main functions, we can split by logical sections
        # but for now, keep it as one chunk since it's application workflow
        chunk_id = hashlib.md5(f"{filename}_main".encode()).hexdigest()[:16]
        
        chunks.append({
            "id": f"cpp_main_{chunk_id}",
            "content": complete_code,
            "metadata": {
                "type": "application_workflow",
                "file": filename,
                "function_name": "main",
                "start_line": main_start + 1,
                "end_line": i + 1,
                "sdk_version": "V1.14.00",
                "language": "cpp"
            }
        })
    
    return chunks

def process_cpp_file(file_path: Path) -> List[Dict[str, Any]]:
    """Process a single C++ file and extract all chunks."""
    print(f"Processing {file_path.name}...")
    
    try:
        content = file_path.read_text(encoding='utf-8-sig')  # Handle BOM
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding='latin1')
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
            return []
    
    chunks = []
    filename = file_path.name
    
    # Extract different types of code structures
    chunks.extend(extract_class_methods(content, filename))
    chunks.extend(extract_standalone_functions(content, filename))
    chunks.extend(extract_static_maps(content, filename))
    chunks.extend(extract_data_structures(content, filename))
    chunks.extend(chunk_main_function(content, filename))
    
    print(f"  Extracted {len(chunks)} chunks from {filename}")
    return chunks

def main():
    """Main function to process all C++ source files."""
    if not CPP_SOURCE_DIR.exists():
        print(f"Directory not found: {CPP_SOURCE_DIR}")
        return
    
    all_chunks = []
    cpp_files = list(CPP_SOURCE_DIR.glob("*.cpp"))
    
    print(f"Found {len(cpp_files)} C++ files to process")
    
    for cpp_file in cpp_files:
        file_chunks = process_cpp_file(cpp_file)
        all_chunks.extend(file_chunks)
    
    print(f"\nTotal chunks extracted: {len(all_chunks)}")
    
    # Save chunks to file
    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2)
    
    print(f"Saved chunks to: {OUTPUT_FILE}")
    
    # Print summary
    type_counts = {}
    for chunk in all_chunks:
        chunk_type = chunk['metadata']['type']
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
    
    print("\nChunk type summary:")
    for chunk_type, count in type_counts.items():
        print(f"  {chunk_type}: {count}")

if __name__ == "__main__":
    main()