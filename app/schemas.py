from pydantic import BaseModel, EmailStr
import datetime

# -------------------------
# Tenant Schemas
# -------------------------

class TenantBase(BaseModel):
    name: str

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: int
    created_at: datetime.datetime

    model_config = {
        "from_attributes": True
    }

# -------------------------
# User Schemas
# -------------------------

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str  # only used when creating a user

class User(UserBase):
    id: int
    tenant_id: int

    model_config = {
        "from_attributes": True
    }
