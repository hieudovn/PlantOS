"""System metrics endpoint — DB stats + server resources (CPU, RAM, disk)."""

import os
import logging
from fastapi import APIRouter
from sqlalchemy import text
from app.db import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


def _pg_stats() -> dict:
    """PostgreSQL database size and table row counts."""
    try:
        with get_session() as session:
            # Database size
            db_size = session.execute(
                text("SELECT pg_database_size(current_database())")
            ).scalar() or 0

            # Count rows in key tables
            tables = ["plants", "areas", "assets", "signals", "alarms", "events", "edge_nodes"]
            counts = {}
            for table in tables:
                try:
                    cnt = session.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    ).scalar() or 0
                    counts[table] = cnt
                except Exception:
                    counts[table] = 0  # table doesn't exist yet

        return {
            "size_bytes": db_size,
            "size_mb": round(db_size / (1024 * 1024), 2),
            "tables": counts,
        }
    except Exception as e:
        logger.warning(f"PG stats failed: {e}")
        return {"error": str(e), "size_bytes": 0, "size_mb": 0, "tables": {}}


def _tdengine_stats() -> dict:
    """TDengine measurement count — best-effort via taos CLI on host."""
    count = 0
    # Try host-level taos command (only works if taos is installed on host)
    try:
        import subprocess
        result = subprocess.run(
            ["taos", "-s", "SELECT COUNT(*) FROM plantos_ts.measurements;"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            parts = line.strip().split("|")
            if len(parts) >= 2:
                val = parts[0].strip()
                if val.isdigit():
                    count = int(val)
                    break
    except FileNotFoundError:
        logger.debug("taos CLI not available on host")
    except Exception as e:
        logger.warning(f"TDengine count failed: {e}")

    return {
        "measurement_count": count,
        "size_bytes": 0,
        "size_mb": 0,
    }


def _system_resources() -> dict:
    """CPU, RAM, disk usage from /proc (Linux only)."""
    # CPU: load average
    cpu_percent = 0.0
    try:
        with open("/proc/loadavg") as f:
            parts = f.read().split()
            if parts:
                cpu_percent = round(float(parts[0]) * 100 / os.cpu_count(), 1) if os.cpu_count() else 0.0
    except Exception:
        pass

    # RAM
    ram_total = 0
    ram_used = 0
    ram_percent = 0.0
    try:
        meminfo = {}
        with open("/proc/meminfo") as f:
            for line in f:
                if ":" in line:
                    key, val = line.split(":", 1)
                    meminfo[key.strip()] = int(val.strip().split()[0])
        ram_total = meminfo.get("MemTotal", 0) * 1024  # kB → bytes
        ram_free = meminfo.get("MemAvailable", meminfo.get("MemFree", 0)) * 1024
        ram_used = ram_total - ram_free
        ram_percent = round(ram_used / ram_total * 100, 1) if ram_total > 0 else 0.0
    except Exception:
        pass

    # Disk
    disk_total = 0
    disk_used = 0
    disk_percent = 0.0
    try:
        import shutil
        usage = shutil.disk_usage("/")
        disk_total = usage.total
        disk_used = usage.used
        disk_percent = round(disk_used / disk_total * 100, 1) if disk_total > 0 else 0.0
    except Exception:
        pass

    def fmt_bytes(b: int) -> str:
        if b >= 1024**3:
            return f"{b / 1024**3:.1f} GB"
        if b >= 1024**2:
            return f"{b / 1024**2:.1f} MB"
        return f"{b / 1024:.0f} KB"

    return {
        "cpu_percent": cpu_percent,
        "cpu_cores": os.cpu_count() or 0,
        "ram_total": ram_total,
        "ram_used": ram_used,
        "ram_percent": ram_percent,
        "ram_total_str": fmt_bytes(ram_total),
        "ram_used_str": fmt_bytes(ram_used),
        "disk_total": disk_total,
        "disk_used": disk_used,
        "disk_percent": disk_percent,
        "disk_total_str": fmt_bytes(disk_total),
        "disk_used_str": fmt_bytes(disk_used),
    }


@router.get("/system/metrics")
def system_metrics():
    """Return database stats + server resource usage."""
    return {
        "postgresql": _pg_stats(),
        "tdengine": _tdengine_stats(),
        "system": _system_resources(),
    }
