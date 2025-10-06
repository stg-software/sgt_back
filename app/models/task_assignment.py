# app/models/task_assignment.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class TaskAssignment(Base):
    """Modelo completo para asignaciones de tareas"""
    __tablename__ = 'task_assignments'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relaciones
    task = relationship("Task", back_populates="assignments")
    user = relationship(
        "User", 
        foreign_keys=[user_id],
        back_populates="task_assignments"
    )
    assigned_by = relationship(
        "User",
        foreign_keys=[assigned_by_id]
    )