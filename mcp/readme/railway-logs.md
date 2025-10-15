{"message":"Starting Container","attributes":{"level":"info"},"timestamp":"2025-10-15T18:10:46.000000000Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - Starting FastMCP server on 0.0.0.0:3000","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102917390Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - === MCP Tools Available ===","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102925637Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - Claude-compatible tools (14): search_sdk, search_code_examples, search_documentation, search_api_functions, search_compatibility, get_sdk_stats, search_exact_api, search_error_codes, search_warning_codes, search_hybrid, search_by_source_file, search_with_intent_analysis, set_sdk_version, get_current_sdk_version","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102930997Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - ChatGPT-compatible tools (2): search, fetch","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102939017Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - Total: 16 MCP tools registered","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102943889Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - Version management: Multi-SDK support (V1.14.00, V2.00.00)","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102949988Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - ChatGPT Deep Research: Compatible ✓","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102955431Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - Health check: /health","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102960978Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - SSE endpoint: /sse","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102966496Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - MCP endpoint: /mcp","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102972243Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - Keepalive interval: 2.0s","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102976856Z"}
{"message":"2025-10-15 18:10:50,168 - __main__ - INFO - Connection timeout: 10.0s","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102981466Z"}
{"message":"INFO:     Started server process [1]","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102987329Z"}
{"message":"INFO:     Waiting for application startup.","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102992035Z"}
{"message":"2025-10-15 18:10:50,192 - rate_limiter - INFO - [RATE_LIMIT_INIT] Attempting Redis connection...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.102997245Z"}
{"message":"2025-10-15 18:10:50,214 - rate_limiter - INFO - [RATE_LIMIT_INIT] ✅ Redis connected successfully","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103001859Z"}
{"message":"2025-10-15 18:10:50,214 - rate_limiter - INFO - [RATE_LIMIT_INIT] Middleware active: 100 req/min per IP","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103023825Z"}
{"message":"2025-10-15 18:10:50,214 - __main__ - INFO - Initializing RAG search system...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103028944Z"}
{"message":"2025-10-15 18:10:50,214 - __main__ - INFO - PINECONE_API_KEY found, proceeding with RAG initialization...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103035534Z"}
{"message":"2025-10-15 18:10:50,214 - search - INFO - === Starting RAG Search Initialization ===","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103041114Z"}
{"message":"2025-10-15 18:10:50,215 - search - INFO - System Resources - RAM: 384GB (Available: 145GB), Disk: 2363GB (Free: 1185GB)","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103047160Z"}
{"message":"2025-10-15 18:10:50,215 - search - INFO - Step 1: Checking environment variables...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103052840Z"}
{"message":"2025-10-15 18:10:50,215 - search - INFO - Environment variables OK","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103058140Z"}
{"message":"2025-10-15 18:10:50,215 - search - INFO - Step 2: Initializing Pinecone connection with multi-version support...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103063889Z"}
{"message":"2025-10-15 18:10:50,215 - search - INFO - Loading V1.14.00 index (sdk-rag-system)...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103068773Z"}
{"message":"2025-10-15 18:10:50,584 - search - INFO - ✅ V1.14.00 index loaded","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103074352Z"}
{"message":"2025-10-15 18:10:50,584 - search - INFO - Loading V2.00.00 index (sdk-rag-system-v2)...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103079224Z"}
{"message":"2025-10-15 18:10:50,838 - search - INFO - ✅ V2.00.00 index loaded","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103083907Z"}
{"message":"2025-10-15 18:10:50,838 - search - INFO - Pinecone multi-version connection established successfully","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103089547Z"}
{"message":"2025-10-15 18:10:50,838 - search - INFO - Default SDK version: V2.00.00","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103094481Z"}
{"message":"2025-10-15 18:10:50,838 - search - INFO - Step 3: Loading GTE-ModernBERT embedding model...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103100266Z"}
{"message":"2025-10-15 18:10:50,838 - search - INFO - Attempting to load SentenceTransformer('Alibaba-NLP/gte-modernbert-base')...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103105380Z"}
{"message":"2025-10-15 18:10:50,838 - search - INFO - HuggingFace cache directory: /root/.cache/huggingface/hub","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103111062Z"}
{"message":"2025-10-15 18:10:50,838 - search - INFO - HuggingFace cache directory does not exist","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103116567Z"}
{"message":"2025-10-15 18:10:50,838 - search - INFO - Creating SentenceTransformer instance...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103122674Z"}
{"message":"2025-10-15 18:10:50,838 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: Alibaba-NLP/gte-modernbert-base","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:51.103128831Z"}
{"message":"2025-10-15 18:10:57,349 - sentence_transformers.SentenceTransformer - INFO - Use pytorch device_name: cpu","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:57.350968021Z"}
{"message":"2025-10-15 18:10:57,351 - search - INFO - Model instance created in 6.51s, moving to CPU...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:57.354368235Z"}
{"message":"2025-10-15 18:10:57,352 - search - INFO - GTE-ModernBERT model loaded successfully in 6.51s","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:57.354373377Z"}
{"message":"2025-10-15 18:10:57,352 - search - INFO - Testing model with simple query...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:57.354378860Z"}
{"message":"\rBatches:   0%|          | 0/1 [00:00<?, ?it/s]\rBatches: 100%|██████████| 1/1 [00:01<00:00,  1.70s/it]\rBatches: 100%|██████████| 1/1 [00:01<00:00,  1.70s/it]","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062743655Z"}
{"message":"2025-10-15 18:10:59,061 - search - INFO - Test embedding shape: (768,), type: <class 'numpy.ndarray'>","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062749116Z"}
{"message":"2025-10-15 18:10:59,061 - search - INFO - Step 4: Setting up thread pool...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062753989Z"}
{"message":"2025-10-15 18:10:59,061 - search - INFO - Step 5: Initializing performance tracking...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062758806Z"}
{"message":"2025-10-15 18:10:59,061 - search - INFO - Step 6: RAG Search initialization completed successfully!","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062763493Z"}
{"message":"2025-10-15 18:10:59,061 - search - INFO - ✅ RAG Search ready - Multi-version support: V1.14.00 + V2.00.00 (active: V2.00.00)","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062768748Z"}
{"message":"2025-10-15 18:10:59,061 - search - INFO -    Model: GTE-ModernBERT, Indexes: sdk-rag-system (V1), sdk-rag-system-v2 (V2)","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062808445Z"}
{"message":"2025-10-15 18:10:59,061 - search - INFO - === RAG Search Initialization Complete ===","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062814071Z"}
{"message":"2025-10-15 18:10:59,061 - search - INFO - Post-initialization RAM usage: 62.5% (238GB used)","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062825778Z"}
{"message":"2025-10-15 18:10:59,061 - __main__ - INFO - RAG search system initialized successfully!","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.062830941Z"}
{"message":"2025-10-15 18:10:59,076 - mcp.server.streamable_http_manager - INFO - StreamableHTTP session manager started","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.078566006Z"}
{"message":"INFO:     Application startup complete.","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.078571699Z"}
{"message":"INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)","attributes":{"level":"error"},"timestamp":"2025-10-15T18:10:59.078577851Z"}
{"message":"INFO:     100.64.0.2:39363 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:10:59.739538019Z"}
{"message":"INFO:     100.64.0.3:28562 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:34:10.586582936Z"}
{"message":"INFO:     100.64.0.4:28314 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:34:10.586590187Z"}
{"message":"INFO:     100.64.0.5:39306 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:34:30.587867658Z"}
{"message":"INFO:     100.64.0.6:41974 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:34:50.584120720Z"}
{"message":"INFO:     100.64.0.7:18376 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:34:50.584129581Z"}
{"message":"INFO:     100.64.0.8:28532 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:34:50.584136418Z"}
{"message":"INFO:     100.64.0.4:46428 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:35:40.588164164Z"}
{"message":"INFO:     100.64.0.8:62406 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:35:46.490106177Z"}
{"message":"INFO:     100.64.0.8:33936 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:41:06.694355351Z"}
{"message":"2025-10-15 18:41:04,038 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694365509Z"}
{"message":"INFO:     100.64.0.8:33936 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-10-15T18:41:06.694373630Z"}
{"message":"2025-10-15 18:41:04,078 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694379531Z"}
{"message":"INFO:     100.64.0.8:33936 - \"GET /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:41:06.694384818Z"}
{"message":"INFO:     100.64.0.4:19964 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:41:06.694390462Z"}
{"message":"2025-10-15 18:41:04,405 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694395836Z"}
{"message":"INFO:     100.64.0.4:19964 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-10-15T18:41:06.694400776Z"}
{"message":"2025-10-15 18:41:04,446 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694407114Z"}
{"message":"INFO:     100.64.0.4:19964 - \"GET /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:41:06.694414570Z"}
{"message":"INFO:     100.64.0.7:30486 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:41:06.694420410Z"}
{"message":"2025-10-15 18:41:04,519 - mcp.server.lowlevel.server - INFO - Processing request of type ListResourcesRequest","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694425867Z"}
{"message":"INFO:     100.64.0.7:30496 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:41:06.694432486Z"}
{"message":"2025-10-15 18:41:04,521 - mcp.server.lowlevel.server - INFO - Processing request of type ListToolsRequest","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694439542Z"}
{"message":"INFO:     100.64.0.9:36070 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:41:06.694445418Z"}
{"message":"2025-10-15 18:41:04,530 - mcp.server.lowlevel.server - INFO - Processing request of type ListPromptsRequest","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694451087Z"}
{"message":"2025-10-15 18:41:04,531 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694456277Z"}
{"message":"2025-10-15 18:41:04,531 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694461281Z"}
{"message":"2025-10-15 18:41:04,532 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-10-15T18:41:06.694479303Z"}
{"message":"INFO:     100.64.0.5:18902 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:42:36.715219286Z"}
{"message":"2025-10-15 18:42:29,946 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-10-15T18:42:36.715231069Z"}
{"message":"2025-10-15 18:42:30,364 - search - ERROR - Error getting index stats: 'NoneType' object is not callable","attributes":{"level":"error"},"timestamp":"2025-10-15T18:42:36.715239431Z"}
{"message":"2025-10-15 18:42:30,367 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-10-15T18:42:36.715247736Z"}
{"message":"INFO:     100.64.0.3:29872 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-10-15T18:42:45.671028103Z"}
{"message":"2025-10-15 18:42:45,669 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-10-15T18:42:45.671034576Z"}
{"message":"2025-10-15 18:42:45,670 - __main__ - INFO - Search progress: {'status': 'analyzing_intent', 'progress': 0.1}","attributes":{"level":"error"},"timestamp":"2025-10-15T18:42:45.671040390Z"}
{"message":"2025-10-15 18:42:45,741 - intent_mapper - INFO - Loading TinyLlama model: TinyLlama/TinyLlama-1.1B-Chat-v1.0","attributes":{"level":"error"},"timestamp":"2025-10-15T18:42:45.742131396Z"}
{"message":"`torch_dtype` is deprecated! Use `dtype` instead!","attributes":{"level":"error"},"timestamp":"2025-10-15T18:42:47.221992146Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - Starting FastMCP server on 0.0.0.0:3000","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228284249Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - === MCP Tools Available ===","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228291691Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - Claude-compatible tools (14): search_sdk, search_code_examples, search_documentation, search_api_functions, search_compatibility, get_sdk_stats, search_exact_api, search_error_codes, search_warning_codes, search_hybrid, search_by_source_file, search_with_intent_analysis, set_sdk_version, get_current_sdk_version","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228296438Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - ChatGPT-compatible tools (2): search, fetch","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228300673Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - Total: 16 MCP tools registered","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228304236Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - Version management: Multi-SDK support (V1.14.00, V2.00.00)","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228308137Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - ChatGPT Deep Research: Compatible ✓","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228313055Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - Health check: /health","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228316887Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - SSE endpoint: /sse","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228320707Z"}
{"message":"2025-10-15 18:43:05,664 - __main__ - INFO - MCP endpoint: /mcp","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228324748Z"}
{"message":"2025-10-15 18:43:05,665 - __main__ - INFO - Keepalive interval: 2.0s","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228328609Z"}
{"message":"2025-10-15 18:43:05,665 - __main__ - INFO - Connection timeout: 10.0s","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228332304Z"}
{"message":"INFO:     Started server process [1]","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228335970Z"}
{"message":"INFO:     Waiting for application startup.","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228339825Z"}
{"message":"2025-10-15 18:43:05,690 - rate_limiter - INFO - [RATE_LIMIT_INIT] Attempting Redis connection...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228343409Z"}
{"message":"2025-10-15 18:43:05,713 - rate_limiter - INFO - [RATE_LIMIT_INIT] ✅ Redis connected successfully","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228346930Z"}
{"message":"2025-10-15 18:43:05,713 - rate_limiter - INFO - [RATE_LIMIT_INIT] Middleware active: 100 req/min per IP","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228398462Z"}
{"message":"2025-10-15 18:43:05,713 - __main__ - INFO - Initializing RAG search system...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228402085Z"}
{"message":"2025-10-15 18:43:05,713 - __main__ - INFO - PINECONE_API_KEY found, proceeding with RAG initialization...","attributes":{"level":"error"},"timestamp":"2025-10-15T18:43:07.228405742Z"}