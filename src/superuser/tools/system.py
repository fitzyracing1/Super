"""Read-only system inspection helpers (low risk)."""

from __future__ import annotations

import getpass
import platform
import socket
from datetime import datetime, timezone
from typing import Any

try:  # psutil is optional (it may not build/work on Android/Termux)
    import psutil
except Exception:  # pragma: no cover - platform dependent
    psutil = None  # type: ignore[assignment]

import os
import shutil


def _fallback_status() -> dict[str, Any]:
    mem: dict[str, Any] = {}
    try:
        info = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                k, _, v = line.partition(":")
                info[k] = int(v.split()[0])
        total, avail = info.get("MemTotal", 0), info.get("MemAvailable", 0)
        mem = {"total_mb": round(total / 1024, 1), "available_mb": round(avail / 1024, 1),
               "percent_used": round(100 * (1 - avail / total), 1) if total else None}
    except Exception:
        pass
    try:
        load_avg = os.getloadavg()
    except (AttributeError, OSError):
        load_avg = None
    return {"cpu_count": os.cpu_count(), "cpu_percent": None, "load_average": load_avg,
            "memory": mem, "boot_time_utc": None, "psutil": False}


def system_status() -> dict[str, Any]:
    if psutil is None:
        try:
            user = getpass.getuser()
        except Exception:
            user = None
        return {"hostname": socket.gethostname(), "user": user,
                "platform": platform.platform(), "python": platform.python_version(),
                **_fallback_status()}
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
    if psutil is None:
        out = []
        for mp in ("/", os.path.expanduser("~")):
            try:
                u = shutil.disk_usage(mp)
            except OSError:
                continue
            out.append({"device": None, "mountpoint": mp, "fstype": None,
                        "total_gb": round(u.total / 1_073_741_824, 2),
                        "used_gb": round(u.used / 1_073_741_824, 2),
                        "percent_used": round(100 * u.used / u.total, 1) if u.total else None})
        return {"partitions": out, "psutil": False}
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
    if psutil is None:
        return {"count": 0, "sorted_by": sort_by, "processes": [], "psutil": False,
                "note": "psutil unavailable on this platform (e.g. Android); install it to enable."}
    procs = []
    for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
        try:
            procs.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
    procs.sort(key=lambda p: p.get(key) or 0.0, reverse=True)
    return {"count": len(procs), "sorted_by": sort_by, "processes": procs[:limit]}
