# ============================================================================
# app/api/roles.py
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.roles import Role
from app.schemas.roles import RoleCreate, RoleUpdate, RoleOut
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/roles", tags=["Roles"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=RoleOut)
def create_role(
    role: RoleCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ Protegido
):
    db_role = Role(name=role.name, description=role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.get("/", response_model=list[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ Protegido
):
    return db.query(Role).all()

@router.get("/{role_id}", response_model=RoleOut)
def get_role(
    role_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ Protegido
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int, 
    role_update: RoleUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ Protegido
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    for key, value in role_update.model_dump(exclude_unset=True).items():
        setattr(role, key, value)

    db.commit()
    db.refresh(role)
    return role

@router.delete("/{role_id}")
def delete_role(
    role_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ Protegido
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    db.delete(role)
    db.commit()
    return {"message": "Role deleted"}