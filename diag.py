# diag.py
import sys
import google.cloud.aiplatform

print("--- Python Executable ---")
print(sys.executable)
print("\n--- google-cloud-aiplatform library ---")
print(f"Version: {google.cloud.aiplatform.__version__}")
print(f"Path: {google.cloud.aiplatform.__file__}")

print("\n--- Checking for TextEmbeddingModel ---")
if hasattr(google.cloud.aiplatform, 'TextEmbeddingModel'):
    print("SUCCESS: 'TextEmbeddingModel' attribute found.")
else:
    print("FAILURE: 'TextEmbeddingModel' attribute NOT FOUND.")