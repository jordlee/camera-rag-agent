# src/embedding/embedder_local.py

import json
from pathlib import Path
import chromadb
import time
import sys
import numpy as np
import torch
import shutil
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data/chunks.json"
DB_PATH = PROJECT_ROOT / "data/chroma_db"
COLLECTION_NAME = "sdk_docs_local" # New collection for local embeddings
BATCH_SIZE = 32                    # Reduced for CodeBERT models which are larger

# --- Model Configuration for Different Data Types ---
# Map metadata types to appropriate embedding models
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
        "model_name": "sentence-transformers/all-mpnet-base-v2",
        "model_type": "sentence_transformer",
        "description": "All-MPNet for documentation text"
    },
    "documentation_table": {
        "model_name": "sentence-transformers/all-mpnet-base-v2",
        "model_type": "sentence_transformer", 
        "description": "All-MPNet for table data"
    },
    "default": {
        "model_name": "sentence-transformers/all-mpnet-base-v2",
        "model_type": "sentence_transformer",
        "description": "Default All-MPNet model"
    }
}

# --- Test Configuration ---
# Set to True to process a limited number of chunks.
# Set to False for a full run on all chunks.
TEST_MODE = False  # Test with small subset first
TEST_CHUNK_LIMIT = 100  # Number of chunks to process when TEST_MODE is True

# --- Metadata Filtering ---
# Use this list to specify which metadata types to embed.
# Possible types: ['summary', 'member', 'example_code', 'documentation_text', 'documentation_table']
# To embed ALL types, leave the list empty: []
METADATA_TYPE_FILTER = []  # Empty list to embed ALL types

# --- Data Source Filtering ---
# Specify which data sources to process (based on file paths in metadata)
# e.g., ['cpp', 'examples'] to only process C++ and example files
# Empty list processes all sources
DATA_SOURCE_FILTER = []  # Process all sources from chunks file

# --- Version Filtering ---
# Specify which SDK version to process
# Set to None to process all versions
SDK_VERSION_FILTER = None  # Already filtered in chunker

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

def get_data_source_from_path(file_path):
    """Extract data source type from file path."""
    if not file_path:
        return "default"
    
    # Check for specific patterns in the path
    if "cpp" in file_path.lower() or ".cpp" in file_path or ".h" in file_path:
        return "cpp"
    elif "example" in file_path.lower():
        return "examples"
    elif "documentation" in file_path.lower() or "docs" in file_path.lower():
        # Check metadata type for more specific classification
        return None  # Will use metadata type instead
    
    return "default"

def get_model_for_chunk(chunk, models_cache):
    """Determine which model to use for a given chunk."""
    # Check by metadata type
    metadata_type = chunk.get('metadata', {}).get('type')
    
    # Use metadata type directly if it exists in config, otherwise use default
    config_key = metadata_type if metadata_type in MODEL_CONFIG else 'default'
    
    # Get or create model instance
    if config_key not in models_cache:
        config = MODEL_CONFIG.get(config_key, MODEL_CONFIG['default'])
        print(f"\nLoading model for '{config_key}': {config['model_name']}")
        
        if config['model_type'] == 'codebert':
            models_cache[config_key] = CodeBERTEmbedder(config['model_name'])
        else:
            models_cache[config_key] = SentenceTransformer(config['model_name'])
    
    return config_key, models_cache[config_key]

