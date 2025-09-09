#!/usr/bin/env python3
"""Comprehensive analysis of chunks.json to identify quality issues."""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_chunks():
    """Analyze chunk quality and identify improvement opportunities."""
    
    chunks_file = Path(__file__).parent.parent / "data/chunks.json"
    
    print("=" * 80)
    print("COMPREHENSIVE CHUNKS.JSON ANALYSIS")
    print("=" * 80)
    
    # Load chunks
    print("\n1. Loading chunks...")
    try:
        with open(chunks_file) as f:
            chunks = json.load(f)
        print(f"✓ Loaded {len(chunks)} chunks")
    except Exception as e:
        print(f"✗ Error loading chunks: {e}")
        return
    
    # Basic statistics
    print("\n2. Basic Statistics")
    print("-" * 40)
    
    type_counts = Counter(chunk['metadata']['type'] for chunk in chunks)
    total_size = sum(len(chunk['content']) for chunk in chunks)
    avg_size = total_size / len(chunks) if chunks else 0
    
    print(f"Total chunks: {len(chunks)}")
    print(f"Total content size: {total_size:,} characters")
    print(f"Average chunk size: {avg_size:.1f} characters")
    
    print(f"\nContent type distribution:")
    for content_type, count in type_counts.most_common():
        percentage = (count / len(chunks)) * 100
        print(f"  {content_type}: {count} ({percentage:.1f}%)")
    
    # Quality analysis
    print("\n3. Quality Issues Analysis")
    print("-" * 40)
    
    quality_issues = {
        'very_short': [],      # < 10 chars
        'fragments': [],       # Just numbers, dashes, etc.
        'object_form': [],     # "Object form" corrupted text
        'enable_477': [],      # "Enable 477" fragments
        'just_numbers': [],    # Only page numbers
        'truncated': [],       # Ends abruptly
        'html_artifacts': [],  # HTML tags or entities
        'empty_functions': [], # Function definitions with no content
    }
    
    for i, chunk in enumerate(chunks):
        content = chunk['content'].strip()
        chunk_type = chunk['metadata']['type']
        
        # Check for various quality issues
        if len(content) < 10:
            quality_issues['very_short'].append((i, chunk_type, content))
        
        if content in ['2', '3', '94', '342', '477', '479', '532']:
            quality_issues['just_numbers'].append((i, chunk_type, content))
        
        if 'Object form' in content:
            quality_issues['object_form'].append((i, chunk_type, content[:100]))
        
        if content.startswith('Enable 477'):
            quality_issues['enable_477'].append((i, chunk_type, content[:100]))
        
        if content.replace('-', '').replace(' ', '').replace('\n', '') == '':
            quality_issues['fragments'].append((i, chunk_type, content))
        
        if chunk_type == 'function' and 'ails:' in content and len(content) < 50:
            quality_issues['empty_functions'].append((i, chunk_type, content))
        
        if any(tag in content for tag in ['<html>', '<div>', '&nbsp;', '&amp;']):
            quality_issues['html_artifacts'].append((i, chunk_type, content[:100]))
    
    # Report quality issues
    total_issues = sum(len(issues) for issues in quality_issues.values())
    print(f"\nFound {total_issues} quality issues:")
    
    for issue_type, issues in quality_issues.items():
        if issues:
            print(f"\n  {issue_type}: {len(issues)} chunks")
            for j, (idx, chunk_type, content) in enumerate(issues[:3]):  # Show first 3 examples
                print(f"    Example {j+1}: Index {idx}, Type {chunk_type}")
                print(f"      Content: {repr(content[:80])}")
            if len(issues) > 3:
                print(f"    ... and {len(issues) - 3} more")
    
    # Content type specific analysis
    print("\n4. Content Type Specific Issues")
    print("-" * 40)
    
    type_issues = defaultdict(list)
    for issue_type, issues in quality_issues.items():
        for idx, chunk_type, content in issues:
            type_issues[chunk_type].append(issue_type)
    
    for chunk_type in type_counts:
        issues = type_issues[chunk_type]
        if issues:
            issue_summary = Counter(issues)
            print(f"\n  {chunk_type} ({type_counts[chunk_type]} total):")
            for issue, count in issue_summary.most_common():
                print(f"    {issue}: {count} chunks")
    
    # Sample good chunks
    print("\n5. Sample Good Chunks (for comparison)")
    print("-" * 40)
    
    good_examples = {}
    for chunk in chunks:
        chunk_type = chunk['metadata']['type']
        content = chunk['content']
        
        # Consider it good if it's reasonably long and doesn't have obvious issues
        if (len(content) > 50 and 
            not any(issue in content for issue in ['Object form', 'Enable 477']) and
            content.strip() not in ['2', '3', '94', '342'] and
            chunk_type not in good_examples):
            good_examples[chunk_type] = content[:200]
    
    for chunk_type, content in good_examples.items():
        print(f"\n  {chunk_type}:")
        print(f"    {repr(content)}...")
    
    # Recommendations
    print("\n6. Improvement Recommendations")
    print("-" * 40)
    
    print("\n  IMMEDIATE FIXES:")
    
    # Calculate impact
    documentation_text_issues = len([i for i, t, c in quality_issues['object_form'] + 
                                    quality_issues['enable_477'] + quality_issues['just_numbers']])
    function_issues = len([i for i, t, c in quality_issues['empty_functions']])
    
    print(f"  1. FIX documentation_text content ({documentation_text_issues} problematic chunks)")
    print(f"     - Remove 'Object form' artifacts from parsing")
    print(f"     - Filter out page numbers and navigation elements")
    print(f"     - Improve text extraction from PDF/HTML sources")
    
    print(f"  2. FIX function definitions ({function_issues} problematic chunks)")
    print(f"     - Ensure complete function signatures and descriptions")
    print(f"     - Verify API documentation extraction")
    
    print(f"  3. REMOVE low-quality chunks ({total_issues} total)")
    print(f"     - Filter chunks shorter than 20 characters")
    print(f"     - Remove pure page number chunks")
    print(f"     - Clean HTML artifacts from content")
    
    print("\n  WORKING WELL (keep as-is):")
    working_types = []
    for chunk_type in ['enum', 'typedef', 'variable', 'define', 'example_code']:
        if chunk_type in type_counts and chunk_type not in type_issues:
            working_types.append(f"{chunk_type} ({type_counts[chunk_type]} chunks)")
    
    if working_types:
        for working in working_types:
            print(f"  ✓ {working}")
    
    # Calculate fix impact
    problematic_types = ['documentation_text', 'function', 'summary']
    problematic_count = sum(type_counts.get(t, 0) for t in problematic_types)
    good_count = len(chunks) - problematic_count
    
    print(f"\n  EXPECTED IMPACT:")
    print(f"  - Current good chunks: {good_count} ({good_count/len(chunks)*100:.1f}%)")
    print(f"  - Chunks needing fixes: {problematic_count} ({problematic_count/len(chunks)*100:.1f}%)")
    print(f"  - After fixes: Expect 90%+ high-quality, relevant search results")
    
    return {
        'total_chunks': len(chunks),
        'quality_issues': total_issues,
        'type_counts': type_counts,
        'problematic_types': problematic_types
    }

if __name__ == "__main__":
    analyze_chunks()