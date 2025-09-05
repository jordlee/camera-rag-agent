#!/usr/bin/env python3
"""
Proper MCP Server with SSE transport following official MCP specification
"""

import os
import sys
import uuid
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Add parent directory to path to import search module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
import mcp.types as types
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.requests import Request
import uvicorn

# Import our existing search functionality
from search import RAGSearch

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("sdk-rag-server")
rag_search: Optional[RAGSearch] = None

# Session management
active_sessions = {}

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """Return the list of available tools for the MCP client."""
    return [
        types.Tool(
            name="search_sdk",
            description="Search the Camera Remote SDK documentation and code examples",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for SDK information"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Filter by content type",
                        "enum": ["example_code", "documentation_text", "documentation_table", "function", "enum", "variable", "summary", "typedef", "define"]
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_code_examples",
            description="Search specifically for C++ code examples and implementations",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for C++ code examples"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_documentation",
            description="Search SDK documentation text (guides, tutorials, explanations)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for documentation"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_compatibility",
            description="Search camera compatibility tables and structured data",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for camera compatibility"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_api_functions",
            description="Search API function definitions and signatures",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for API functions"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_sdk_stats",
            description="Get statistics about the SDK documentation database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle tool calls from the MCP client."""
    global rag_search
    
    if rag_search is None:
        return [types.TextContent(type="text", text="RAG search system not initialized")]
    
    try:
        if name == "search_sdk":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            content_type = arguments.get("content_type")
            
            results = rag_search.search(query, top_k=top_k, content_type_filter=content_type)
            
        elif name == "search_code_examples":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            results = rag_search.search(query, top_k=top_k, content_type_filter="example_code")
            
        elif name == "search_documentation":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            results = rag_search.search(query, top_k=top_k, content_type_filter="documentation_text")
            
        elif name == "search_compatibility":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            results = rag_search.search(query, top_k=top_k, content_type_filter="documentation_table")
            
        elif name == "search_api_functions":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            results = rag_search.search(query, top_k=top_k, content_type_filter="function")
            
        elif name == "get_sdk_stats":
            results = rag_search.get_stats()
            
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        
        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
    except Exception as e:
        logger.error(f"Error in tool call {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def mcp_sse_handler(request: Request):
    """Handle MCP SSE connections - provides the /sse endpoint."""
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Store session - keep it alive for longer
    active_sessions[session_id] = {
        "created_at": asyncio.get_event_loop().time(),
        "last_ping": asyncio.get_event_loop().time()
    }
    
    async def event_stream():
        try:
            # Send endpoint event as required by MCP spec
            endpoint_url = f"/messages?session_id={session_id}"
            yield f"event: endpoint\n"
            yield f"data: {endpoint_url}\n\n"
            
            # Send one ping and then finish
            # Session will remain active for messages
            await asyncio.sleep(1)
            yield f": ping - {asyncio.get_event_loop().time()}\n\n"
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        }
    )

async def mcp_messages_handler(request: Request):
    """Handle MCP messages - provides the /messages endpoint for JSON-RPC."""
    session_id = request.query_params.get("session_id")
    
    # Be more permissive with sessions for testing
    if not session_id:
        return JSONResponse({"error": "Missing session_id"}, status_code=400)
    
    # Auto-create session if it doesn't exist (for testing)
    if session_id not in active_sessions:
        active_sessions[session_id] = {
            "created_at": asyncio.get_event_loop().time(),
            "last_ping": asyncio.get_event_loop().time()
        }
    
    try:
        data = await request.json()
        
        # Handle JSON-RPC 2.0 messages
        if data.get("jsonrpc") != "2.0":
            return JSONResponse({
                "jsonrpc": "2.0", 
                "id": data.get("id"),
                "error": {"code": -32600, "message": "Invalid Request"}
            }, status_code=400)
        
        method = data.get("method")
        params = data.get("params", {})
        msg_id = data.get("id")
        
        # Handle different MCP methods
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                    },
                    "serverInfo": {
                        "name": "sdk-rag-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            tools = await handle_list_tools()
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        } for tool in tools
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            results = await handle_call_tool(tool_name, arguments)
            
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": content.type,
                            "text": content.text
                        } for content in results
                    ]
                }
            }
        
        else:
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
        
        return JSONResponse(response)
        
    except Exception as e:
        logger.error(f"Messages handler error: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": data.get("id") if 'data' in locals() else None,
            "error": {"code": -32603, "message": str(e)}
        }, status_code=500)

async def health_check(request):
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "service": "mcp-sse-server", "rag_initialized": rag_search is not None})

async def startup():
    """Initialize the RAG search system on startup."""
    global rag_search
    try:
        logger.info("Initializing RAG search system...")
        rag_search = RAGSearch()
        logger.info("RAG search system initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize RAG search: {e}")
        rag_search = None

# Create Starlette app
app = Starlette(
    routes=[
        Route("/sse", mcp_sse_handler),
        Route("/messages", mcp_messages_handler, methods=["POST"]),
        Route("/health", health_check),
    ],
    on_startup=[startup]
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting MCP SSE server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")