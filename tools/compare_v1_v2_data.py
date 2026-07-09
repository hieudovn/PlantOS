#!/usr/bin/env python3
"""
Edge v1 vs v2 Data Comparison Tool

Compares measurement data between WTP-DEMO-01 (v1) and EDGEV2-DEMO (v2) workspaces.
For matching signal_ids, compares: count, min, max, avg, stddev.

Usage:
    python tools/compare_v1_v2_data.py [--center-url http://localhost:8000]
                                      [--v1-workspace DEMO-PLANT]
                                      [--v2-workspace EDGEV2-DEMO]
                                      [--hours 1] [--output report.csv]

SA Constraint: Mirror-first. This does NOT modify any data.
"""

import argparse
import csv
import os
import statistics
import sys
from datetime import datetime, timezone, timedelta

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


def _get_token_cached(api_url: str) -> str:
    """Get auth token (cached in module). Uses env vars for credentials."""
    if not hasattr(_get_token_cached, "_token"):
        _get_token_cached._token = ""
    if _get_token_cached._token:
        return _get_token_cached._token
    
    username = os.environ.get("PLANTOS_CENTER_USERNAME", "admin")
    password = os.environ.get("PLANTOS_CENTER_PASSWORD", "")
    if not password:
        # Fallback: read from file (avoids shell escaping issues with special chars)
        pw_file = os.environ.get("PLANTOS_CENTER_PASSWORD_FILE", "/tmp/plantos_center_pw.txt")
        try:
            with open(pw_file) as f:
                password = f.read().strip()
        except FileNotFoundError:
            pass
    if not password:
        print("  ⚠ PLANTOS_CENTER_PASSWORD not set — auth will fail")
        return ""
    try:
        resp = httpx.post(f"{api_url}/api/v1/auth/login",
                         json={"username": username, "password": password},
                         timeout=10)
        if resp.status_code == 200:
            _get_token_cached._token = resp.json().get("access_token", "")
            if _get_token_cached._token:
                return _get_token_cached._token
        print(f"  ⚠ Login failed: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ⚠ Login error: {e}")
    return ""


def fetch_measurements(api_url: str, plant_id: str, signal_ids: list[str],
                       hours: int = 1) -> dict[str, list[float]]:
    """Fetch measurements for given signal_ids from Center API.

    Returns {signal_id: [value, ...]}
    """
    from collections import defaultdict
    results = defaultdict(list)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    token = _get_token_cached(api_url)
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    for sig_id in signal_ids:
        try:
            to_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            from_ts = cutoff.strftime("%Y-%m-%dT%H:%M:%S")
            params = f"signal_id={sig_id}&from={from_ts}&to={to_ts}"
            resp = httpx.get(f"{api_url}/api/v1/measurements/history?{params}",
                            headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"  ⚠ Skipping {sig_id}: HTTP {resp.status_code}")
                continue

            data = resp.json()
            points = data if isinstance(data, list) else data.get("data", data.get("measurements", []))

            for pt in points:
                ts_str = pt.get("timestamp", pt.get("ts", ""))
                val = pt.get("value", pt.get("val"))
                if val is None:
                    continue
                try:
                    # Filter by time range
                    if ts_str:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts < cutoff:
                            continue
                    results[sig_id].append(float(val))
                except (ValueError, TypeError):
                    continue

        except Exception as e:
            print(f"  ⚠ Error fetching {sig_id}: {e}")

    return dict(results)


def compute_stats(values: list[float]) -> dict:
    """Compute statistics for a list of values."""
    if not values:
        return {"count": 0, "min": None, "max": None, "avg": None, "stddev": None}
    return {
        "count": len(values),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "avg": round(statistics.mean(values), 4),
        "stddev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
    }


def compare_signal(signal_id: str, v1_values: list[float],
                    v2_values: list[float]) -> dict:
    """Compare v1 and v2 data for a single signal."""
    v1_stats = compute_stats(v1_values)
    v2_stats = compute_stats(v2_values)

    # Determine comparison result
    result = "PASS"
    notes = []

    if v1_stats["count"] == 0 and v2_stats["count"] == 0:
        result = "SKIP"
        notes.append("No data for either workspace")
    elif v1_stats["count"] == 0:
        result = "WARN"
        notes.append("No v1 data")
    elif v2_stats["count"] == 0:
        result = "WARN"
        notes.append("No v2 data")
    else:
        # Compare averages within ±5% tolerance
        if v1_stats["avg"] and v2_stats["avg"] and v1_stats["avg"] != 0:
            pct_diff = abs((v2_stats["avg"] - v1_stats["avg"]) / v1_stats["avg"]) * 100
            if pct_diff > 5.0:
                result = "FAIL"
                notes.append(f"Avg diff: {pct_diff:.2f}% (>5% tolerance)")
            else:
                notes.append(f"Avg diff: {pct_diff:.2f}% (within tolerance)")

        # Compare count ratio
        if v1_stats["count"] > 0 and v2_stats["count"] > 0:
            ratio = v2_stats["count"] / v1_stats["count"]
            if ratio < 0.5:
                notes.append(f"v2 count is only {ratio:.0%} of v1")
            elif ratio > 2.0:
                notes.append(f"v2 count is {ratio:.0%} of v1 (possible duplicate)")

    return {
        "signal_id": signal_id,
        "v1_count": v1_stats["count"],
        "v2_count": v2_stats["count"],
        "v1_min": v1_stats["min"],
        "v2_min": v2_stats["min"],
        "v1_max": v1_stats["max"],
        "v2_max": v2_stats["max"],
        "v1_avg": v1_stats["avg"],
        "v2_avg": v2_stats["avg"],
        "v1_stddev": v1_stats["stddev"],
        "v2_stddev": v2_stats["stddev"],
        "result": result,
        "notes": "; ".join(notes),
    }


