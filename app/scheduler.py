import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from . import models
from .database import SessionLocal
from .automation_engine import perform_basic_network_diagnostics, run_cisco_command

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.INFO)

scheduler = BackgroundScheduler()

def schedule_task(db_task: models.ScheduledTask):
    """Adds a single task to the scheduler based on its type and schedule."""
    job_id = f"task_{db_task.id}"

    job_func = None
    job_args = []

    # Determine the function and arguments to call based on the task type
    if db_task.task_type == "ping":
        job_func = perform_basic_network_diagnostics
        # The scheduled function needs its own DB session
        job_args = [SessionLocal(), "api", db_task.target, f"task_id_{db_task.id}"]

    elif db_task.task_type == "cisco_command":
        if not db_task.details or "command" not in db_task.details:
            logging.error(f"Task {db_task.id} ('cisco_command') is missing 'command' in details JSON. Skipping.")
            return

        # NOTE: Credentials are hardcoded. In a real system, these should be fetched
        # securely from Vault for the specific device/tenant.
        user = "cisco"
        password = "cisco"

        job_func = run_cisco_command
        job_args = [db_task.target, user, password, db_task.details["command"]]
        # NOTE: The result of run_cisco_command is not currently logged to the database.
        # This could be a future enhancement.

    else:
        logging.warning(f"Unknown task type '{db_task.task_type}' for task {db_task.id}. Skipping.")
        return

    # Add the job to the scheduler with a cron trigger
    try:
        scheduler.add_job(
            func=job_func,
            trigger=CronTrigger.from_crontab(db_task.cron_schedule),
            args=job_args,
            id=job_id,
            name=db_task.name,
            replace_existing=True,
        )
        logging.info(f"Successfully scheduled job '{db_task.name}' (ID: {job_id}) with schedule: '{db_task.cron_schedule}'")
    except Exception as e:
        logging.error(f"Error scheduling job {job_id} for task '{db_task.name}': {e}")


def start_scheduler():
    """
    Starts the scheduler and loads all enabled tasks from the database.
    This function is called once on application startup.
    """
    logging.info("Scheduler starting up. Loading tasks from database...")
    db = SessionLocal()
    try:
        # Fetch all enabled tasks from the database
        enabled_tasks = db.query(models.ScheduledTask).filter(models.ScheduledTask.is_enabled == True).all()

        if not enabled_tasks:
            logging.info("No enabled tasks found in the database. Scheduler will run but has no jobs.")
        else:
            logging.info(f"Found {len(enabled_tasks)} enabled tasks to schedule.")
            for task in enabled_tasks:
                schedule_task(task)
    except Exception as e:
        logging.error(f"Failed to load tasks from database: {e}")
    finally:
        db.close()

    # Start the scheduler engine if it's not already running
    if not scheduler.running:
        scheduler.start()
        logging.info("Scheduler started successfully.")
    else:
        logging.info("Scheduler is already running.")
