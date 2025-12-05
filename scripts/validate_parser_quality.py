"""
Validation script for help guide PDF parser quality metrics

Usage:
    python scripts/validate_parser_quality.py \\
        --input data/help-guides/ILCE-1M2/parsed/hierarchical_chunks_v3.json \\
        --target 5.0 \\
        --report data/help-guides/ILCE-1M2/parsed/quality_report.json
"""

import json
import argparse
import random
from pathlib import Path
from typing import Dict, List, Tuple


def validate_chunks(chunks: List[Dict]) -> Dict:
    """
    Calculate quality metrics for parsed chunks

    Args:
        chunks: List of chunk dictionaries

    Returns:
        Dictionary with validation metrics
    """
    total = len(chunks)
    incomplete = []
    empty = []
    page_coverage = set()

    for i, chunk in enumerate(chunks):
        # Track page coverage
        page_coverage.add(chunk.get('page_start'))
        if chunk.get('page_end') and chunk['page_end'] != chunk['page_start']:
            for p in range(chunk['page_start'], chunk['page_end'] + 1):
                page_coverage.add(p)

        # Check if chunk has title
        has_title = bool(chunk.get('subheader_title') or
                         chunk.get('section_title') or
                         chunk.get('topic_title'))

        # Check if chunk has body
        has_body = bool(chunk.get('subheader_body', '').strip() or
                        chunk.get('section_body', '').strip() or
                        chunk.get('topic_body', '').strip())

        # Classify chunk quality
        if has_title and not has_body:
            incomplete.append((i, chunk))

        if not has_title and not has_body:
            empty.append((i, chunk))

    # Calculate percentages
    incomplete_pct = len(incomplete) / total * 100 if total > 0 else 0
    empty_pct = len(empty) / total * 100 if total > 0 else 0

    # Calculate average body length
    body_lengths = []
    for chunk in chunks:
        body = chunk.get('subheader_body', '') or chunk.get('section_body', '') or chunk.get('topic_body', '')
        if body.strip():
            body_lengths.append(len(body.strip()))

    avg_body_length = sum(body_lengths) / len(body_lengths) if body_lengths else 0

    # Check for specific artifacts
    file_maximum_artifacts = sum(1 for c in chunks if 'FileMaximum' in c.get('subheader_title', ''))
    mode_dial_artifacts = sum(1 for c in chunks if 'Mode dialDescription' in c.get('subheader_title', '') or
                              'Mode dialExposure' in c.get('subheader_title', ''))

    return {
        'total_chunks': total,
        'incomplete_chunks': len(incomplete),
        'incomplete_percentage': incomplete_pct,
        'empty_chunks': len(empty),
        'empty_percentage': empty_pct,
        'avg_body_length': avg_body_length,
        'page_coverage': len(page_coverage),
        'file_maximum_artifacts': file_maximum_artifacts,
        'mode_dial_artifacts': mode_dial_artifacts,
        'quality_pass': incomplete_pct < 5.0 and empty_pct < 1.0,
        'sample_incomplete': [
            {
                'index': idx,
                'page': chunk['page_start'],
                'title': chunk.get('subheader_title') or chunk.get('section_title') or chunk.get('topic_title', ''),
                'body_length': len(chunk.get('subheader_body', '') or chunk.get('section_body', '') or chunk.get('topic_body', ''))
            }
            for idx, chunk in incomplete[:10]
        ],
        'sample_empty': [
            {
                'index': idx,
                'page': chunk['page_start'],
                'has_footnotes': len(chunk.get('footnotes', [])),
                'has_hints': len(chunk.get('hints', [])),
                'has_related': len(chunk.get('related_topics', []))
            }
            for idx, chunk in empty[:10]
        ]
    }


