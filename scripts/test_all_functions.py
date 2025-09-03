#!/usr/bin/env python3
"""Test all extraction functions on RemoteCli.cpp."""

import sys
sys.path.append('/Users/jordanlee/Documents/GitHub/sdk-rag-agent')

from pathlib import Path
from src.parsing.cpp_source_chunker import (
    extract_class_methods, extract_standalone_functions, 
    extract_static_maps, extract_data_structures, chunk_main_function
)

# Test on RemoteCli.cpp
test_file = Path("/Users/jordanlee/Documents/GitHub/sdk-rag-agent/data/raw_sdk_docs/sdk_source/V1.14.00/RemoteCli.cpp")
content = test_file.read_text(encoding='utf-8-sig')
filename = "RemoteCli.cpp"

print("Testing all extraction functions on RemoteCli.cpp...")

print("1. Class methods:")
chunks1 = extract_class_methods(content, filename)
print(f"   {len(chunks1)} chunks")
for c in chunks1:
    print(f"   - {c['metadata']['function_name']}")

print("\\n2. Standalone functions:")
chunks2 = extract_standalone_functions(content, filename)
print(f"   {len(chunks2)} chunks")
for c in chunks2:
    print(f"   - {c['metadata']['function_name']}")

print("\\n3. Static maps:")
chunks3 = extract_static_maps(content, filename)
print(f"   {len(chunks3)} chunks")
for c in chunks3:
    print(f"   - {c['metadata']['map_name']}")

print("\\n4. Data structures:")
chunks4 = extract_data_structures(content, filename)
print(f"   {len(chunks4)} chunks")

print("\\n5. Main function:")
chunks5 = chunk_main_function(content, filename)
print(f"   {len(chunks5)} chunks")
for c in chunks5:
    print(f"   - {c['metadata']['function_name']}")

total = len(chunks1) + len(chunks2) + len(chunks3) + len(chunks4) + len(chunks5)
print(f"\\nTotal: {total} chunks")