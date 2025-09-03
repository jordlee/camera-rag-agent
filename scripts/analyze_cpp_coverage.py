#!/usr/bin/env python3
"""Analyze coverage of C++ source code chunking."""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
CPP_SOURCE_DIR = PROJECT_ROOT / "data/raw_sdk_docs/sdk_source/V1.14.00"
CHUNKS_FILE = PROJECT_ROOT / "data/cpp_source_chunks.json"

def count_functions_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """Count functions and return their names."""
    try:
        content = file_path.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding='latin1')
        except:
            return 0, []
    
    functions = []
    lines = content.split('\n')
    
    # Patterns for different function types
    patterns = [
        # Class methods
        r'^[a-zA-Z_][a-zA-Z0-9_\s\*&]*\s+([a-zA-Z_][a-zA-Z0-9_]*::[a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        # Standalone functions
        r'^(std::string|CrInt32|static\s+std::string|void|bool|int)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
    ]
    
    # Static maps
    map_pattern = r'^const\s+std::unordered_map<[^>]+>\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*$'
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check for functions
        for pattern in patterns:
            match = re.match(pattern, stripped)
            if match:
                if '::' in pattern:
                    func_name = match.group(1)
                else:
                    func_name = match.group(2) if match.lastindex > 1 else match.group(1)
                functions.append(func_name)
                break
        
        # Check for maps
        map_match = re.match(map_pattern, stripped)
        if map_match:
            functions.append(f"map_{map_match.group(1)}")
    
    return len(functions), functions

def analyze_coverage():
    """Analyze coverage of C++ chunking."""
    # Load chunks
    with open(CHUNKS_FILE, 'r') as f:
        chunks = json.load(f)
    
    print(f"Total chunks: {len(chunks)}")
    print("\nChunk type breakdown:")
    
    type_counts = {}
    file_chunks = {}
    
    for chunk in chunks:
        chunk_type = chunk['metadata']['type']
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
        
        filename = chunk['metadata']['file']
        if filename not in file_chunks:
            file_chunks[filename] = []
        
        # Extract function/map name
        if 'function_name' in chunk['metadata']:
            file_chunks[filename].append(chunk['metadata']['function_name'])
        elif 'map_name' in chunk['metadata']:
            file_chunks[filename].append(f"map_{chunk['metadata']['map_name']}")
    
    for chunk_type, count in sorted(type_counts.items()):
        print(f"  {chunk_type}: {count}")
    
    print("\n" + "="*60)
    print("Coverage Analysis by File:")
    print("="*60)
    
    total_functions_found = 0
    total_functions_chunked = 0
    
    for cpp_file in sorted(CPP_SOURCE_DIR.glob("*.cpp")):
        filename = cpp_file.name
        
        # Count actual functions in file
        func_count, func_names = count_functions_in_file(cpp_file)
        
        # Count chunked functions
        chunked_funcs = file_chunks.get(filename, [])
        chunked_count = len(chunked_funcs)
        
        # Calculate coverage
        coverage = (chunked_count / func_count * 100) if func_count > 0 else 0
        
        # Count file size for context
        file_size = len(cpp_file.read_bytes())
        
        print(f"\n{filename}:")
        print(f"  File size: {file_size:,} bytes")
        print(f"  Functions found: {func_count}")
        print(f"  Functions chunked: {chunked_count}")
        print(f"  Coverage: {coverage:.1f}%")
        
        # Show what's missing if coverage is low
        if coverage < 95 and func_count > 0:
            missing = set(func_names) - set(chunked_funcs)
            if missing:
                print(f"  Missing ({len(missing)} items):")
                for item in list(missing)[:10]:  # Show first 10
                    print(f"    - {item}")
                if len(missing) > 10:
                    print(f"    ... and {len(missing) - 10} more")
        
        total_functions_found += func_count
        total_functions_chunked += chunked_count
    
    print("\n" + "="*60)
    print("Overall Statistics:")
    print(f"  Total functions found: {total_functions_found}")
    print(f"  Total functions chunked: {total_functions_chunked}")
    print(f"  Overall coverage: {total_functions_chunked/total_functions_found*100:.1f}%")

if __name__ == "__main__":
    analyze_coverage()