from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app import models, schemas
from app.core.config import settings

# Добавьте эту строку
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(
        models.User.email == email,
        models.User.is_active == True
    ).first()
    if not user or not verify_password(password, user.password_hash):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_session(db: Session, user_id: int, token: str):
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    db_session = models.Session(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(db_session)
    db.commit()
    return db_session

def get_current_user(db: Session, token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    session = db.query(models.Session).filter(
        models.Session.token == token,
        models.Session.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        return None
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user