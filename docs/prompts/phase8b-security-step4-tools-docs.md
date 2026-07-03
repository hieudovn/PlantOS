# Security Hardening — Bước 4: Tools + Docs Cleanup

## Context

Steps 1-3 done. Center, Edge, Frontend all use new credentials. The final code step: remove the old `{EDGE_API_KEY}` from ALL tools, scripts, and documentation files.

## ⚠️ IMPORTANT

This is a **mechanical find-and-replace** task. Do NOT change any logic. Only replace the hardcoded key string.

---

## Step 1: Update All Python Tools

Every `tools/*.py` file that hardcodes the API key must now read it from an environment variable.

### Pattern to find:
```python
API_KEY = "{EDGE_API_KEY}"
HEADERS = {"X-API-Key": "{EDGE_API_KEY}"}
```

### Pattern to replace with:
```python
import os
API_KEY = os.environ.get("EDGE_API_KEY", "")
HEADERS = {"X-API-Key": os.environ.get("EDGE_API_KEY", "")}
```

### Files affected (verify each exists and update):

| File | Lines to update |
|------|----------------|
| `tools/apply_wtp_on_vps.py` | Replace hardcoded key with `os.environ.get("EDGE_API_KEY")` |
| `tools/check_api_endpoints.py` | Same |
| `tools/diag_wtp_ingestion.py` | Same |
| `tools/e2e_test_wtp.py` | Same |
| `tools/validate_wtp_on_vps.py` | Same |
| `tools/verify_ingestion.py` | Same |
| `tools/verify_ingestion2.py` | Same |

### Add a check at the top of EACH file:

```python
import os
import sys

EDGE_API_KEY = os.environ.get("EDGE_API_KEY", "")
if not EDGE_API_KEY:
    print("ERROR: EDGE_API_KEY environment variable not set.", file=sys.stderr)
    print("Set it to the Edge API key from deployment/.env", file=sys.stderr)
    sys.exit(1)
```

## Step 2: Update Prompt Documents

Replace `{EDGE_API_KEY}` with `{API_KEY}` placeholder in ALL prompt Markdown files.

### Files to search and replace:

```bash
grep -rl "{EDGE_API_KEY}" docs/prompts/
```

For each file found, replace:
- `{EDGE_API_KEY}` → `{EDGE_API_KEY}` (for Edge/internal contexts)
- `X-API-Key: {EDGE_API_KEY}` → `X-API-Key: {EDGE_API_KEY}` (in curl examples)

### Specific replacements:

| Context | Replace with |
|---------|-------------|
| Edge Agent config examples | `{EDGE_API_KEY}` |
| curl command examples | `{EDGE_API_KEY}` |
| Diagnostic script examples | `{EDGE_API_KEY}` |
| Environment setup docs | `{EDGE_API_KEY}` |

## Step 3: Update Reference Model Docs

Check and update:
- `docs/reference-models/wtp-demo-01-*.md` (all 4 files)
- `docs/prompts/phase8a-vf-*.md` (VF project prompts)

## Step 4: Final Verification

Run this to confirm ZERO instances of the old key remain in code:

```bash
cd d:\Project\Github\PlantOS
# Exclude .git directory and node_modules
grep -r "{EDGE_API_KEY}" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.yaml" --include="*.yml" --include="*.json" --include="*.md" backend/ edge/ frontend/src/ tools/ docs/ deployment/ 2>nul
```

Expected: **0 matches** (or only in `.env.example` where it should say `change-me`).

## Deliverables

1. Updated 7 `tools/*.py` files — read key from env var
2. Updated `docs/prompts/*.md` files — `{EDGE_API_KEY}` placeholder
3. Updated `docs/reference-models/*.md` files
4. Verification report: 0 instances of old key in code

## Acceptance Criteria

- [ ] `grep -r "{EDGE_API_KEY}"` returns 0 matches in code files
- [ ] All tools print clear error if `EDGE_API_KEY` env var is missing
- [ ] Prompt docs use `{EDGE_API_KEY}` placeholder, not real key
- [ ] No logic changes — only key references updated
