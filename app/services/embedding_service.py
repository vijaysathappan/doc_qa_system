import chromadb
from sentence_transformers import SentenceTransformer
import os

MODEL_NAME  = "all-MiniLM-L6-v2"
CACHE_DIR   = "model_cache"
MODEL_PATH  = f"{CACHE_DIR}/{MODEL_NAME}"

# Load from local cache if available, otherwise download (and cache for next time)
if os.path.exists(MODEL_PATH):
    print(f"[Embedding] Loading model from local cache: {MODEL_PATH}")
    model = SentenceTransformer(MODEL_PATH)
else:
    print(f"[Embedding] model_cache not found — downloading {MODEL_NAME} (first run only)...")
    os.makedirs(CACHE_DIR, exist_ok=True)
    model = SentenceTransformer(MODEL_NAME)
    model.save(MODEL_PATH)
    print(f"[Embedding] Model saved to {MODEL_PATH} for future use.")

CHROMA_DIR = "chroma_data"
os.makedirs(CHROMA_DIR, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

def get_or_create_collection(collection_name: str):
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

def embed_and_store_chunks(document_id: str, chunks: list[dict]):
    collection = get_or_create_collection(f"doc_{document_id}")

    texts     = [chunk["chunk_text"] for chunk in chunks]
    ids       = [f"{document_id}_chunk_{chunk['chunk_index']}" for chunk in chunks]
    metadatas = [
        {
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "document_id": document_id
        }
        for chunk in chunks
    ]

    # Generate embeddings locally — no network call
    embeddings = model.encode(texts).tolist()

    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )

    return len(chunks)

def search_similar_chunks(document_id: str, query: str, n_results: int = 5) -> list[dict]:
    collection = get_or_create_collection(f"doc_{document_id}")

    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
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