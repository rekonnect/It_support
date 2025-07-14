from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, database, schemas

router = APIRouter(prefix="/tenants", tags=["tenants"])

# Dependency for DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Tenant, status_code=201)
def create_tenant(tenant_in: schemas.TenantCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Tenant).filter(models.Tenant.name == tenant_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant name already registered")
    new_tenant = models.Tenant(name=tenant_in.name)
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    return new_tenant
