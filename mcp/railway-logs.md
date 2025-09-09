{"message":"INFO:     100.64.0.3:61736 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T23:57:37.894466241Z"}
{"message":"2025-09-08 23:57:34,216 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-08T23:57:37.894473553Z"}
{"message":"INFO:     100.64.0.3:61736 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-09-08T23:57:37.894478220Z"}
{"message":"2025-09-08 23:57:34,588 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-08T23:57:37.894492744Z"}
{"message":"INFO:     100.64.0.4:23890 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T23:57:37.894500460Z"}
{"message":"2025-09-08 23:57:34,841 - mcp.server.lowlevel.server - INFO - Processing request of type ListResourcesRequest","attributes":{"level":"error"},"timestamp":"2025-09-08T23:57:37.894522840Z"}
{"message":"2025-09-08 23:57:34,843 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-08T23:57:37.894529118Z"}
{"message":"INFO:     100.64.0.5:54814 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T23:57:37.894534581Z"}
{"message":"2025-09-08 23:57:34,856 - mcp.server.lowlevel.server - INFO - Processing request of type ListToolsRequest","attributes":{"level":"error"},"timestamp":"2025-09-08T23:57:37.894539786Z"}
{"message":"2025-09-08 23:57:34,859 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-08T23:57:37.894545295Z"}
{"message":"INFO:     100.64.0.6:11332 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T23:57:37.894551794Z"}
{"message":"2025-09-08 23:57:34,876 - mcp.server.lowlevel.server - INFO - Processing request of type ListPromptsRequest","attributes":{"level":"error"},"timestamp":"2025-09-08T23:57:37.894558210Z"}
{"message":"2025-09-08 23:57:34,877 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-08T23:57:37.894562285Z"}
{"message":"INFO:     100.64.0.7:18904 - \"GET /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-08T23:58:37.903451283Z"}
{"message":"2025-09-08 23:59:05,059 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-08T23:59:07.898606054Z"}
{"message":"INFO:     100.64.0.8:26336 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-09T00:02:28.006514941Z"}
{"message":"2025-09-09 00:02:24,830 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006527273Z"}
{"message":"INFO:     100.64.0.6:56196 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-09-09T00:02:28.006534800Z"}
{"message":"2025-09-09 00:02:25,260 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006541073Z"}
{"message":"INFO:     100.64.0.8:26336 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-09T00:02:28.006546903Z"}
{"message":"2025-09-09 00:02:25,413 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006553533Z"}
{"message":"2025-09-09 00:02:25,413 - __main__ - INFO - Search progress: {'status': 'analyzing_intent', 'progress': 0.1}","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006560277Z"}
{"message":"2025-09-09 00:02:25,413 - __main__ - ERROR - Intelligent search error","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006567493Z"}
{"message":"Traceback (most recent call last):","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006573471Z"}
{"message":"  File \"/app/mcp_server.py\", line 59, in search_sdk","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006579990Z"}
{"message":"    results = await rag_search.search_with_intent(","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006585682Z"}
{"message":"              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006591201Z"}
{"message":"  File \"/app/search.py\", line 562, in search_with_intent","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006597299Z"}
{"message":"    await progress_callback({\"status\": \"analyzing_intent\", \"progress\": 0.1})","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006603044Z"}
{"message":"TypeError: object NoneType can't be used in 'await' expression","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:28.006607883Z"}
{"message":"\rBatches:   0%|          | 0/1 [00:00<?, ?it/s]\rBatches: 100%|██████████| 1/1 [00:04<00:00,  4.43s/it]\rBatches: 100%|██████████| 1/1 [00:04<00:00,  4.43s/it]","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:29.852498809Z"}
{"message":"2025-09-09 00:02:29,851 - search - WARNING - Embedding took 4.44s (exceeds 3.0s limit)","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:29.852505209Z"}
{"message":"2025-09-09 00:02:30,490 - search - INFO - Found 5 results for query: connect to camera...","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:30.513260911Z"}
{"message":"INFO:     100.64.0.7:29242 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-09T00:02:30.513266603Z"}
{"message":"INFO:     100.64.0.7:29256 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-09T00:02:30.513272335Z"}
{"message":"INFO:     100.64.0.7:21262 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-09-09T00:02:30.513277928Z"}
{"message":"2025-09-09 00:02:30,511 - mcp.server.lowlevel.server - INFO - Processing request of type ListToolsRequest","attributes":{"level":"error"},"timestamp":"2025-09-09T00:02:30.513283482Z"}