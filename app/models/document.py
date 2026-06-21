from sqlalchemy import Column, String , JSON,Integer, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import uuid
class Document(Base):
    __tablename__="documents"
    id= Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title=Column(String, nullable=False)
    content=Column(String,nullable=False)
    tags=Column(JSON, default=[])
    created_at=Column(String, default=func.now())
    owner_id = Column(String, nullable=False)
class DocumentChunk(Base):
    __tablename__="document_chunks"
    id= Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id=Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_text=Column(Text, nullable=False) #text for long content
    chunk_index=Column(Integer, nullable=False)#position of chunk in doc
    page_number=Column(Integer, nullable=True)# which page it came from
    created_at=Column(String, default=func.now())