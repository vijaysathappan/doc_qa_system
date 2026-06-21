from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
import logging
from app.models.document import Document as DocumentModel
from app.auth_utils import decode_token
from app.cache import get_cached, set_cached,deleted_cached
from fastapi.security import OAuth2PasswordBearer
import uuid

router = APIRouter(prefix="/documents", tags=["documents"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login",auto_error=True)
logger=logging.getLogger(__name__)
class DocumentCreate(BaseModel):
    title: str
    content: str
    tags: list[str] | None = None

class DocumentResponse(BaseModel):
    id: str
    title: str
    tags: list = []
    created_at: str
    class Config:
        from_attributes = True

# Reusable dependency — get current logged in user from token
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.post("/", response_model=DocumentResponse)
async def create(
    doc: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # protected
):
    db_doc = DocumentModel(
        id=str(uuid.uuid4()),
        title=doc.title,
        content=doc.content,
        tags=doc.tags or [],
        created_at="2026-06-03",
        owner_id=current_user["sub"]
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    cache_key=f"document:{db_doc.id}"
    set_cached(cache_key,{
        "id":db_doc.id,
        "title":db_doc.title,
        "tags":db_doc.tags,
        "created_at":db_doc.created_at
    })
    return db_doc

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_doc(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # protected
):
    cache_key=f"document:{doc_id}"
    cached=get_cached(cache_key)
    if cached:
        #print(f"CACHE HIT for {doc_id}")
        logger.info(f"CACHE HIT for {doc_id}")
        return cached
    #print(f"Cache Miss fofr {doc_id}")
    logger.info(f"Cache Miss for {doc_id}")
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    set_cached(cache_key,{
        "id":doc.id,
        "title":doc.title,
        "tags":doc.tags,
        "created_at":doc.created_at
    })
    return doc