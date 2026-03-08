from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import timedelta
from app import schemas, models, auth  # этот импорт должен быть
from app.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Проверка совпадения паролей
    if user_data.password != user_data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Проверка существования пользователя
    existing_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Создание пользователя
    hashed_password = auth.get_password_hash(user_data.password)
    db_user = models.User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        patronymic=user_data.patronymic
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Назначение роли "Пользователь" по умолчанию
    user_role = db.query(models.Role).filter(models.Role.name == "Пользователь").first()
    if user_role:
        db_user_role = models.UserRole(user_id=db_user.id, role_id=user_role.id)
        db.add(db_user_role)
        db.commit()
    
    return db_user

@router.post("/login", response_model=schemas.Token)
def login(login_data: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Создание токена
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Сохранение сессии
    auth.create_session(db, user.id, access_token)
    
    # Установка cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(
    response: Response,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Удаление сессии
    db.query(models.Session).filter(models.Session.token == token).delete()
    db.commit()
    
    # Очистка cookie
    response.delete_cookie("access_token")
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    user = auth.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user