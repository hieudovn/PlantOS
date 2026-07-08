"""OPC UA tag mapper — maps NodeId → signal_id for RawReading generation."""

from datetime import datetime, timezone
from typing import Any

from agent.connectors.base import RawReading, TagConfig


class OpcUaMapper:
    """Maps OPC UA NodeId read results to RawReadings."""

    def __init__(self, tags: list[TagConfig]):
        self.tags = tags
        self.node_id_map: dict[str, TagConfig] = {}
        for t in tags:
            self.node_id_map[t.source_ref] = t

    @property
    def node_ids(self) -> list[str]:
        return [t.source_ref for t in self.tags if t.enabled]

    def map_values(self, raw_results: list[dict[str, Any]]) -> list[RawReading]:
        """Map OPC UA read results to RawReadings."""
        readings = []
        now = datetime.now(timezone.utc)
        for r in raw_results:
            tag = self.node_id_map.get(r["node_id"])
            if not tag:
                continue
            value = r["value"]
            # Apply scale + offset (raw mapping, not processing)
            if tag.scale != 1.0 or tag.offset != 0.0:
                value = value * tag.scale + tag.offset
            readings.append(RawReading(
                source_ref=r["node_id"],
                signal_id=tag.signal_id,
                raw_value=float(value),
                timestamp=now,
                quality_hint=r.get("quality", "GOOD"),
            ))
        return readings
