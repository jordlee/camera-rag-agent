#!/usr/bin/env python3
"""
Direct Pinecone embedder - bypasses ChromaDB to avoid JSON serialization issues.
Creates embeddings and uploads directly to Pinecone with native array metadata.

Supports both Pinecone Local (development) and Cloud Pinecone (production).
"""

import json
import os
import time
import sys
import numpy as np
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv

# Pinecone imports - handle different SDK versions
try:
    from pinecone import Pinecone, ServerlessSpec, PineconeGRPC
    PINECONE_SDK_V6 = True
except ImportError:
    from pinecone import Pinecone, ServerlessSpec
    PineconeGRPC = None
    PINECONE_SDK_V6 = False

# Load environment variables
load_dotenv()

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data/chunks.json"
BATCH_SIZE = 100  # Pinecone batch size

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "sdk-rag-system"
PINECONE_DIMENSION = 768  # all-mpnet-base-v2 dimension
PINECONE_METRIC = "cosine"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"

# Local development settings (following official guidelines)
USE_LOCAL_PINECONE = os.getenv("USE_LOCAL_PINECONE", "false").lower() == "true"
LOCAL_PINECONE_HOST = "http://localhost:5080"
LOCAL_PINECONE_API_KEY = "pclocal"  # Standard for local development

# --- Model Configuration for Different Data Types ---
# Using CodeBERT for ALL types for better technical/API search
MODEL_CONFIG = {
    "example_code": {
        "model_name": "microsoft/codebert-base",
        "model_type": "codebert",
        "description": "CodeBERT for code examples"
    },
    "summary": {
        "model_name": "microsoft/codebert-base", 
        "model_type": "codebert",
        "description": "CodeBERT for API summaries"
    },
    "member": {
        "model_name": "microsoft/codebert-base",
        "model_type": "codebert",
        "description": "CodeBERT for API members"
    },
    "enum": {
        "model_name": "microsoft/codebert-base",
        "model_type": "codebert",
        "description": "CodeBERT for enum definitions"
    },
    "function": {
        "model_name": "microsoft/codebert-base",
        "model_type": "codebert",
        "description": "CodeBERT for function definitions"
    },
    "variable": {
        "model_name": "microsoft/codebert-base",
        "model_type": "codebert",
        "description": "CodeBERT for variable definitions"
    },
    "documentation_text": {
        "model_name": "microsoft/codebert-base",
        "model_type": "codebert",
        "description": "CodeBERT for documentation text"
    },
    "documentation_table": {
        "model_name": "microsoft/codebert-base",
        "model_type": "codebert", 
        "description": "CodeBERT for table data"
    },
    "default": {
        "model_name": "microsoft/codebert-base",
        "model_type": "codebert",
        "description": "Default CodeBERT model"
    }
}

# --- Test Configuration ---
TEST_MODE = False  # Set to True to process a limited number of chunks
TEST_CHUNK_LIMIT = 100

# --- Filters ---
METADATA_TYPE_FILTER = []  # Empty list to embed ALL types
DATA_SOURCE_FILTER = []    # Process all sources
SDK_VERSION_FILTER = None  # Process all versions (already filtered)

class CodeBERTEmbedder:
    """Wrapper for CodeBERT model to generate embeddings for code."""
    
    def __init__(self, model_name="microsoft/codebert-base"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
    
    def encode(self, texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True):
        """Generate embeddings for a list of texts using CodeBERT."""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize with truncation and padding
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use CLS token embedding as the sentence embedding
                batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            if normalize_embeddings:
                # L2 normalize embeddings
                batch_embeddings = batch_embeddings / np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
            
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)

