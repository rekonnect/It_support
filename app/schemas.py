from pydantic import BaseModel, Field
from datetime import datetime

class TenantBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The unique name of the tenant"
    )

class TenantCreate(TenantBase):
    """Schema for tenant creation request"""
    pass

class Tenant(TenantBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
