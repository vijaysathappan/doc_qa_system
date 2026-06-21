from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import engine, Base, add_columns_if_missing
from app.routes import auth, documents, upload, query, otp_auth
from app.middleware import global_exception_handler, not_found_handler

limiter = Limiter(key_func=get_remote_address)
Base.metadata.create_all(bind=engine)
add_columns_if_missing()

app = FastAPI(
    title="Doc QA System",
    version="0.1.0",
    swagger_ui_parameters={"persistAuthorization": True}
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",   # Vite dev server (React)
        "http://localhost:4173",   # Vite preview
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",  # Vite dev server (React)
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(404, not_found_handler)
app.include_router(auth.router)
app.include_router(otp_auth.router)  # passwordless OTP auth
app.include_router(documents.router)
app.include_router(upload.router)
app.include_router(query.router)
@app.get('/health')
async def get_status():
    return {"status": "ok", "service": "doc-qa-system"}
# from fastapi import FastAPI, HTTPException,Request, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.exceptions import HTTPException
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
# from pydantic import BaseModel
# from typing import Optional
# import uuid
# from sqlalchemy.orm import Session
# from app.database import engine, get_db,Base
# from app.models.document import Document as DocumentModel
# from app.routes import auth, documents
# from app.middleware import global_exception_handler,not_found_handler
# #Rate Limiter-identifies users by IP Address
# limiter=Limiter(key_func=get_remote_address)
# Base.metadata.create_all(bind=engine)
# app= FastAPI(title="Doc AQ System",version="0.1.0",
# swagger_ui_parameters={"persistAuthorization": True})
# # Attach limiter to app
# app.state.limiter=limiter
# # --- MIDDLEWARE ---
# # 1. CORS — allow frontend on port 3000 to talk to this API
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["Https://localhost:3000",
#                     "http://localhost:8000",
#         "http://127.0.0.1:8000",
#         "http://127.0.0.1:3000",],
#     allow_credentials=True,
#     allow_methods=["*"],# allow GET, POST, PUT, DELETE etc
#     allow_headers=["*"],# allow all headers including Authorization
# )
# # 2. Rate limit exceeded handler
# app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
# # 3. Global error handler — catches all unhandled exceptions
# app.add_exception_handler(Exception,global_exception_handler)
# # 4. 404 handler
# app.add_exception_handler(404,not_found_handler)
# app.include_router(auth.router)
# app.include_router(documents.router)
# #db={}
# class Document(BaseModel):
#     title:str
#     content:str
#     tags: list[str] | None=None
# class DocumentResponse(BaseModel):
#     id: str
#     title:str
#     tags:list[str]=[]
#     created_at: str
#     class Config:
#         from_attributes=True #lets Pydantic read SQLAlchemy objects
# class QueryRequest(BaseModel):
#     question: str
#     document_id:str
# @app.get('/')
# async def root():
#     return {"message":"Hello World"}
# @app.get('/health')
# async def get_status():
#     return{
#         "status":"ok",
#         "service":"doc-qa-system"
#     }
# @app.post('/documents')
# async def create(doc: Document) -> DocumentResponse:
#     doc_id = str(uuid.uuid4())
#     db[doc_id] = {
#         "id": doc_id,
#         "title": doc.title,
#         "content": doc.content,
#         "tags": doc.tags or [],
#         "created_at": "2026-06-01"
#     }
#     return DocumentResponse(**db[doc_id])
# @app.get("/break")
# async def break_it():
#     raise Exception("intentional crash")
# @app.post('/documents',response_model=DocumentResponse)
# async def create(doc : Document,db:Session = Depends(get_db)):
#     db_doc=DocumentModel(
#         id=str(uuid.uuid4()),
#         title=doc.title,
#         content=doc.content,
#         tags=doc.tags,
#         created_at= "2026-06-01"
#     )
#     db.add(db_doc)
#     db.commit()
#     db.refresh(db_doc) # fetch the saved object from DB
#     return db_doc
# @app.get("/documents/{doc_id}")
# async def get_doc(doc_id : str,db:Session =Depends(get_db)):
#     doc=db.query(DocumentModel).filter(DocumentModel.id==doc_id).first()
#     if not doc:
#         raise HTTPException(
#             status_code=404,
#             detail="Document Not Found"
#         )
#     return doc
# @app.get("/documents")
# async def get_all(db:Session = Depends(get_db)):
#     doc=db.query(DocumentModel).all()
#     return doc
# @app.post("/query")
# async def query(req : QueryRequest,db:Session=Depends(get_db)):
#     doc=db.query(DocumentModel).filter(DocumentModel.id==req.document_id).first()
#     if not doc:
#         raise HTTPException(status_code=404, detail="Doc not found")
#     return{
#         "question":req.question,
#         "answer":"LLM not connected yet",
#         "Document_id":req.document_id
#     }