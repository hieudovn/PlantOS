"""Auto-generate OPC UA bindings from PlantOS contract YAML."""

import logging

logger = logging.getLogger(__name__)


def generate_bindings_from_contract(contract_path: str, node_id_template: str) -> list[dict]:
    """Read contract YAML and generate OPC UA bindings for all signals.

    Args:
        contract_path: Path to contract YAML file (e.g., /opt/plantos/.../wtp-demo-01.contract.yaml)
        node_id_template: Template with {signal_id} placeholder (e.g., "ns=2;s={signal_id}")

    Returns:
        List of tag dicts with node_id, signal_id, scale, offset
    """
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML not installed. Run: pip install pyyaml")
        return []

    try:
        with open(contract_path) as f:
            contract = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Contract file not found: {contract_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading contract {contract_path}: {e}")
        return []

    signals = contract.get("signals", [])
    if not signals:
        logger.warning(f"No signals found in contract: {contract_path}")
        return []

    bindings = []
    for signal in signals:
        node_id = node_id_template.replace("{signal_id}", signal["signal_id"])
        bindings.append({
            "node_id": node_id,
            "signal_id": signal["signal_id"],
            "scale": signal.get("scale", 1.0),
            "offset": signal.get("offset", 0.0),
        })

    logger.info(f"Generated {len(bindings)} OPC UA bindings from {contract_path}")
    return bindings
