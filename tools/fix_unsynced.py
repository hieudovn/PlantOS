import duckdb
c = duckdb.connect('/opt/plantos/edge/agent/edge_data.duckdb')
c.execute('UPDATE measurements SET synced=TRUE WHERE synced=FALSE')
print(f'Marked {c.rowcount} rows as synced')
c.close()
