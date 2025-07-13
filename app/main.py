import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database
import hashlib

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Jules AI Agent PoC")

# Mount the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------
# DB Session Dependency
# -------------------------

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Routes
# -------------------------

# ✅ Serve HTML on root
@app.get("/", response_class=FileResponse)
async def read_index():
    return "static/index.html"

# --- Tenant Endpoints ---

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

@app.get("/tenants/", response_model=List[schemas.Tenant])
def read_tenants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Tenant).offset(skip).limit(limit).all()

# --- User Endpoints ---

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Very basic password hashing using SHA256 (❗ not secure in production)
    hashed_pw = hashlib.sha256(user.password.encode()).hexdigest()

    new_user = models.User(
        email=user.email,
        hashed_password=hashed_pw,
        is_active=user.is_active,
        tenant_id=1  # Static for now, improve later
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.User).offset(skip).limit(limit).all()
