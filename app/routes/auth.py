from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app.models.user import User
from app.auth_utils import hash_password,verify_password,create_access_token
router = APIRouter(prefix="/auth", tags=["auth"])
limiter=Limiter(key_func=get_remote_address)
class RegisterRequest(BaseModel):
    email:str
    password : str
# class LoginRequest(BaseModel):
#     email: str
#     password: str
@router.post("/register")
@limiter.limit("3/minute")
async def register(request:Request,req: RegisterRequest, db:Session = Depends(get_db)):
    existing=db.query(User).filter(User.email==req.email).first()
    if(existing):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user=User(
        email=req.email,
        hashed_password=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    return {"message":"User Registered Successfully"}
@router.post("/login")
@limiter.limit("3/minute")
async def login(request:Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    token = create_access_token({"sub": user.id, "email": user.email})
    return {"access_token": token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordBearer
from app.auth_utils import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "total_tokens_consumed": getattr(user, "total_tokens_consumed", 0)
    }
# @router.post("/login")
# async def login(req: LoginRequest,db:Session=Depends(get_db)):
#     user=db.query(User).filter(User.email==req.email).first()
#     if not user or not verify_password(req.password , user.hashed_password):
#         raise HTTPException(status_code=401, detail="Invalid Credentials")
#     token= create_access_token({"sub":user.id , "email":user.email})
#     return {"access_token":token , "token_type":"bearer"}