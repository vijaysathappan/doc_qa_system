from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.auth_utils import decode_token
from app.services.embedding_service import search_similar_chunks
from app.cache import get_cached, set_cached
from fastapi.security import OAuth2PasswordBearer
from groq import Groq
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
import os
import hashlib

router = APIRouter(prefix="/query", tags=["query"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

groq_api_key = os.getenv("GROQ_API_KEY")
if groq_api_key:
    groq_client = Groq(api_key=groq_api_key)
else:
    groq_client = None

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

class QueryRequest(BaseModel):
    document_id: str
    question: str

def make_cache_key(document_id: str, question: str) -> str:
    """Create a unique cache key for this document + question combo."""
    # hash the question so cache keys stay short and consistent
    question_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()
    return f"query:{document_id}:{question_hash}"

@router.post("/")
async def query_document(
    req: QueryRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve relevant chunks and get LLM answer, with caching and token tracking."""
    if not groq_client:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured on the Vercel deployment server."
        )

    cache_key = make_cache_key(req.document_id, req.question)

    # Step 1 — check cache first
    cached_result = get_cached(cache_key)
    if cached_result:
        cached_result["from_cache"] = True
        user = db.query(User).filter(User.id == current_user["sub"]).first()
        cached_result["total_tokens_consumed"] = user.total_tokens_consumed if user else 0
        cached_result["tokens_used"] = 0
        return cached_result

    # Step 2 — cache miss, do the real work
    all_chunks = search_similar_chunks(req.document_id, req.question, n_results=5)

    if not all_chunks:
        raise HTTPException(status_code=404, detail="No relevant content found")

    # Filter chunks based on similarity threshold (e.g. >= 0.35)
    chunks = [c for c in all_chunks if c.get("similarity_score", 0) >= 0.35]
    if not chunks:
        chunks = all_chunks[:1]  # Keep at least the best matching chunk

    context = "\n\n".join([c["chunk_text"] for c in chunks])

    prompt = f"""Answer the question using only the context below. If the answer isn't in the context, say so.

Context:
{context}

Question: {req.question}

Answer:"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    answer = response.choices[0].message.content

    tokens_used = 0
    if hasattr(response, "usage") and response.usage:
        tokens_used = getattr(response.usage, "total_tokens", 0)

    # Update total tokens in database
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if user:
        user.total_tokens_consumed = getattr(user, "total_tokens_consumed", 0) + tokens_used
        db.commit()
        db.refresh(user)

    sources = [
        {
            "page_number": c["page_number"],
            "chunk_index": c["chunk_index"],
            "chunk_text": c["chunk_text"],
            "similarity_score": c["similarity_score"]
        }
        for c in chunks
    ]

    result = {
        "question": req.question,
        "answer": answer,
        "document_id": req.document_id,
        "sources_used": len(chunks),
        "sources": sources,
        "from_cache": False,
        "tokens_used": tokens_used,
        "total_tokens_consumed": user.total_tokens_consumed if user else 0
    }

    # Step 3 — store in cache for next time
    set_cached(cache_key, result)

    return result