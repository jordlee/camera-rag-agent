#!/usr/bin/env python3
"""Test C++ chunker on a single file for debugging."""

import sys
sys.path.append('/Users/jordanlee/Documents/GitHub/sdk-rag-agent')

from pathlib import Path
from src.parsing.cpp_source_chunker import process_cpp_file

# Test on CrDebugString.cpp which has issues
test_file = Path("/Users/jordanlee/Documents/GitHub/sdk-rag-agent/data/raw_sdk_docs/sdk_source/V1.14.00/CrDebugString.cpp")

print(f"Testing chunker on {test_file.name}...")
chunks = process_cpp_file(test_file)

print(f"\nExtracted {len(chunks)} chunks")
print("\nChunk details:")
for chunk in chunks:
    meta = chunk['metadata']
    chunk_type = meta.get('type')
    if chunk_type == 'complete_function':
        name = meta.get('function_name', 'unknown')
        print(f"  Function: {name}")
    elif chunk_type == 'static_map':
        name = meta.get('map_name', 'unknown')
        print(f"  Map: {name}")
    elif chunk_type == 'data_structure':
        name = meta.get('name', 'unknown')
        print(f"  Data structure: {name}")