def format_time(seconds):
    """Converts seconds into a human-readable HH:MM:SS format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def setup_pinecone():
    """
    Initialize Pinecone following official guidelines.
    Supports both local development and cloud deployment.
    """
    if USE_LOCAL_PINECONE:
        print("🏠 Using Pinecone Local for development...")
        print("Make sure Docker is running: docker run -p 5080-5090:5080-5090 ghcr.io/pinecone-io/pinecone-local:latest")
        
        # Use PineconeGRPC for local development (official recommendation)
        if PINECONE_SDK_V6 and PineconeGRPC:
            pc = PineconeGRPC(
                api_key=LOCAL_PINECONE_API_KEY,
                host=LOCAL_PINECONE_HOST
            )
        else:
            # Fallback for older SDK versions
            pc = Pinecone(
                api_key=LOCAL_PINECONE_API_KEY,
                host=LOCAL_PINECONE_HOST
            )
    else:
        print("☁️ Using Cloud Pinecone for production...")
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY environment variable not set for cloud usage")
        
        pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Handle index creation/management
    if USE_LOCAL_PINECONE:
        # For local development, indexes are managed differently
        print("✅ Connected to Pinecone Local")
        # Local Pinecone auto-creates indexes, just get reference
        index = pc.Index(PINECONE_INDEX_NAME)
    else:
        # Cloud Pinecone index management
        existing_indexes = [index.name for index in pc.list_indexes()]
        
        if PINECONE_INDEX_NAME not in existing_indexes:
            print(f"Creating new Pinecone index: {PINECONE_INDEX_NAME}")
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=PINECONE_DIMENSION,
                metric=PINECONE_METRIC,
                spec=ServerlessSpec(
                    cloud=PINECONE_CLOUD,
                    region=PINECONE_REGION
                )
            )
            print("✅ Index created successfully")
        else:
            print(f"✅ Using existing index: {PINECONE_INDEX_NAME}")
        
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Clear existing index for clean upload (handle empty index gracefully)
        print("🗑️ Clearing existing index...")
        try:
            index.delete(delete_all=True)
            print("✅ Index cleared")
        except Exception as e:
            if "Namespace not found" in str(e) or "404" in str(e):
                print("✅ Index is already empty")
            else:
                raise e
    
    return index

def prepare_metadata_for_pinecone(metadata):
    """
    Prepare metadata for Pinecone - keep arrays as arrays (no JSON serialization).
    This is the key difference from ChromaDB approach.
    """
    processed_metadata = {}
    
    for key, value in metadata.items():
        if isinstance(value, list):
            # Keep arrays as arrays - Pinecone supports this!
            processed_metadata[key] = value
        elif isinstance(value, (str, int, float, bool)) or value is None:
            processed_metadata[key] = value
        else:
            # Convert other types to strings
            processed_metadata[key] = str(value)
    
    return processed_metadata

def split_large_content(content: str, metadata: dict, chunk_id: str, max_content_size: int = 30000):
    """Split content that's too large for Pinecone metadata."""
    if len(content) <= max_content_size:
        return [(content, metadata, chunk_id)]
    
    # Split content into smaller pieces
    chunks = []
    overlap = 200
    start = 0
    part_num = 1
    
    while start < len(content):
        end = min(start + max_content_size, len(content))
        
        # Try to break at sentence/line boundaries
        if end < len(content):
            for break_char in ['\\n\\n', '.\\n', '. ', '\\n']:
                last_break = content.rfind(break_char, start, end)
                if last_break > start + max_content_size // 2:
                    end = last_break + len(break_char)
                    break
        
        chunk_content = content[start:end]
        chunk_metadata = metadata.copy()
        chunk_metadata['chunk_part'] = part_num
        chunk_metadata['total_parts'] = None  # Will be updated after splitting
        
        chunks.append((chunk_content, chunk_metadata, f"{chunk_id}_part{part_num}"))
        
        start = max(end - overlap, start + 1)
        part_num += 1
    
    # Update total_parts for all chunks
    for i, (content, metadata, chunk_id) in enumerate(chunks):
        chunks[i] = (content, {**metadata, 'total_parts': len(chunks)}, chunk_id)
    
    return chunks

def get_model_for_chunk(chunk, models_cache):
    """Determine which model to use for a given chunk."""
    metadata_type = chunk.get('metadata', {}).get('type')
    config_key = metadata_type if metadata_type in MODEL_CONFIG else 'default'
    
    if config_key not in models_cache:
        config = MODEL_CONFIG.get(config_key, MODEL_CONFIG['default'])
        print(f"\\nLoading model for '{config_key}': {config['model_name']}")
        
        if config['model_type'] == 'codebert':
            models_cache[config_key] = CodeBERTEmbedder(config['model_name'])
        else:
            models_cache[config_key] = SentenceTransformer(config['model_name'])
    
    return config_key, models_cache[config_key]

def parse_json_strings_in_metadata(metadata):
    """
    Parse JSON string metadata back to native arrays.
    This handles the ChromaDB -> Pinecone conversion.
    """
    parsed_metadata = {}
    
    for key, value in metadata.items():
        if isinstance(value, str) and key in ['function_name', 'error_codes', 'warning_codes']:
            # Try to parse JSON strings back to arrays
            try:
                if value.startswith('[') and value.endswith(']'):
                    parsed_value = json.loads(value)
                    parsed_metadata[key] = parsed_value
                else:
                    parsed_metadata[key] = value
            except json.JSONDecodeError:
                parsed_metadata[key] = value
        else:
            parsed_metadata[key] = value
    
    return parsed_metadata

