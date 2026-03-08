from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import datetime
from app import schemas, models, auth
from app.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.put("/me", response_model=schemas.UserResponse)
def update_user(
    user_update: schemas.UserUpdate,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    current_user = auth.get_current_user(db, token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Обновление данных
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.delete("/me")
def delete_user(
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db),
    response: Response = None
):
    current_user = auth.get_current_user(db, token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Мягкое удаление
    current_user.is_active = False
    current_user.deleted_at = datetime.utcnow()
    
    # Удаление сессий
    db.query(models.Session).filter(models.Session.user_id == current_user.id).delete()
    db.commit()
    
    # Очистка cookie
    response.delete_cookie("access_token")
    
    return {"message": "Account successfully deleted"}

@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    current_user = auth.get_current_user(db, token)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user