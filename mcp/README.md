# Camera Remote SDK RAG MCP Server

FastAPI-based MCP server that provides semantic search over Camera Remote SDK documentation and C++ code examples.

## Features

- 🔍 **Semantic Search**: Search across 8,962+ embedded chunks
- 💻 **C++ Code Examples**: 229 function implementations and static maps
- 📚 **Documentation**: API docs, guides, and explanatory text
- 🔧 **MCP Protocol**: Native integration with ChatGPT and Claude
- ☁️ **Cloud Ready**: Deployed on Railway with Pinecone backend

## Quick Start

### 1. Setup Environment

```bash
# Copy your Pinecone API key to mcp/.env
PINECONE_API_KEY=your_api_key_here
```

### 2. Install Dependencies

```bash
pip install -r mcp/requirements.txt
```

### 3. Run Server Locally

```bash
python mcp/server.py
```

### 4. Test Server

```bash
python mcp/test_server.py
```

## API Endpoints

### Search Endpoints

- `GET /search?q={query}&top_k=5&type={filter}` - General search
- `GET /search/code?q={query}` - Search C++ code examples  
- `GET /search/docs?q={query}` - Search documentation
- `GET /search/functions?q={query}` - Search API functions

### System Endpoints

- `GET /` - Server information
- `GET /health` - Health check
- `GET /stats` - Database statistics
- `GET /mcp/tools` - MCP tool definitions

## Example Queries

```bash
# Search for connection examples
curl "http://localhost:$PORT/search/code?q=camera%20connection"

# Find API documentation  
curl "http://localhost:$PORT/search/docs?q=SDK%20initialization"

# Search function definitions
curl "http://localhost:$PORT/search/functions?q=capture%20image"
```

## MCP Integration

### ChatGPT/Claude Setup

1. Deploy server to Railway (see deployment section)
2. Get your public URL: `https://your-app.railway.app`
3. Configure in ChatGPT/Claude MCP settings:
   - **Server URL**: `https://your-app.railway.app`
   - **Tools**: Use `/mcp/tools` endpoint for tool definitions

### Available MCP Tools

- `search_sdk(query, top_k, type)` - General SDK search
- `search_code_examples(query, top_k)` - C++ code search
- `get_sdk_stats()` - Database statistics

## Content Types

The server searches across different content types:

- **`example_code`**: C++ functions, static maps, implementations (229 chunks)
- **`documentation_text`**: API docs, guides, explanatory text (2,220 chunks) 
- **`documentation_table`**: API tables, parameter lists (5,230 chunks)
- **`function`**: API function definitions (353 chunks)
- **`enum`**: Enum definitions (528 chunks)
- **`variable`**: Variable definitions (322 chunks)

## Architecture

```
ChatGPT/Claude ↔️ MCP Server (Railway) ↔️ Pinecone (Vector DB)
                        ↕️
                 SentenceTransformer
                  (Query Embeddings)
```

## Deployment

Ready for Railway deployment with included configuration files:

- `requirements.txt` - Python dependencies
- `railway.toml` - Railway deployment config
- `.env` - Environment variables (add your Pinecone API key)

## Development

### Local Testing

1. Ensure Pinecone API key is set in `.env`
2. Start server: `python server.py`
3. Run tests: `python test_server.py`
4. Check health: `curl http://localhost:$PORT/health`

### Adding New Endpoints

1. Add endpoint to `server.py`
2. Update MCP tool definitions in `/mcp/tools`
3. Test with `test_server.py`

## Monitoring

- Health check: `GET /health`
- Index stats: `GET /stats` 
- Server logs via Railway dashboard