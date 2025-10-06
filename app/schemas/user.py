# ============================================================================
# app/schemas/user.py
# ============================================================================
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role_id: int

class UserCreate(UserBase):
    password: str  # se hasheará en la API

class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role_id: Optional[int] = None

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True