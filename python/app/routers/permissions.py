from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models
from app.database import get_db
from app.dependencies import PermissionChecker, get_current_active_user

router = APIRouter(prefix="/admin", tags=["admin"])

# Только для администраторов
admin_required = PermissionChecker(["users:manage"])

@router.get("/permissions", response_model=List[schemas.PermissionResponse])
def get_permissions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_required)
):
    permissions = db.query(models.Permission).all()
    return permissions

@router.post("/permissions", response_model=schemas.PermissionResponse)
def create_permission(
    permission: schemas.PermissionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_required)
):
    db_permission = models.Permission(**permission.dict())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

@router.get("/roles", response_model=List[schemas.RoleResponse])
def get_roles(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_required)
):
    roles = db.query(models.Role).all()
    return roles

@router.post("/roles", response_model=schemas.RoleResponse)
def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_required)
):
    db_role = models.Role(name=role.name, description=role.description)
    db.add(db_role)
    db.flush()
    
    # Добавление разрешений
    for permission_id in role.permission_ids:
        db_role_permission = models.RolePermission(
            role_id=db_role.id,
            permission_id=permission_id
        )
        db.add(db_role_permission)
    
    db.commit()
    db.refresh(db_role)
    return db_role

@router.post("/access-rules")
def create_access_rule(
    rule: schemas.AccessRuleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_required)
):
    if rule.user_id:
        # Индивидуальное правило
        db_rule = models.UserPermission(
            user_id=rule.user_id,
            permission_id=rule.permission_id,
            resource_id=rule.resource_id,
            is_granted=rule.is_granted
        )
    elif rule.role_id:
        # Правило для роли
        db_rule = models.RolePermission(
            role_id=rule.role_id,
            permission_id=rule.permission_id,
            resource_id=rule.resource_id
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user_id or role_id must be provided"
        )
    
    db.add(db_rule)
    db.commit()
    
    return {"message": "Access rule created successfully"}