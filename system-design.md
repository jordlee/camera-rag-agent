Metadata fields to MCP Tool mapping for SDK packages:
{
    (sdk_version (exists) : [V1.14.00,V2.00.00]) : set_sdk_version},
    (sdk_type (new): [camera-remote,ptp,client]) : set_sdk_type ,
    (sdk_language (new) : [cpp,csharp,python,typescript]) : set_sdk_language,
    (sdk_subtype (new) : [ptp-2,ptp-3,none]) : set_sdk_subtype,
    (sdk_os (new) : [linux,windows,cross-platform]) : set_sdk_os
}

Pinecone Index Naming

sdk-rag-system-[sdk_version]-[sdk-type]

excpetions to naming:

sdk-rag-system (V1.14.00-Camera-Remote)
sdk-rag-system-V2 (V2.00.00-Camera Remote)
sdk-rag-system-v2.10 (V2.10-Camera Remote)

Camera remote sdk-type is defaulta nd not appended, v1.14 is default and not appended (considered V1)

Pinecone document type to mcp tool:

For sdk_type [camera-remote] filtered via [set_sdk_type] mcp tool
{
    code types : set_sdk_language,

    all other types : set_sdk_type (same for all languages)

}

For sdk_type [ptp] filtered via [set_sdk_type] mcp tool
{
    code types : set_sdk_language and set_sdk_subtype and set_sdk_os,

    all other types: set_sdk_subtype and set_sdk_type

}

For sdk_type [client] filtered via [set_sdk_type] mcp tool
{
    code types : set_sdk_language,

    all other types : set_sdk_type (same for all languages)

}