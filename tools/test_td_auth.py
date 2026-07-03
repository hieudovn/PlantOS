import sys
sys.path.insert(0, '/app')
from taosws import connect
# Try default taosdata
try:
    conn = connect('taosws://root:taosdata@tdengine:6041')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM plantos_ts.measurements')
    print('taosdata OK:', cur.fetchone())
    conn.close()
except Exception as e:
    print('taosdata FAIL:', e)

# Try the from-env password
try:
    conn = connect('taosws://root:T-so8gSmY1zxhKTA@tdengine:6041')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM plantos_ts.measurements')
    print('T-so8... OK:', cur.fetchone())
    conn.close()
except Exception as e:
    print('T-so8... FAIL:', e)
