import os
import requests
import json
import math
from app.database import SessionLocal
from app.models.document import DocumentChunk

MODEL_NAME  = "all-MiniLM-L6-v2"
CACHE_DIR   = "model_cache"
MODEL_PATH  = f"{CACHE_DIR}/{MODEL_NAME}"

# We check if local sentence-transformers can be imported
model = None
try:
    if os.path.exists(MODEL_PATH):
        from sentence_transformers import SentenceTransformer
        print(f"[Embedding] Loading model from local cache: {MODEL_PATH}")
        model = SentenceTransformer(MODEL_PATH)
    elif os.getenv("VERCEL") != "1":
        from sentence_transformers import SentenceTransformer
        print(f"[Embedding] model_cache not found — downloading {MODEL_NAME} (first run only)...")
        os.makedirs(CACHE_DIR, exist_ok=True)
        model = SentenceTransformer(MODEL_NAME)
        model.save(MODEL_PATH)
        print(f"[Embedding] Model saved to {MODEL_PATH} for future use.")
except ImportError:
    print("[Embedding] sentence-transformers not installed. Falling back to Hugging Face Inference API.")

# Keep Chroma client optional
chroma_client = None
try:
    import chromadb
    CHROMA_DIR = "chroma_data"
    os.makedirs(CHROMA_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
except ImportError:
    print("[Embedding] chromadb not installed. Chroma persistent operations will be bypassed.")

def get_or_create_collection(collection_name: str):
    if chroma_client is not None:
        return chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    return None

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using local model or Hugging Face Inference API fallback."""
    global model
    if model is not None:
        return model.encode(texts).tolist()

    # Fallback to Hugging Face Inference API
    hf_token = os.getenv("HF_TOKEN")
    api_url = f"https://api-inference.huggingface.co/models/sentence-transformers/{MODEL_NAME}"
    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    payload = {
        "inputs": texts,
        "options": {"wait_for_model": True}
    }

    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        res_json = response.json()
        if isinstance(res_json, list):
            return res_json
        raise Exception(f"Unexpected response format from Hugging Face: {res_json}")
    else:
        raise Exception(f"Hugging Face Inference API failed with code {response.status_code}: {response.text}")

def cosine_similarity(v1, v2):
    """Compute cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = math.sqrt(sum(x * x for x in v1))
    norm_v2 = math.sqrt(sum(x * x for x in v2))
    if not norm_v1 or not norm_v2:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def embed_and_store_chunks(document_id: str, chunks: list[dict]):
    """Generate embeddings and store them directly in the chunks."""
    texts = [chunk["chunk_text"] for chunk in chunks]
    embeddings = get_embeddings_batch(texts)
    
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb

    # Optionally store in local ChromaDB if available
    collection = get_or_create_collection(f"doc_{document_id}")
    if collection is not None:
        ids = [f"{document_id}_chunk_{chunk['chunk_index']}" for chunk in chunks]
        metadatas = [
            {
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "document_id": document_id
            }
            for chunk in chunks
        ]
        collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

    return len(chunks)

def search_similar_chunks(document_id: str, query: str, n_results: int = 5) -> list[dict]:
    """Retrieve relevant chunks using local database stored embeddings and in-memory cosine similarity search."""
    # 1. Generate query embedding
    query_emb = get_embeddings_batch([query])[0]

    # 2. Query all chunks for this document from the relational database
    db = SessionLocal()
    try:
        db_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        if not db_chunks:
            # Fallback to ChromaDB if database chunks not found but ChromaDB is available
            collection = get_or_create_collection(f"doc_{document_id}")
            if collection is not None:
                try:
                    results = collection.query(
                        query_embeddings=[query_emb],
                        n_results=n_results
                    )
                    chunks = []
                    for i, doc in enumerate(results["documents"][0]):
                        chunks.append({
                            "chunk_text":      doc,
                            "page_number":     results["metadatas"][0][i]["page_number"],
                            "chunk_index":     results["metadatas"][0][i]["chunk_index"],
                            "similarity_score": 1 - results["distances"][0][i]
                        })
                    return chunks
                except Exception as e:
                    print(f"ChromaDB search fallback failed: {e}")
            return []

        # 3. Calculate similarity score for each chunk
        scored_chunks = []
        for c in db_chunks:
            # If embedding is stored, use it. If not, generate on-demand.
            emb = c.embedding
            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except Exception:
                    pass

            if not emb:
                try:
                    emb = get_embeddings_batch([c.chunk_text])[0]
                    c.embedding = emb
                    db.add(c)
                    db.commit()
                except Exception as e:
                    print(f"Failed to generate embedding on-demand for chunk: {e}")
                    emb = None

            if emb:
                sim = cosine_similarity(query_emb, emb)
            else:
                sim = 0.0

            scored_chunks.append({
                "chunk_text":      c.chunk_text,
                "page_number":     c.page_number,
                "chunk_index":     c.chunk_index,
                "similarity_score": sim
            })

        # 4. Sort and return top results
        scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_chunks[:n_results]
    finally:
        db.close()