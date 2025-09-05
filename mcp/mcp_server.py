#!/usr/bin/env python3
"""
MCP Server for Claude Web Connector
Implements Streamable HTTP transport per MCP specification 2025-06-18
Single /mcp endpoint supporting GET (SSE) and POST (JSON-RPC)
"""

import os
import sys
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Add parent directory to path to import search module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware
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

# Initialize RAG search
rag_search: Optional[RAGSearch] = None

async def handle_mcp_endpoint(request: Request):
    """
    Single MCP endpoint supporting both GET and POST per Streamable HTTP spec
    GET: Returns SSE stream for real-time communication
    POST: Handles JSON-RPC requests directly
    """
    
    # Log origin for debugging, but allow all origins for now
    origin = request.headers.get("origin", "")
    logger.info(f"Request from origin: {origin}")
    
    # TODO: Re-enable origin validation after debugging
    # if origin and not (origin.startswith("https://claude.ai") or origin.startswith("http://localhost")):
    #     logger.warning(f"Rejecting request from invalid origin: {origin}")
    #     return JSONResponse(
    #         {"error": "Invalid origin"}, 
    #         status_code=403,
    #         headers={"Access-Control-Allow-Origin": "https://claude.ai"}
    #     )
    
    # Handle POST requests (JSON-RPC)
    if request.method == "POST":
        return await handle_jsonrpc_request(request)
    
    # Handle GET requests (SSE streaming)
    elif request.method == "GET":
        accept_header = request.headers.get("accept", "")
        
        # Check if client wants SSE streaming
        if "text/event-stream" in accept_header:
            return await handle_sse_stream(request)
        else:
            # Return server info for non-SSE GET requests
            return JSONResponse({
                "name": "SDK RAG MCP Server",
                "version": "1.0.0",
                "protocol": "MCP",
                "protocolVersion": "2025-06-18",
                "transport": "streamable-http",
                "endpoints": {
                    "mcp": "/mcp"
                }
            })

async def handle_jsonrpc_request(request: Request):
    """Handle JSON-RPC 2.0 requests from Claude web"""
    try:
        data = await request.json()
        
        # Validate JSON-RPC 2.0 format
        if data.get("jsonrpc") != "2.0":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {"code": -32600, "message": "Invalid Request"}
            })
        
        method = data.get("method")
        params = data.get("params", {})
        msg_id = data.get("id")
        
        logger.info(f"Received JSON-RPC method: {method}, params: {params}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Route to appropriate handler
        if method == "initialize":
            result = await handle_initialize(params)
        elif method == "tools/list":
            result = await handle_tools_list(params)
        elif method == "tools/call":
            result = await handle_tool_call(params)
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })
        
        # Return successful response
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        })
        
    except json.JSONDecodeError:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error"}
        })
    except Exception as e:
        logger.error(f"JSON-RPC handler error: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": data.get("id") if 'data' in locals() else None,
            "error": {"code": -32603, "message": str(e)}
        })

async def handle_sse_stream(request: Request):
    """Handle SSE streaming for real-time communication"""
    
    async def event_generator():
        try:
            # Send initial ready message with unique event ID
            yield f"id: init-1\n"
            yield f"event: message\n"
            yield f"data: {json.dumps({'jsonrpc': '2.0', 'method': 'server/ready', 'params': {}})}\n\n"
            
            # Keep connection alive with periodic pings
            counter = 2
            while True:
                await asyncio.sleep(30)
                yield f"id: ping-{counter}\n"
                yield f"event: message\n"
                yield f"data: {json.dumps({'jsonrpc': '2.0', 'method': 'ping', 'params': {}})}\n\n"
                counter += 1
                
        except asyncio.CancelledError:
            logger.info("SSE stream cancelled by client")
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Accept, Content-Type, Authorization",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        }
    )

async def handle_initialize(params: dict) -> dict:
    """Handle MCP initialize request"""
    return {
        "protocolVersion": "2025-06-18",
        "capabilities": {
            "tools": {
                "listChanged": True
            }
        },
        "serverInfo": {
            "name": "sdk-rag-server",
            "version": "1.0.0"
        }
    }

async def handle_tools_list(params: dict) -> dict:
    """Handle tools/list request"""
    return {
        "tools": [
            {
                "name": "search_sdk",
                "description": "Search the Camera Remote SDK documentation and code examples",
                "inputSchema": {
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
                            "enum": ["example_code", "documentation_text", "documentation_table", 
                                   "function", "enum", "variable", "summary", "typedef", "define"]
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_code_examples",
                "description": "Search specifically for C++ code examples and implementations",
                "inputSchema": {
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
            },
            {
                "name": "search_documentation",
                "description": "Search SDK documentation text (guides, tutorials, explanations)",
                "inputSchema": {
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
            },
            {
                "name": "get_sdk_stats",
                "description": "Get statistics about the SDK documentation database",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }

async def handle_tool_call(params: dict) -> dict:
    """Handle tools/call request"""
    global rag_search
    
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if rag_search is None:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "RAG search system not initialized"
                }
            ]
        }
    
    try:
        if tool_name == "search_sdk":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            content_type = arguments.get("content_type")
            
            results = rag_search.search(query, top_k=top_k, content_type_filter=content_type)
            
        elif tool_name == "search_code_examples":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            results = rag_search.search(query, top_k=top_k, content_type_filter="example_code")
            
        elif tool_name == "search_documentation":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            results = rag_search.search(query, top_k=top_k, content_type_filter="documentation_text")
            
        elif tool_name == "get_sdk_stats":
            results = rag_search.get_stats()
            
        else:
            results = {"error": f"Unknown tool: {tool_name}"}
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(results, indent=2)
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Tool call error for {tool_name}: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error executing {tool_name}: {str(e)}"
                }
            ]
        }

async def handle_health(request: Request):
    """Health check endpoint for Railway"""
    return JSONResponse({
        "status": "healthy",
        "service": "claude-mcp-server",
        "rag_initialized": rag_search is not None,
        "protocol_version": "2025-06-18"
    })

async def startup():
    """Initialize RAG search system on startup"""
    global rag_search
    try:
        logger.info("Initializing RAG search system...")
        rag_search = RAGSearch()
        logger.info("RAG search system initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize RAG search: {e}")
        rag_search = None

# Create Starlette application
app = Starlette(
    routes=[
        Route("/mcp", handle_mcp_endpoint, methods=["GET", "POST", "OPTIONS"]),
        Route("/health", handle_health),
    ],
    on_startup=[startup]
)

# Add CORS middleware for Claude web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://claude.ai", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "Authorization", "Origin"],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting Claude MCP server on {host}:{port}")
    logger.info(f"MCP endpoint available at: http://{host}:{port}/mcp")
    uvicorn.run(app, host=host, port=port, log_level="info")