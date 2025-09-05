#!/usr/bin/env python3
"""
MCP Server for Camera Remote SDK RAG System
Uses the official Anthropic MCP SDK for proper protocol compliance.
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
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

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

async def main():
    """Main entry point for the MCP server."""
    global rag_search
    
    # Initialize RAG search system
    try:
        logger.info("Initializing RAG search system...")
        rag_search = RAGSearch()
        logger.info("RAG search system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG search: {e}")
        sys.exit(1)
    
    # Run the MCP server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sdk-rag-server",
                server_version="1.0.0"
            )
        )

if __name__ == "__main__":
    # Run the server
    asyncio.run(main())