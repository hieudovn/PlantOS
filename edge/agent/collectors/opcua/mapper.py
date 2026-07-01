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

    def __init__(self, tags: list[dict] = None):
        self.mappings: list[SignalMapping] = []
        if tags:
            for tag in tags:
                self.mappings.append(SignalMapping(
                    node_id=tag["node_id"],
                    signal_id=tag["signal_id"],
                    scale=tag.get("scale", 1.0),
                    offset=tag.get("offset", 0.0),
                ))

    @classmethod
    def from_manifest(cls, manifest: dict):
        """Build mapper from Center-synced manifest or YAML contract manifest.

        Reads signal_id, source_ref (OPC UA NodeId), and optional scale.
        Falls back to empty mapper if manifest has no signals with OPC UA source.
        """
        mapper = cls(tags=[])
        # Build lookup for scale from YAML manifest signals (which have scale field)
        scale_lookup: dict[str, float] = {}
        for s in manifest.get("signals", []):
            if "scale" in s:
                scale_lookup[s["signal_id"]] = float(s["scale"])
            elif "opcua_node_id" in s and "signal_id" in s:
                # YAML manifest format: signal_id + opcua_node_id + scale
                node_id = s["opcua_node_id"]
                sig_id = s["signal_id"]
                scale = float(s.get("scale", 1.0))
                mapper.mappings.append(SignalMapping(
                    node_id=node_id, signal_id=sig_id, scale=scale,
                ))

        # If we already built from YAML manifest (opcua_node_id present), return
        if mapper.mappings:
            logger.info(f"Built {len(mapper.mappings)} OPC UA mappings from YAML manifest")
            return mapper

        # Otherwise build from Center sync manifest (source.source_type + source.source_ref)
        for s in manifest.get("signals", []):
            source = s.get("source") or {}
            if source.get("source_type") == "opcua" and source.get("source_ref"):
                sig_id = s["signal_id"]
                scale = scale_lookup.get(sig_id, 1.0)
                mapper.mappings.append(SignalMapping(
                    node_id=source["source_ref"],
                    signal_id=sig_id,
                    scale=scale,
                ))
        if mapper.mappings:
            logger.info(f"Built {len(mapper.mappings)} OPC UA mappings from Center manifest")
        return mapper

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
