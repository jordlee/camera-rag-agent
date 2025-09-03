#!/usr/bin/env python3
"""Test C++ chunker specifically on RemoteCli.cpp."""

import sys
sys.path.append('/Users/jordanlee/Documents/GitHub/sdk-rag-agent')

from pathlib import Path
from src.parsing.cpp_source_chunker import process_cpp_file

# Test on RemoteCli.cpp
test_file = Path("/Users/jordanlee/Documents/GitHub/sdk-rag-agent/data/raw_sdk_docs/sdk_source/V1.14.00/RemoteCli.cpp")

print(f"Testing chunker on {test_file.name}...")
chunks = process_cpp_file(test_file)

print(f"\nExtracted {len(chunks)} chunks")
print("\nChunk details:")
for chunk in chunks:
    meta = chunk['metadata']
    chunk_type = meta.get('type')
    if chunk_type == 'application_workflow':
        print(f"  Main function (application workflow)")
    elif chunk_type == 'complete_function':
        name = meta.get('function_name', 'unknown')
        print(f"  Function: {name}")
    else:
        print(f"  {chunk_type}: {meta.get('name', 'unknown')}")