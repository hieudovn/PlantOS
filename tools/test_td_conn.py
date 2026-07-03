import sys
sys.path.insert(0, '/app')
from app.db.tdengine import create_tdengine_connection
conn, cur = create_tdengine_connection()
cur.execute('SELECT COUNT(*) FROM plantos_ts.measurements')
print('COUNT:', cur.fetchone())
conn.close()
