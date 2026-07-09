#!/usr/bin/env python3
"""Analyze initial comparison CSV."""
import csv
r = list(csv.DictReader(open('/opt/plantos/edge-v2/data/e2v2-13-initial-comparison.csv')))
print(f"Total signals: {len(r)}")
print(f"PASS:  {sum(1 for x in r if x['result']=='PASS')}")
print(f"FAIL:  {sum(1 for x in r if x['result']=='FAIL')}")
print(f"SKIP:  {sum(1 for x in r if x['result']=='SKIP')}")
print()
for x in r:
    if x['result'] != 'PASS':
        print(f"  [{x['result']}] {x['signal_id']}: {x['notes']}")
