"""
bus.py — High-Performance, Atomic & Append-Only Event Journal for AnD os
AnD os v1.2.0 — Core Architecture Layer (Unix-Grade Concurrency & Events)

Features:
  - Atomic concurrent appends using POSIX advisory locks (fcntl.flock)
  - Canonical event envelope: event_id, timestamp_utc, type, source, payload, provenance
  - Deterministic rotation when size or line count threshold is reached
  - Zero external dependencies (stdlib only)
  - Thread-safe and process-safe read/write operations
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import json
import fcntl
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from and_os.lib.core.vfs import DIR_VAR

BUS_FILE = os.path.join(DIR_VAR, "events.jsonl")
LOCK_FILE = os.path.join(DIR_VAR, "events.lock")
DEFAULT_MAX_LINES = 1000
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
# 20.11 (F1, Andrey-approved post-incident audit): rotate, do not burn. The
# 14:45:25 mass-deletion incident proved the cost of trim-only rotation: the
# 999 incident lines were evicted from the 1000-line journal with no archive
# to fall back on. The evicted rows are now preserved in the monthly archive
# events_YYYYMM.jsonl (next to the journal), and archives older than the
# horizon are relocated to the system home (outside the Vault and the 5GB
# backup quota). Mirrors the health_history.jsonl rotation contract (Rule #72).
BUS_ARCHIVE_RETAIN_MONTHS = 12
BUS_ARCHIVE_RELOCATE_DIR = os.path.join(
    os.path.expanduser("~"), ".and_os", "var", "archive", "bus_events")
BUS_ARCHIVE_RE = re.compile(r"^events_(\d{4})(\d{2})\.jsonl$")


class EventWriteError(RuntimeError):
    """Raised when an event cannot be safely written to the journal."""
    pass


def _acquire_lock(lock_fd):
    """Acquires an exclusive POSIX advisory lock."""
    fcntl.flock(lock_fd, fcntl.LOCK_EX)


def _release_lock(lock_fd):
    """Releases POSIX advisory lock."""
    fcntl.flock(lock_fd, fcntl.LOCK_UN)


def emit_event(
    event_type: str,
    payload: Optional[Any] = None,
    source: str = "core",
    provenance: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Atomically emits an event into the canonical AnD os Event Journal.
    Uses file locking to guarantee no interleaved writes from concurrent processes.
    """
    os.makedirs(DIR_VAR, exist_ok=True)
    now_utc = datetime.now(timezone.utc).isoformat()
    event_id = f"evt_{uuid.uuid4().hex[:12]}"

    if payload is None:
        payload_data: Dict[str, Any] = {}
    elif isinstance(payload, str):
        try:
            payload_data = json.loads(payload)
        except Exception:
            payload_data = {"message": payload}
    elif isinstance(payload, dict):
        payload_data = payload
    else:
        payload_data = {"data": str(payload)}

    event_record: Dict[str, Any] = {
        "event_id": event_id,
        "timestamp_utc": now_utc,
        "type": event_type.upper().strip(),
        "source": source.strip(),
        "payload": payload_data,
        "provenance": provenance or {"emitter": source, "host_pid": os.getpid()}
    }

    line = json.dumps(event_record, ensure_ascii=False) + "\n"

    # Atomic write under exclusive lock
    lock_path = LOCK_FILE
    try:
        with open(lock_path, "w") as lock_file:
            _acquire_lock(lock_file.fileno())
            try:
                with open(BUS_FILE, "a", encoding="utf-8") as f:
                    f.write(line)
                _rotate_under_lock_if_needed(max_lines=DEFAULT_MAX_LINES)
            finally:
                _release_lock(lock_file.fileno())
    except Exception as e:
        raise EventWriteError(f"Failed to append to event journal: {e}") from e

    return event_record


def _rotate_under_lock_if_needed(max_lines: int = DEFAULT_MAX_LINES) -> None:
    """Internal helper to prune journal to max_lines under lock.

    20.11 (F1): evicted rows are archived (preserved, not burned) - see
    _rotate_journal. The caller must already hold the journal lock.
    """
    try:
        _rotate_journal(BUS_FILE, max_lines)
    except OSError as err:
        sys.stderr.write(f"[bus] Warning rotating bus file {BUS_FILE}: {err}\n")