def get_signal_ids_for_plant(api_url: str, plant_id: str) -> list[str]:
    """Get all signal_ids for a plant."""
    token = _get_token_cached(api_url)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = httpx.get(f"{api_url}/api/v1/signals?plant_id={plant_id}",
                        headers=headers, timeout=10)
        if resp.status_code == 200:
            signals = resp.json()
            return [s["signal_id"] for s in signals if "signal_id" in s]
    except Exception as e:
        print(f"  ⚠ Error fetching signals: {e}")
    return []


def _check_env_password():
    """Check that PLANTOS_CENTER_PASSWORD is available (env var or file)."""
    pw = os.environ.get("PLANTOS_CENTER_PASSWORD", "")
    if not pw:
        pw_file = os.environ.get("PLANTOS_CENTER_PASSWORD_FILE", "/tmp/plantos_center_pw.txt")
        try:
            with open(pw_file) as f:
                pw = f.read().strip()
        except FileNotFoundError:
            pass
    if not pw:
        print("ERROR: PLANTOS_CENTER_PASSWORD env var or /tmp/plantos_center_pw.txt required.")
        print("Usage: PLANTOS_CENTER_PASSWORD=\"password\" python tools/compare_v1_v2_data.py")
        print("   or: printf '%s' 'password' > /tmp/plantos_center_pw.txt")
        sys.exit(1)


def main():
    _check_env_password()
    parser = argparse.ArgumentParser(description="Compare v1 vs v2 measurement data")
    parser.add_argument("--center-url", default="http://localhost:8000",
                        help="Center API URL")
    parser.add_argument("--v1-workspace", default="DEMO-PLANT",
                        help="v1 workspace/plant_id")
    parser.add_argument("--v2-workspace", default="EDGEV2-DEMO",
                        help="v2 workspace/plant_id")
    parser.add_argument("--hours", type=float, default=1.0,
                        help="Hours of data to compare (supports decimals, e.g., 0.5)")
    parser.add_argument("--output", default=None,
                        help="CSV output path (default: print to console)")
    parser.add_argument("--signal-ids", nargs="*", default=[],
                        help="Specific signal_ids to compare (default: all shared signals)")
    args = parser.parse_args()

    if not HAS_HTTPX:
        print("ERROR: httpx required. pip install httpx")
        sys.exit(1)

    api = args.center_url.rstrip("/") + "/api/v1"

    print("=" * 60)
    print("Edge v1 vs v2 Data Comparison")
    print(f"Center: {args.center_url}")
    print(f"v1 workspace: {args.v1_workspace}")
    print(f"v2 workspace: {args.v2_workspace}")
    print(f"Time range: last {args.hours} hour(s)")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Get signal IDs
    if args.signal_ids:
        all_signal_ids = args.signal_ids
    else:
        v1_signals = set(get_signal_ids_for_plant(api, args.v1_workspace))
        v2_signals = set(get_signal_ids_for_plant(api, args.v2_workspace))
        all_signal_ids = sorted(v1_signals & v2_signals)
        print(f"\nv1 signals: {len(v1_signals)}, v2 signals: {len(v2_signals)}")
        print(f"Shared signal_ids: {len(all_signal_ids)}")

    if not all_signal_ids:
        print("\nNo shared signal_ids to compare. Run seed scripts first.")
        print("  python scripts/seed_demo_plant.py")
        print("  python scripts/seed_edgev2_demo.py")
        sys.exit(1)

    # Fetch data
    print(f"\nFetching measurements for {len(all_signal_ids)} signal_ids...")
    v1_data = fetch_measurements(api, args.v1_workspace, all_signal_ids, args.hours)
    v2_data = fetch_measurements(api, args.v2_workspace, all_signal_ids, args.hours)

    # Compare
    print("\nComparing...")
    results = []
    for sig_id in all_signal_ids:
        r = compare_signal(sig_id,
                          v1_data.get(sig_id, []),
                          v2_data.get(sig_id, []))
        results.append(r)

    # Summary
    passed = sum(1 for r in results if r["result"] == "PASS")
    failed = sum(1 for r in results if r["result"] == "FAIL")
    skipped = sum(1 for r in results if r["result"] == "SKIP")
    warned = sum(1 for r in results if r["result"] == "WARN")

    print(f"\nResults: {passed} PASS, {failed} FAIL, {warned} WARN, {skipped} SKIP")

    # Print details
    for r in results:
        if r["result"] != "PASS":
            print(f"  [{r['result']}] {r['signal_id']}: {r['notes']}")
            if r["result"] == "FAIL":
                print(f"    v1: count={r['v1_count']}, avg={r['v1_avg']}")
                print(f"    v2: count={r['v2_count']}, avg={r['v2_avg']}")

    # Output CSV
    if args.output:
        fieldnames = ["signal_id", "result", "v1_count", "v2_count",
                      "v1_min", "v2_min", "v1_max", "v2_max",
                      "v1_avg", "v2_avg", "v1_stddev", "v2_stddev", "notes"]
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nReport written: {args.output}")

    # Final judgment
    if failed > 0:
        print(f"\n⚠ {failed} signal(s) exceeded ±5% tolerance. Review required before switch.")
        sys.exit(1)
    else:
        print("\n✅ All shared signals within tolerance.")
        sys.exit(0)


if __name__ == "__main__":
    main()
