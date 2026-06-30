import duckdb
c = duckdb.connect("edge_data.duckdb")
r = c.execute("SELECT DISTINCT signal_id FROM measurements ORDER BY signal_id").fetchall()
for x in r:
    print(x[0])
total = c.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]
print(f"Total: {total} rows")
