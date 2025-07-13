import subprocess

def ping_host(source_ip: str = "127.0.0.1", destination_ip: str = "8.8.8.8") -> dict:
    try:
        completed_process = subprocess.run(
            ["ping", "-c", "4", destination_ip],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "source": source_ip,
            "destination": destination_ip,
            "success": completed_process.returncode == 0,
            "output": completed_process.stdout if completed_process.returncode == 0 else completed_process.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "source": source_ip,
            "destination": destination_ip,
            "success": False,
            "output": "Ping command timed out."
        }
    except Exception as e:
        return {
            "source": source_ip,
            "destination": destination_ip,
            "success": False,
            "output": str(e)
        }
