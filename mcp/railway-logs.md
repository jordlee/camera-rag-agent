{"message":"2025-09-23 20:49:43,402 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729309541Z"}
{"message":"2025-09-23 20:49:43,402 - mcp.server.streamable_http - ERROR - Error in message router","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729314153Z"}
{"message":"Traceback (most recent call last):","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729318354Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/mcp/server/streamable_http.py\", line 831, in message_router","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729323259Z"}
{"message":"    async for session_message in write_stream_reader:","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729328549Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/anyio/abc/_streams.py\", line 41, in __anext__","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729332890Z"}
{"message":"    return await self.receive()","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729337139Z"}
{"message":"           ^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729341571Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py\", line 111, in receive","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729345528Z"}
{"message":"    return self.receive_nowait()","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729350661Z"}
{"message":"           ^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729356223Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py\", line 93, in receive_nowait","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729362779Z"}
{"message":"    raise ClosedResourceError","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729370160Z"}
{"message":"anyio.ClosedResourceError","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729375686Z"}
{"message":"INFO:     100.64.0.7:42524 - \"GET /.well-known/oauth-protected-resource/mcp HTTP/1.1\" 404 Not Found","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729381583Z"}
{"message":"INFO:     100.64.0.3:26802 - \"GET /.well-known/oauth-authorization-server/mcp HTTP/1.1\" 404 Not Found","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729387299Z"}
{"message":"INFO:     100.64.0.3:26802 - \"GET /.well-known/oauth-authorization-server HTTP/1.1\" 404 Not Found","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729392025Z"}
{"message":"INFO:     100.64.0.5:47952 - \"GET /.well-known/oauth-authorization-server/mcp HTTP/1.1\" 404 Not Found","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729396591Z"}
{"message":"INFO:     100.64.0.5:47952 - \"GET /.well-known/oauth-authorization-server HTTP/1.1\" 404 Not Found","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729465885Z"}
{"message":"INFO:     100.64.0.3:26802 - \"POST /register HTTP/1.1\" 404 Not Found","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729471771Z"}
{"message":"INFO:     100.64.0.10:43352 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729477423Z"}
{"message":"2025-09-23 20:49:46,453 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729483425Z"}
{"message":"INFO:     100.64.0.4:32344 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729489292Z"}
{"message":"2025-09-23 20:49:46,803 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729496022Z"}
{"message":"INFO:     100.64.0.7:42524 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729501974Z"}
{"message":"2025-09-23 20:49:46,928 - mcp.server.lowlevel.server - INFO - Processing request of type ListPromptsRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729508357Z"}
{"message":"2025-09-23 20:49:46,929 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729515116Z"}
{"message":"INFO:     100.64.0.10:43352 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729522198Z"}
{"message":"2025-09-23 20:49:46,933 - mcp.server.lowlevel.server - INFO - Processing request of type ListResourcesRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729528959Z"}
{"message":"2025-09-23 20:49:46,934 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729535109Z"}
{"message":"INFO:     100.64.0.7:42532 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:49:50.729541395Z"}
{"message":"2025-09-23 20:49:46,998 - mcp.server.lowlevel.server - INFO - Processing request of type ListToolsRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729545824Z"}
{"message":"2025-09-23 20:49:46,999 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:49:50.729549965Z"}
{"message":"INFO:     100.64.0.8:61518 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:50:11.069317248Z"}
{"message":"2025-09-23 20:50:03,730 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:11.069324033Z"}
{"message":"2025-09-23 20:50:03,730 - search - INFO - Query 'GetOSDImage DownloadSettingFile ImportLUTFile' appears to be API name, trying exact match first","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:11.069329516Z"}
{"message":"2025-09-23 20:50:04,127 - search - INFO - Found 0 exact matches for API: GetOSDImage DownloadSettingFile ImportLUTFile","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:11.069334471Z"}
{"message":"\rBatches:   0%|          | 0/1 [00:00<?, ?it/s]\rBatches: 100%|██████████| 1/1 [00:06<00:00,  6.61s/it]\rBatches: 100%|██████████| 1/1 [00:06<00:00,  6.61s/it]","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:11.069630941Z"}
{"message":"2025-09-23 20:50:10,745 - search - WARNING - Embedding took 6.62s (exceeds 3.0s limit)","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:11.069636464Z"}
{"message":"2025-09-23 20:50:10,968 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:11.072476112Z"}
{"message":"2025-09-23 20:50:10,965 - search - INFO - Found 10 results for query: GetOSDImage DownloadSettingFile ImportLUTFile...","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:11.072547643Z"}
{"message":"INFO:     100.64.0.7:54440 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:50:18.628608329Z"}
{"message":"2025-09-23 20:50:18,627 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:18.628617110Z"}
{"message":"\rBatches:   0%|          | 0/1 [00:00<?, ?it/s]\rBatches: 100%|██████████| 1/1 [00:07<00:00,  7.13s/it]\rBatches: 100%|██████████| 1/1 [00:07<00:00,  7.13s/it]","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:25.770996727Z"}
{"message":"2025-09-23 20:50:25,765 - search - WARNING - Embedding took 7.14s (exceeds 3.0s limit)","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:25.771004358Z"}
{"message":"2025-09-23 20:50:25,995 - search - INFO - Found 10 results for query: ImportLUTFile LUT camera support compatibility...","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:26.022342562Z"}
{"message":"2025-09-23 20:50:25,997 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:26.022354243Z"}
{"message":"INFO:     100.64.0.10:50006 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:50:33.578654157Z"}
{"message":"2025-09-23 20:50:33,576 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:33.578660988Z"}
{"message":"\rBatches:   0%|          | 0/1 [00:00<?, ?it/s]\rBatches: 100%|██████████| 1/1 [00:07<00:00,  7.18s/it]\rBatches: 100%|██████████| 1/1 [00:07<00:00,  7.18s/it]","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:40.760551444Z"}
{"message":"2025-09-23 20:50:40,759 - search - WARNING - Embedding took 7.18s (exceeds 3.0s limit)","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:40.760558741Z"}
{"message":"2025-09-23 20:50:40,909 - search - INFO - Found 10 results for query: GetOSDImage DownloadSettingFile camera compatibili...","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:40.910590968Z"}
{"message":"2025-09-23 20:50:40,912 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:50:40.914230118Z"}
{"message":"INFO:     100.64.0.5:31792 - \"GET /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:51:50.906941289Z"}
{"message":"2025-09-23 20:52:11,240 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:52:20.910137278Z"}
{"message":"INFO:     100.64.0.8:56956 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:54:10.930686686Z"}
{"message":"2025-09-23 20:54:07,321 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930694477Z"}
{"message":"INFO:     100.64.0.7:34758 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-09-23T20:54:10.930699643Z"}
{"message":"2025-09-23 20:54:07,637 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930703707Z"}
{"message":"INFO:     100.64.0.3:26802 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:54:10.930707832Z"}
{"message":"2025-09-23 20:54:07,770 - mcp.server.lowlevel.server - INFO - Processing request of type ListToolsRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930725049Z"}
{"message":"2025-09-23 20:54:07,771 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930729108Z"}
{"message":"INFO:     100.64.0.3:26802 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:54:10.930733617Z"}
{"message":"2025-09-23 20:54:07,847 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930738987Z"}
{"message":"2025-09-23 20:54:08,232 - search - INFO - Found 0 exact matches for API: FocalDistanceInFeet","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930743271Z"}
{"message":"INFO:     100.64.0.5:23082 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:54:10.930747039Z"}
{"message":"2025-09-23 20:54:08,236 - mcp.server.lowlevel.server - INFO - Processing request of type ListResourcesRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930750984Z"}
{"message":"INFO:     100.64.0.6:10010 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:54:10.930754663Z"}
{"message":"2025-09-23 20:54:08,237 - mcp.server.lowlevel.server - INFO - Processing request of type ListPromptsRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930758508Z"}
{"message":"2025-09-23 20:54:08,238 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930762643Z"}
{"message":"2025-09-23 20:54:08,238 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930766685Z"}
{"message":"2025-09-23 20:54:08,238 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:10.930771066Z"}
{"message":"INFO:     100.64.0.5:23092 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:54:14.675049975Z"}
{"message":"2025-09-23 20:54:14,672 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:14.675061346Z"}
{"message":"2025-09-23 20:54:14,850 - search - INFO - Found 5 exact matches for API: CrDeviceProperty_FocalDistanceInFeet","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:14.851668431Z"}
{"message":"2025-09-23 20:54:14,852 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:54:14.855200751Z"}
{"message":"INFO:     100.64.0.3:55426 - \"GET /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-23T20:55:24.883939380Z"}
{"message":"2025-09-23 20:55:45,094 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-23T20:55:54.885782122Z"}