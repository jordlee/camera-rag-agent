{
 "project_title": "Sony Camera SDK RAG System: Critical Issues & Improvement Plan",
 "project_description": "MCP server with RAG system for Sony Camera Remote SDK documentation search. Currently has connection stability issues and poor semantic search performance that need immediate fixes.",
 
 "current_system_overview": {
   "technology_stack": [
     "Python MCP server",
     "FastAPI/Uvicorn backend", 
     "Vector embeddings with microsoft/codebert-base",
     "Railway cloud deployment",
     "Multiple search tools: search_exact_api, search_hybrid, search_documentation"
   ],
   "strengths": [
     "Excellent exact API search (100% success rate for known function names)",
     "Rich metadata extraction (function names, error codes, compatibility tables)",
     "Stable performance with controlled parameters (top_k=5, targeted queries)",
     "Multiple content types: documentation text, code examples, tables"
   ]
 },

 "critical_issues": {
   "issue_1_connection_timeouts": {
     "severity": "CRITICAL",
     "description": "Embedding operations >7 seconds cause MCP connection timeouts and server crashes",
     "evidence": "Batches: 100%|██████████| 1/1 [00:07<00:00, 7.31s/it] → Multiple rapid session terminations",
     "impact": "Railway deployment becomes unresponsive, users lose connection during complex searches",
     "root_cause": "Long-running embedding computations block event loop, exceed Railway timeout thresholds"
   },
   
   "issue_2_semantic_search_failure": {
     "severity": "HIGH", 
     "description": "Natural language queries have ~25% success rate vs 100% for exact API names",
     "evidence": {
       "failed_queries": [
         "connect to camera → Found camera code, missed Connect API (score: 0.05)",
         "save file location → Found video streaming, missed SetSaveInfo (score: 0.01)", 
         "get camera settings → Found misc docs, missed GetDeviceProperties (score: 0.02)"
       ]
     },
     "root_cause": "microsoft/codebert-base not specialized for API documentation, missing intent→API mapping"
   },

   "issue_3_table_parsing_corruption": {
     "severity": "HIGH",
     "description": "Compatibility tables show systematic data corruption with wrong camera compatibility",
     "evidence": "ILX-LR1 should be compatible but consistently shows as not-compatible across all files",
     "impact": "Developers get incorrect compatibility information for camera models",
     "root_cause": "PDF extraction misaligns table columns during chunking process"
   }
 },

 "priority_tasks": [
   {
     "task_id": "TASK_1_FIX_TIMEOUTS",
     "priority": "CRITICAL",
     "timeline": "Week 1",
     "title": "Implement Connection Timeout Prevention",
     "description": "Fix 7+ second embedding operations causing MCP disconnections",
     "technical_requirements": [
       "Add async processing with progress updates for long operations",
       "Implement connection keepalive during embedding computations", 
       "Reduce batch processing time to <3 seconds per operation",
       "Add graceful degradation for complex queries",
       "Monitor memory usage and add resource limits"
     ],
     "implementation_options": [
       {
         "option": "async_streaming",
         "code_pattern": "async def search_with_streaming(query): yield {'status': 'processing'}; for chunk in process_in_small_chunks(query): yield {'progress': chunk.completion_percent}; yield {'results': final_results}"
       },
       {
         "option": "keepalive_heartbeat", 
         "code_pattern": "async def search_with_keepalive(query): keepalive_task = asyncio.create_task(heartbeat_every_2_seconds()); try: return await embedding_search(query); finally: keepalive_task.cancel()"
       },
       {
         "option": "batch_size_limiting",
         "code_pattern": "def limit_embedding_batch_size(max_time_per_batch=3.0): # Keep individual operations under Railway timeout threshold"
       }
     ],
     "success_criteria": "0 crashes during normal operations, all queries complete in <5 seconds"
   },

   {
     "task_id": "TASK_2_FIX_TABLE_PARSING", 
     "priority": "HIGH",
     "timeline": "Week 2",
     "title": "Repair Table Data Extraction Accuracy",
     "description": "Fix systematic corruption in compatibility table parsing",
     "technical_requirements": [
       "Implement table-specific parsing logic for PDF extraction",
       "Add data validation for compatibility tables",
       "Cross-reference multiple table instances for consistency", 
       "Add confidence scores for structured data extraction"
     ],
     "success_criteria": "100% accuracy for camera compatibility tables, correct alignment of camera models with compatibility status"
   },

   {
     "task_id": "TASK_3_IMPROVE_SEMANTIC_SEARCH",
     "priority": "HIGH", 
     "timeline": "Week 3",
     "title": "Implement Multi-Modal Semantic Search",
     "description": "Bridge gap between natural language queries and API function names",
     "technical_requirements": [
       "Create intent→API mapping for common developer workflows",
       "Implement query expansion with technical synonyms",
       "Add hierarchical search with fallbacks (semantic → keyword → fuzzy → suggestions)",
       "Enhance embeddings with API metadata",
       "Build evaluation framework with test cases"
     ],
     "semantic_search_architecture": {
       "phase_1_intent_extraction": "Extract technical terms from natural language",
       "phase_2_multi_modal_retrieval": "Run semantic + metadata + pattern + workflow searches in parallel", 
       "phase_3_result_fusion": "Combine and rank results from multiple search modes"
     },
     "intent_mappings": {
       "connect.*camera": ["SCRSDK::Connect", "EnumCameraObjects"],
       "save.*focus.*position": ["CrDeviceProperty_ZoomAndFocusPosition_Save"],
       "get.*camera.*settings": ["GetDeviceProperties", "GetSelectDeviceProperties"],
       "save.*file.*location": ["SetSaveInfo"]
     },
     "success_criteria": ">80% accuracy for natural language queries, robust fallback suggestions"
   },

   {
     "task_id": "TASK_4_API_AWARE_CHUNKING",
     "priority": "MEDIUM",
     "timeline": "Week 4", 
     "title": "Implement Context-Preserving Chunking",
     "description": "Keep complete API definitions together during document processing",
     "technical_requirements": [
       "Detect API boundaries (function signatures, parameters, examples)",
       "Ensure complete API definitions stay in single chunks",
       "Generate semantic tags for better searchability",
       "Maintain cross-references between related functions"
     ],
     "success_criteria": "Complete API context preserved, improved semantic signal strength"
   }
 ],

 "testing_framework": {
   "semantic_test_cases": [
     {"query": "how do I connect to a camera", "expected_api": "SCRSDK::Connect"},
     {"query": "connect camera", "expected_api": "SCRSDK::Connect"},
     {"query": "save image location", "expected_api": "SetSaveInfo"},
     {"query": "set file save path", "expected_api": "SetSaveInfo"},
     {"query": "get camera settings", "expected_api": "GetDeviceProperties"},
     {"query": "save focus position", "expected_api": "CrDeviceProperty_ZoomAndFocusPosition_Save"},
     {"query": "store zoom preset", "expected_api": "CrDeviceProperty_ZoomAndFocusPosition_Save"}
   ],
   "performance_benchmarks": {
     "connection_stability": "0 crashes during normal operations",
     "search_accuracy": ">80% success rate for natural language queries", 
     "response_time": "<5 seconds for all operations",
     "data_quality": "100% accuracy for compatibility tables"
   }
 },

 "deployment_considerations": {
   "railway_constraints": [
     "Connection timeout thresholds (~5-7 seconds)",
     "Memory limitations requiring efficient batch processing",
     "Need for graceful degradation under resource pressure"
   ],
   "monitoring_requirements": [
     "Track embedding operation duration",
     "Monitor memory usage during search operations",
     "Log semantic search accuracy metrics",
     "Alert on connection timeout patterns"
   ]
 },

 "success_metrics": {
   "immediate_goals": [
     "Eliminate server crashes during search operations",
     "Fix data corruption in compatibility tables", 
     "Achieve >80% accuracy for common developer queries"
   ],
   "longer_term_goals": [
     "Handle all major Sony SDK workflows via natural language",
     "Provide helpful suggestions even when exact matches fail",
     "Maintain sub-3 second response times under load"
   ]
 },

 "file_structure_context": {
   "likely_files_to_modify": [
     "search.py (embedding and retrieval logic)",
     "mcp_server.py (connection handling and timeouts)",
     "table_parser.py (PDF extraction and table processing)",
     "semantic_search.py (query understanding and intent mapping)"
   ],
   "new_files_to_create": [
     "intent_mapper.py (natural language → API mapping)",
     "connection_manager.py (async processing and keepalive)",
     "evaluation.py (semantic search test framework)"
   ]
 }
}