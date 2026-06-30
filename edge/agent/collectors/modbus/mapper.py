"""Tag mapping: Modbus register address -> PlantOS signal_id."""

import struct


class TagMapper:
    def __init__(self, tags: list[dict]):
        self.tags = tags
        # Group by register type for batch reading
        self.holding_tags = [t for t in tags if t.get("type") == "holding"]
        self.coil_tags = [t for t in tags if t.get("type") == "coil"]

    def get_holding_registers(self) -> list[int]:
        return [t["register"] for t in self.holding_tags]

    def get_coil_addresses(self) -> list[int]:
        return [t["register"] for t in self.coil_tags]

    def map_holding_values(self, registers: list[int], start_addr: int) -> list[dict]:
        """Map raw register values to measurements using tag definitions."""
        results = []
        for tag in self.holding_tags:
            offset = tag["register"] - start_addr
            if 0 <= offset < len(registers):
                raw = registers[offset]
                if tag.get("data_type") == "float" and offset + 1 < len(registers):
                    # Combine 2 registers for float32
                    raw_bytes = struct.pack(">HH", registers[offset], registers[offset + 1])
                    value = struct.unpack(">f", raw_bytes)[0]
                else:
                    value = float(raw)
                value = value * tag.get("scale", 1.0) + tag.get("offset", 0.0)
                results.append({
                    "signal_id": tag["signal_id"],
                    "value": round(value, 3),
                })
        return results

    def map_coil_values(self, bits: list[bool], start_addr: int) -> list[dict]:
        results = []
        for tag in self.coil_tags:
            offset = tag["register"] - start_addr
            if 0 <= offset < len(bits):
                results.append({
                    "signal_id": tag["signal_id"],
                    "value": bits[offset],
                })
        return results
