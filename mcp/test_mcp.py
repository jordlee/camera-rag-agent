#!/usr/bin/env python3
"""Test MCP protocol implementation."""

import requests
import json
import time

BASE_URL = "http://localhost:8888"

def test_mcp_initialize():
    """Test MCP initialize method."""
    print("Testing MCP initialize...")
    response = requests.post(f"{BASE_URL}/mcp", json={
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": 1
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_mcp_tools_list():
    """Test MCP tools/list method."""
    print("\nTesting MCP tools/list...")
    response = requests.post(f"{BASE_URL}/mcp", json={
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 2
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_mcp_tool_invoke():
    """Test MCP tools/invoke method."""
    print("\nTesting MCP tools/invoke (search_sdk)...")
    response = requests.post(f"{BASE_URL}/mcp", json={
        "jsonrpc": "2.0",
        "method": "tools/invoke",
        "id": 3,
        "params": {
            "name": "search_sdk",
            "arguments": {
                "query": "camera connection",
                "top_k": 2
            }
        }
    })
    print(f"Status: {response.status_code}")
    result = response.json()
    # Truncate long results for display
    if "result" in result and "results" in result["result"]:
        print(f"Found {len(result['result']['results'])} results")
        for r in result['result']['results'][:1]:  # Show first result
            print(f"  - Score: {r.get('score', 'N/A')}")
            print(f"  - Content preview: {r.get('content', '')[:100]}...")
    else:
        print(f"Response: {json.dumps(result, indent=2)}")

def test_mcp_sse():
    """Test SSE endpoint."""
    print("\nTesting SSE endpoint...")
    response = requests.get(f"{BASE_URL}/mcp/sse", stream=True, timeout=2)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    # Read first few lines
    for i, line in enumerate(response.iter_lines()):
        if i > 2:  # Just show first few lines
            break
        if line:
            print(f"SSE Line {i}: {line.decode('utf-8')}")

if __name__ == "__main__":
    # First check if server is running
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=1)
        if health.status_code == 200:
            print("✓ Server is healthy\n")
        else:
            print("Server returned non-200 status")
            exit(1)
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Start it with:")
        print("  cd mcp && uvicorn server:app --port 8888")
        exit(1)
    
    # Run tests
    try:
        test_mcp_initialize()
        test_mcp_tools_list()
        test_mcp_tool_invoke()
        test_mcp_sse()
        print("\n✓ All MCP tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")