def sample_random_chunks(chunks: List[Dict], n: int = 20) -> List[Dict]:
    """
    Sample random chunks for manual review

    Args:
        chunks: List of all chunks
        n: Number of chunks to sample

    Returns:
        List of sampled chunks with index
    """
    if len(chunks) <= n:
        return [{'index': i, 'chunk': chunk} for i, chunk in enumerate(chunks)]

    indices = random.sample(range(len(chunks)), n)
    return [{'index': idx, 'chunk': chunks[idx]} for idx in sorted(indices)]


def generate_quality_report(validation: Dict, chunks: List[Dict], output_path: Path):
    """
    Generate and save quality report

    Args:
        validation: Validation metrics dictionary
        chunks: List of all chunks (for sampling)
        output_path: Path to save report
    """
    # Sample random chunks for review
    sampled = sample_random_chunks(chunks, n=20)

    report = {
        **validation,
        'manual_review_samples': [
            {
                'index': sample['index'],
                'page': sample['chunk']['page_start'],
                'topic_title': sample['chunk'].get('topic_title', ''),
                'section_title': sample['chunk'].get('section_title', ''),
                'subheader_title': sample['chunk'].get('subheader_title', ''),
                'body_preview': (sample['chunk'].get('subheader_body') or
                                 sample['chunk'].get('section_body') or
                                 sample['chunk'].get('topic_body', ''))[:200],
                'footnotes_count': len(sample['chunk'].get('footnotes', [])),
                'hints_count': len(sample['chunk'].get('hints', [])),
                'related_topics_count': len(sample['chunk'].get('related_topics', []))
            }
            for sample in sampled
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def print_summary(validation: Dict):
    """Print validation summary to console"""
    print("\n" + "=" * 70)
    print("PARSER QUALITY VALIDATION REPORT")
    print("=" * 70)

    print(f"\nTotal Chunks: {validation['total_chunks']}")
    print(f"Page Coverage: {validation['page_coverage']} pages")

    print(f"\n--- Quality Metrics ---")
    print(f"Incomplete Chunks: {validation['incomplete_chunks']} ({validation['incomplete_percentage']:.1f}%)")
    print(f"Empty Chunks: {validation['empty_chunks']} ({validation['empty_percentage']:.1f}%)")
    print(f"Average Body Length: {validation['avg_body_length']:.0f} characters")

    print(f"\n--- Artifact Detection ---")
    print(f"'FileMaximum' artifacts: {validation['file_maximum_artifacts']}")
    print(f"'Mode dial' artifacts: {validation['mode_dial_artifacts']}")

    print(f"\n--- Quality Assessment ---")
    if validation['quality_pass']:
        print("✅ PASS: Quality meets target (<5% incomplete, <1% empty)")
    else:
        print("❌ FAIL: Quality does not meet target")
        if validation['incomplete_percentage'] >= 5.0:
            print(f"   - Incomplete chunks: {validation['incomplete_percentage']:.1f}% (target: <5%)")
        if validation['empty_percentage'] >= 1.0:
            print(f"   - Empty chunks: {validation['empty_percentage']:.1f}% (target: <1%)")

    if validation['sample_incomplete']:
        print(f"\n--- Sample Incomplete Chunks (first 10) ---")
        for sample in validation['sample_incomplete'][:5]:
            print(f"  [{sample['index']}] Page {sample['page']}: {sample['title'][:60]}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Validate help guide parser quality')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to parsed chunks JSON file')
    parser.add_argument('--target', type=float, default=5.0,
                        help='Target incomplete percentage threshold (default: 5.0)')
    parser.add_argument('--report', type=str,
                        help='Path to save quality report JSON (optional)')

    args = parser.parse_args()

    # Load chunks
    print(f"Loading chunks from {args.input}...")
    with open(args.input, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Validate
    print("Validating...")
    validation = validate_chunks(chunks)

    # Print summary
    print_summary(validation)

    # Save report if requested
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        generate_quality_report(validation, chunks, report_path)
        print(f"\n✓ Quality report saved to: {args.report}")

    # Exit with appropriate code
    exit(0 if validation['quality_pass'] else 1)


if __name__ == "__main__":
    main()
