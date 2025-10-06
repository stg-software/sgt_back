# app/schemas/task_assignment.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserAssignmentBase(BaseModel):
    """Usuario asignado a una tarea (info básica)"""
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    
    class Config:
        from_attributes = True


class TaskAssignmentCreate(BaseModel):
    """Asignar usuarios a una tarea"""
    user_ids: list[int]


class TaskAssignmentRemove(BaseModel):
    """Remover usuarios de una tarea"""
    user_ids: list[int]