import os, sys
sys.path.insert(0, '/app')
from app.core.security import hash_password
new_hash = hash_password('PlantOS@2026!')
print(f"NEW_HASH={new_hash}")

# Now update DB directly via psycopg2
import psycopg2
conn = psycopg2.connect(
    host=os.environ.get('POSTGRES_HOST', 'postgres'),
    user=os.environ.get('POSTGRES_USER', 'plantos'),
    password=os.environ.get('POSTGRES_PASSWORD', ''),
    dbname=os.environ.get('POSTGRES_DB', 'plantos')
)
cur = conn.cursor()
cur.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (new_hash,))
conn.commit()
cur.execute("SELECT username FROM users WHERE username = 'admin'")
row = cur.fetchone()
print(f"ADMIN_USER={row[0] if row else 'NOT_FOUND'}")
cur.close()
conn.close()
print("PASSWORD_RESET_OK")
