import hashlib
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, database
# REMOVED: from .diagnostics import ping_host # This line caused the ImportError
# UPDATED: Import both ping_host and run_cisco_command from automation_engine.py
from .automation_engine import ping_host as network_ping_host, run_cisco_command
from .scheduler import start_scheduler
from .diagnostics import connectivity # CORRECT: Import the connectivity module from the diagnostics package

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

# This endpoint was likely intended to use the old diagnostics.py ping_host.
# If you still need this specific endpoint, you might need to re-evaluate its purpose
# or adjust it to use network_ping_host if it's meant to be a simple ping.
# For consistency, I will update it to use network_ping_host.
@app.post("/diagnose/connectivity/")
def diagnose_connectivity(data: dict):
    source_ip = data.get("source_ip")
    destination_ip = data.get("destination_ip")
    if not source_ip or not destination_ip:
        raise HTTPException(status_code=400, detail="source_ip and destination_ip are required")

    # This now uses the ping_host from automation_engine (aliased as network_ping_host)
    result = network_ping_host(destination_ip)
    return {"source_ip": source_ip, "destination_ip": destination_ip, "ping_result": result}


@app.post("/diagnose/ping")
def diagnose_ping(ip_address: str = Body(..., embed=True)):
    return network_ping_host(ip_address) # Calls the ping_host function from automation_engine.py

# Endpoint for running Cisco commands via SSH
@app.post("/diagnose/cisco_command")
def diagnose_cisco_command(host: str = Body(..., embed=True), command: str = Body(..., embed=True)):
    # For PoC, we are hardcoding credentials.
    # In a real app, these would come from the secure credential vault!
    user = "cisco"
    password = "cisco"
    
    # Call the run_cisco_command function from automation_engine.py
    result = run_cisco_command(host, user, password, command)
    return result

# Endpoint for full connectivity diagnostic scenario
@app.post("/diagnose/full_connectivity")
def full_connectivity_check(source_ip: str = Body(..., embed=True), destination_ip: str = Body(..., embed=True)):
    # Call the diagnose_connectivity function from the new connectivity module
    report = connectivity.diagnose_connectivity(source_ip, destination_ip)
    return report

# Start the scheduler on app startup
start_scheduler()
