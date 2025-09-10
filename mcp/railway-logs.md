{"message":"Starting Container","attributes":{"level":"info"},"timestamp":"2025-09-10T17:59:12.000000000Z"}
{"message":"2025-09-10 17:59:15,941 - __main__ - INFO - Starting FastMCP server on 0.0.0.0:3000","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338792194Z"}
{"message":"2025-09-10 17:59:15,941 - __main__ - INFO - Available tools: search_sdk, search_code_examples, search_documentation, search_api_functions, search_compatibility, get_sdk_stats, search_exact_api, search_error_codes, search_warning_codes, search_hybrid, search_by_source_file","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338796643Z"}
{"message":"2025-09-10 17:59:15,941 - __main__ - INFO - Health check: /health","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338800660Z"}
{"message":"2025-09-10 17:59:15,941 - __main__ - INFO - SSE endpoint: /sse","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338805010Z"}
{"message":"2025-09-10 17:59:15,941 - __main__ - INFO - MCP endpoint: /mcp","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338808993Z"}
{"message":"2025-09-10 17:59:15,941 - __main__ - INFO - Keepalive interval: 2.0s","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338813754Z"}
{"message":"2025-09-10 17:59:15,941 - __main__ - INFO - Connection timeout: 10.0s","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338817340Z"}
{"message":"INFO:     Started server process [1]","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338821101Z"}
{"message":"INFO:     Waiting for application startup.","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338825076Z"}
{"message":"2025-09-10 17:59:15,962 - __main__ - INFO - Initializing RAG search system...","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338828688Z"}
{"message":"2025-09-10 17:59:15,962 - __main__ - INFO - PINECONE_API_KEY found, proceeding with RAG initialization...","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338833073Z"}
{"message":"2025-09-10 17:59:15,962 - search - INFO - === Starting RAG Search Initialization ===","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338836883Z"}
{"message":"2025-09-10 17:59:15,962 - search - INFO - System Resources - RAM: 384GB (Available: 173GB), Disk: 2221GB (Free: 1021GB)","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338842340Z"}
{"message":"2025-09-10 17:59:15,962 - search - INFO - Step 1: Checking environment variables...","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338846311Z"}
{"message":"2025-09-10 17:59:15,962 - search - INFO - Environment variables OK - Index name: sdk-rag-system","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338850571Z"}
{"message":"2025-09-10 17:59:15,962 - search - INFO - Step 2: Initializing Pinecone connection...","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338854401Z"}
{"message":"2025-09-10 17:59:16,168 - search - INFO - Pinecone connection established successfully","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338859171Z"}
{"message":"2025-09-10 17:59:16,168 - search - INFO - Step 3: Loading GTE-ModernBERT embedding model...","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338863469Z"}
{"message":"2025-09-10 17:59:16,168 - search - INFO - Attempting to load SentenceTransformer('Alibaba-NLP/gte-modernbert-base')...","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338867345Z"}
{"message":"2025-09-10 17:59:16,168 - search - INFO - HuggingFace cache directory: /root/.cache/huggingface/hub","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338871020Z"}
{"message":"2025-09-10 17:59:16,168 - search - INFO - Cache contents (first 5): ['version.txt']","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338874722Z"}
{"message":"2025-09-10 17:59:16,168 - search - INFO - Creating SentenceTransformer instance...","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338878485Z"}
{"message":"2025-09-10 17:59:16,168 - sentence_transformers.SentenceTransformer - INFO - Load pretrained SentenceTransformer: Alibaba-NLP/gte-modernbert-base","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:16.338882338Z"}
{"message":"2025-09-10 17:59:17,693 - search - ERROR - Failed to load GTE embedding model: The checkpoint you are trying to load has model type `modernbert` but Transformers does not recognize this architecture. This could be because of an issue with the checkpoint, or because your version of Transformers is out of date.","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728029766Z"}
{"message":"2025-09-10 17:59:17,694 - search - ERROR - Full error traceback: Traceback (most recent call last):","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728033727Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/transformers/models/auto/configuration_auto.py\", line 993, in from_pretrained","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728037554Z"}
{"message":"    config_class = CONFIG_MAPPING[config_dict[\"model_type\"]]","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728042179Z"}
{"message":"                   ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728046426Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/transformers/models/auto/configuration_auto.py\", line 695, in __getitem__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728050078Z"}
{"message":"    raise KeyError(key)","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728053914Z"}
{"message":"KeyError: 'modernbert'","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728057908Z"}
{"message":"","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728062124Z"}
{"message":"During handling of the above exception, another exception occurred:","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728065901Z"}
{"message":"","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728069733Z"}
{"message":"Traceback (most recent call last):","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728073482Z"}
{"message":"  File \"/app/search.py\", line 127, in __init__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728077542Z"}
{"message":"    self.embedding_model = SentenceTransformer('Alibaba-NLP/gte-modernbert-base')","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728081583Z"}
{"message":"                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728085716Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py\", line 197, in __init__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728089618Z"}
{"message":"    modules = self._load_sbert_model(","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728093837Z"}
{"message":"              ^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728097870Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py\", line 1296, in _load_sbert_model","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728102424Z"}
{"message":"    module = Transformer(model_name_or_path, cache_dir=cache_folder, **kwargs)","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728107039Z"}
{"message":"             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728111185Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/sentence_transformers/models/Transformer.py\", line 35, in __init__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728115128Z"}
{"message":"    config = AutoConfig.from_pretrained(model_name_or_path, **model_args, cache_dir=cache_dir)","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728119360Z"}
{"message":"             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728123956Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/transformers/models/auto/configuration_auto.py\", line 995, in from_pretrained","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728128211Z"}
{"message":"    raise ValueError(","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728132541Z"}
{"message":"ValueError: The checkpoint you are trying to load has model type `modernbert` but Transformers does not recognize this architecture. This could be because of an issue with the checkpoint, or because your version of Transformers is out of date.","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728136808Z"}
{"message":"","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728140936Z"}
{"message":"2025-09-10 17:59:17,697 - search - ERROR - Error type: ValueError","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728144868Z"}
{"message":"2025-09-10 17:59:17,697 - search - ERROR - Error args: ('The checkpoint you are trying to load has model type `modernbert` but Transformers does not recognize this architecture. This could be because of an issue with the checkpoint, or because your version of Transformers is out of date.',)","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728148842Z"}
{"message":"2025-09-10 17:59:17,697 - __main__ - ERROR - Failed to initialize RAG search: Could not initialize GTE-ModernBERT embedding model: The checkpoint you are trying to load has model type `modernbert` but Transformers does not recognize this architecture. This could be because of an issue with the checkpoint, or because your version of Transformers is out of date.","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728153659Z"}
{"message":"Traceback (most recent call last):","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728157494Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/transformers/models/auto/configuration_auto.py\", line 993, in from_pretrained","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728161650Z"}
{"message":"    config_class = CONFIG_MAPPING[config_dict[\"model_type\"]]","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728166274Z"}
{"message":"                   ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728170254Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/transformers/models/auto/configuration_auto.py\", line 695, in __getitem__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728174020Z"}
{"message":"    raise KeyError(key)","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728177775Z"}
{"message":"KeyError: 'modernbert'","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728183074Z"}
{"message":"","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728188379Z"}
{"message":"During handling of the above exception, another exception occurred:","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728192264Z"}
{"message":"","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728196163Z"}
{"message":"Traceback (most recent call last):","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728199913Z"}
{"message":"  File \"/app/search.py\", line 127, in __init__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728204484Z"}
{"message":"    self.embedding_model = SentenceTransformer('Alibaba-NLP/gte-modernbert-base')","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728920067Z"}
{"message":"                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728926523Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py\", line 197, in __init__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728930627Z"}
{"message":"    modules = self._load_sbert_model(","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728935296Z"}
{"message":"              ^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728939051Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py\", line 1296, in _load_sbert_model","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728942816Z"}
{"message":"    module = Transformer(model_name_or_path, cache_dir=cache_folder, **kwargs)","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728946552Z"}
{"message":"             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728950484Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/sentence_transformers/models/Transformer.py\", line 35, in __init__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728954805Z"}
{"message":"    config = AutoConfig.from_pretrained(model_name_or_path, **model_args, cache_dir=cache_dir)","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728960490Z"}
{"message":"             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728966619Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/transformers/models/auto/configuration_auto.py\", line 995, in from_pretrained","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728973930Z"}
{"message":"    raise ValueError(","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728979745Z"}
{"message":"ValueError: The checkpoint you are trying to load has model type `modernbert` but Transformers does not recognize this architecture. This could be because of an issue with the checkpoint, or because your version of Transformers is out of date.","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728984983Z"}
{"message":"","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728990313Z"}
{"message":"During handling of the above exception, another exception occurred:","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.728995757Z"}
{"message":"","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729003587Z"}
{"message":"Traceback (most recent call last):","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729010835Z"}
{"message":"  File \"/app/mcp_server.py\", line 331, in lifespan","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729015579Z"}
{"message":"    rag_search = RAGSearch()","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729020910Z"}
{"message":"                 ^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729025743Z"}
{"message":"  File \"/app/search.py\", line 159, in __init__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729031545Z"}
{"message":"    raise RuntimeError(f\"Could not initialize GTE-ModernBERT embedding model: {e}\")","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729037135Z"}
{"message":"RuntimeError: Could not initialize GTE-ModernBERT embedding model: The checkpoint you are trying to load has model type `modernbert` but Transformers does not recognize this architecture. This could be because of an issue with the checkpoint, or because your version of Transformers is out of date.","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729044277Z"}
{"message":"2025-09-10 17:59:17,699 - __main__ - ERROR - Error type: RuntimeError","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729050086Z"}
{"message":"2025-09-10 17:59:17,699 - __main__ - ERROR - Error details: Could not initialize GTE-ModernBERT embedding model: The checkpoint you are trying to load has model type `modernbert` but Transformers does not recognize this architecture. This could be because of an issue with the checkpoint, or because your version of Transformers is out of date.","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729055342Z"}
{"message":"2025-09-10 17:59:17,708 - mcp.server.streamable_http_manager - INFO - StreamableHTTP session manager started","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729060354Z"}
{"message":"INFO:     Application startup complete.","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729066459Z"}
{"message":"INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)","attributes":{"level":"error"},"timestamp":"2025-09-10T17:59:17.729071658Z"}
{"message":"INFO:     100.64.0.2:41597 - \"GET /health HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-10T17:59:18.223540660Z"}