# Security Hardening — Bước 2: Edge Agent + MQTT Credentials

## Context

Step 1 is done. The Center backend now requires real credentials from `.env`. The old `{EDGE_API_KEY}` is no longer valid. This task updates the Edge Agent to use the new `EDGE_API_KEY` and new MQTT credentials.

## ⚠️ SAFETY

- **DO NOT deploy to VPS yet.** Only modify local files.
- **DO NOT break the existing VF Compressor OPC UA collection.**
- The Edge Agent must continue to work with BOTH old and new config formats (for smooth transition).

## Required Reading

```text
edge/agent/config.yaml              ← Current config with old API key
edge/agent/main.py                  ← How config is loaded and passed
edge/agent/sync.py                  ← StoreAndForward (HTTP sync with API key)
edge/agent/health.py                ← HealthReporter (heartbeat with API key)
edge/agent/metadata.py              ← MetadataManager (MISSING auth — BUG!)
edge/agent/publisher.py             ← MQTT publisher (no auth currently)
deployment/.env                     ← New credentials (read EDGE_API_KEY, MQTT_PASSWORD)
```

---

## Implementation Checklist

### Step 1: Update `edge/agent/config.yaml`

Replace the hardcoded key with a placeholder:

```yaml
# BEFORE:
api_key: {EDGE_API_KEY}

# AFTER:
api_key: ${EDGE_API_KEY}  # Set via environment variable
```

Also add MQTT credentials:

```yaml
# BEFORE:
mqtt:
  host: localhost
  port: 1883
  topic_prefix: avenue/demo-plant

# AFTER:
mqtt:
  host: localhost
  port: 1883
  topic_prefix: avenue/demo-plant
  username: ${MQTT_USER}      # edge-agent
  password: ${MQTT_PASSWORD}  # from .env
```

### Step 2: Update Edge Agent Main to Read Env Vars

In `edge/agent/main.py`, add env var substitution to the config loading:

```python
import os
import re

def _resolve_env(config: dict) -> dict:
    """Replace ${VAR} placeholders with environment variable values."""
    resolved = {}
    for key, value in config.items():
        if isinstance(value, dict):
            resolved[key] = _resolve_env(value)
        elif isinstance(value, str):
            # Replace ${VAR} patterns
            def replace_env(match):
                var = match.group(1)
                return os.environ.get(var, "")
            resolved[key] = re.sub(r'\$\{(\w+)\}', replace_env, value)
        else:
            resolved[key] = value
    return resolved

# In Agent.__init__:
raw_config = yaml.safe_load(f)
self.cfg = _resolve_env(raw_config)
```

### Step 3: Fix Metadata Sync Bug (Add Auth Header)

In `edge/agent/metadata.py`, add the API key header that was missing:

```python
class MetadataManager:
    def __init__(self, center_url: str, api_key: str = ""):  # ← ADD api_key param
        self.center_url = center_url.rstrip("/")
        self.api_key = api_key  # ← STORE IT

    async def sync(self):
        url = f"{self.center_url}/api/v1/edge/sync/manifest"
        headers = {"Content-Type": "application/json"}
        if self.api_key:  # ← ADD AUTH HEADER
            headers["X-API-Key"] = self.api_key
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)  # ← USE headers
            # ... rest unchanged
```

In `edge/agent/main.py`, pass the api_key when creating MetadataManager:

```python
# BEFORE:
self.metadata = MetadataManager(self.cfg.get("center_url", "http://localhost:8000"))

# AFTER:
self.metadata = MetadataManager(
    self.cfg.get("center_url", "http://localhost:8000"),
    api_key=self.cfg.get("api_key", "")
)
```

### Step 4: Add MQTT Auth to Publisher

In `edge/agent/publisher.py`, add username/password from config:

```python
class MqttPublisher:
    def __init__(self, config: dict):
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 1883)
        self.topic_prefix = config.get("topic_prefix", "avenue/demo-plant")
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        # ...
    
    def connect(self):
        self.client = mqtt.Client(client_id=self.edge_node_id)
        if self.username:  # ← ADD AUTH
            self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.host, self.port, keepalive=30)
```

### Step 5: Verify Changes Don't Break Dev Mode

For local dev without `.env`, the `_resolve_env` function should return empty strings for missing vars (not crash). The agent should log a warning but continue:

```python
if not self.cfg.get("api_key"):
    logger.warning("EDGE_API_KEY not set — API calls will fail unless DEBUG mode is on")
```

---

## Deliverables

1. Updated `edge/agent/config.yaml` — `${EDGE_API_KEY}`, MQTT user/pass placeholders
2. Updated `edge/agent/main.py` — `_resolve_env()` function, pass api_key to MetadataManager
3. Updated `edge/agent/metadata.py` — Added `api_key` param, auth header in HTTP call
4. Updated `edge/agent/publisher.py` — MQTT username/password auth

## Files NOT to touch

- ❌ `frontend/*` (Step 3)
- ❌ `tools/*.py` (Step 4)
- ❌ `deployment/.env` (already done in Step 1)
- ❌ VPS running system

## Acceptance Criteria

- [ ] Edge Agent config uses `${EDGE_API_KEY}` instead of hardcoded key
- [ ] `_resolve_env()` substitutes env vars correctly
- [ ] MetadataManager sends `X-API-Key` header (bug fix)
- [ ] MQTT publisher sends username/password when configured
- [ ] Missing env vars → log warning, don't crash
- [ ] Old config format still works (backward compatible)
- [ ] No hardcoded `{EDGE_API_KEY}` in any of the 4 modified files
