#!/usr/bin/env python3
"""Check full connector config inside container."""
import subprocess

# Read config from container
r = subprocess.run(["docker", "exec", "plantos-edge-v2", "cat", "/app/agent/config/config.edge-v2.yaml"],
                   capture_output=True, text=True, timeout=10)
config = r.stdout

# Count tags in mirror_wtp_signals
import re
tags = re.findall(r'tag_id:\s+\S+', config)
wtp_tags = 0
in_wtp = False
for line in config.split('\n'):
    if 'mirror_wtp_signals' in line:
        in_wtp = True
    elif 'mirror_vf_compressor' in line:
        in_wtp = False
    if in_wtp and 'tag_id:' in line:
        wtp_tags += 1

print(f"Total tag_ids in config: {len(tags)}")
print(f"mirror_wtp_signals tags: {wtp_tags}")

# Check connector section
start = config.find('mirror_wtp_signals')
if start >= 0:
    end = config.find('mirror_vf_compressor')
    section = config[start:end] if end >= 0 else config[start:]
    # Show first few tags
    tag_lines = [l.strip() for l in section.split('\n') if 'tag_id:' in l]
    print(f"\nFirst 5 tags:")
    for t in tag_lines[:5]:
        print(f"  {t}")
    print(f"...")
    for t in tag_lines[-3:]:
        print(f"  {t}")
