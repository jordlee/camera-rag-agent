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

# MCP Search System Analysis & Improvement Plan

## Executive Summary

Testing of the Camera Remote SDK MCP connector revealed that **semantic search works well for natural language queries but struggles with exact API name lookups**. The current system using `sentence-transformers/all-mpnet-base-v2` and `microsoft/codebert-base` excels at intent-based searches but needs complementary exact-match capabilities for developer workflows.

## Current System Performance

### ✅ Works Well (Semantic/Conceptual Queries)
- **"connect to camera API"** → 0.74 similarity score, immediately found Connect API documentation
- **"file path directory destination"** → 0.53+ scores, successfully located SetSaveInfo references
- **Natural language questions** about functionality and usage

### ❌ Struggles (Exact Technical Lookups)
- **"SetSaveInfo"** → 0.47 score, fragmented/irrelevant results
- **"Connect"** (exact function name) → Poor results despite rich documentation existing
- **Precise API names** without semantic context

## Root Cause Analysis

1. **Semantic Gap**: API names like "SetSaveInfo" lack descriptive context for embedding models
2. **Document Fragmentation**: API definitions split across multiple pages/blocks
3. **Embedding Model Limitations**: Current models not optimized for technical documentation
4. **Missing Exact Match Layer**: No fallback for precise string matching

## Improvement Recommendations

### Phase 1: Quick Wins (1-2 days)

#### 1. Add Exact String Search Tool
```python
@tool
def search_exact_api_name(api_name: str) -> List[SearchResult]:
    """Direct string search for exact API names in documentation"""
    # Search for exact matches in:
    # - Function definitions
    # - API compatibility tables  
    # - Parameter descriptions
    # - Function signatures
    return exact_matches
```

#### 2. Multi-Strategy Search Function
```python
def search_api_hybrid(query: str):
    """Combine exact match + semantic search with intelligent fallback"""
    # 1. Try exact match first
    exact_results = search_exact_api_name(query)
    if exact_results and max(r.score for r in exact_results) > 0.8:
        return exact_results
    
    # 2. Expand query with synonyms
    expanded_query = expand_technical_terms(query)
    semantic_results = search_semantic(expanded_query)
    
    # 3. Merge and rank
    return merge_and_rank(exact_results, semantic_results)
```

### Phase 2: Enhanced Indexing (3-5 days)

#### 3. Improve API Function Extraction
- **Issue**: SetSaveInfo exists in documentation but not in `search_api_functions` results
- **Fix**: Audit and enhance function parsing logic to capture all API definitions
- **Validate**: Ensure all APIs referenced in compatibility tables are indexed

#### 4. Structure-Aware Search
```python
@tool  
def search_structured_content(query: str, content_types: List[str]):
    """Search specifically in structured elements"""
    # Target: compatibility tables, parameter lists, function signatures
    # Higher weight for structured vs prose content
    return structured_matches
```

### Phase 3: Embedding Improvements (1-2 weeks)

#### 5. Domain-Specific Embedding Model
**Current**: `sentence-transformers/all-mpnet-base-v2` (general purpose)
**Evaluate**: 
- `text-embedding-ada-002` (better mixed technical content)
- `microsoft/graphcodebert-base` (code + documentation)
- **Custom fine-tuning** on camera SDK documentation

#### 6. Query Expansion System
```python
TECHNICAL_SYNONYMS = {
    "SetSaveInfo": ["save file path", "destination directory", "save location", "file storage path"],
    "Connect": ["connection", "establish connection", "camera connection", "device connect"],
    "GetDeviceProperties": ["device settings", "camera properties", "device configuration"]
}
```

### Phase 4: Advanced Features (2-3 weeks)

#### 7. Intelligent Search Routing
```python
def route_search_strategy(query: str) -> SearchStrategy:
    """Determine optimal search approach based on query characteristics"""
    if is_exact_api_name(query):
        return SearchStrategy.EXACT_MATCH
    elif is_conceptual_query(query):
        return SearchStrategy.SEMANTIC
    else:
        return SearchStrategy.HYBRID
```

#### 8. Enhanced System Prompt for Claude
```
When searching SDK documentation:
1. For exact API names: Use exact search first, fallback to semantic
2. For natural language: Use semantic search with query expansion  
3. If initial results have low scores (<0.6): Try alternative search strategies
4. Always check both function definitions AND parameter descriptions
5. For compatibility questions: Search structured tables specifically
```

## Implementation Plan

### Week 1: Foundation
- [ ] **Day 1-2**: Implement exact string search tool
- [ ] **Day 3-4**: Create hybrid search wrapper
- [ ] **Day 5**: Test and validate improvements with known problem cases

### Week 2: Enhanced Indexing  
- [ ] **Day 1-3**: Audit and fix API function extraction/indexing
- [ ] **Day 4-5**: Implement structure-aware search for tables/lists

### Week 3: Embedding Evaluation
- [ ] **Day 1-2**: Benchmark current vs alternative embedding models
- [ ] **Day 3-4**: Implement query expansion system
- [ ] **Day 5**: A/B test with real queries

### Week 4: Integration & Polish
- [ ] **Day 1-2**: Implement intelligent search routing
- [ ] **Day 3-4**: Update Claude system prompts and error handling
- [ ] **Day 5**: Final testing and documentation

## Success Metrics

1. **Exact API Lookup**: "SetSaveInfo" should return >0.8 similarity score with complete parameter info
2. **Semantic Search Maintained**: "connect to camera" should continue working at >0.7 score
3. **Coverage**: All APIs in compatibility tables should be discoverable via search
4. **Response Quality**: Reduced fragmented results, more complete API documentation blocks

## Test Cases for Validation

```python
# Exact API queries that should work after improvements
test_queries = [
    "SetSaveInfo",           # Should find complete API definition
    "Connect parameters",    # Should find Connect API with parameters  
    "GetDeviceProperties",   # Should find function signature + docs
    "EnumCameraObjects",     # Should find basic API description
]

# Semantic queries that should continue working
semantic_queries = [
    "connect to camera",           # Should find Connect API (score >0.7)
    "save file location",          # Should find SetSaveInfo references  
    "camera compatibility",        # Should find compatibility tables
    "get camera settings",         # Should find GetDeviceProperties
]
```

## Priority Ranking

**High Priority** (Immediate Impact):
1. Exact string search tool
2. API function indexing audit
3. Hybrid search implementation

**Medium Priority** (Significant Improvement):  
4. Query expansion system
5. Structure-aware search
6. Alternative embedding model evaluation

**Low Priority** (Nice to Have):
7. Intelligent search routing
8. Advanced system prompts

---

*Analysis conducted through systematic testing of Camera Remote SDK v1.14.00 MCP connector with various query types and search strategies.*