"""NodeId -> PlantOS signal_id mapping with unit conversion."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SignalMapping:
    node_id: str
    signal_id: str
    scale: float = 1.0
    offset: float = 0.0


class OpcUaMapper:
    """Maps OPC UA NodeIds to PlantOS signal_ids with optional conversion."""

    def __init__(self, tags: list[dict]):
        self.mappings: list[SignalMapping] = []
        for tag in tags:
            self.mappings.append(SignalMapping(
                node_id=tag["node_id"],
                signal_id=tag["signal_id"],
                scale=tag.get("scale", 1.0),
                offset=tag.get("offset", 0.0),
            ))

    @property
    def node_ids(self) -> list[str]:
        return [m.node_id for m in self.mappings]

    def map_values(self, raw: dict[str, float | bool | int | None]) -> list[dict]:
        results = []
        for mapping in self.mappings:
            value = raw.get(mapping.node_id)
            if value is None:
                continue
            try:
                converted = float(value) * mapping.scale + mapping.offset
            except (TypeError, ValueError):
                converted = value
            results.append({
                "signal_id": mapping.signal_id,
                "value": round(converted, 4) if isinstance(converted, float) else converted,
            })
        return results