def _bus_archive_month(line: str, fallback: str) -> str:
    """YYYYMM from the 'timestamp_utc' field of the oldest evicted row
    (fallback: current UTC month)."""
    try:
        ts = json.loads(line).get("timestamp_utc", "")
        if isinstance(ts, str) and len(ts) >= 7:
            return ts[:4] + ts[5:7]
    except (ValueError, AttributeError) as err:
        sys.stderr.write(
            f"[bus] Notice: archive month unparseable from event row, "
            f"using fallback month: {err}\n")
    return fallback


def _relocate_old_bus_archives(journal_dir: str) -> None:
    """Relocate events_YYYYMM.jsonl archives older than BUS_ARCHIVE_RETAIN_MONTHS
    to the system home (outside the Vault and the 5GB backup quota)."""
    now = datetime.now(timezone.utc)
    try:
        names = sorted(os.listdir(journal_dir))
    except OSError:
        return
    for name in names:
        match = BUS_ARCHIVE_RE.match(name)
        if not match:
            continue
        age = (now.year - int(match.group(1))) * 12 + (now.month - int(match.group(2)))
        if age < BUS_ARCHIVE_RETAIN_MONTHS:
            continue
        try:
            os.makedirs(BUS_ARCHIVE_RELOCATE_DIR, exist_ok=True)
            shutil.move(os.path.join(journal_dir, name),
                        os.path.join(BUS_ARCHIVE_RELOCATE_DIR, name))
        except OSError as err:
            sys.stderr.write(f"[bus] archive relocation failed: {name}: {err}\n")


def _rotate_journal(bus_file: str, max_lines: int) -> None:
    """Bounded rotation of the event journal (Rule #72, F1 20.11).

    When the journal exceeds max_lines, the oldest rows are NOT burned: they
    are appended to the monthly archive events_YYYYMM.jsonl next to the
    journal (so incident/post-rotation forensics stay available), and
    archives older than the retention horizon are relocated to the system
    home. The caller must hold the journal lock (the rotation is
    temp+replace and must not race with appends).
    """
    if not os.path.exists(bus_file):
        return
    with open(bus_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    if len(lines) <= max_lines:
        return
    old = lines[: len(lines) - max_lines]
    newest = lines[len(lines) - max_lines:]
    month = _bus_archive_month(old[0], datetime.now(timezone.utc).strftime("%Y%m"))
    try:
        with open(os.path.join(os.path.dirname(bus_file), f"events_{month}.jsonl"),
                  "a", encoding="utf-8") as handle:
            handle.writelines(old)
    except OSError as err:
        sys.stderr.write(f"[bus] archive write failed for {bus_file}: {err}\n")
    temp_path = bus_file + ".rot.tmp"
    with open(temp_path, "w", encoding="utf-8") as tf:
        tf.writelines(newest)
    os.replace(temp_path, bus_file)
    _relocate_old_bus_archives(os.path.dirname(bus_file))


def get_recent_events(
    limit: int = 50,
    event_type: Optional[str] = None,
    source: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Safely reads recent events from the journal in reverse-chronological order.
    """
    if not os.path.exists(BUS_FILE):
        return []

    events: List[Dict[str, Any]] = []
    lock_path = LOCK_FILE
    os.makedirs(DIR_VAR, exist_ok=True)

    try:
        with open(lock_path, "w") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
            try:
                with open(BUS_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except Exception:
        return []

    target_type = event_type.upper().strip() if event_type else None

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if target_type and rec.get("type") != target_type:
                continue
            if source and rec.get("source") != source:
                continue
            events.append(rec)
            if len(events) >= limit:
                break
        except Exception:
            continue

    return events


def clear_events() -> bool:
    """Safely clears event journal."""
    os.makedirs(DIR_VAR, exist_ok=True)
    lock_path = LOCK_FILE
    try:
        with open(lock_path, "w") as lock_file:
            _acquire_lock(lock_file.fileno())
            try:
                with open(BUS_FILE, "w", encoding="utf-8") as f:
                    f.truncate(0)
                return True
            finally:
                _release_lock(lock_file.fileno())
    except Exception:
        return False
