# download_model.py — Downloads and caches the embedding model locally
# Run this ONCE before starting the server: py download_model.py
# Developer: vijay_sathappan

from sentence_transformers import SentenceTransformer
import os

MODEL_NAME = "all-MiniLM-L6-v2"
CACHE_DIR  = "model_cache"

print(f"Downloading {MODEL_NAME} to ./{CACHE_DIR}/ ...")
os.makedirs(CACHE_DIR, exist_ok=True)

model = SentenceTransformer(MODEL_NAME)
model.save(f"{CACHE_DIR}/{MODEL_NAME}")

print(f"\n✅ Model saved to ./{CACHE_DIR}/{MODEL_NAME}")
print("You can now run: py -m uvicorn app.main:app --reload")
