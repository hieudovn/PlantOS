#!/usr/bin/env python3
"""Fix TrendChart.tsx toLocalTs to properly convert UTC -> Vietnam +07:00."""

FILE = "/opt/plantos/frontend/src/features/historian/TrendChart.tsx"

with open(FILE, "r") as f:
    content = f.read()

# Backup
with open(FILE + ".bak", "w") as f:
    f.write(content)

old = '''  const toLocalTs = (ts: string): string => {
    // Backend stores VN time but returns with Z suffix. Convert for display.
    if (ts.endsWith("Z")) return ts.slice(0, -1) + "+07:00";
    return ts;
  };'''

new = '''  const toLocalTs = (ts: string): string => {
    // Convert any UTC timestamp (+00:00, Z, or no tz) to VN time (+07:00)
    try {
      const d = new Date(ts);
      if (isNaN(d.getTime())) return ts;
      const vnTime = new Date(d.getTime() + 7 * 3600000);
      const pad = (n: number) => n.toString().padStart(2, "0");
      return vnTime.getUTCFullYear() + "-" +
        pad(vnTime.getUTCMonth() + 1) + "-" +
        pad(vnTime.getUTCDate()) + "T" +
        pad(vnTime.getUTCHours()) + ":" +
        pad(vnTime.getUTCMinutes()) + ":" +
        pad(vnTime.getUTCSeconds()) + "." +
        String(vnTime.getUTCMilliseconds()).padStart(3, "0") + "+07:00";
    } catch {
      return ts;
    }
  };'''

if old in content:
    content = content.replace(old, new)
    with open(FILE, "w") as f:
        f.write(content)
    print("FIXED: toLocalTs converts UTC -> VN +07:00")
else:
    print("WARNING: old toLocalTs pattern not found")
    # Print current
    for i, line in enumerate(content.split("\n")):
        if "toLocalTs" in line:
            print(f"  L{i+1}: {line.strip()}")
