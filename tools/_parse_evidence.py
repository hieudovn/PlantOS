import csv

# Read soak CSV
soak = list(csv.DictReader(open("/opt/plantos/edge-v2/data/soak_20260709_123114.csv")))
def safe_float(v):
    try: return float(v)
    except: return None

cpu_vals = [x for x in [safe_float(r["cpu_pct"]) for r in soak] if x is not None]
mem_vals = [safe_float(r["mem_mb"]) for r in soak]
backlog_vals = [int(r["v2_backlog"]) for r in soak]
buffer_vals = [int(r["v2_buffer_rows"]) for r in soak]

print(f"Soak: {len(soak)} iterations, {soak[0]['timestamp']} → {soak[-1]['timestamp']}")
print(f"CPU: min={min(cpu_vals):.1f}% max={max(cpu_vals):.1f}% avg={sum(cpu_vals)/len(cpu_vals):.1f}%")
print(f"Memory: min={min(mem_vals):.0f}MB max={max(mem_vals):.0f}MB start={mem_vals[0]:.0f}MB end={mem_vals[-1]:.0f}MB (+{mem_vals[-1]-mem_vals[0]:.0f}MB)")
print(f"Backlog: min={min(backlog_vals)} max={max(backlog_vals)} avg={sum(backlog_vals)/len(backlog_vals):.1f}")
print(f"Buffer: {buffer_vals[0]} → {buffer_vals[-1]} (+{buffer_vals[-1]-buffer_vals[0]} rows)")
print(f"v1=200: {sum(1 for r in soak if r['v1_code']=='200')}/{len(soak)}")
print(f"v2=running: {sum(1 for r in soak if r['v2_status']=='running')}/{len(soak)}")
print(f"JWT OK: {sum(1 for r in soak if r['jwt_ok']=='1')}/{len(soak)}")
print(f"Center 200: {sum(1 for r in soak if r['center_code']=='200')}/{len(soak)}")
