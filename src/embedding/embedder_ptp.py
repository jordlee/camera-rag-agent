#!/usr/bin/env python3
"""
PTP Embedder for Camera Remote SDK V2.00.00-PTP

Thin wrapper around unified_embedder.py for backward compatibility.
Processes chunks_ptp_v2.json and upserts to Pinecone index sdk-rag-system-v2-ptp.
"""

import argparse
from unified_embedder import UnifiedEmbedder

# Configuration (PTP-specific)
CHUNKS_FILE = "data/v2.00.00/ptp/chunks.json"
INDEX_NAME = "sdk-rag-system-v2-ptp"
SDK_TYPE = "ptp"
SDK_VERSION = "V2.00.00"
MODEL_NAME = "Alibaba-NLP/gte-modernbert-base"
BATCH_SIZE = 100

# Test mode
TEST_MODE = False
TEST_LIMIT = 100


def main():
    """Run PTP embedder using unified embedder."""
    parser = argparse.ArgumentParser(description="PTP Embedder for Camera Remote SDK V2.00.00-PTP")
    parser.add_argument("--env", "--environment", type=str, default="production",
                        choices=["staging", "production"],
                        help="Target environment (staging or production). Default: production")
    args = parser.parse_args()

    embedder = UnifiedEmbedder(
        chunks_file=CHUNKS_FILE,
        index_name=INDEX_NAME,
        sdk_type=SDK_TYPE,
        sdk_version=SDK_VERSION,
        batch_size=BATCH_SIZE,
        model_name=MODEL_NAME,
        test_mode=TEST_MODE,
        test_limit=TEST_LIMIT,
        clear_existing=False,
        environment=args.env
    )

    embedder.run()


if __name__ == "__main__":
    main()
