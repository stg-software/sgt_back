# ============================================================================
# app/api/workflows.py
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.workflow import WorkflowTemplate, WorkflowState
from app.schemas.workflow import WorkflowTemplateCreate, WorkflowTemplateOut
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/workflows", tags=["Workflows"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=WorkflowTemplateOut)
def create_workflow(
    workflow: WorkflowTemplateCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ Protegido
):
    db_workflow = WorkflowTemplate(name=workflow.name)
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)

    # Insertar estados
    for state in workflow.states:
        db_state = WorkflowState(
            name=state.name, 
            order=state.order, 
            workflow_id=db_workflow.id
        )
        db.add(db_state)
    db.commit()
    db.refresh(db_workflow)

    return db_workflow

@router.get("/", response_model=list[WorkflowTemplateOut])
def list_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ Protegido
):
    return db.query(WorkflowTemplate).all()