#!/usr/bin/env python3
"""Test script for the MCP server."""

import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

async def test_endpoint(client: httpx.AsyncClient, endpoint: str, description: str) -> Dict[str, Any]:
    """Test a specific endpoint."""
    print(f"\n🔍 Testing: {description}")
    print(f"   Endpoint: {endpoint}")
    
    try:
        response = await client.get(endpoint)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success")
            return {"success": True, "data": data}
        else:
            print(f"   ❌ Failed: {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"   💥 Error: {e}")
        return {"success": False, "error": str(e)}

async def test_search(client: httpx.AsyncClient, query: str, endpoint: str = "/search") -> Dict[str, Any]:
    """Test search functionality."""
    print(f"\n🔍 Testing search: '{query}'")
    print(f"   Endpoint: {endpoint}")
    
    try:
        response = await client.get(f"{BASE_URL}{endpoint}?q={query}&top_k=3")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"   ✅ Found {len(results)} results")
            
            # Show first result
            if results:
                first_result = results[0]
                print(f"   📄 Top result:")
                print(f"      ID: {first_result['id']}")
                print(f"      Score: {first_result['score']:.4f}")
                print(f"      Type: {first_result['metadata'].get('type', 'unknown')}")
                print(f"      Content: {first_result['content'][:100]}...")
            
            return {"success": True, "data": data}
        else:
            print(f"   ❌ Failed: {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"   💥 Error: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Main test function."""
    print("🚀 Testing MCP Server")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test basic endpoints
        await test_endpoint(client, f"{BASE_URL}/", "Root endpoint")
        await test_endpoint(client, f"{BASE_URL}/health", "Health check")
        await test_endpoint(client, f"{BASE_URL}/stats", "Index statistics")
        await test_endpoint(client, f"{BASE_URL}/mcp/tools", "MCP tool definitions")
        
        # Test search functionality
        test_queries = [
            ("camera connection", "/search"),
            ("CameraDevice connect", "/search/code"),
            ("API documentation", "/search/docs"),
            ("function parameters", "/search/functions")
        ]
        
        for query, endpoint in test_queries:
            await test_search(client, query, endpoint)
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")
    print("\nIf all tests passed, your MCP server is ready for deployment!")

if __name__ == "__main__":
    print("Make sure the server is running with: python mcp/server.py")
    print("Then run this test script in another terminal")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")