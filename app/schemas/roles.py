# app/schemas/roles.py
from pydantic import BaseModel

class RoleBase(BaseModel):
    name: str
    description: str | None = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class RoleOut(RoleBase):
    id: int

    class Config:
        from_attributes = True
