import duckdb
c = duckdb.connect('/opt/plantos/edge/agent/edge_data.duckdb')
rows = c.execute('SELECT ts, signal_id FROM measurements ORDER BY ts DESC LIMIT 5').fetchall()
for r in rows:
    print(r)
c.close()
