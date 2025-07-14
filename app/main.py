import hashlib
from fastapi import FastAPI, Depends, HTTPException, Body # NEW: Import Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, database
from .diagnostics import ping_host # Keep this import for the original diagnostics endpoint
from .automation_engine import ping_host as network_ping_host # Import ping_host from automation_engine.py
from .scheduler import start_scheduler

# Create tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Jules AI Agent PoC")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Serve the index.html file on root
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
    # Check if email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username already exists
    db_username = db.query(models.User).filter(models.User.username == user.username).first()
    if db_username:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Verify tenant exists
    tenant = db.query(models.Tenant).filter(models.Tenant.id == user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    hashed_pw = hashlib.sha256(user.password.encode()).hexdigest()

    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw,
        tenant_id=user.tenant_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.User).offset(skip).limit(limit).all()

# --- Diagnostics Endpoints ---

@app.post("/diagnose/connectivity/")
def diagnose_connectivity(data: dict):
    source_ip = data.get("source_ip")
    destination_ip = data.get("destination_ip")
    if not source_ip or not destination_ip:
        raise HTTPException(status_code=400, detail="source_ip and destination_ip are required")

    # This ping_host comes from .diagnostics
    result = ping_host(destination_ip)
    return {"source_ip": source_ip, "destination_ip": destination_ip, "ping_result": result}

# CORRECTED: Endpoint for ping diagnostic to expect a JSON object
@app.post("/diagnose/ping")
def diagnose_ping(ip_address: str = Body(..., embed=True)): # Expects a JSON body like {"ip_address": "..."}
    return network_ping_host(ip_address) # Calls the ping_host function from automation_engine.py

# Start the scheduler on app startup
start_scheduler()
