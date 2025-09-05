#!/usr/bin/env python3
"""
MCP Server with SSE transport for cloud deployment
Provides Server-Sent Events endpoint for remote MCP clients
"""

import os
import sys
import logging
import asyncio
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Add parent directory to path to import search module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
import mcp.types as types
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
import uvicorn
import json

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
                        "enum": [
                            "example_code",
                            "documentation_text", 
                            "documentation_table",
                            "function",
                            "enum",
                            "variable",
                            "summary",
                            "typedef",
                            "define"
                        ]
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
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool invocations from the MCP client."""
    global rag_search
    
    if not rag_search:
        return [types.TextContent(
            type="text",
            text="Error: RAG search system not initialized"
        )]
    
    try:
        if name == "search_sdk":
            # General SDK search
            results = rag_search.search(
                query=arguments.get("query", ""),
                top_k=arguments.get("top_k", 5),
                content_type_filter=arguments.get("content_type")
            )
            
            # Format results as text
            if results:
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"**Result {i}** (Score: {result['score']:.3f})\n"
                        f"Type: {result['metadata'].get('type', 'unknown')}\n"
                        f"Source: {result['metadata'].get('source', 'unknown')}\n\n"
                        f"{result['content']}\n"
                        f"{'-' * 80}"
                    )
                return [types.TextContent(
                    type="text",
                    text="\n".join(formatted_results)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="No results found for your query."
                )]
        
        elif name == "search_code_examples":
            # Search C++ code examples
            results = rag_search.search_code_examples(
                query=arguments.get("query", ""),
                top_k=arguments.get("top_k", 5)
            )
            
            if results:
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"**Code Example {i}** (Score: {result['score']:.3f})\n"
                        f"Source: {result['metadata'].get('source', 'unknown')}\n\n"
                        f"```cpp\n{result['content']}\n```\n"
                        f"{'-' * 80}"
                    )
                return [types.TextContent(
                    type="text",
                    text="\n".join(formatted_results)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="No code examples found for your query."
                )]
        
        elif name == "search_documentation":
            # Search documentation text
            results = rag_search.search_documentation(
                query=arguments.get("query", ""),
                top_k=arguments.get("top_k", 5)
            )
            
            if results:
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"**Documentation {i}** (Score: {result['score']:.3f})\n"
                        f"Source: {result['metadata'].get('source', 'unknown')}\n\n"
                        f"{result['content']}\n"
                        f"{'-' * 80}"
                    )
                return [types.TextContent(
                    type="text",
                    text="\n".join(formatted_results)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="No documentation found for your query."
                )]
        
        elif name == "search_compatibility":
            # Search compatibility tables
            results = rag_search.search_compatibility_tables(
                query=arguments.get("query", ""),
                top_k=arguments.get("top_k", 5)
            )
            
            if results:
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"**Compatibility Info {i}** (Score: {result['score']:.3f})\n"
                        f"Source: {result['metadata'].get('source', 'unknown')}\n\n"
                        f"{result['content']}\n"
                        f"{'-' * 80}"
                    )
                return [types.TextContent(
                    type="text",
                    text="\n".join(formatted_results)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="No compatibility information found for your query."
                )]
        
        elif name == "search_api_functions":
            # Search API functions
            results = rag_search.search_api_functions(
                query=arguments.get("query", ""),
                top_k=arguments.get("top_k", 5)
            )
            
            if results:
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"**API Function {i}** (Score: {result['score']:.3f})\n"
                        f"Source: {result['metadata'].get('source', 'unknown')}\n\n"
                        f"```cpp\n{result['content']}\n```\n"
                        f"{'-' * 80}"
                    )
                return [types.TextContent(
                    type="text",
                    text="\n".join(formatted_results)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="No API functions found for your query."
                )]
        
        elif name == "get_sdk_stats":
            # Get database statistics
            stats = rag_search.get_index_stats()
            
            formatted_stats = [
                "**SDK Documentation Database Statistics**\n",
                f"Total Chunks: {stats.get('total_chunks', 0)}",
                f"Index Name: {stats.get('index_name', 'unknown')}",
                f"Dimensions: {stats.get('dimensions', 0)}",
                f"Metric: {stats.get('metric', 'unknown')}\n",
                "**Content Type Distribution:**"
            ]
            
            content_types = stats.get('content_types', {})
            for content_type, count in content_types.items():
                formatted_stats.append(f"  - {content_type}: {count} chunks")
            
            return [types.TextContent(
                type="text",
                text="\n".join(formatted_stats)
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error executing tool: {str(e)}"
        )]

async def mcp_sse_handler(_):
    """Handle MCP over Server-Sent Events."""
    async def event_stream():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'jsonrpc': '2.0', 'method': 'server.ready', 'params': {}})}\n\n"
            
            # Keep connection alive
            while True:
                await asyncio.sleep(30)
                yield f"data: {json.dumps({'jsonrpc': '2.0', 'method': 'heartbeat', 'params': {}})}\n\n"
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
        }
    )

async def health_check(_):
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "service": "mcp-sse-server", "rag_initialized": rag_search is not None})

async def mcp_tools_handler(_):
    """Return available MCP tools."""
    try:
        tools = await handle_list_tools()
        return JSONResponse({
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                } for tool in tools
            ]
        })
    except Exception as e:
        logger.error(f"Tools handler error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def mcp_call_handler(request):
    """Handle MCP tool calls."""
    try:
        data = await request.json()
        tool_name = data.get("name")
        arguments = data.get("arguments", {})
        
        results = await handle_call_tool(tool_name, arguments)
        
        return JSONResponse({
            "results": [
                {
                    "type": result.type,
                    "text": result.text
                } for result in results
            ]
        })
    except Exception as e:
        logger.error(f"Call handler error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def main():
    """Main entry point for the MCP SSE server."""
    global rag_search
    
    # Initialize RAG search system
    try:
        logger.info("Initializing RAG search system...")
        rag_search = RAGSearch()
        logger.info("RAG search system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG search: {e}")
        sys.exit(1)
    
    # Get port from environment or default
    port = int(os.getenv("PORT", 8000))
    
    # Create Starlette app with routes
    app = Starlette(routes=[
        Route("/health", health_check),
        Route("/sse", mcp_sse_handler),
        Route("/tools", mcp_tools_handler), 
        Route("/call", mcp_call_handler, methods=["POST"]),
    ])
    
    # Run the server
    logger.info(f"MCP SSE Server running on port {port}")
    logger.info(f"Health check: http://0.0.0.0:{port}/health")
    logger.info(f"SSE endpoint: http://0.0.0.0:{port}/sse")
    logger.info(f"Tools endpoint: http://0.0.0.0:{port}/tools")
    
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    # Run the server
    asyncio.run(main())