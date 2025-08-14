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
# Scheduled Task Schemas
# -------------------------------

class ScheduledTaskBase(BaseModel):
    name: str
    task_type: str
    target: str
    cron_schedule: str
    is_enabled: bool = True
    details: Optional[dict] = None
    tenant_id: int


class ScheduledTaskCreate(ScheduledTaskBase):
    pass


class ScheduledTaskUpdate(BaseModel):
    name: Optional[str] = None
    task_type: Optional[str] = None
    target: Optional[str] = None
    cron_schedule: Optional[str] = None
    is_enabled: Optional[bool] = None
    details: Optional[dict] = None


class ScheduledTask(ScheduledTaskBase):
    id: int
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
