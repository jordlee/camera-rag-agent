#!/usr/bin/env python3
"""Test all search tools to identify which ones are affected by the high score/wrong content issue."""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from search import RAGSearch

async def test_all_search_tools():
    """Test every search method to see which ones have the issue."""
    
    print("=" * 80)
    print("Testing ALL Search Tools - Comprehensive Analysis")
    print("=" * 80)
    
    # Initialize RAG search
    print("\n1. Initializing RAG Search...")
    try:
        rag_search = RAGSearch()
        print("✓ RAG Search initialized")
        
        # Get index stats first
        stats = rag_search.get_index_stats()
        print(f"\nIndex Statistics:")
        print(f"  Total vectors: {stats.get('total_vectors', 0)}")
        print(f"  Dimensions: {stats.get('dimension', 0)}")
        print(f"  Index fullness: {stats.get('index_fullness', 0):.2%}")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return
    
    # Test query
    test_query = "connect to camera"
    
    print(f"\n2. Testing all search methods with query: '{test_query}'")
    print("=" * 80)
    
    # Define all search methods to test
    search_methods = [
        ("search", lambda: rag_search.search(test_query, top_k=3)),
        ("search_async", lambda: rag_search.search_async(test_query, top_k=3)),
        ("search_code_examples", lambda: rag_search.search_code_examples(test_query, top_k=3)),
        ("search_documentation", lambda: rag_search.search_documentation(test_query, top_k=3)),
        ("search_compatibility_tables", lambda: rag_search.search_compatibility_tables(test_query, top_k=3)),
        ("search_api_functions", lambda: rag_search.search_api_functions(test_query, top_k=3)),
        ("search_api_properties", lambda: rag_search.search_api_properties(test_query, top_k=3)),
        ("search_enums", lambda: rag_search.search_enums(test_query, top_k=3)),
        ("search_typedefs", lambda: rag_search.search_typedefs(test_query, top_k=3)),
        ("search_variables", lambda: rag_search.search_variables(test_query, top_k=3)),
        ("search_summaries", lambda: rag_search.search_summaries(test_query, top_k=3)),
        ("search_defines", lambda: rag_search.search_defines(test_query, top_k=3)),
        ("search_by_category (code)", lambda: rag_search.search_by_category(test_query, 'code', top_k=3)),
        ("search_by_category (api)", lambda: rag_search.search_by_category(test_query, 'api', top_k=3)),
        ("search_by_category (docs)", lambda: rag_search.search_by_category(test_query, 'docs', top_k=3)),
        ("search_by_category (compatibility)", lambda: rag_search.search_by_category(test_query, 'compatibility', top_k=3)),
        ("search_by_category (all)", lambda: rag_search.search_by_category(test_query, 'all', top_k=3)),
        ("search_hybrid", lambda: rag_search.search_hybrid(test_query, top_k=3)),
        ("search_with_intent", lambda: rag_search.search_with_intent(test_query, top_k=3, use_intent_mapping=False)),
    ]
    
    # Test each method
    results_summary = []
    
    for method_name, method_func in search_methods:
        print(f"\n{method_name}:")
        print("-" * 40)
        
        try:
            # Handle async methods
            if asyncio.iscoroutinefunction(method_func):
                results = await method_func()
            else:
                result = method_func()
                # Handle sync methods that might return coroutines
                if asyncio.iscoroutine(result):
                    results = await result
                else:
                    results = result
            
            # Handle search_with_intent special case
            if method_name == "search_with_intent":
                if isinstance(results, dict) and 'results' in results:
                    actual_results = results['results']
                    print(f"  Intent analysis: {results.get('intent_analysis', {})}")
                    results = actual_results
            
            if results and len(results) > 0:
                # Analyze first result
                first_result = results[0]
                score = first_result.get('score', 0)
                content = first_result.get('content', '')
                metadata = first_result.get('metadata', {})
                content_type = metadata.get('type', metadata.get('content_type', 'unknown'))
                
                # Clean content for display
                content_preview = ' '.join(content.split())[:100]
                
                print(f"  Results found: {len(results)}")
                print(f"  Top score: {score:.4f}")
                print(f"  Content type: {content_type}")
                print(f"  Content preview: {content_preview}...")
                
                # Check for the problematic patterns
                problematic = False
                if score > 0.99:
                    print(f"  ⚠️  WARNING: Unusually high score ({score:.4f})")
                    problematic = True
                
                problematic_patterns = ["Object form", "Enable 477", "^2$", "^\\d+$", "- - -"]
                for pattern in problematic_patterns:
                    if pattern in content_preview or content_preview.strip().isdigit():
                        print(f"  ⚠️  WARNING: Found problematic content pattern: '{pattern}'")
                        problematic = True
                        break
                
                # Check if expected API is found
                expected_apis = ["SCRSDK::Connect", "Connect", "CrSDK"]
                found_api = any(api.lower() in content.lower() for api in expected_apis)
                if found_api:
                    print(f"  ✓ Found expected API content")
                else:
                    print(f"  ✗ Expected API not found")
                
                results_summary.append({
                    'method': method_name,
                    'score': score,
                    'problematic': problematic,
                    'found_api': found_api,
                    'content_type': content_type,
                    'num_results': len(results)
                })
                
            else:
                print(f"  No results returned")
                results_summary.append({
                    'method': method_name,
                    'score': 0,
                    'problematic': False,
                    'found_api': False,
                    'content_type': 'none',
                    'num_results': 0
                })
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            results_summary.append({
                'method': method_name,
                'score': 0,
                'problematic': False,
                'found_api': False,
                'content_type': 'error',
                'num_results': 0
            })
    
    # Summary analysis
    print("\n" + "=" * 80)
    print("SUMMARY ANALYSIS")
    print("=" * 80)
    
    # Group by content type
    by_content_type = {}
    for result in results_summary:
        ct = result['content_type']
        if ct not in by_content_type:
            by_content_type[ct] = []
        by_content_type[ct].append(result)
    
    print("\nResults by content type:")
    for content_type, methods in by_content_type.items():
        print(f"\n{content_type}:")
        for method in methods:
            status = "⚠️ " if method['problematic'] else "✓ " if method['num_results'] > 0 else "✗ "
            print(f"  {status} {method['method']}: Score={method['score']:.4f}, Results={method['num_results']}")
    
    # Check which methods have the issue
    problematic_methods = [r['method'] for r in results_summary if r['problematic']]
    working_methods = [r['method'] for r in results_summary if not r['problematic'] and r['num_results'] > 0]
    
    print(f"\n⚠️  Problematic methods ({len(problematic_methods)}):")
    for method in problematic_methods:
        print(f"  - {method}")
    
    print(f"\n✓ Working methods ({len(working_methods)}):")
    for method in working_methods:
        print(f"  - {method}")
    
    print("\nConclusions:")
    if len(problematic_methods) == len(results_summary):
        print("  ❌ ALL methods show the same issue (high scores, wrong content)")
        print("  → This indicates a problem with the INDEX CONTENT, not the search methods")
    elif len(problematic_methods) > 0:
        print(f"  ⚠️  Some methods affected ({len(problematic_methods)}/{len(results_summary)})")
        print("  → Could be content-type specific issue")
    else:
        print("  ✓ No methods show the high score/wrong content issue")

if __name__ == "__main__":
    asyncio.run(test_all_search_tools())