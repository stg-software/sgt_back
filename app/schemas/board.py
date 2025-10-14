# app/schemas/board.py
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# Importamos TaskOut desde task
from .task import TaskOut

class BoardCreate(BaseModel):
    name: str
    template_id: int
    description: Optional[str] = None
    color: Optional[str] = None
    assigned_user_ids: Optional[List[int]] = []  # ✅ NUEVO: IDs de usuarios a asignar

class TemplateOut(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class OwnerOut(BaseModel):
    """Schema simplificado del dueño del board"""
    id: int
    username: str
    email: str
    first_name: str 
    last_name: str
    
    class Config:
        from_attributes = True

class BoardAssignmentOut(BaseModel):
    """Schema para asignaciones de usuarios a tableros"""
    id: int
    user_id: int
    board_id: int
    created_at: datetime
    user: Optional[OwnerOut] = None
    
    class Config:
        from_attributes = True

class BoardAssignmentCreate(BaseModel):
    """Schema para crear asignación"""
    user_id: int

class BoardOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    template_id: int
    owner_id: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    # Relaciones
    tasks: List[TaskOut] = []
    template: Optional[TemplateOut] = None
    owner: Optional[OwnerOut] = None
    assignments: List[BoardAssignmentOut] = []

    class Config:
        from_attributes = True