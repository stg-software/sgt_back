# app/models/workflow.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    boards = relationship("Board", back_populates="template", cascade="all, delete-orphan")
    states = relationship(
        "WorkflowState", back_populates="workflow", cascade="all, delete-orphan"
    )
    

class WorkflowState(Base):
    __tablename__ = "workflow_states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    workflow_id = Column(Integer, ForeignKey("workflow_templates.id"))

    workflow = relationship("WorkflowTemplate", back_populates="states")
    tasks = relationship("Task", back_populates="state")
