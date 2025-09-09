"""
app/automation_engine.py
Core automation engine for interacting with network devices via SSH.
"""
import asyncio
import asyncssh
import threading
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

SSH_LOOP: Optional[asyncio.AbstractEventLoop] = None
SSH_LOOP_THREAD: Optional[threading.Thread] = None
SESSION_POOL: Dict[tuple, Dict[str, Any]] = {}
DEFAULT_CMD_TIMEOUT = 20
SESSION_IDLE_TIMEOUT = 60 * 60

def _ssh_loop_runner():
    global SSH_LOOP
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    SSH_LOOP = loop
    loop.create_task(_session_cleanup_task())
    loop.run_forever()

def _ensure_ssh_loop_started(timeout: float = 5.0):
    global SSH_LOOP_THREAD
    if SSH_LOOP is not None: return
    t = threading.Thread(target=_ssh_loop_runner, name="ssh-loop-thread", daemon=True)
    SSH_LOOP_THREAD = t
    t.start()
    start_time = time.time()
    while SSH_LOOP is None:
        if time.time() - start_time > timeout:
            raise RuntimeError("Failed to start SSH event loop thread.")
        time.sleep(0.01)

def _submit_to_ssh_loop(coro):
    _ensure_ssh_loop_started()
    return asyncio.run_coroutine_threadsafe(coro, SSH_LOOP)

async def _create_connection(host: str, username: str, password: str, port: int = 22, **kwargs) -> asyncssh.SSHClientConnection:
    return await asyncssh.connect(host, port=port, username=username, password=password, **kwargs)

async def _ensure_session(host: str, username: str, password: str, port: int = 22) -> asyncssh.SSHClientConnection:
    key = (host, username)
    entry = SESSION_POOL.get(key)
    if entry and (conn := entry.get("conn")):
        try:
            await asyncio.wait_for(conn.run("echo ping", check=True), timeout=3)
            entry["last_used"] = time.time()
            return conn
        except Exception:
            if conn: conn.close()
            SESSION_POOL.pop(key, None)

    conn = await _create_connection(host=host, username=username, password=password, port=port, known_hosts=None)
    SESSION_POOL[key] = {"conn": conn, "lock": asyncio.Lock(), "last_used": time.time()}
    return conn

async def _run_command_on_session(device_type: str, host: str, command: str, username: str, password: str, adapter: Optional[Any], timeout: int) -> Dict[str, Any]:
    try:
        conn = await _ensure_session(host, username, password)
        entry = SESSION_POOL.get((host, username))
        if not entry: raise Exception("Session not found after creation")

        async with entry["lock"]:
            final_command = command

            # If an adapter is provided and the device is 'frr', use the adapter's shell
            if adapter and device_type == 'frr':
                shell = adapter.get_shell()
                # Handle multi-line commands for vtysh
                if "\n" in command:
                    final_command = f"{shell} << 'EOF'\n{command}\nEOF"
                else:
                    final_command = f'{shell} -c "{command}"'
            # If no adapter is provided, the command is run in the base system shell

            proc = await asyncio.wait_for(conn.run(final_command, check=True), timeout=timeout)
            return {"success": True, "output": proc.stdout.strip() if proc.stdout else "", "host": host, "command": command}
    except Exception as e:
        return {"success": False, "output": str(e), "host": host, "command": command}

async def run_device_command_async(device_type: str, host: str, command: str, username: str, password: str, adapter: Optional[Any] = None, timeout: int = DEFAULT_CMD_TIMEOUT) -> Dict[str, Any]:
    coro = _run_command_on_session(device_type, host, command, username, password, adapter, timeout)
    fut = _submit_to_ssh_loop(coro)
    return await asyncio.wrap_future(fut)

async def test_command_async(device_type: str, host: str, command: str, username: str, password: str, adapter: Optional[Any] = None, timeout: int = 5) -> bool:
    result = await run_device_command_async(device_type, host, command, username, password, adapter, timeout)
    return result.get("success", False)

async def _session_cleanup_task():
    while True:
        await asyncio.sleep(SESSION_IDLE_TIMEOUT)
        now = time.time()
        to_close = [key for key, entry in SESSION_POOL.items() if now - entry.get("last_used", 0) > SESSION_IDLE_TIMEOUT]
        for key in to_close:
            if entry := SESSION_POOL.pop(key, None):
                if conn := entry.get("conn"):
                    conn.close()

_ensure_ssh_loop_started()