def main():
    """
    Main function to generate embeddings using appropriate models for different data types
    and store them in ChromaDB.
    """
    print(f"--- Starting Multi-Model Embedding Process ---")
    print(f"Models configured:")
    for key, config in MODEL_CONFIG.items():
        print(f"  - {key}: {config['description']}")

    # 1. Load the chunked data
    print(f"\nLoading chunks from {CHUNKS_FILE}...")
    try:
        with CHUNKS_FILE.open("r", encoding="utf-8") as f:
            chunks = json.load(f)
        total_chunks = len(chunks)
        print(f"Successfully loaded {total_chunks} chunks.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading chunks file: {e}")
        return

    # --- Apply Version Filtering ---
    if SDK_VERSION_FILTER:
        print(f"\nFiltering chunks by SDK version: {SDK_VERSION_FILTER}...")
        filtered_chunks = []
        for chunk in chunks:
            file_path = chunk.get('metadata', {}).get('file_path', '')
            version = chunk.get('metadata', {}).get('version', '')
            # Check both file path and metadata version field
            if SDK_VERSION_FILTER in file_path or version == SDK_VERSION_FILTER:
                filtered_chunks.append(chunk)
        chunks = filtered_chunks
        print(f"Filtered down to {len(chunks)} chunks for version {SDK_VERSION_FILTER}.")

    # --- Apply Data Source Filtering ---
    if DATA_SOURCE_FILTER:
        print(f"\nFiltering chunks by data source: {DATA_SOURCE_FILTER}...")
        filtered_chunks = []
        for chunk in chunks:
            file_path = chunk.get('metadata', {}).get('file_path', '')
            # Check if file path contains any of the filter keywords
            if any(source in file_path.lower() for source in DATA_SOURCE_FILTER):
                filtered_chunks.append(chunk)
        chunks = filtered_chunks
        print(f"Filtered down to {len(chunks)} chunks from specified sources.")

    # --- Apply Metadata Filtering ---
    if METADATA_TYPE_FILTER:
        print(f"Filtering chunks by type: {METADATA_TYPE_FILTER}...")
        chunks = [
            chunk for chunk in chunks
            if chunk.get('metadata', {}).get('type') in METADATA_TYPE_FILTER
        ]
        print(f"Filtered down to {len(chunks)} chunks.")

    # --- Apply Test Mode Subset ---
    if TEST_MODE:
        print(f"\n--- Running in TEST MODE: Processing only {TEST_CHUNK_LIMIT} chunks ---")
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

    # 2. Clean ChromaDB completely for new model
    print(f"\nSetting up ChromaDB at: {DB_PATH}")
    
    # Complete database cleanup for model upgrade
    if DB_PATH.exists():
        print("Removing existing ChromaDB directory for clean multi-model setup...")
        shutil.rmtree(DB_PATH)
        print("ChromaDB directory removed")
    
    # Create fresh ChromaDB with default local settings
    DB_PATH.mkdir(parents=True, exist_ok=True)
    db_client = chromadb.PersistentClient(path=str(DB_PATH))
    
    collection = db_client.get_or_create_collection(name=COLLECTION_NAME)
    print(f"ChromaDB collection '{COLLECTION_NAME}' is ready for multi-model embeddings.")
    
    # 3. Group chunks by model type for efficient processing
    print("\nGrouping chunks by model type...")
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
    
    # 4. Generate embeddings and store in ChromaDB
    start_time = time.time()
    total_processed = 0
    
    # Process chunks grouped by model type
    for model_key, model_chunks in chunks_by_model.items():
        config = MODEL_CONFIG.get(model_key, MODEL_CONFIG['default'])
        print(f"\n--- Processing {len(model_chunks)} chunks with {config['description']} ---")
        
        # Get or create model
        if model_key not in models_cache:
            print(f"Loading model: {config['model_name']}")
            if config['model_type'] == 'codebert':
                models_cache[model_key] = CodeBERTEmbedder(config['model_name'])
            else:
                models_cache[model_key] = SentenceTransformer(config['model_name'])
        
        model = models_cache[model_key]
        
        # Process in batches
        for i in range(0, len(model_chunks), BATCH_SIZE):
            batch_chunks = model_chunks[i:i + BATCH_SIZE]
            contents = [chunk['content'] for chunk in batch_chunks]
            ids = [chunk['id'] for chunk in batch_chunks]
            metadatas = [chunk['metadata'] for chunk in batch_chunks]
            
            # Add model info to metadata
            for metadata in metadatas:
                metadata['embedding_model'] = config['model_name']

            embeddings = model.encode(
                contents, 
                show_progress_bar=False,
                normalize_embeddings=True
            )

            collection.add(
                ids=ids,
                embeddings=np.array(embeddings, dtype=np.float32),
                documents=contents,
                metadatas=metadatas
            )

            total_processed += len(batch_chunks)
            elapsed_time = time.time() - start_time
            chunks_per_second = total_processed / elapsed_time if elapsed_time > 0 else 0
            remaining_chunks = total_chunks - total_processed
            etr_seconds = (remaining_chunks / chunks_per_second) if chunks_per_second > 0 else 0
            
            progress_message = (
                f"\rOverall Progress: {(total_processed / total_chunks):.2%} | "
                f"Chunks: {total_processed}/{total_chunks} | "
                f"Rate: {chunks_per_second:.1f} chunks/sec | "
                f"ETR: {format_time(etr_seconds)}"
            )
            sys.stdout.write(progress_message)
            sys.stdout.flush()

    print(f"\n\n--- Multi-Model Embedding Process Complete ---")
    print(f"All chunks have been embedded and stored in the '{COLLECTION_NAME}' collection.")
    print(f"Total items in collection: {collection.count()}")

if __name__ == "__main__":
    main()