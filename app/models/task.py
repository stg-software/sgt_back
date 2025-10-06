# app/models/task.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    record = Column(JSON, nullable=True, default=[])

    # a qué tablero pertenece
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False)
    board = relationship("Board", back_populates="tasks")

    # en qué estado está (estado de la plantilla del board)
    state_id = Column(Integer, ForeignKey("workflow_states.id"), nullable=False)
    state = relationship("WorkflowState", back_populates="tasks")

    # Usuario asignado a la tarea
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

    # Usuario que creó la tarea
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])

    # opcionales, útiles para Gantt/Calendario
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Campos personalizados en formato JSON
    custom_fields = Column(JSON, nullable=True, default={})

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)