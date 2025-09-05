# MCP Server for Camera Remote SDK RAG System

This directory contains the official MCP (Model Context Protocol) server implementation for the Camera Remote SDK RAG system, built using Anthropic's official MCP SDK.

## Overview

The MCP server provides a standardized interface for AI assistants (Claude Desktop, LM Studio, etc.) to interact with the Camera Remote SDK documentation and code examples through a RAG (Retrieval-Augmented Generation) system.

## Features

- **Official MCP SDK**: Uses Anthropic's official `mcp` package for proper protocol compliance
- **Stdio Transport**: Communicates via standard input/output for compatibility with all MCP clients
- **Pinecone Vector Search**: Searches across 8,962 SDK documentation chunks
- **Multiple Search Tools**: Specialized search for code, docs, compatibility, and API functions
- **Content Type Filtering**: Search by specific content types (functions, enums, examples, etc.)

## Available Tools

1. **search_sdk** - General SDK search across all content types
2. **search_code_examples** - Search C++ code implementations (229 chunks)
3. **search_documentation** - Search documentation text (2,220 chunks)
4. **search_compatibility** - Search camera compatibility tables (5,230 chunks)
5. **search_api_functions** - Search API function definitions (353 chunks)
6. **get_sdk_stats** - Get database statistics and content distribution

## Setup

### Prerequisites

1. Python 3.8+
2. Pinecone API key
3. Environment variables configured

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your PINECONE_API_KEY
```

### Environment Variables

- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_INDEX_NAME`: Index name (default: `sdk-rag-system`)

## Usage

### Local Usage (Claude Desktop)

1. Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sdk-rag": {
      "command": "python3",
      "args": ["/path/to/sdk-rag-agent/mcp/mcp_server.py"],
      "env": {
        "PINECONE_API_KEY": "your-api-key-here",
        "PINECONE_INDEX_NAME": "sdk-rag-system"
      }
    }
  }
}
```

2. Restart Claude Desktop
3. The SDK search tools will be available in your conversations

### Cloud Usage (Remote Models)

For cloud deployment and access from remote AI models, use the SSE server:

1. **Deploy to Railway:**
   ```bash
   # Use the SSE configuration
   cp railway-sse.toml railway.toml
   railway up
   ```

2. **Deploy to Vercel:**
   ```bash
   vercel deploy
   ```

3. **Configure MCP Client for Cloud:**
   ```json
   {
     "mcpServers": {
       "sdk-rag-cloud": {
         "transport": "sse",
         "url": "https://your-deployment.railway.app/sse",
         "headers": {
           "Authorization": "Bearer your-token"
         }
       }
     }
   }
   ```

### Testing Locally

```bash
# Run the test script
python3 test_mcp_server.py

# Or test manually with stdio
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}' | python3 mcp_server.py
```

## Architecture

```
MCP Client (Claude/LM Studio)
    ↕️ (JSON-RPC over stdio)
MCP Server (mcp_server.py)
    ↕️
RAG Search (search.py)
    ↕️
Pinecone Vector DB (8,962 chunks)
```

## Content Types in Database

- **documentation_table**: 5,230 chunks (camera compatibility)
- **documentation_text**: 2,220 chunks (guides, tutorials)
- **enum**: 528 chunks (enumeration definitions)
- **function**: 353 chunks (API functions)
- **variable**: 322 chunks (variable definitions)
- **example_code**: 229 chunks (C++ implementations)
- **summary**: 56 chunks (API summaries)
- **typedef**: 17 chunks (type definitions)
- **define**: 7 chunks (preprocessor defines)

## Files

- `mcp_server.py` - Local MCP server (stdio transport)
- `mcp_server_sse.py` - **Cloud MCP server (SSE transport)**
- `search.py` - Pinecone search functionality
- `server.py` - FastAPI REST API (alternative interface)
- `test_mcp_server.py` - Test script for MCP protocol
- `claude_desktop_config.json` - Example Claude Desktop configuration
- `railway-sse.toml` - Railway deployment config for SSE server
- `vercel.json` - Vercel deployment config
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies

## Differences from FastAPI Implementation

The original `server.py` is a FastAPI REST API that mimics MCP endpoints but isn't a true MCP server. Issues with the REST approach:

1. **Wrong Protocol**: MCP clients expect JSON-RPC 2.0, not REST
2. **Transport Mismatch**: MCP uses stdio or SSE, not HTTP endpoints
3. **No Session Management**: REST is stateless, MCP maintains sessions

The new `mcp_server.py` fixes these issues by:

1. **Using Official SDK**: Proper MCP protocol implementation
2. **Stdio Transport**: Native support in all MCP clients
3. **Correct Message Handling**: Bidirectional JSON-RPC communication

## Troubleshooting

### Server won't start
- Check Python version (3.8+ required)
- Verify environment variables are set
- Ensure Pinecone API key is valid

### No results returned
- Check Pinecone index name matches your database
- Verify network connectivity to Pinecone
- Check search query syntax

### Claude Desktop can't connect
- Verify path to mcp_server.py is absolute
- Check Python executable path is correct
- Restart Claude Desktop after config changes

## Development

To modify or extend the MCP server:

1. Follow MCP protocol specification
2. Use `@server.list_tools()` to add new tools
3. Use `@server.call_tool()` to handle tool calls
4. Test with `test_mcp_server.py`

## License

Part of the Camera Remote SDK RAG System project.