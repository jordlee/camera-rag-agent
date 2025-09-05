#!/usr/bin/env python3
"""
Test MCP SSE client to verify the server works correctly
"""
import aiohttp
import asyncio
import json
import time

async def test_mcp_server():
    """Test the MCP SSE server functionality"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("🔄 Testing MCP SSE Server...")
        
        # Step 1: Connect to SSE endpoint
        print("\n1. Connecting to SSE endpoint...")
        async with session.get(f"{base_url}/sse") as resp:
            if resp.status != 200:
                print(f"❌ SSE connection failed: {resp.status}")
                return
            
            # Read the endpoint event
            async for line in resp.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    endpoint_path = line[6:]  # Remove 'data: '
                    print(f"✅ Got endpoint: {endpoint_path}")
                    break
        
        # Step 2: Extract session ID and test messages endpoint
        if '?' in endpoint_path:
            messages_url = f"{base_url}{endpoint_path}"
            print(f"\n2. Testing messages endpoint: {messages_url}")
            
            # Test tools/list
            print("\n3. Testing tools/list...")
            tools_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            async with session.post(messages_url, json=tools_request) as resp:
                if resp.status == 200:
                    tools_response = await resp.json()
                    print(f"✅ Tools list response: {json.dumps(tools_response, indent=2)}")
                    
                    # Test tool call
                    print("\n4. Testing tool call...")
                    tool_request = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "search_sdk",
                            "arguments": {
                                "query": "camera connect",
                                "top_k": 2
                            }
                        }
                    }
                    
                    async with session.post(messages_url, json=tool_request) as tool_resp:
                        if tool_resp.status == 200:
                            tool_response = await tool_resp.json()
                            print(f"✅ Tool call response: {json.dumps(tool_response, indent=2)}")
                        else:
                            print(f"❌ Tool call failed: {tool_resp.status}")
                            print(await tool_resp.text())
                else:
                    print(f"❌ Tools list failed: {resp.status}")
                    print(await resp.text())

if __name__ == "__main__":
    asyncio.run(test_mcp_server())