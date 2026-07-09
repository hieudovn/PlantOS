import asyncio, sys
sys.path.insert(0, "/app")
try:
    from taosws import connect
    from app.db.tdengine import build_tdengine_dsn
    dsn = build_tdengine_dsn()
    print(f"DSN: {dsn}")
    conn = connect(dsn)
    print("taosws connect OK")
    c = conn.cursor()
    c.execute("SELECT 1")
    print(f"Query OK: {c.fetchall()}")
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")
