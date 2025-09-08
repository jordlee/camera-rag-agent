{"message":"INFO:     Waiting for application startup.","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:20.218013885Z"}
{"message":"2025-09-08 22:18:20,206 - __main__ - INFO - Initializing RAG search system...","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:20.218019311Z"}
{"message":"2025-09-08 22:18:20,467 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: sentence-transformers/all-mpnet-base-v2","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:20.470172491Z"}
{"message":"/usr/local/lib/python3.11/site-packages/transformers/tokenization_utils_base.py:1601: FutureWarning: `clean_up_tokenization_spaces` was not set. It will be set to `True` by default. This behavior will be depracted in transformers v4.45, and will be then set to `False` by default. For more details check this issue: https://github.com/huggingface/transformers/issues/31884","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:22.060846674Z"}
{"message":"  warnings.warn(","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:22.060854774Z"}
{"message":"2025-09-08 22:18:22,145 - sentence_transformers.SentenceTransformer - INFO - Use pytorch device_name: cpu","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:22.148753711Z"}
{"message":"2025-09-08 22:18:22,148 - search - INFO - RAG Search initialized with index: sdk-rag-system","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:22.149264459Z"}
{"message":"2025-09-08 22:18:22,148 - __main__ - INFO - RAG search system initialized successfully!","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:22.149562167Z"}
{"message":"2025-09-08 22:18:22,153 - mcp.server.streamable_http_manager - INFO - StreamableHTTP session manager started","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:22.159043269Z"}
{"message":"INFO:     Application startup complete.","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:22.159049524Z"}
{"message":"INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)","attributes":{"level":"error"},"timestamp":"2025-09-08T22:18:22.159091096Z"}
{"message":"INFO:     100.64.0.2:21838 - \"GET /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T22:19:12.168598796Z"}
{"message":"INFO:     100.64.0.3:15152 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T22:20:52.189994537Z"}
{"message":"2025-09-08 22:20:42,944 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-08T22:20:52.190003693Z"}
{"message":"INFO:     100.64.0.4:42340 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-09-08T22:20:52.190010512Z"}
{"message":"2025-09-08 22:20:43,366 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-08T22:20:52.190017688Z"}
{"message":"INFO:     100.64.0.3:15152 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T22:20:52.190023837Z"}
{"message":"2025-09-08 22:20:43,523 - mcp.server.lowlevel.server - INFO - Processing request of type ListResourcesRequest","attributes":{"level":"error"},"timestamp":"2025-09-08T22:20:52.190032404Z"}
{"message":"2025-09-08 22:20:43,524 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-08T22:20:52.190036647Z"}
{"message":"INFO:     100.64.0.5:47152 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T22:20:52.190041040Z"}
{"message":"2025-09-08 22:20:43,576 - mcp.server.lowlevel.server - INFO - Processing request of type ListPromptsRequest","attributes":{"level":"error"},"timestamp":"2025-09-08T22:20:52.190045253Z"}
{"message":"INFO:     100.64.0.6:52688 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T22:20:52.190049437Z"}
{"message":"2025-09-08 22:20:43,579 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-09-08T22:20:52.190055582Z"}
{"message":"2025-09-08 22:20:43,632 - intent_mapper - INFO - Loading LLM model: microsoft/Phi-3-mini-4k-instruct","attributes":{"level":"error"},"timestamp":"2025-09-08T22:20:52.190059762Z"}
{"message":"2025-09-08 22:20:44,094 - transformers_modules.microsoft.Phi-3-mini-4k-instruct.0a67737cc96d2554230f90338b163bc6380a2a85.modeling_phi3 - WARNING - `flash-attention` package not found, consider installing for better performance: No module named 'flash_attn'.","attributes":{"level":"error"},"timestamp":"2025-09-08T22:20:52.190063978Z"}
{"message":"2025-09-08 22:20:44,094 - transformers_modules.microsoft.Phi-3-mini-4k-instruct.0a67737cc96d2554230f90338b163bc6380a2a85.modeling_phi3 - WARNING - Current `flash-attention` does not support `window_size`. Either upgrade or use `attn_implementation='eager'`.","attributes":{"level":"error"},"timestamp":"2025-09-08T22:20:52.190068058Z"}
{"message":"\rLoading checkpoint shards:   0%|          | 0/2 [00:00<?, ?it/s]2025-09-08 22:21:02,149 - __main__ - INFO - Starting FastMCP server on 0.0.0.0:3000","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.151959959Z"}
{"message":"2025-09-08 22:21:02,149 - __main__ - INFO - Available tools: search_sdk, search_code_examples, search_documentation, search_api_functions, search_compatibility, get_sdk_stats, search_exact_api, search_error_codes, search_warning_codes, search_hybrid, search_by_source_file","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.151964062Z"}
{"message":"2025-09-08 22:21:02,149 - __main__ - INFO - Health check: /health","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.151968159Z"}
{"message":"2025-09-08 22:21:02,149 - __main__ - INFO - SSE endpoint: /sse","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.151971907Z"}
{"message":"2025-09-08 22:21:02,149 - __main__ - INFO - MCP endpoint: /mcp","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.151976398Z"}
{"message":"2025-09-08 22:21:02,149 - __main__ - INFO - Keepalive interval: 2.0s","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.151981810Z"}
{"message":"2025-09-08 22:21:02,149 - __main__ - INFO - Connection timeout: 10.0s","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.151986953Z"}
{"message":"INFO:     Started server process [1]","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.178892376Z"}
{"message":"INFO:     Waiting for application startup.","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.178896428Z"}
{"message":"2025-09-08 22:21:02,178 - __main__ - INFO - Initializing RAG search system...","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.178901909Z"}
{"message":"2025-09-08 22:21:02,418 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: sentence-transformers/all-mpnet-base-v2","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:02.420256112Z"}
{"message":"/usr/local/lib/python3.11/site-packages/transformers/tokenization_utils_base.py:1601: FutureWarning: `clean_up_tokenization_spaces` was not set. It will be set to `True` by default. This behavior will be depracted in transformers v4.45, and will be then set to `False` by default. For more details check this issue: https://github.com/huggingface/transformers/issues/31884","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:03.825739247Z"}
{"message":"  warnings.warn(","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:03.825746399Z"}
{"message":"2025-09-08 22:21:03,912 - sentence_transformers.SentenceTransformer - INFO - Use pytorch device_name: cpu","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:03.916378501Z"}
{"message":"2025-09-08 22:21:03,914 - search - INFO - RAG Search initialized with index: sdk-rag-system","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:03.916386017Z"}
{"message":"2025-09-08 22:21:03,914 - __main__ - INFO - RAG search system initialized successfully!","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:03.916391081Z"}
{"message":"2025-09-08 22:21:03,918 - mcp.server.streamable_http_manager - INFO - StreamableHTTP session manager started","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:03.919013847Z"}
{"message":"INFO:     Application startup complete.","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:03.919022796Z"}
{"message":"INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)","attributes":{"level":"error"},"timestamp":"2025-09-08T22:21:03.919065397Z"}