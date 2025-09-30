#!/usr/bin/env python3
"""
MCP Server Test Battery
Tests the deployed MCP server for connection stability, timeout handling, and tool functionality.

Usage:
    python test_battery.py

Tests address issues from railway-logs.md:
- ClosedResourceError during MCP handshake
- Embedding timeout (4.23s exceeding 3s limit)
- Connection drops during tool execution
"""

import asyncio
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import httpx

# Configuration
MCP_SERVER_URL = "https://sdk-rag-agent-production.up.railway.app/mcp"
HEALTH_URL = "https://sdk-rag-agent-production.up.railway.app/health"
TIMEOUT = 30.0  # seconds

class TestResult:
    def __init__(self, test_name: str, phase: str):
        self.test_name = test_name
        self.phase = phase
        self.success = False
        self.duration = 0.0
        self.error = None
        self.response = None
        self.notes = []

    def to_dict(self):
        return {
            "test_name": self.test_name,
            "phase": self.phase,
            "success": self.success,
            "duration": self.duration,
            "error": str(self.error) if self.error else None,
            "notes": self.notes
        }

class MCPTestBattery:
    def __init__(self):
        self.results: List[TestResult] = []
        self.request_id = 1

    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool via SSE endpoint."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        self.request_id += 1

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(MCP_SERVER_URL, json=payload, headers=headers)

            # Parse SSE response
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    return data

            raise ValueError("No data in SSE response")

    async def list_tools(self) -> Dict[str, Any]:
        """List available MCP tools."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/list"
        }

        self.request_id += 1

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(MCP_SERVER_URL, json=payload, headers=headers)

            # Parse SSE response
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    return data

            raise ValueError("No data in SSE response")

    async def check_health(self) -> Dict[str, Any]:
        """Check server health."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(HEALTH_URL)
            return response.json()

    # ==================== PHASE 1: Connection & Tool Discovery ====================

    async def phase1_test1_list_tools(self):
        """Test 1: List all available tools"""
        result = TestResult("List all available tools", "Phase 1")
        start = time.time()

        try:
            response = await self.list_tools()
            result.duration = time.time() - start

            if "result" in response and "tools" in response["result"]:
                tools = response["result"]["tools"]
                result.success = True
                result.notes.append(f"Found {len(tools)} tools")
                result.notes.append(f"Tools: {[t['name'] for t in tools]}")
            else:
                result.error = "No tools in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase1_test2_get_stats(self):
        """Test 2: Get SDK stats (quick tool)"""
        result = TestResult("Get SDK stats", "Phase 1")
        start = time.time()

        try:
            response = await self.call_mcp_tool("get_sdk_stats", {})
            result.duration = time.time() - start

            if "result" in response:
                stats_data = json.loads(response["result"]["result"])
                result.success = True
                result.notes.append(f"Database vectors: {stats_data.get('database', {}).get('total_vectors', 'N/A')}")
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase1_test3_list_tools_again(self):
        """Test 3: List tools again (test reconnection)"""
        result = TestResult("List tools again (reconnection test)", "Phase 1")
        start = time.time()

        try:
            response = await self.list_tools()
            result.duration = time.time() - start

            if "result" in response and "tools" in response["result"]:
                result.success = True
                result.notes.append("Reconnection successful")
            else:
                result.error = "No tools in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase1_test4_health_check(self):
        """Test 4: Health check validation"""
        result = TestResult("Health check validation", "Phase 1")
        start = time.time()

        try:
            response = await self.check_health()
            result.duration = time.time() - start

            if response.get("status") == "healthy" and response.get("rag_initialized"):
                result.success = True
                result.notes.append(f"Server healthy, RAG initialized")
                result.notes.append(f"Active connections: {response.get('active_connections', 0)}")
            else:
                result.error = f"Unhealthy: {response}"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase1_test5_rapid_calls(self):
        """Test 5: Rapid consecutive tool calls (stress test)"""
        result = TestResult("Rapid consecutive tool calls", "Phase 1")
        start = time.time()

        try:
            # Make 5 rapid calls
            tasks = [self.call_mcp_tool("get_sdk_stats", {}) for _ in range(5)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            result.duration = time.time() - start

            successes = sum(1 for r in responses if not isinstance(r, Exception))
            result.success = successes == 5
            result.notes.append(f"Successful calls: {successes}/5")
            result.notes.append(f"Total time: {result.duration:.2f}s")

            if not result.success:
                errors = [str(r) for r in responses if isinstance(r, Exception)]
                result.notes.append(f"Errors: {errors}")

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    # ==================== PHASE 2: Timeout & Performance Tests ====================

    async def phase2_test1_simple_query(self):
        """Test 2.1: Simple query - 'connect to camera'"""
        result = TestResult("Simple query: 'connect to camera'", "Phase 2")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_sdk", {
                "query": "connect to camera",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                search_data = json.loads(response["result"]["result"])
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
                result.notes.append(f"Fallback triggered: {search_data.get('fallback', False)}")
                result.notes.append(f"Results found: {len(search_data.get('results', []))}")

                # Check for timeout
                if result.duration > 8.0:
                    result.notes.append("⚠️ WARNING: Exceeded 8s timeout threshold")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase2_test2_complex_query(self):
        """Test 2.2: Complex multi-intent query"""
        result = TestResult("Complex query: multi-step workflow", "Phase 2")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_sdk", {
                "query": "After connecting to camera, how do I save images to a specific folder?",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                search_data = json.loads(response["result"]["result"])
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
                result.notes.append(f"Fallback triggered: {search_data.get('fallback', False)}")

                if result.duration > 8.0:
                    result.notes.append("⚠️ WARNING: Exceeded 8s timeout threshold")

                # Check if fallback was used appropriately
                if result.duration > 8.0 and not search_data.get('fallback'):
                    result.notes.append("❌ ERROR: Timeout occurred but fallback not triggered")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase2_test3_natural_language(self):
        """Test 2.3: Natural language query"""
        result = TestResult("Natural language: 'How do I establish a connection'", "Phase 2")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_sdk", {
                "query": "How do I establish a connection with my Sony camera?",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase2_test4_technical_query(self):
        """Test 2.4: Technical query with exact API name"""
        result = TestResult("Technical query: 'SCRSDK Connect function parameters'", "Phase 2")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_sdk", {
                "query": "SCRSDK Connect function parameters",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    # ==================== PHASE 3: Tool-Specific Tests ====================

    async def phase3_test1_search_code(self):
        """Test 3.1: search_code_examples"""
        result = TestResult("search_code_examples: 'camera connection code'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_code_examples", {
                "query": "camera connection code",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase3_test2_search_docs(self):
        """Test 3.2: search_documentation"""
        result = TestResult("search_documentation: 'camera remote SDK guide'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_documentation", {
                "query": "camera remote SDK guide",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase3_test3_search_api(self):
        """Test 3.3: search_api_functions"""
        result = TestResult("search_api_functions: 'SetSaveInfo'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_api_functions", {
                "query": "SetSaveInfo",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase3_test4_search_compat(self):
        """Test 3.4: search_compatibility"""
        result = TestResult("search_compatibility: 'ILX-LR1 support'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_compatibility", {
                "query": "ILX-LR1 support",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase3_test5_exact_api(self):
        """Test 3.5: search_exact_api"""
        result = TestResult("search_exact_api: 'SetSaveInfo'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_exact_api", {
                "api_name": "SetSaveInfo",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase3_test6_error_codes(self):
        """Test 3.6: search_error_codes"""
        result = TestResult("search_error_codes: 'CrError_Connect_TimeOut'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_error_codes", {
                "error_code": "CrError_Connect_TimeOut",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase3_test7_warning_codes(self):
        """Test 3.7: search_warning_codes"""
        result = TestResult("search_warning_codes: 'CrWarning_BatteryLow'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_warning_codes", {
                "warning_code": "CrWarning_BatteryLow",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase3_test8_hybrid(self):
        """Test 3.8: search_hybrid"""
        result = TestResult("search_hybrid: 'connect to camera'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_hybrid", {
                "query": "connect to camera",
                "top_k": 10
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase3_test9_by_source(self):
        """Test 3.9: search_by_source_file"""
        result = TestResult("search_by_source_file: 'CameraDevice.cpp'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_by_source_file", {
                "file_name": "CameraDevice.cpp",
                "query": "",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase3_test10_intent_analysis(self):
        """Test 3.10: search_with_intent_analysis"""
        result = TestResult("search_with_intent_analysis: 'save file location'", "Phase 3")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_with_intent_analysis", {
                "query": "save file location",
                "top_k": 10,
                "explain_intent": True
            })
            result.duration = time.time() - start

            if "result" in response:
                search_data = json.loads(response["result"]["result"])
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")

                # Check for intent expansion
                if "intent_analysis" in search_data:
                    intent = search_data["intent_analysis"]
                    result.notes.append(f"Expansion successful: {intent.get('expansion_successful', False)}")
                    if intent.get('expansion_successful'):
                        result.notes.append(f"Expanded query available")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    # ==================== PHASE 4: Stress & Edge Cases ====================

    async def phase4_test1_long_query(self):
        """Test 4.1: Long query (500+ chars)"""
        long_query = "I need to understand how to properly establish a connection to my Sony camera using the Camera Remote SDK, then configure the save location for images, set up the exposure mode to manual, adjust the focus position, and finally start capturing images while monitoring for any error codes or warnings that might occur during this process. Can you provide detailed documentation and code examples?" * 2

        result = TestResult("Long query (500+ chars)", "Phase 4")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_sdk", {
                "query": long_query[:500],  # Truncate to 500
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase4_test2_empty_query(self):
        """Test 4.2: Empty query"""
        result = TestResult("Empty query error handling", "Phase 4")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_sdk", {
                "query": "",
                "top_k": 5
            })
            result.duration = time.time() - start

            # Empty query should either return error or handle gracefully
            if "error" in response:
                result.success = True
                result.notes.append("Properly handled empty query with error")
            elif "result" in response:
                result.success = True
                result.notes.append("Handled empty query gracefully")
            else:
                result.error = "Unexpected response format"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            # Exception is acceptable for empty query
            result.success = True
            result.notes.append(f"Raised exception (acceptable): {type(e).__name__}")

        self.results.append(result)
        return result

    async def phase4_test3_special_chars(self):
        """Test 4.3: Special characters query"""
        result = TestResult("Special characters: 'C++ SDK::Connect()'", "Phase 4")
        start = time.time()

        try:
            response = await self.call_mcp_tool("search_sdk", {
                "query": "C++ SDK::Connect()",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase4_test4_rapid_searches(self):
        """Test 4.4: 5 rapid consecutive searches"""
        result = TestResult("5 rapid consecutive searches", "Phase 4")
        start = time.time()

        try:
            queries = [
                "connect to camera",
                "save file location",
                "get camera settings",
                "error codes",
                "compatibility"
            ]

            tasks = [
                self.call_mcp_tool("search_sdk", {"query": q, "top_k": 5})
                for q in queries
            ]

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            result.duration = time.time() - start

            successes = sum(1 for r in responses if not isinstance(r, Exception))
            result.success = successes == 5
            result.notes.append(f"Successful searches: {successes}/5")
            result.notes.append(f"Total time: {result.duration:.2f}s")
            result.notes.append(f"Avg time per search: {result.duration/5:.2f}s")

            if not result.success:
                errors = [str(r) for r in responses if isinstance(r, Exception)]
                result.notes.append(f"Errors: {errors[:2]}")  # Show first 2 errors

        except Exception as e:
            result.duration = time.time() - start
            result.error = e

        self.results.append(result)
        return result

    async def phase4_test5_timeout_recovery(self):
        """Test 4.5: Connection timeout recovery (wait 30s then search)"""
        result = TestResult("Connection timeout recovery (30s wait)", "Phase 4")

        try:
            result.notes.append("Waiting 30 seconds...")
            await asyncio.sleep(30)

            start = time.time()
            response = await self.call_mcp_tool("search_sdk", {
                "query": "connect to camera",
                "top_k": 5
            })
            result.duration = time.time() - start

            if "result" in response:
                result.success = True
                result.notes.append("Connection recovered successfully")
                result.notes.append(f"Response time: {result.duration:.2f}s")
            else:
                result.error = "No result in response"

            result.response = response

        except Exception as e:
            result.duration = time.time() - start if 'start' in locals() else 0
            result.error = e

        self.results.append(result)
        return result

    # ==================== Test Execution ====================

    async def run_all_tests(self):
        """Run all test phases."""
        print("=" * 80)
        print("MCP SERVER TEST BATTERY")
        print("=" * 80)
        print(f"Server: {MCP_SERVER_URL}")
        print(f"Started: {datetime.now().isoformat()}")
        print()

        # Phase 1: Connection & Tool Discovery
        print("\n" + "=" * 80)
        print("PHASE 1: Connection & Tool Discovery Tests (5 tests)")
        print("=" * 80)

        await self.phase1_test1_list_tools()
        print(f"✓ Test 1.1 - {self.results[-1].success}")

        await self.phase1_test2_get_stats()
        print(f"✓ Test 1.2 - {self.results[-1].success}")

        await self.phase1_test3_list_tools_again()
        print(f"✓ Test 1.3 - {self.results[-1].success}")

        await self.phase1_test4_health_check()
        print(f"✓ Test 1.4 - {self.results[-1].success}")

        await self.phase1_test5_rapid_calls()
        print(f"✓ Test 1.5 - {self.results[-1].success}")

        # Phase 2: Timeout & Performance
        print("\n" + "=" * 80)
        print("PHASE 2: Timeout & Performance Tests (4 tests)")
        print("=" * 80)

        await self.phase2_test1_simple_query()
        print(f"✓ Test 2.1 - {self.results[-1].success} ({self.results[-1].duration:.2f}s)")

        await self.phase2_test2_complex_query()
        print(f"✓ Test 2.2 - {self.results[-1].success} ({self.results[-1].duration:.2f}s)")

        await self.phase2_test3_natural_language()
        print(f"✓ Test 2.3 - {self.results[-1].success} ({self.results[-1].duration:.2f}s)")

        await self.phase2_test4_technical_query()
        print(f"✓ Test 2.4 - {self.results[-1].success} ({self.results[-1].duration:.2f}s)")

        # Phase 3: Tool-Specific Tests
        print("\n" + "=" * 80)
        print("PHASE 3: Tool-Specific Tests (10 tests)")
        print("=" * 80)

        await self.phase3_test1_search_code()
        print(f"✓ Test 3.1 - {self.results[-1].success}")

        await self.phase3_test2_search_docs()
        print(f"✓ Test 3.2 - {self.results[-1].success}")

        await self.phase3_test3_search_api()
        print(f"✓ Test 3.3 - {self.results[-1].success}")

        await self.phase3_test4_search_compat()
        print(f"✓ Test 3.4 - {self.results[-1].success}")

        await self.phase3_test5_exact_api()
        print(f"✓ Test 3.5 - {self.results[-1].success}")

        await self.phase3_test6_error_codes()
        print(f"✓ Test 3.6 - {self.results[-1].success}")

        await self.phase3_test7_warning_codes()
        print(f"✓ Test 3.7 - {self.results[-1].success}")

        await self.phase3_test8_hybrid()
        print(f"✓ Test 3.8 - {self.results[-1].success}")

        await self.phase3_test9_by_source()
        print(f"✓ Test 3.9 - {self.results[-1].success}")

        await self.phase3_test10_intent_analysis()
        print(f"✓ Test 3.10 - {self.results[-1].success}")

        # Phase 4: Stress & Edge Cases
        print("\n" + "=" * 80)
        print("PHASE 4: Stress & Edge Case Tests (5 tests)")
        print("=" * 80)

        await self.phase4_test1_long_query()
        print(f"✓ Test 4.1 - {self.results[-1].success}")

        await self.phase4_test2_empty_query()
        print(f"✓ Test 4.2 - {self.results[-1].success}")

        await self.phase4_test3_special_chars()
        print(f"✓ Test 4.3 - {self.results[-1].success}")

        await self.phase4_test4_rapid_searches()
        print(f"✓ Test 4.4 - {self.results[-1].success}")

        await self.phase4_test5_timeout_recovery()
        print(f"✓ Test 4.5 - {self.results[-1].success}")

        # Summary
        self.print_summary()

        # Save detailed results
        self.save_results()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed

        print(f"Total tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print()

        # Phase breakdown
        phases = {}
        for r in self.results:
            if r.phase not in phases:
                phases[r.phase] = {"total": 0, "passed": 0}
            phases[r.phase]["total"] += 1
            if r.success:
                phases[r.phase]["passed"] += 1

        for phase, stats in sorted(phases.items()):
            print(f"{phase}: {stats['passed']}/{stats['total']} passed")

        print()

        # Failed tests
        if failed > 0:
            print("Failed Tests:")
            for r in self.results:
                if not r.success:
                    print(f"  - {r.test_name}: {r.error}")

        # Performance stats for Phase 2
        phase2_results = [r for r in self.results if r.phase == "Phase 2" and r.success]
        if phase2_results:
            avg_time = sum(r.duration for r in phase2_results) / len(phase2_results)
            max_time = max(r.duration for r in phase2_results)
            print(f"\nPhase 2 Performance:")
            print(f"  Average response time: {avg_time:.2f}s")
            print(f"  Max response time: {max_time:.2f}s")

            if max_time > 8.0:
                print(f"  ⚠️ WARNING: Some queries exceeded 8s timeout threshold")

        print()

    def save_results(self):
        """Save detailed results to JSON file."""
        output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "server_url": MCP_SERVER_URL,
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results if r.success),
                "failed": sum(1 for r in self.results if not r.success)
            },
            "results": [r.to_dict() for r in self.results]
        }

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"Detailed results saved to: {output_file}")

async def main():
    """Main entry point."""
    battery = MCPTestBattery()

    try:
        await battery.run_all_tests()

        # Exit with appropriate code
        failed = sum(1 for r in battery.results if not r.success)
        sys.exit(1 if failed > 0 else 0)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
