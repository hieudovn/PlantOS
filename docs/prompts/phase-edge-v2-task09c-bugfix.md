# E2V2-7c: Fix processing_loop tag_configs bug

> **Blocker for:** E2V2-7b Phase 2 (side-by-side comparison)
> **Root cause:** `processing_loop` reads tags from ConfigManager instead of connector
> **Impact:** Buffer always 0 rows — data fetched but never written

## Context

HTTP Poll connector successfully fetches data from simulator (200 OK every 10s), but `processing_loop` gets empty `tag_configs` → skips → buffer stays at 0.

### Bug location

`edge-v2/agent/main.py` line 165:

```python
tag_configs = self.config.get(f"connectors.{conn_id}.tags", [])
```

**Why it fails:** `ConfigManager.get()` with dot-path `connectors.mirror_wtp_signals.tags` returns `[]` because the config's `_data` dict may not have the structure the method expects, or the YAML structure differs from what the dot-path assumes.

### Fix (1 line)

```python
# BEFORE (broken):
tag_configs = self.config.get(f"connectors.{conn_id}.tags", [])

# AFTER (fixed):
tag_configs = connector.tags
```

**Why this works:** Every connector already parses and stores its tags during `__init__`:
```python
# base.py: __init__
self.tags = [TagConfig(**t) if isinstance(t, dict) else t for t in tags_raw]
```

The connector's `self.tags` is always populated from the config it was initialized with. Reading from `connector.tags` is the canonical source.

### Verification

After fix, restart Edge v2 and check buffer:

```bash
# On VPS:
docker restart plantos-edge-v2
sleep 30
curl -s http://localhost:8011/api/status | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'rows={d[\"buffer\"][\"row_count\"]}')
"
# Expected: rows > 0
```

Then re-run comparison:

```bash
python tools/vps_execute_e2v2_7b.py --skip-phases 1 3
# Phase 2 should now find shared signals
```

## Files to Modify

```
edge-v2/agent/main.py  — line 165, 1-line fix
```

## Red Flags

- Do NOT change connector internals (they work correctly)
- Do NOT change ConfigManager.get() (it works for other paths)
- Test on VPS: buffer must show row_count > 0 after 30s