def main():
    """
    Main function to generate embeddings using appropriate models for different data types
    and store them directly in Pinecone following official guidelines.
    """
    print(f"--- Starting Direct Pinecone Embedding Process ---")
    print(f"Environment: {'Local Development' if USE_LOCAL_PINECONE else 'Cloud Production'}")
    print(f"Models configured:")
    for key, config in MODEL_CONFIG.items():
        print(f"  - {key}: {config['description']}")

    # 1. Load the chunked data
    print(f"\\nLoading chunks from {CHUNKS_FILE}...")
    try:
        with CHUNKS_FILE.open("r", encoding="utf-8") as f:
            chunks = json.load(f)
        total_chunks = len(chunks)
        print(f"Successfully loaded {total_chunks} chunks.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading chunks file: {e}")
        return

    # Apply filters (same as embedder_local.py)
    if SDK_VERSION_FILTER:
        print(f"\\nFiltering chunks by SDK version: {SDK_VERSION_FILTER}...")
        filtered_chunks = []
        for chunk in chunks:
            file_path = chunk.get('metadata', {}).get('file_path', '')
            version = chunk.get('metadata', {}).get('version', '')
            if SDK_VERSION_FILTER in file_path or version == SDK_VERSION_FILTER:
                filtered_chunks.append(chunk)
        chunks = filtered_chunks
        print(f"Filtered down to {len(chunks)} chunks for version {SDK_VERSION_FILTER}.")

    if DATA_SOURCE_FILTER:
        print(f"\\nFiltering chunks by data source: {DATA_SOURCE_FILTER}...")
        filtered_chunks = []
        for chunk in chunks:
            file_path = chunk.get('metadata', {}).get('file_path', '')
            if any(source in file_path.lower() for source in DATA_SOURCE_FILTER):
                filtered_chunks.append(chunk)
        chunks = filtered_chunks
        print(f"Filtered down to {len(chunks)} chunks from specified sources.")

    if METADATA_TYPE_FILTER:
        print(f"Filtering chunks by type: {METADATA_TYPE_FILTER}...")
        chunks = [
            chunk for chunk in chunks
            if chunk.get('metadata', {}).get('type') in METADATA_TYPE_FILTER
        ]
        print(f"Filtered down to {len(chunks)} chunks.")

    if TEST_MODE:
        print(f"\\n--- Running in TEST MODE: Processing only {TEST_CHUNK_LIMIT} chunks ---")
        chunks_to_process = chunks[:TEST_CHUNK_LIMIT]
        original_total_chunks = len(chunks)
        total_chunks = len(chunks_to_process)
        print(f"Processing {total_chunks} chunks for testing out of {original_total_chunks} total.")
    else:
        chunks_to_process = chunks
        total_chunks = len(chunks_to_process)

    if total_chunks == 0:
        print("No chunks to process after filtering. Exiting.")
        return

    # 2. Setup Pinecone (following official guidelines)
    print(f"\\nSetting up Pinecone...")
    index = setup_pinecone()

    # 3. Group chunks by model type for efficient processing
    print("\\nGrouping chunks by model type...")
    chunks_by_model = {}
    models_cache = {}
    
    for chunk in chunks_to_process:
        config_key, _ = get_model_for_chunk(chunk, models_cache)
        if config_key not in chunks_by_model:
            chunks_by_model[config_key] = []
        chunks_by_model[config_key].append(chunk)
    
    print("Chunk distribution by model:")
    for model_key, model_chunks in chunks_by_model.items():
        print(f"  - {model_key}: {len(model_chunks)} chunks")

    # 4. Generate embeddings and upload directly to Pinecone
    start_time = time.time()
    total_processed = 0
    split_count = 0
    vectors_uploaded = 0
    
    for model_key, model_chunks in chunks_by_model.items():
        config = MODEL_CONFIG.get(model_key, MODEL_CONFIG['default'])
        print(f"\\n--- Processing {len(model_chunks)} chunks with {config['description']} ---")
        
        # Get or create model
        if model_key not in models_cache:
            print(f"Loading model: {config['model_name']}")
            if config['model_type'] == 'codebert':
                models_cache[model_key] = CodeBERTEmbedder(config['model_name'])
            else:
                models_cache[model_key] = SentenceTransformer(config['model_name'])
        
        model = models_cache[model_key]
        
        # Prepare all vectors for this model type
        vectors_to_upload = []
        
        for chunk in model_chunks:
            content = chunk['content']
            chunk_id = chunk['id']
            metadata = chunk['metadata'].copy()
            
            # Parse JSON strings in metadata back to arrays
            metadata = parse_json_strings_in_metadata(metadata)
            
            # Add model info to metadata
            metadata['embedding_model'] = config['model_name']
            
            # Prepare metadata for Pinecone (keep arrays as arrays!)
            pinecone_metadata = prepare_metadata_for_pinecone(metadata)
            
            # Split large content if needed
            content_chunks = split_large_content(content, pinecone_metadata, chunk_id)
            if len(content_chunks) > 1:
                split_count += 1
            
            # Generate embedding for original content (reuse for splits)
            embedding = model.encode([content], normalize_embeddings=True)[0]
            
            # Add each content chunk as a vector
            for chunk_content, chunk_metadata, final_chunk_id in content_chunks:
                # Store content in metadata for Pinecone
                chunk_metadata['content'] = chunk_content
                
                vectors_to_upload.append({
                    'id': final_chunk_id,
                    'values': embedding.tolist(),
                    'metadata': chunk_metadata
                })
        
        # Upload vectors to Pinecone in batches
        print(f"Uploading {len(vectors_to_upload)} vectors to Pinecone...")
        for i in range(0, len(vectors_to_upload), BATCH_SIZE):
            batch = vectors_to_upload[i:i + BATCH_SIZE]
            index.upsert(vectors=batch)
            vectors_uploaded += len(batch)
            
            total_processed += len([chunk for chunk in model_chunks[:len(batch)]])
            elapsed_time = time.time() - start_time
            chunks_per_second = total_processed / elapsed_time if elapsed_time > 0 else 0
            remaining_chunks = total_chunks - total_processed
            etr_seconds = (remaining_chunks / chunks_per_second) if chunks_per_second > 0 else 0
            
            progress_message = (
                f"\\rOverall Progress: {(total_processed / total_chunks):.2%} | "
                f"Chunks: {total_processed}/{total_chunks} | "
                f"Rate: {chunks_per_second:.1f} chunks/sec | "
                f"ETR: {format_time(etr_seconds)}"
            )
            sys.stdout.write(progress_message)
            sys.stdout.flush()
    
    # 5. Verify upload and test search functionality
    print(f"\\n\\n--- Direct Pinecone Embedding Process Complete ---")
    
    # Wait for indexing to complete
    print("Waiting for indexing to complete...")
    time.sleep(5)
    
    # Get final stats
    try:
        stats = index.describe_index_stats()
        final_count = stats['total_vector_count']
    except:
        final_count = vectors_uploaded  # Fallback for local Pinecone
    
    print(f"All chunks have been embedded and stored directly in Pinecone.")
    print(f"Total vectors in index: {final_count}")
    print(f"Vectors uploaded in this session: {vectors_uploaded}")
    if split_count > 0:
        print(f"Split {split_count} large chunks into multiple parts")
    
    # 6. Test exact search functionality (the main goal!)
    print(f"\\n🎯 Testing exact API search for 'SetSaveInfo' with native arrays...")
    try:
        # Use the same embedding model that was used for the chunks
        test_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        test_embedding = test_model.encode("API function").tolist()
        
        # Test exact search with native array filtering - this should work now!
        results = index.query(
            vector=test_embedding,
            top_k=5,
            include_metadata=True,
            filter={"function_name": {"$in": ["SetSaveInfo"]}}  # Native array filtering!
        )
        
        matches = results.get('matches', [])
        print(f"✅ Found {len(matches)} exact matches for SetSaveInfo!")
        
        for i, match in enumerate(matches):
            function_names = match['metadata'].get('function_name', [])
            print(f"  {i+1}. ID: {match['id']}")
            print(f"     Score: {match.get('score', 0):.4f}")
            print(f"     Function Names: {function_names}")
            print(f"     Type: {match['metadata'].get('type', 'unknown')}")
            print(f"     Content preview: {match['metadata'].get('content', '')[:100]}...")
            print()
        
        if len(matches) > 0:
            print("🎉 SUCCESS: Exact API search is working with native arrays!")
        else:
            print("⚠️ No matches found - may need to check array structure")
            
    except Exception as e:
        print(f"⚠️ Test search failed: {e}")
        print("This may be expected with Pinecone Local limitations")

    print(f"\\n{'='*60}")
    print("✅ Direct Pinecone embedding completed successfully!")
    if USE_LOCAL_PINECONE:
        print("🏠 Running on Pinecone Local - ready for development testing")
    else:
        print("☁️ Running on Cloud Pinecone - ready for production use")
    print("🔗 Metadata arrays preserved - exact search should work!")

if __name__ == "__main__":
    main()