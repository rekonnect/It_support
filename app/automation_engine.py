import subprocess # Used to run external commands like 'ping'
import platform   # Used to detect the operating system (though simplified for Linux container)
from sqlalchemy.orm import Session # For database session management
import logging # For logging information
from datetime import datetime # Needed for datetime.utcnow()
from .models import DiagnosticsLog # Import your DiagnosticsLog model
from netmiko import ConnectHandler # NEW: Import ConnectHandler for SSH connections

# This is the ping_host function that executes the system ping command.
def ping_host(ip_address: str) -> dict:
    """
    Pings a given IP address and returns the success status and output.
    This version is simplified for a Linux-based container environment.
    """
    print(f"--- Automation Engine: Pinging {ip_address} ---")

    # Use '-c 1' for Linux to send only one ping packet
    # The 'command' list defines the parts of the shell command
    command = ['ping', '-c', '1', ip_address]

    try:
        # Run the ping command
        # capture_output=True: captures stdout and stderr
        # text=True: decodes stdout/stderr as text
        # timeout=5: sets a timeout for the command to prevent indefinite hangs
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)

        # Check the return code: 0 usually means success
        if result.returncode == 0:
            return {"ip_address": ip_address, "success": True, "output": result.stdout}
        else:
            # If ping failed, return failure status and error/output
            return {"ip_address": ip_address, "success": False, "output": result.stderr or result.stdout}
    except Exception as e:
        # Catch any exceptions during the process (e.g., command not found, timeout)
        return {"ip_address": ip_address, "success": False, "output": f"An error occurred: {str(e)}"}

# This function performs a basic network diagnostic (ping) and logs the result.
# It now takes source_ip and destination_ip as arguments.
def perform_basic_network_diagnostics(db: Session, source_ip: str, destination_ip: str, trigger: str = "scheduler"):
    """
    Performs a ping diagnostic from a source IP to a destination IP
    and logs the result in the database.

    Args:
        db (Session): The SQLAlchemy database session.
        source_ip (str): The IP address from which the ping is conceptually initiated.
        destination_ip (str): The IP address to ping.
        trigger (str): Describes what triggered this diagnostic (e.g., "scheduler", "manual").

    Returns:
        dict: The result of the ping operation.
    """
    # Call the ping_host function defined within this same file
    result = ping_host(destination_ip)

    # Create a new DiagnosticsLog entry based on the ping result
    log = DiagnosticsLog(
        source_ip=source_ip, # Use the provided source_ip
        destination_ip=result["ip_address"], # Use the IP address from the ping result (which is our destination)
        status="success" if result["success"] else "failure", # Map success boolean to "success" or "failure" string
        output=result["output"], # Store the full ping output
        created_at=datetime.utcnow() # Set the current UTC time for the log entry
    )
    db.add(log) # Add the log entry to the database session
    db.commit() # Commit the transaction to save it to the database
    db.refresh(log) # Refresh the log object to get its ID

    logging.info(f"[Automation Engine][{trigger}] Logged diagnostic #{log.id} for {destination_ip}")
    return result # Return the raw ping result

# NEW: Function to connect to a Cisco IOS device and run a command via SSH
def run_cisco_command(host: str, user: str, password: str, command: str) -> dict:
    """
    Connects to a Cisco IOS device via SSH and runs a command.

    Args:
        host (str): The hostname or IP address of the Cisco device.
        user (str): The SSH username for the device.
        password (str): The SSH password for the device.
        command (str): The command to execute on the device.

    Returns:
        dict: A dictionary containing the host, command, success status, and output.
    """
    print(f"--- Automation Engine: Running '{command}' on {host} ---")
    
    # Define device parameters for Netmiko
    cisco_device = {
        'device_type': 'cisco_ios', # Specify the device type
        'host': host,
        'username': user,
        'password': password,
        'global_delay_factor': 2, # Add a delay factor for slower devices/connections
    }
    
    try:
        # Establish SSH connection and execute command
        with ConnectHandler(**cisco_device) as net_connect:
            output = net_connect.send_command(command) # Send the command and capture output
            return {
                "host": host,
                "command": command,
                "success": True,
                "output": output
            }
    except Exception as e:
        # Catch any exceptions during connection or command execution
        return {
            "host": host,
            "command": command,
            "success": False,
            "output": f"An unexpected error occurred: {str(e)}"
        }

