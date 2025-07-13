from sqlalchemy.orm import Session
from .diagnostics import ping_host
from .models import DiagnosticsLog
import logging

def perform_basic_network_diagnostics(db: Session, trigger: str = "scheduler"):
    result = ping_host()
    log = DiagnosticsLog(
        source=result["source"],
        destination=result["destination"],
        success=result["success"],
        output=result["output"],
        trigger=trigger
    )
    db.add(log)
    db.commit()
    logging.info(f"[Automation Engine][{trigger}] Logged diagnostic #{log.id}")
    return result
