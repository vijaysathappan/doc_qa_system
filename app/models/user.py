from sqlalchemy import Column, String, Integer
from app.database import Base 
import uuid
class User(Base):
    __tablename__="users"
    id=Column(String, primary_key=True, default=lambda : str(uuid.uuid4()))
    email=Column(String , unique=True,nullable=False)
    hashed_password=Column(String, nullable=False)
    total_tokens_consumed=Column(Integer, default=0, nullable=False)