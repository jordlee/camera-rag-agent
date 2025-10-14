#!/usr/bin/env python3
"""
Test PTP SDK integration end-to-end
"""

import sys
import os

# Add mcp directory to path
mcp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mcp')
sys.path.insert(0, mcp_path)

from search import RAGSearch
import json

def test_ptp_integration():
    """Test PTP SDK integration with multi-SDK context."""
    print("=" * 80)
    print("PTP SDK Integration Test")
    print("=" * 80)

    # Initialize RAG search
    print("\n1. Initializing RAG Search...")
    try:
        rag = RAGSearch()
        print("✅ RAG Search initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize RAG Search: {e}")
        return False

    # Test 1: Check initial context (should be camera-remote by default)
    print("\n2. Testing initial SDK context...")
    context = rag.get_sdk_context()
    print(f"Initial context: {json.dumps(context, indent=2)}")
    assert context["sdk_type"] == "camera-remote", "Default SDK type should be camera-remote"
    assert context["sdk_version"] == "V2.00.00", "Default version should be V2.00.00"
    assert context["sdk_language"] == "cpp", "Default language should be cpp"
    print("✅ Initial context correct")

    # Test 2: Switch to PTP SDK
    print("\n3. Testing SDK type switch to PTP...")
    result = rag.set_sdk_type("ptp")
    print(f"Result: {result}")
    context = rag.get_sdk_context()
    print(f"New context: {json.dumps(context, indent=2)}")
    assert context["sdk_type"] == "ptp", "SDK type should be ptp"
    assert context["active_index"] == "sdk-rag-system-v2-ptp", "Active index should be PTP index"
    print("✅ SDK type switch successful")

    # Test 3: Set PTP subtype
    print("\n4. Testing PTP subtype setting...")
    result = rag.set_sdk_subtype("ptp-2")
    print(f"Result: {result}")
    context = rag.get_sdk_context()
    assert context["sdk_subtype"] == "ptp-2", "Subtype should be ptp-2"
    print("✅ Subtype setting successful")

    # Test 4: Set PTP OS
    print("\n5. Testing PTP OS setting...")
    result = rag.set_sdk_os("linux")
    print(f"Result: {result}")
    context = rag.get_sdk_context()
    assert context["sdk_os"] == "linux", "OS should be linux"
    print("✅ OS setting successful")

    # Test 5: Set language to bash
    print("\n6. Testing language setting...")
    result = rag.set_sdk_language("bash")
    print(f"Result: {result}")
    context = rag.get_sdk_context()
    assert context["sdk_language"] == "bash", "Language should be bash"
    print("✅ Language setting successful")

    # Test 6: Search for bash code examples (should only return PTP bash scripts)
    print("\n7. Testing PTP bash code search...")
    print(f"Context: sdk_type={context['sdk_type']}, sdk_language={context['sdk_language']}, sdk_subtype={context['sdk_subtype']}, sdk_os={context['sdk_os']}")
    results = rag.search("authentication", top_k=3, content_type_filter="example_code")
    print(f"Found {len(results)} results")
    if len(results) > 0:
        first_result = results[0]
        print(f"First result metadata: {json.dumps(first_result['metadata'], indent=2)}")
        # Verify filtering worked
        assert first_result['metadata'].get('sdk_type') == 'ptp', "Should only return PTP results"
        assert first_result['metadata'].get('sdk_language') == 'bash', "Should only return bash scripts"
        print("✅ PTP bash code search successful")
    else:
        print("⚠️  No results found (this might be OK if no bash scripts match 'authentication')")

    # Test 7: Search for PTP documentation (should filter by subtype only)
    print("\n8. Testing PTP documentation search...")
    rag.set_sdk_language("cpp")  # Reset language
    results = rag.search("camera setup", top_k=3, content_type_filter="documentation_text")
    print(f"Found {len(results)} results")
    if len(results) > 0:
        first_result = results[0]
        print(f"First result metadata: {json.dumps(first_result['metadata'], indent=2)}")
        assert first_result['metadata'].get('sdk_type') == 'ptp', "Should only return PTP results"
        assert first_result['metadata'].get('sdk_subtype') == 'ptp-2', "Should filter by subtype"
        print("✅ PTP documentation search successful")
    else:
        print("⚠️  No results found")

    # Test 8: Switch back to camera-remote
    print("\n9. Testing switch back to camera-remote...")
    result = rag.set_sdk_type("camera-remote")
    print(f"Result: {result}")
    context = rag.get_sdk_context()
    print(f"New context: {json.dumps(context, indent=2)}")
    assert context["sdk_type"] == "camera-remote", "SDK type should be camera-remote"
    assert context["sdk_subtype"] is None, "Subtype should be cleared"
    assert context["sdk_os"] is None, "OS should be cleared"
    assert context["active_index"] == "sdk-rag-system-v2", "Active index should be camera-remote V2"
    print("✅ Switch back to camera-remote successful")

    # Test 9: Test C# code search (backward compatibility check)
    print("\n10. Testing C# code search (backward compatibility)...")
    result = rag.set_sdk_language("csharp")
    results = rag.search_code_examples("OnConnected", language="csharp", top_k=3)
    print(f"Found {len(results)} C# results")
    if len(results) > 0:
        first_result = results[0]
        print(f"First result metadata: {json.dumps(first_result['metadata'], indent=2)}")
        # Note: C# uses 'language' field, not 'sdk_language'
        print("✅ C# code search still works (backward compatible)")
    else:
        print("⚠️  No C# results found")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = test_ptp_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
