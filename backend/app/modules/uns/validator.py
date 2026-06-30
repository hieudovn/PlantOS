"""UNS path validation and generation.

UNS (Unified Namespace) paths follow the convention:
    enterprise/plant/area/asset/signal_name

This module enforces path format rules and blocks raw tag patterns
that would bypass the UNS hierarchy.
"""

import re

# Allowed: lowercase alphanumeric, underscore, hyphen, forward slash, dot
UNS_PATTERN = re.compile(r"^[a-z0-9_-]+(/[a-z0-9_.-]+)*$")

# Patterns that indicate a raw tag bypassing UNS
_BLOCKED_PATTERNS = ["plc:", "opc:", "ns=", "modbus:", "mqtt://"]


def validate_uns_path(path: str) -> bool:
    """Validate a UNS path string.

    Rules:
    - Must match ^[a-z0-9_-]+(/[a-z0-9_.-]+)*$
    - Must not contain raw tag indicators (plc:, opc:, ns=, etc.)

    Returns True if the path is valid.
    """
    if not path or not isinstance(path, str):
        return False
    if not UNS_PATTERN.match(path):
        return False
    lower = path.lower()
    for blocked in _BLOCKED_PATTERNS:
        if blocked in lower:
            return False
    return True


def generate_uns_path(
    enterprise: str,
    plant_id: str,
    area_id: str = "",
    asset_id: str = "",
    signal_name: str = "",
) -> str:
    """Generate a UNS path from asset hierarchy components.

    All components are lowercased. Empty components are skipped.
    """
    parts = [p for p in [enterprise, plant_id, area_id, asset_id, signal_name] if p]
    return "/".join(parts).lower()
