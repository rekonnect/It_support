import os
import time
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database

# Create DB tables automatically (for development only)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Jules AI Agent PoC")

# --- Dependency to get DB session ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Health check route ---
@app.get("/")
async def root():
    return {"message": "Jules AI Agent PoC is running!"}

# --- Create Tenant ---
@app.post("/tenants/", response_model=schemas.Tenant)
def create_tenant(tenant: schemas.TenantCreate, db: Session = Depends(get_db)):
    db_tenant = db.query(models.Tenant).filter(models.Tenant.name == tenant.name).first()
    if db_tenant:
        raise HTTPException(status_code=400, detail="Tenant name already registered")
    new_tenant = models.Tenant(name=tenant.name)
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    return new_tenant

# --- Read all Tenants ---
@app.get("/tenants/", response_model=List[schemas.Tenant])
def read_tenants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Tenant).offset(skip).limit(limit).all()
