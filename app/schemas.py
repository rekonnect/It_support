from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# -------------------------------
# Tenant Schemas
# -------------------------------

class TenantCreate(BaseModel):
    name: str

class Tenant(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------
# User Schemas
# -------------------------------

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    tenant_id: int

class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    tenant_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------
# DiagnosticsLog Schemas
# -------------------------------

class DiagnosticsLogCreate(BaseModel):
    source_ip: str
    destination_ip: str
    status: str
    output: Optional[str] = None

class DiagnosticsLog(BaseModel):
    id: int
    source_ip: str
    destination_ip: str
    status: str
    output: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
