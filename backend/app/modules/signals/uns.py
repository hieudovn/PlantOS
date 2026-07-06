"""UNS Topic derivation — deterministic from PlantOS data model."""


def build_uns_topic(plant_id: str, area_id: str, asset_id: str, signal_category: str, signal_name: str) -> str:
    """Derive UNS topic from PlantOS identifiers.

    Format: plantos/{plant_lower}/{area_lower}/{asset_lower}/{category}/{signal_name}

    All segments are lowercased. Hyphens and underscores preserved.
    This function is deterministic — same input always produces same topic.
    Topics are never manually authored or stored; they are computed at read time.
    """
    return (
        f"plantos/"
        f"{plant_id.lower()}/"
        f"{area_id.lower()}/"
        f"{asset_id.lower()}/"
        f"{signal_category.lower()}/"
        f"{signal_name.lower()}"
    )
