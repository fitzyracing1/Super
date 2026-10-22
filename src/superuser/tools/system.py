"""Read-only system inspection helpers (low risk)."""

from __future__ import annotations

import getpass
import platform
import socket
from datetime import datetime, timezone
from typing import Any

import psutil


def system_status() -> dict[str, Any]:
    vm = psutil.virtual_memory()
    boot = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
    load_avg: tuple[float, float, float] | None
    try:
        load_avg = psutil.getloadavg()
    except (AttributeError, OSError):
        load_avg = None

    return {
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "load_average": load_avg,
        "memory": {
            "total_mb": round(vm.total / 1_048_576, 1),
            "available_mb": round(vm.available / 1_048_576, 1),
            "percent_used": vm.percent,
        },
        "boot_time_utc": boot.isoformat(),
    }


def disk_usage() -> dict[str, Any]:
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        partitions.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fstype": part.fstype,
            "total_gb": round(usage.total / 1_073_741_824, 2),
            "used_gb": round(usage.used / 1_073_741_824, 2),
            "percent_used": usage.percent,
        })
    return {"partitions": partitions}


def list_processes(limit: int = 20, sort_by: str = "memory") -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    procs = []
    for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
        try:
            procs.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
    procs.sort(key=lambda p: p.get(key) or 0.0, reverse=True)
    return {"count": len(procs), "sorted_by": sort_by, "processes": procs[:limit]}
