#!/usr/bin/env python3
"""Merge C++ chunks into main chunks.json file."""

import json
import shutil
from pathlib import Path

# Load existing chunks
main_chunks_file = Path("data/chunks.json")
cpp_chunks_file = Path("data/cpp_source_chunks.json")

print("Loading chunks...")
with open(main_chunks_file, 'r') as f:
    main_chunks = json.load(f)

with open(cpp_chunks_file, 'r') as f:
    cpp_chunks = json.load(f)

print(f"Loaded {len(main_chunks)} main chunks")
print(f"Loaded {len(cpp_chunks)} C++ chunks")

# Check for ID conflicts
main_ids = {chunk['id'] for chunk in main_chunks}
cpp_ids = {chunk['id'] for chunk in cpp_chunks}
conflicts = main_ids.intersection(cpp_ids)

if conflicts:
    print(f"Warning: Found {len(conflicts)} ID conflicts")
    # Update conflicting C++ chunk IDs
    for chunk in cpp_chunks:
        if chunk['id'] in conflicts:
            chunk['id'] = f"cpp_{chunk['id']}"
    print("Updated conflicting C++ chunk IDs with 'cpp_' prefix")

# Merge chunks
print("Merging chunks...")
merged_chunks = main_chunks + cpp_chunks

print(f"Total merged chunks: {len(merged_chunks)}")

# Create backup of original file
backup_file = main_chunks_file.with_suffix('.json.backup')
if not backup_file.exists():
    shutil.copy2(main_chunks_file, backup_file)
    print(f"Created backup: {backup_file}")

# Save merged chunks
with open(main_chunks_file, 'w') as f:
    json.dump(merged_chunks, f, indent=2)

print(f"Saved merged chunks to {main_chunks_file}")

# Show final type distribution
type_counts = {}
for chunk in merged_chunks:
    t = chunk['metadata']['type']
    type_counts[t] = type_counts.get(t, 0) + 1

print("\nFinal type distribution:")
for t, count in sorted(type_counts.items()):
    print(f"  {t}: {count}")

print(f"\nC++ code chunks ready for embedding with CodeBERT!")