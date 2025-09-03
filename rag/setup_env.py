#!/usr/bin/env python3
"""Setup script for RAG environment variables."""

import os
from pathlib import Path

def create_env_file():
    """Create a .env template file for Pinecone configuration."""
    env_content = """# Pinecone Configuration
# Get your API key from: https://app.pinecone.io/
PINECONE_API_KEY=your_pinecone_api_key_here

# Pinecone Index Settings (modify if needed)
PINECONE_INDEX_NAME=sdk-rag-system
PINECONE_DIMENSION=768
PINECONE_METRIC=cosine
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
"""
    
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {env_file}")
        print("📝 Please edit the .env file and add your Pinecone API key")
    else:
        print(f"⚠️ {env_file} already exists")

def setup_instructions():
    """Print setup instructions."""
    print("\n🚀 RAG Setup Instructions:")
    print("=" * 40)
    print("1. Sign up for Pinecone (free): https://app.pinecone.io/")
    print("2. Create a new API key")
    print("3. Edit rag/.env file with your API key")
    print("4. Install requirements: pip install -r rag/requirements.txt")
    print("5. Run migration: python rag/migrate_to_pinecone.py")
    print("=" * 40)

if __name__ == "__main__":
    create_env_file()
    setup_instructions()