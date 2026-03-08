from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from app import models, auth
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    if not token:
        return None
    
    user = auth.get_current_user(db, token)
    if not user:
        return None
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    return current_user

class PermissionChecker:
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    async def __call__(
        self,
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        if current_user.is_superuser:
            return current_user
        
        # Получаем все разрешения пользователя через роли
        role_permissions = db.query(models.RolePermission).join(
            models.UserRole,
            models.UserRole.role_id == models.RolePermission.role_id
        ).filter(
            models.UserRole.user_id == current_user.id
        ).all()
        
        # Получаем индивидуальные разрешения
        user_permissions = db.query(models.UserPermission).filter(
            models.UserPermission.user_id == current_user.id
        ).all()
        
        # Проверяем наличие требуемых разрешений
        for required in self.required_permissions:
            resource_code, permission_code = required.split(':')
            
            # Проверяем индивидуальные запреты
            for up in user_permissions:
                resource = db.query(models.Resource).filter(
                    models.Resource.id == up.resource_id
                ).first()
                permission = db.query(models.Permission).filter(
                    models.Permission.id == up.permission_id
                ).first()
                
                if (resource and resource.code == resource_code and 
                    permission and permission.code == permission_code and 
                    not up.is_granted):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied"
                    )
            
            # Проверяем разрешения
            has_permission = False
            
            # Через роли
            for rp in role_permissions:
                resource = db.query(models.Resource).filter(
                    models.Resource.id == rp.resource_id
                ).first()
                permission = db.query(models.Permission).filter(
                    models.Permission.id == rp.permission_id
                ).first()
                
                if (resource and resource.code == resource_code and 
                    permission and permission.code == permission_code):
                    has_permission = True
                    break
            
            # Через индивидуальные разрешения
            if not has_permission:
                for up in user_permissions:
                    resource = db.query(models.Resource).filter(
                        models.Resource.id == up.resource_id
                    ).first()
                    permission = db.query(models.Permission).filter(
                        models.Permission.id == up.permission_id
                    ).first()
                    
                    if (resource and resource.code == resource_code and 
                        permission and permission.code == permission_code and 
                        up.is_granted):
                        has_permission = True
                        break
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {required}"
                )
        
        return current_user