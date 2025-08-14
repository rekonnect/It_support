from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, database

# Dependency to get DB session, this should eventually be moved to a central place
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix="/tasks",
    tags=["Scheduled Tasks"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.ScheduledTask, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.ScheduledTaskCreate, db: Session = Depends(get_db)):
    """
    Create a new scheduled task.
    """
    # Verify tenant exists
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == task.tenant_id).first()
    if not db_tenant:
        raise HTTPException(status_code=400, detail=f"Tenant with id {task.tenant_id} not found")

    db_task = models.ScheduledTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/", response_model=List[schemas.ScheduledTask])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all scheduled tasks.
    """
    tasks = db.query(models.ScheduledTask).offset(skip).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=schemas.ScheduledTask)
def read_task(task_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific scheduled task by its ID.
    """
    db_task = db.query(models.ScheduledTask).filter(models.ScheduledTask.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.put("/{task_id}", response_model=schemas.ScheduledTask)
def update_task(task_id: int, task: schemas.ScheduledTaskUpdate, db: Session = Depends(get_db)):
    """
    Update a scheduled task.
    """
    db_task = db.query(models.ScheduledTask).filter(models.ScheduledTask.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Delete a scheduled task.
    """
    db_task = db.query(models.ScheduledTask).filter(models.ScheduledTask.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return
