"""
experience_db.py

This module acts as the agent's long-term memory. It stores and retrieves
learned experiences about specific devices, such as which commands have
succeeded or failed for a particular action.

For this prototype, it's a simple in-memory dictionary. In a production
system, this would be backed by a persistent database (e.g., SQLite, Redis).
"""
from typing import Dict, Any, Optional, List

# In-memory database
_experience_db: Dict[str, Dict[str, Any]] = {}


def get_experience(device_ip: str) -> Optional[Dict[str, Any]]:
    """Retrieves the full experience record for a given device IP."""
    return _experience_db.get(device_ip)

def get_known_good_command(device_ip: str, action: str) -> Optional[str]:
    """
    Retrieves a known-working command for a specific action on a device.
    Returns None if no experience has been logged for this action.
    """
    experience = get_experience(device_ip)
    if experience:
        return experience.get("working_commands", {}).get(action)
    return None

def log_success(device_ip: str, device_type: str, action: str, command: str):
    """Logs a successful command for a given device and action."""
    if device_ip not in _experience_db:
        _experience_db[device_ip] = {
            "device_type": device_type,
            "working_commands": {},
            "failed_commands": {}
        }
    _experience_db[device_ip]["working_commands"][action] = command
    print(f"EXPERIENCE GAINED: Logged successful command for '{action}' on {device_ip}.")

def log_failure(device_ip: str, device_type: str, action: str, command: str):
    """Logs a failed command attempt."""
    if device_ip not in _experience_db:
        _experience_db[device_ip] = {
            "device_type": device_type,
            "working_commands": {},
            "failed_commands": {}
        }

    if action not in _experience_db[device_ip]["failed_commands"]:
        _experience_db[device_ip]["failed_commands"][action] = []

    if command not in _experience_db[device_ip]["failed_commands"][action]:
        _experience_db[device_ip]["failed_commands"][action].append(command)
    print(f"EXPERIENCE GAINED: Logged failed command for '{action}' on {device_ip}.")
