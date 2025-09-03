#!/usr/bin/env python3
"""Update C++ chunks metadata to use example_code type."""

import json
from pathlib import Path

# Load the current C++ chunks
cpp_chunks_file = Path("data/cpp_source_chunks.json")
with open(cpp_chunks_file, 'r') as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} C++ chunks")

# Update metadata types to example_code
updated_count = 0
for chunk in chunks:
    metadata = chunk['metadata']
    old_type = metadata['type']
    
    # Map the different chunk types to example_code
    if old_type in ['complete_function', 'static_map', 'application_workflow', 'data_structure']:
        metadata['type'] = 'example_code'
        metadata['original_type'] = old_type  # Keep track of original type
        updated_count += 1

print(f"Updated {updated_count} chunks to use 'example_code' type")

# Save updated chunks
with open(cpp_chunks_file, 'w') as f:
    json.dump(chunks, f, indent=2)

print(f"Saved updated chunks to {cpp_chunks_file}")

# Show summary
type_counts = {}
original_type_counts = {}
for chunk in chunks:
    t = chunk['metadata']['type']
    type_counts[t] = type_counts.get(t, 0) + 1
    
    if 'original_type' in chunk['metadata']:
        orig_t = chunk['metadata']['original_type']
        original_type_counts[orig_t] = original_type_counts.get(orig_t, 0) + 1

print("\nUpdated type distribution:")
for t, count in type_counts.items():
    print(f"  {t}: {count}")

print("\nOriginal type distribution:")
for t, count in original_type_counts.items():
    print(f"  {t}: {count}")