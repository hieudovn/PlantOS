#!/usr/bin/env python3
"""Run SQL migration directly."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=30)
    out = r.stdout.strip()
    err = r.stderr.strip()
    if err and "Warning" not in err:
        print(f"  STDERR: {err[:200]}")
    return out

# Step 1: Create table
sql = "CREATE TABLE IF NOT EXISTS edge_user_assignments (id VARCHAR(36) PRIMARY KEY, edge_node_id VARCHAR(128) NOT NULL, user_id VARCHAR(36) NOT NULL, created_at TIMESTAMP DEFAULT NOW())"
r = ssh(f"docker exec -i plantos-postgres psql -U plantos -d plantos -c \"{sql}\"")
print(f"Table: {r[:100]}")

# Step 2: Create indexes
r = ssh("docker exec -i plantos-postgres psql -U plantos -d plantos -c \"CREATE INDEX IF NOT EXISTS ix_eua_edge_node ON edge_user_assignments(edge_node_id)\"")
print(f"Index 1: {r[:100]}")
r = ssh("docker exec -i plantos-postgres psql -U plantos -d plantos -c \"CREATE INDEX IF NOT EXISTS ix_eua_user ON edge_user_assignments(user_id)\"")
print(f"Index 2: {r[:100]}")

# Step 3: Seed data
r = ssh("docker exec -i plantos-postgres psql -U plantos -d plantos -c \"INSERT INTO edge_user_assignments (id, edge_node_id, user_id) SELECT gen_random_uuid()::text, 'EDGEV2-PC-01', id::text FROM users ON CONFLICT DO NOTHING\"")
print(f"Seed: {r[:100]}")

# Step 4: Verify
r = ssh("docker exec -i plantos-postgres psql -U plantos -d plantos -c \"SELECT u.username, eua.edge_node_id FROM edge_user_assignments eua JOIN users u ON u.id::text = eua.user_id LIMIT 5\"")
print(f"Verify:\n{r}")

# Step 5: Write alembic version (since chain is broken)
r = ssh("docker exec -i plantos-postgres psql -U plantos -d plantos -c \"INSERT INTO alembic_version (version_num) VALUES ('010') ON CONFLICT (version_num) DO NOTHING\"")
print(f"Alembic version: {r[:100]}")

print("\nMigration complete")
