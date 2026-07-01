#!/usr/bin/env python
"""One-shot: create tables, seed VF-DEMO, verify."""
import sys, json, urllib.request

# Step 0: Import ALL models so Base.metadata knows about them
import app.modules.assets.models      # noqa: F401
import app.modules.signals.models     # noqa: F401
import app.modules.edge_nodes.models  # noqa: F401
import app.modules.alarms.models      # noqa: F401
import app.modules.events.models      # noqa: F401

# Step 1: Create tables
from app.db import Base, get_engine
engine = get_engine()
Base.metadata.create_all(engine)

# Verify
from sqlalchemy import inspect
insp = inspect(engine)
tables = insp.get_table_names()
print(f"Tables in DB: {tables}")

# Step 2: Seed
url = "http://localhost:8000/api/v1/seed/vf-demo"
req = urllib.request.Request(url, method="POST")
with urllib.request.urlopen(req) as resp:
    result = json.load(resp)
    print(f"Seed: {result}")

# Step 3: Verify plants
with urllib.request.urlopen("http://localhost:8000/api/v1/plants") as resp:
    plants = json.load(resp)
    print(f"Plants: {len(plants)}")
    for p in plants:
        print(f"  - {p['plant_id']}: {p['name']}")
