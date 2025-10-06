# app/models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

    role_id = Column(Integer, ForeignKey("roles.id"))
    
    # Relaciones
    role = relationship("Role", back_populates="users")
    boards = relationship("Board", back_populates="owner", foreign_keys="Board.owner_id")
    
    # ✅ NUEVO: Asignaciones a tableros
    board_assignments = relationship("BoardAssignment", back_populates="user", cascade="all, delete-orphan")