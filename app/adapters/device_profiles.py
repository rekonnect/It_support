"""
device_profiles.py

This module contains the agent's "textbook" knowledge about different
device vendors and operating systems. It provides a baseline set of
commands and logic for the agent to try when it encounters a new device type.
"""

DEVICE_PROFILES = {
    # --- FRR (Free Range Routing) ---
    "frr": {
        "name": "FRR (Free Range Routing)",
        "fingerprint_commands": [
            "which vtysh",
            "/usr/bin/vtysh -c 'show version' | grep FRR",
        ],
        "exec_mode_commands": {
            "show_running_config": "/usr/bin/vtysh -c 'show running-config'",
            "show_interfaces": "/usr/bin/vtysh -c 'show interface'",
            "show_ip_route": "/usr/bin/vtysh -c 'show ip route'",
        },
        "config_mode_commands": {
            "enter_config": "configure terminal",
            "exit_config": "end",
            "set_hostname": "hostname {hostname}",
            "interface_config": "interface {interface}",
            "no_shutdown": "no shutdown",
        },
        "save_commands": [
            "write file",
            "write memory"
        ],
        "post_action_commands": {
            "set_hostname": [
                {"command": "service frr restart", "type": "system"},
                {"command": "/etc/init.d/frr restart", "type": "system"}
            ]
        },
        "validation_patterns": {
            "hostname": r"hostname\s+(.+)",
            "interface_status": r"^Interface (\S+) is .*, line protocol is (\w+)",
        }
    },

    # --- Other profiles ... ---
    "cisco_ios": {
        "name": "Cisco IOS",
        "fingerprint_commands": ["show version | include Cisco"],
        "exec_mode_commands": { "show_running_config": "show running-config" },
        "config_mode_commands": { "set_hostname": "hostname {hostname}" },
        "save_commands": ["write memory", "copy running-config startup-config"],
    },
}

def get_profile(device_type: str) -> dict:
    """Returns the full profile for a given device type."""
    return DEVICE_PROFILES.get(device_type, {})
