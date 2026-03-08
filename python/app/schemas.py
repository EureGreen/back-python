from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    patronymic: Optional[str] = None

class UserCreate(UserBase):
    password: str
    password_confirm: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    patronymic: Optional[str] = None
    email: Optional[EmailStr] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    pass

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Permission schemas
class PermissionBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: int
    
    class Config:
        from_attributes = True

# Resource schemas
class ResourceBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class ResourceCreate(ResourceBase):
    pass

class ResourceResponse(ResourceBase):
    id: int
    
    class Config:
        from_attributes = True

# Role schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_ids: List[int] = []

class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Access rule schemas
class AccessRuleCreate(BaseModel):
    user_id: Optional[int] = None
    role_id: Optional[int] = None
    permission_id: int
    resource_id: int
    is_granted: bool = True

class AccessRuleResponse(BaseModel):
    id: int
    user_id: Optional[int]
    role_id: Optional[int]
    permission_id: int
    resource_id: int
    is_granted: bool
    
    class Config:
        from_attributes = True