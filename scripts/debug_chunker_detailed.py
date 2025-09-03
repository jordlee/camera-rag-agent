#!/usr/bin/env python3
"""Detailed debugging of chunker function."""

import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any

def debug_extract_standalone_functions(content: str, filename: str) -> List[Dict[str, Any]]:
    """Debug version of extract_standalone_functions."""
    chunks = []
    
    patterns = [
        r'^static\s+(std::string|CrInt32|void|bool|int)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        r'^(std::string|std::vector[^)]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        r'^(SCRSDK::[a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        r'^(CrInt32|void|bool|int|float|double)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        r'^([a-zA-Z_][a-zA-Z0-9_\s\*&]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*$'
    ]
    
    lines = content.split('\n')
    i = 0
    
    print(f"Processing {filename}...")
    
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
        pattern_idx = -1
        for j, pattern in enumerate(patterns):
            func_match = re.match(pattern, line)
            if func_match:
                pattern_idx = j
                break
        
        if func_match:
            print(f"  Line {i+1}: Found match with pattern {pattern_idx}")
            print(f"    Raw: >{raw_line}<")
            print(f"    Stripped: >{line}<")
            print(f"    Match groups: {func_match.groups()}")
            
            # Check for opening brace
            has_opening_brace = '{' in line
            if not has_opening_brace and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                has_opening_brace = next_line.startswith('{')
            
            print(f"    Has opening brace: {has_opening_brace}")
            
            if has_opening_brace:
                return_type = func_match.group(1).strip()
                func_name = func_match.group(2)
                print(f"    Would extract: {func_name}")
                chunks.append({"function_name": func_name, "line": i+1})
                
            i += 1
        else:
            i += 1
    
    return chunks

# Test on RemoteCli.cpp
test_file = Path("/Users/jordanlee/Documents/GitHub/sdk-rag-agent/data/raw_sdk_docs/sdk_source/V1.14.00/RemoteCli.cpp")
content = test_file.read_text(encoding='utf-8-sig')

result = debug_extract_standalone_functions(content, "RemoteCli.cpp")
print(f"\nTotal functions found: {len(result)}")
for func in result:
    print(f"  {func['function_name']} at line {func['line']}")