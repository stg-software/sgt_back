# app/models/board_assignment.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class BoardAssignment(Base):
    """Tabla para asignar usuarios a tableros"""
    __tablename__ = "board_assignments"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relaciones
    board = relationship("Board", back_populates="assignments")
    user = relationship("User", back_populates="board_assignments")