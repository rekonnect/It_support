from apscheduler.schedulers.background import BackgroundScheduler
from .database import SessionLocal
from .automation_engine import perform_basic_network_diagnostics

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(
        func=lambda: perform_basic_network_diagnostics(SessionLocal(), trigger="scheduler"),
        trigger="interval",
        hours=1,
        id="hourly_ping",
        replace_existing=True
    )
    scheduler.start()
