#!/usr/bin/env python3
"""
Test all MCP tools with the new GTE embeddings to ensure they work correctly.
This tests both semantic and exact search tools.
"""

from search import RAGSearch

def test_semantic_tools():
    """Test MCP tools that use semantic embeddings (now GTE)"""
    print("🧪 Testing Semantic MCP Tools (using GTE embeddings)")
    print("=" * 55)
    
    rag = RAGSearch()
    
    semantic_tools = [
        ("search_sdk", "ILX-LR1 focus control"),
        ("search_code_examples", "CameraDevice connect"),
        ("search_documentation", "focus position setting"),
        ("search_api_functions", "SetSaveInfo"),
        ("search_compatibility", "ILCE-7RM5 supported features"),
        ("search_hybrid", "CrPriorityKey_PCRemote")
    ]
    
    for tool_name, test_query in semantic_tools:
        print(f"\nTesting {tool_name} with query: '{test_query}'")
        
        try:
            if tool_name == "search_sdk":
                results = rag.search(test_query, top_k=3)
            elif tool_name == "search_code_examples":
                results = rag.search(test_query, top_k=3, content_type_filter="example_code")
            elif tool_name == "search_documentation":
                results = rag.search(test_query, top_k=3, content_type_filter="documentation_text")
            elif tool_name == "search_api_functions":
                results = rag.search(test_query, top_k=3, content_type_filter="function")
            elif tool_name == "search_compatibility":
                results = rag.search(test_query, top_k=3, content_type_filter="documentation_table")
            elif tool_name == "search_hybrid":
                results = rag.search_hybrid(test_query, top_k=3)
            
            print(f"  ✅ Found {len(results)} results")
            
            # Check for problematic content
            has_partial_color = any('Partial Color Yellow' in r.get('content', '') for r in results)
            if has_partial_color:
                print(f"  ❌ Still contains 'Partial Color Yellow'")
            else:
                print(f"  ✅ No 'Partial Color Yellow' found")
            
            # Show top result
            if results:
                top_result = results[0]
                score = top_result.get('score', 0)
                content_preview = top_result.get('content', '')[:100].replace('\n', ' ').strip()
                print(f"  Top result: Score {score:.4f} - {content_preview}...")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_exact_tools():
    """Test MCP tools that use exact matching (should work regardless of embeddings)"""
    print(f"\n\n🎯 Testing Exact Matching MCP Tools")
    print("=" * 40)
    
    rag = RAGSearch()
    
    exact_tools = [
        ("search_exact_api", "SetSaveInfo"),
        ("search_error_codes", "CrError_Connect_TimeOut"),
        ("search_warning_codes", "CrWarning_BatteryLow")
    ]
    
    for tool_name, test_query in exact_tools:
        print(f"\nTesting {tool_name} with query: '{test_query}'")
        
        try:
            if tool_name == "search_exact_api":
                results = rag.search_exact_api(test_query, top_k=3)
            elif tool_name == "search_error_codes":
                results = rag.search_error_codes(test_query, top_k=3)
            elif tool_name == "search_warning_codes":
                results = rag.search_warning_codes(test_query, top_k=3)
            
            print(f"  ✅ Found {len(results)} results")
            
            # Show top result
            if results:
                top_result = results[0]
                score = top_result.get('score', 0)
                content_preview = top_result.get('content', '')[:100].replace('\n', ' ').strip()
                print(f"  Top result: Score {score:.4f} - {content_preview}...")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_utility_tools():
    """Test utility MCP tools"""
    print(f"\n\n📊 Testing Utility MCP Tools")
    print("=" * 32)
    
    rag = RAGSearch()
    
    print("Testing get_sdk_stats...")
    try:
        stats = rag.get_stats()
        db_stats = stats.get('database', {})
        total_vectors = db_stats.get('total_vector_count', 0)
        print(f"  ✅ Database contains {total_vectors} vectors")
        print(f"  ✅ Stats retrieved successfully")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    """Main test function"""
    print("🚀 Testing All MCP Tools with GTE Embeddings")
    print("=" * 50)
    
    # Test semantic tools (affected by embedding model change)
    test_semantic_tools()
    
    # Test exact tools (unaffected by embedding model change)  
    test_exact_tools()
    
    # Test utility tools
    test_utility_tools()
    
    print(f"\n{'='*60}")
    print("✅ MCP Tools Testing Complete!")
    print("All tools should now work with GTE embeddings")
    print("No more 'Partial Color Yellow' issues expected")

if __name__ == "__main__":
    main()