#!/usr/bin/env python3
"""Test the specific function directly."""

import sys
sys.path.append('/Users/jordanlee/Documents/GitHub/sdk-rag-agent')

from pathlib import Path
from src.parsing.cpp_source_chunker import extract_standalone_functions

# Test on RemoteCli.cpp
test_file = Path("/Users/jordanlee/Documents/GitHub/sdk-rag-agent/data/raw_sdk_docs/sdk_source/V1.14.00/RemoteCli.cpp")
content = test_file.read_text(encoding='utf-8-sig')

print("Testing extract_standalone_functions directly...")
chunks = extract_standalone_functions(content, "RemoteCli.cpp")

print(f"Extracted {len(chunks)} standalone function chunks")
for chunk in chunks:
    func_name = chunk['metadata']['function_name']
    start_line = chunk['metadata']['start_line']
    print(f"  {func_name} at line {start_line}")