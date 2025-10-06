# app/schemas/task.py
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, field_validator

class StateInfo(BaseModel):
    """Información básica del estado de la tarea"""
    id: int
    name: str
    order: int
    
    class Config:
        from_attributes = True

class UserInfo(BaseModel):
    """Información básica del usuario"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    
    class Config:
        from_attributes = True

# ✅ NUEVO: Schema para un registro del historial
class TaskRecordEntry(BaseModel):
    """Entrada individual del historial de la tarea"""
    fecha: str  # Formato: "DD/MM/AAAA"
    hora: str   # Formato: "HH:MM:SS"
    user: str   # Username del usuario que documentó
    status: str # Estado de la tarea en ese momento
    doc: str    # Comentario/documentación

class TaskCreate(BaseModel):
    """Schema para crear una tarea"""
    title: str
    description: Optional[str] = None
    board_id: int
    state_id: int
    assigned_to_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    custom_fields: Optional[Dict[str, Any]] = {}
    # ✅ NUEVO: No se incluye record en creación, se genera automáticamente
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        if v and info.data.get('start_date') and v < info.data['start_date']:
            raise ValueError('end_date debe ser posterior o igual a start_date')
        return v

class TaskUpdate(BaseModel):
    """Schema para actualizar una tarea"""
    title: Optional[str] = None
    description: Optional[str] = None
    state_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    custom_fields: Optional[Dict[str, Any]] = None
    # ✅ NUEVO: No se permite actualizar record directamente desde aquí
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        if v and info.data.get('start_date') and v < info.data['start_date']:
            raise ValueError('end_date debe ser posterior o igual a start_date')
        return v

# ✅ NUEVO: Schema para agregar una entrada al historial
class TaskRecordAdd(BaseModel):
    """Schema para agregar un comentario al historial"""
    doc: str  # Comentario/documentación del usuario

class TaskOut(BaseModel):
    """Schema de salida de una tarea"""
    id: int
    title: str
    description: Optional[str] = None
    board_id: int
    state_id: int
    state: Optional[StateInfo] = None
    
    # Información de asignación y creación
    assigned_to_id: Optional[int] = None
    assigned_to: Optional[UserInfo] = None
    created_by_id: int
    created_by: Optional[UserInfo] = None
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    custom_fields: Optional[Dict[str, Any]] = {}
    
    # ✅ NUEVO: Historial de cambios
    record: Optional[List[Dict[str, Any]]] = []
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True