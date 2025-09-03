#!/usr/bin/env python3
"""Debug RemoteCli.cpp chunking."""

import re
from pathlib import Path

test_file = Path("/Users/jordanlee/Documents/GitHub/sdk-rag-agent/data/raw_sdk_docs/sdk_source/V1.14.00/RemoteCli.cpp")
content = test_file.read_text(encoding='utf-8-sig')
lines = content.split('\n')

# Patterns from the chunker
patterns = [
    r'^static\s+(std::string|CrInt32|void|bool|int)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
    r'^(std::string|std::vector[^)]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
    r'^(SCRSDK::[a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
    r'^(CrInt32|void|bool|int|float|double)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
    r'^([a-zA-Z_][a-zA-Z0-9_\s\*&]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*$'
]

print("Checking lines that match function patterns:")
for i, raw_line in enumerate(lines):
    line = raw_line.strip()
    
    # Check if line would be skipped by indentation
    is_indented = raw_line and raw_line[0] in ' \t'
    
    # Check if it matches any pattern
    for j, pattern in enumerate(patterns):
        if re.match(pattern, line):
            print(f"Line {i+1}: {'INDENTED' if is_indented else 'NOT_INDENTED'}")
            print(f"  Raw: >{raw_line}<")
            print(f"  Stripped: >{line}<")
            print(f"  Pattern {j}: {pattern}")
            print(f"  Match: {re.match(pattern, line).groups()}")
            print()
            break