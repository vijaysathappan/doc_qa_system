from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document as DocumentMode, DocumentChunk
from app.auth_utils import decode_token
from app.services.document_processor import load_and_chunk_pdf
from fastapi.security import OAuth2PasswordBearer
from app.services.embedding_service import embed_and_store_chunks
import uuid
import os
import shutil
router = APIRouter(prefix="/upload", tags=["upload"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token:str= Depends(oauth2_scheme)):
    payload=decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload
UPLOAD_DIR="uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
@router.post("/pdf")
async def upload_pdf(
    file: UploadFile =File(...),
    db:Session=Depends(get_db),
    current_user: dict=Depends(get_current_user)
):
    """Uplaod a PDF, chunk it , and soter chunks in DB."""
    #Step 1- Validate the file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF file ALlowed")
   # Step 2- Save PDF to dist temporarily
    file_path=f"{UPLOAD_DIR}/{uuid.uuid4()}_{file.filename}"
    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        #Step 3- Create document record in DB
        doc_id=str(uuid.uuid4())
        db_doc=DocumentMode(
            id=doc_id,
            title=file.filename,
            content="",
            tags=[],
            created_at="2026-06-03",
            owner_id=current_user["sub"]
        )
        db.add(db_doc)
        db.commit()
        #Step 4- Process PDF and create chunks
        chunks=load_and_chunk_pdf(file_path)
        #Step 5 - Save chunk to DB
        embed_and_store_chunks(doc_id, chunks)
        for chunk in chunks:
            db_chunk= DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                chunk_text=chunk["chunk_text"],
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page_number"]
            )
            db.add(db_chunk)
            db.commit()
        return {
            "message":"PDF processed successfully",
            "document_id":doc_id,
            "chunks_created":len(chunks),
            "filename":file.filename
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Step 6- Delete temp file after processing
        if os.path.exists(file_path):
            os.remove(file_path)