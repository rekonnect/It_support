"""
command_discovery.py

This module contains the agent's learning algorithm. It allows the agent
to autonomously discover which commands work for a specific device and action
by testing a list of candidate commands from the device profile.
"""
import asyncio
import logging
from typing import List, Tuple, Optional, Dict, Any

from app.automation_engine import test_command_async
from app.adapters.device_profiles import get_profile
from ai_engine.experience_db import log_success, log_failure

logger = logging.getLogger(__name__)


async def discover_working_command(
    host: str,
    device_type: str,
    action: str,
    username: str,
    password: str,
    params: Dict[str, Any] = None
) -> Optional[str]:
    """
    Tests candidate commands for a given action and returns the first one that succeeds.
    This version intelligently tries commands in both user and config mode.

    Returns:
        A string containing the successful command or script, otherwise None.
    """
    logger.info(
        f"--- [LEARN] Starting command discovery for action '{action}' on {host} ({device_type}) ---"
    )

    profile = get_profile(device_type)
    if not profile:
        logger.error(f"No device profile found for '{device_type}'.")
        return None

    # Find the command template from the profile
    command_template = None
    action_to_find = "save" if action == "save_config" else action

    if f"{action_to_find}_commands" in profile:
        # For now, we only support discovery of the first command in a list
        command_template = profile[f"{action_to_find}_commands"][0]
    elif action in profile.get("config_mode_commands", {}):
        command_template = profile["config_mode_commands"][action]
    elif action in profile.get("exec_mode_commands", {}):
        command_template = profile["exec_mode_commands"][action]

    if not command_template:
        logger.warning(f"No command template found for action '{action}' in '{device_type}' profile.")
        return None

    # Format the command with parameters
    formatted_command = command_template.format(**params) if params else command_template

    # --- Attempt 1: Try the command directly (User Mode) ---
    logger.info(f"[*] Testing '{action}' in user mode: {formatted_command}")
    if await test_command_async(device_type, host, formatted_command, username, password):
        logger.info(f"✅ Success in user mode! Learned command for '{action}': {formatted_command}")
        log_success(host, device_type, action, formatted_command)
        return formatted_command

    logger.warning(f"[-] User mode failed for '{action}'.")

    # --- Attempt 2: Try the command in a config mode script ---
    enter_cmd = profile.get("config_mode_commands", {}).get("enter_config")
    exit_cmd = profile.get("config_mode_commands", {}).get("exit_config")

    if enter_cmd and exit_cmd:
        config_script = f"{enter_cmd}\n{formatted_command}\n{exit_cmd}"
        logger.info(f"[*] Testing '{action}' in config mode with script...")

        if await test_command_async(device_type, host, config_script, username, password):
            logger.info(f"✅ Success in config mode! Learned script for '{action}'.")
            # We log the *script* as the working command now
            log_success(host, device_type, action, config_script)
            return config_script
        logger.warning(f"[-] Config mode failed for '{action}'.")

    # If both attempts fail, log the original formatted command as a failure
    log_failure(host, device_type, action, formatted_command)
    logger.error(f"❌ Discovery failed. No working method found for action '{action}'.")
    return None
