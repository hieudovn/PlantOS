"""Allowed edge commands — definitions and validation for E2V2-4."""

from typing import Literal

ALLOWED_COMMANDS: dict[str, dict] = {
    "sync_now": {
        "description": "Trigger immediate sync flush",
        "requires_target": False,
    },
    "reload_config": {
        "description": "Reload config from YAML",
        "requires_target": False,
    },
    "restart_connector": {
        "description": "Restart a specific connector",
        "requires_target": True,
        "target_description": "connector_id",
    },
    "enable_connector": {
        "description": "Enable a disabled connector",
        "requires_target": True,
        "target_description": "connector_id",
    },
    "disable_connector": {
        "description": "Disable a running connector",
        "requires_target": True,
        "target_description": "connector_id",
    },
}

# restart_agent is explicitly excluded — requires Docker/systemd supervisor (E2V2-5)
ALLOWED_COMMANDS_E2V2_5 = {
    "restart_agent": {
        "description": "Restart the edge agent process (requires supervisor)",
        "requires_target": False,
    },
}


def validate_command(command_type: str, target: str | None = None) -> list[str]:
    """Validate a command. Returns list of error messages. Empty list = valid."""
    errors = []
    if command_type not in ALLOWED_COMMANDS:
        errors.append(
            f"Unknown command type '{command_type}'. "
            f"Allowed: {', '.join(ALLOWED_COMMANDS.keys())}"
        )
        return errors

    cmd_def = ALLOWED_COMMANDS[command_type]
    if cmd_def["requires_target"] and not target:
        errors.append(f"Command '{command_type}' requires a target ({cmd_def.get('target_description', 'target_id')})")
    if not cmd_def["requires_target"] and target:
        errors.append(f"Command '{command_type}' does not accept a target")

    return errors
