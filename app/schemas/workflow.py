# app/schemas/workflow.py
from pydantic import BaseModel
from typing import List

class WorkflowStateBase(BaseModel):
    name: str
    order: int


class WorkflowStateCreate(WorkflowStateBase):
    pass


class WorkflowStateOut(WorkflowStateBase):
    id: int

    class Config:
        from_attributes = True  # para mapear desde SQLAlchemy


# Versión liviana para usar en /boards/{id}/states
class WorkflowStateOutLight(BaseModel):
    id: int
    name: str
    order: int

    class Config:
        from_attributes = True


# ======================
# Workflow Templates
# ======================

class WorkflowTemplateBase(BaseModel):
    name: str


class WorkflowTemplateCreate(WorkflowTemplateBase):
    states: List[WorkflowStateCreate]


class WorkflowTemplateOut(WorkflowTemplateBase):
    id: int
    states: List[WorkflowStateOut]

    class Config:
        from_attributes = True
