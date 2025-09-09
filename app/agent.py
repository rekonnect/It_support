"""
agent.py
The core autonomous agent loop.
"""
import asyncio
import logging
import importlib
from typing import List, Dict, Any

from app.monitoring.validators import run_all_validations
from app.planner import generate_remediation_plan
from app.automation_engine import run_device_command_async
from app.discovery import discover_default_gateway
from app.fingerprinting import fingerprint_device
from ai_engine.experience_db import get_known_good_command, log_failure
from ai_engine.command_discovery import discover_working_command
from app.adapters.device_profiles import get_profile

logging.basicConfig(level=logging.INFO, format="%(asctime)s - AGENT - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEVICE_HOST = "192.168.122.50"
DEVICE_USERNAME = "root"
DEVICE_PASSWORD = "cisco"
EXPECTATIONS = {
    "hostname": "core-router-01",
    "configs": ["router ospf", "network 192.168.1.0/24 area 0"],
    "routes": ["0.0.0.0/0 via 192.168.122.1"],
    "interfaces_up": ["eth0"],
}

def get_adapter_for_device(device_type: str):
    try:
        adapter_module_name = f"app.adapters.{device_type}_adapter"
        adapter = importlib.import_module(adapter_module_name)
        logger.info(f"Successfully loaded adapter: {adapter_module_name}")
        return adapter
    except ImportError:
        logger.error(f"Could not find or import adapter for device type '{device_type}'.")
        return None

async def execute_plan_with_learning(
    device_type: str, host: str, username: str, password: str,
    intentions: List[Dict[str, Any]], adapter: Any
) -> bool:
    logger.info(f"--- [ACT-LEARN] Executing plan with learning loop on {host} ---")
    overall_success = True

    # The plan is now a list of intentions. We can translate the whole plan at once.
    logger.info("Translating the full intention plan using the device adapter...")
    command_script = adapter.translate_plan_to_commands(intentions)

    if not command_script:
        logger.error("Adapter failed to translate the plan. Stopping.")
        return False

    logger.info(f"Executing full remediation script:\n---\n{command_script}\n---")
    # Remediation commands are always CLI commands, so pass the adapter
    exec_result = await run_device_command_async(
        device_type, host, command_script, username, password, adapter=adapter
    )

    if not exec_result.get("success"):
        logger.error("Remediation script execution failed.")
        overall_success = False
    else:
        logger.info("Successfully executed remediation script.")
        # Post-actions are still handled one by one if needed, for actions that require them.
        for intention in intentions:
            action = intention.get("action")
            profile = get_profile(device_type)
            post_action_commands = profile.get("post_action_commands", {}).get(action, [])

            if post_action_commands:
                logger.info(f"Action '{action}' requires post-action commands. Executing...")
                action_succeeded = False
                for cmd_info in post_action_commands:
                    cmd = cmd_info.get("command")
                    cmd_type = cmd_info.get("type")
                    if not cmd: continue

                    logger.info(f"Trying post-action command: '{cmd}' (type: {cmd_type})")
                    cmd_adapter = adapter if cmd_type == 'cli' else None

                    post_result = await run_device_command_async(
                        device_type, host, cmd, username, password, adapter=cmd_adapter
                    )

                    if post_result.get("success"):
                        logger.info(f"Post-action command '{cmd}' succeeded.")
                        if cmd_type == 'system':
                            await asyncio.sleep(5)
                        action_succeeded = True
                        break

                if not action_succeeded:
                    logger.error(f"All post-action commands for '{action}' failed.")
                    overall_success = False
                    # If any post-action fails, we should stop the whole process.
                    return False

    return overall_success

async def run_agent_loop_once():
    device_type = await fingerprint_device(DEVICE_HOST, DEVICE_USERNAME, DEVICE_PASSWORD)
    if device_type == "unknown": return

    adapter = get_adapter_for_device(device_type)
    if not adapter: return

    gateway_ip = discover_default_gateway()
    if not gateway_ip: return

    logger.info(f"--- [SENSE] Running validation checks on {DEVICE_HOST} ---")
    validation_result = await run_all_validations(adapter, DEVICE_HOST, EXPECTATIONS)
    if not validation_result: return

    logger.info(f"Validation complete. Overall status: {validation_result.get('overall_status')}")

    if validation_result.get("overall_status") == "FAIL":
        logger.info("--- [PLAN] Validation failed. Generating remediation plan. ---")
        intentions_plan = generate_remediation_plan(validation_result, gateway_ip)

        if not intentions_plan:
            logger.warning("No remediation intentions generated.")
            return

        logger.info(f"Generated {len(intentions_plan)} intentions.")

        execution_succeeded = await execute_plan_with_learning(
            device_type, DEVICE_HOST, DEVICE_USERNAME, DEVICE_PASSWORD, intentions_plan, adapter
        )

        if not execution_succeeded:
            logger.error("Remediation plan execution failed.")
            return

        logger.info("--- [STABILIZE] Waiting for 10 seconds... ---")
        await asyncio.sleep(10)

        logger.info("--- [VERIFY] Re-running validation to verify the fix. ---")
        verification_result = await run_all_validations(adapter, DEVICE_HOST, EXPECTATIONS)
        logger.info(f"Verification complete. Final status: {verification_result.get('overall_status')}")

        if verification_result.get('overall_status') == "PASS":
            logger.info("✅ 🎉 Agent successfully remediated the device to a compliant state!")
        else:
            logger.error("❌ Agent failed to remediate the device.")
    else:
        logger.info("✅ Device is compliant. No action needed.")

if __name__ == '__main__':
    logger.info("Starting agent loop...")
    asyncio.run(run_agent_loop_once())
    logger.info("Agent loop finished.")
