# app/models/board.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(16), nullable=True)

    # referencia a la plantilla elegida
    template_id = Column(Integer, ForeignKey("workflow_templates.id"), nullable=False)

    # dueño/creador del tablero
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    template = relationship("WorkflowTemplate", back_populates="boards")
    owner = relationship("User", back_populates="boards", foreign_keys=[owner_id])
    tasks = relationship("Task", back_populates="board", cascade="all, delete-orphan")
    
    # ✅ NUEVO: Asignaciones de usuarios al tablero
    assignments = relationship("BoardAssignment", back_populates="board", cascade="all, delete-orphan")