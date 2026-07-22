#!/usr/bin/env python3
"""Validate core-stabilization-findings.csv format and content."""
import csv
import sys
from pathlib import Path

CSV_PATH = Path("docs/reports/core-stabilization-findings.csv")
REQUIRED_COLUMNS = 14
VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
VALID_STATUSES = {
    "OPEN", "SOURCE_PATCHED", "CI_VERIFIED", "RUNTIME_APPLIED",
    "RUNTIME_VERIFIED", "CLOSED", "RISK_ACCEPTED", "CONTROL_DEFINED",
    "NOT_VERIFIED", "SOURCE_FIXED",
}

def validate():
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found")
        sys.exit(1)

    errors = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if len(rows) < 2:
        errors.append("CSV has no data rows")

    header = rows[0]
    if len(header) != REQUIRED_COLUMNS:
        errors.append(f"Header has {len(header)} columns, expected {REQUIRED_COLUMNS}")

    seen_ids = set()
    for i, row in enumerate(rows[1:], start=2):
        if len(row) != REQUIRED_COLUMNS:
            errors.append(f"Row {i}: {len(row)} columns, expected {REQUIRED_COLUMNS}")
            continue

        fid = row[0].strip()
        severity = row[2].strip()
        status = row[-1].strip()

        if not fid:
            errors.append(f"Row {i}: empty ID")
        elif fid in seen_ids:
            errors.append(f"Row {i}: duplicate ID '{fid}'")
        seen_ids.add(fid)

        if severity not in VALID_SEVERITIES:
            errors.append(f"Row {i} ({fid}): invalid severity '{severity}'")

        if status not in VALID_STATUSES:
            errors.append(f"Row {i} ({fid}): invalid status '{status}'")

    # Summary
    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    status_counts = {}
    for row in rows[1:]:
        sev = row[2].strip() if len(row) > 2 else ""
        st = row[-1].strip() if len(row) > 13 else ""
        if sev in sev_counts:
            sev_counts[sev] += 1
        status_counts[st] = status_counts.get(st, 0) + 1

    print(f"Findings: {len(rows)-1} total")
    print(f"Severity: {sev_counts}")
    print(f"Status: {status_counts}")

    if errors:
        print(f"\n{len(errors)} errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nCSV validation PASSED")
        sys.exit(0)


if __name__ == "__main__":
    validate()
