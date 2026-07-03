# Task 8B-01 — Edge Agent WTP OPC UA Integration

## Context

You are the Coder-Executioner for PlantOS Phase 8B — Edge Consistency.

Currently the Edge Agent only collects 26 signals from VF Compressor via OPC UA port 4840. The WTP simulator exposes 92 signals on OPC UA port 4841 (namespace `WTP-Simulator`) but the Edge Agent doesn't read them. WTP data reaches Center via a separate HTTP ingest path, bypassing the Edge entirely. This creates architectural inconsistency.

**Goal:** Add WTP OPC UA collection to Edge Agent, so all 118 signals (26 VF + 92 WTP) flow through a single Edge-Center pipeline.

## Required Reading

```text
edge/agent/config.yaml                    ← Current Edge config (only VF 4840)
edge/agent/main.py                         ← Agent initialization
edge/agent/collectors/opcua/collector.py   ← OPC UA collector
examples/contracts/wtp-demo-01.contract.yaml  ← WTP signal definitions
```

## Key Technical Facts

- WTP OPC UA: `opc.tcp://localhost:4841`, namespace `WTP-Simulator`
- NodeId convention: `ns=2;s={signal_id}` (e.g., `ns=2;s=RWP-101.flow_rate`)
- 92 signals total
- The collector currently supports ONE OPC UA endpoint
- VF endpoint: `opc.tcp://localhost:4840`

## Implementation Checklist

### Step 1: Add WTP OPC UA Section to Config

Add to `edge/agent/config.yaml`:

```yaml
# OPC UA collector — WTP Water Treatment Plant
opcua_wtp:
  enabled: true
  endpoint: opc.tcp://localhost:4841
  timeout: 5.0
  poll_interval_ms: 30000  # 30s poll cycle
  # Auto-generate bindings from contract
  auto_bind:
    enabled: true
    contract_path: /opt/plantos/examples/contracts/wtp-demo-01.contract.yaml
    node_id_template: "ns=2;s={signal_id}"
```

### Step 2: Auto-Generate OPC UA Bindings from Contract

Create a helper function that reads the contract and generates the tag list:

```python
# In a new file: edge/agent/collectors/opcua/bindings.py
def generate_bindings_from_contract(contract_path: str, node_id_template: str) -> list[dict]:
    """Read contract YAML and generate OPC UA bindings for all signals."""
    import yaml
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    
    bindings = []
    for signal in contract.get("signals", []):
        node_id = node_id_template.replace("{signal_id}", signal["signal_id"])
        bindings.append({
            "node_id": node_id,
            "signal_id": signal["signal_id"],
            "scale": signal.get("scale", 1.0),
            "offset": signal.get("offset", 0.0),
        })
    return bindings
```

### Step 3: Modify Collector to Support Multiple Endpoints

In `edge/agent/collectors/opcua/collector.py`, refactor to accept multiple config sections:

```python
class MultiOpcuaCollector:
    def __init__(self, configs: list[dict]):
        """configs: list of endpoint configs, each with endpoint, tags, timeout, poll_interval_ms"""
        self.collectors = []
        for cfg in configs:
            if cfg.get("enabled", True):
                self.collectors.append(OpcuaCollector(cfg))
    
    async def start(self):
        tasks = [c.start() for c in self.collectors]
        await asyncio.gather(*tasks)
    
    async def poll_all(self) -> list[dict]:
        results = []
        for c in self.collectors:
            results.extend(await c.poll())
        return results
```

### Step 4: Update Agent Main

In `edge/agent/main.py`:

```python
# Build collector configs from config.yaml
opcua_configs = []

# VF Compressor (existing)
vf_config = self.cfg.get("opcua", {})
if vf_config.get("enabled", True):
    opcua_configs.append(vf_config)

# WTP (new)
wtp_config = self.cfg.get("opcua_wtp", {})
if wtp_config.get("enabled", False):
    # Auto-generate bindings if configured
    auto_bind = wtp_config.get("auto_bind", {})
    if auto_bind.get("enabled"):
        wtp_config["tags"] = generate_bindings_from_contract(
            auto_bind["contract_path"],
            auto_bind["node_id_template"]
        )
    opcua_configs.append(wtp_config)

self.opcua = MultiOpcuaCollector(opcua_configs)
```

### Step 5: Verify Signal IDs Match PlantOS Registry

The signal_id in the contract (e.g., `RWP-101.flow_rate`) must match what's in the PlantOS signal registry. Since the contract was applied via Task 8A-04, they will match. Run a quick verification:

```bash
# Get WTP signal IDs from API and compare with what the collector would send
curl -s "http://localhost:8000/api/v1/signals?plant_id=WTP-DEMO-01" \
  -H "X-API-Key: plantos-edge-key-2026" | \
  python -c "import sys,json; signals=json.load(sys.stdin); print('\n'.join(s['signal_id'] for s in signals[:5])); print(f'Total: {len(signals)}')"
```

Expected: 92 signals.

### Step 6: Test the Pipeline

After deploying:

```bash
# 1. Check Edge Agent logs for WTP connection
tail -50 /opt/plantos/edge/agent/logs/agent.log | grep -i wtp

# 2. Verify DuckDB has WTP data
python -c "
import duckdb
conn = duckdb.connect('/opt/plantos/edge/agent/edge_data.duckdb')
result = conn.execute('SELECT signal_id, COUNT(*) FROM measurements WHERE signal_id LIKE \"%-101.%\" GROUP BY signal_id LIMIT 5').fetchall()
for r in result:
    print(r)
"

# 3. Verify Center receives WTP data through Edge
# Check historian for a WTP signal with recent timestamp
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=RWP-101.flow_rate&limit=1" \
  -H "X-API-Key: plantos-edge-key-2026"
```

### Step 7: Cleanup — Remove WTP HTTP Ingest (Optional)

Once OPC UA path is confirmed working, the WTP simulator's direct HTTP ingest can be disabled to avoid duplicate data. Coordinate with VF team.

## Deliverables

1. Updated `edge/agent/config.yaml` — added `opcua_wtp` section
2. New file `edge/agent/collectors/opcua/bindings.py` — contract binding generator
3. Updated `edge/agent/collectors/opcua/collector.py` — multi-endpoint support
4. Updated `edge/agent/main.py` — initialize WTP collector

## Acceptance Criteria

- [ ] Edge Agent connects to OPC UA port 4841 successfully
- [ ] Edge Agent collects all 92 WTP signals (verify in logs)
- [ ] WTP data is buffered in DuckDB
- [ ] WTP data syncs to Center via MQTT (or HTTP fallback)
- [ ] Center historian shows WTP data with source: edge-agent
- [ ] Edge Fleet shows 118 total signals (26 VF + 92 WTP)
- [ ] VF Compressor data continues to flow normally (no regression)

## Guardrails

- Do NOT break the existing VF Compressor OPC UA collection
- Do NOT modify the WTP simulator (it's in a different project)
- Keep backward compatibility: if `opcua_wtp` section is missing, behave exactly as before
- Do NOT hardcode the 92 bindings by hand — use auto_bind from contract
