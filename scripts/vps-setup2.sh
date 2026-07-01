#!/bin/bash
set -e
echo "=== Check models loaded ==="
docker exec plantos-backend python -c "
from app.db import Base
print('Models:', [t for t in Base.metadata.tables.keys()])
"
echo "=== Create tables ==="
docker exec plantos-backend python -c "
from app.db import Base, get_engine
Base.metadata.create_all(get_engine())
print('Done')
"
echo "=== Verify tables exist ==="
docker exec plantos-backend python -c "
from app.db import get_engine
from sqlalchemy import inspect
insp = inspect(get_engine())
tables = insp.get_table_names()
print('Tables in DB:', tables)
"
echo "=== Seed ==="
curl -s -X POST http://localhost:8000/api/v1/seed/vf-demo
echo
echo "=== Plants ==="
curl -s http://localhost:8000/api/v1/plants
