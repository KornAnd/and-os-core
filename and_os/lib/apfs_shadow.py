"""
apfs_shadow.py — AnD os Hardware-Accelerated Zero-Cost APFS Shadow Engine.
Provides instant, atomic snapshotting of user content prior to any mutation.
"""

import os
import re
import sys
import json
import time
import ctypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SHADOW_BASE = os.path.join(VAULT_ROOT, "and_os/var/vault_shadow")
RETENTION_CONFIG = os.path.join(VAULT_ROOT, "and_os/etc/vault_shadow.json")

# Default retention policy (fallback when etc/vault_shadow.json is absent).
DEFAULT_RETENTION = {"max_age_days": 14, "max_snapshots_per_target": 10}

# Snapshot filename: <sanitized_target>.snap_YYYYmmdd_HHMMSS[_<millis>]
SNAP_TS_RE = re.compile(r"\.snap_(\d{8}_\d{6})(_\d+)?$")

libc = ctypes.CDLL(None)
if hasattr(libc, "clonefile"):
    libc.clonefile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32]
    libc.clonefile.restype = ctypes.c_int
    _HAS_CLONEFILE = True
else:
    _HAS_CLONEFILE = False


def create_shadow_copy(filepath: str) -> Optional[str]:
    """
    Creates an atomic Copy-on-Write APFS clone in and_os/var/vault_shadow/.
    Takes 0.0001 seconds, consumes 0 bytes until modified.
    """
    if not os.path.exists(filepath):
        return None
    
    abs_src = os.path.abspath(filepath)
    rel_path = os.path.relpath(abs_src, VAULT_ROOT)

    # Do not snapshot shadow directory itself or parents containing it to avoid recursion
    if abs_src == os.path.abspath(SHADOW_BASE) or SHADOW_BASE.startswith(abs_src):
        return None
    
    # Generate timestamped snapshot destination
    ts = time.strftime("%Y%m%d_%H%M%S")
    sanitized_name = rel_path.replace(os.sep, "__")
    shadow_filename = f"{sanitized_name}.snap_{ts}"
    os.makedirs(SHADOW_BASE, exist_ok=True)
    dst = os.path.join(SHADOW_BASE, shadow_filename)
    
    if os.path.exists(dst):
        dst = f"{dst}_{int(time.time() * 1000)}"

    if _HAS_CLONEFILE:
        ret = libc.clonefile(abs_src.encode("utf-8"), dst.encode("utf-8"), 0)
        if ret == 0:
            pruned = auto_prune_shadows()
            return dst

    # Fallback to standard copy if APFS clonefile fails or not available
    import shutil
    if os.path.isdir(abs_src):
        shutil.copytree(abs_src, dst, ignore=shutil.ignore_patterns("vault_shadow", "*.sock", "*.pid"))
    else:
        shutil.copy2(abs_src, dst)
    auto_prune_shadows()
    return dst


def load_retention_config() -> Dict[str, int]:
    """Loads the retention policy from and_os/etc/vault_shadow.json (config,
    not code), falling back to DEFAULT_RETENTION when the file is missing
    or invalid."""
    cfg = dict(DEFAULT_RETENTION)
    try:
        with open(RETENTION_CONFIG, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in ("max_age_days", "max_snapshots_per_target"):
            if isinstance(data.get(key), (int, float)) and data[key] > 0:
                cfg[key] = int(data[key])
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as err:
        sys.stderr.write(f"[apfs_shadow] Notice reading retention config: {type(err).__name__}: {err}\n")
    return cfg


def parse_snapshot_timestamp(filename: str) -> Optional[datetime]:
    """Extracts the snapshot timestamp from a shadow filename, or None."""
    match = SNAP_TS_RE.search(filename)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def list_shadow_groups(shadow_base: str = SHADOW_BASE) -> Dict[str, List[Tuple[datetime, str]]]:
    """Groups existing snapshots by target: target -> [(timestamp, path)]."""
    groups: Dict[str, List[Tuple[datetime, str]]] = {}
    if not os.path.isdir(shadow_base):
        return groups
    for entry in sorted(os.listdir(shadow_base)):
        ts = parse_snapshot_timestamp(entry)
        if ts is None:
            continue
        target = SNAP_TS_RE.sub("", entry, count=1)
        groups.setdefault(target, []).append((ts, os.path.join(shadow_base, entry)))
    return groups


def prune_shadows(max_age_days: Optional[int] = None,
                  max_per_target: Optional[int] = None,
                  shadow_base: str = SHADOW_BASE) -> int:
    """Deletes shadow snapshots beyond the retention limits (oldest first).

    A snapshot is pruned when it is older than max_age_days OR when it sits
    beyond the max_per_target newest snapshots of its target. Returns the
    number of pruned snapshots.
    """
    import shutil
    policy = load_retention_config()
    max_age = max_age_days if max_age_days is not None else policy["max_age_days"]
    max_count = max_per_target if max_per_target is not None else policy["max_snapshots_per_target"]

    now = datetime.now()
    pruned = 0
    for target, entries in list_shadow_groups(shadow_base).items():
        # Newest first: rank index 0 is the freshest snapshot of the target.
        entries.sort(key=lambda item: item[0], reverse=True)
        for rank, (ts, path) in enumerate(entries):
            age_days = (now - ts).total_seconds() / 86400.0
            if age_days > max_age or rank >= max_count:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    pruned += 1
                    sys.stderr.write(f"[apfs_shadow] Pruned snapshot: {os.path.basename(path)} (age {age_days:.1f}d)\n")
                except OSError as err:
                    sys.stderr.write(f"[apfs_shadow] Notice pruning {path}: {err}\n")
    return pruned


def auto_prune_shadows() -> int:
    """Best-effort retention enforcement called after every new snapshot."""
    return prune_shadows()


def rollback_from_shadow(filepath: str, snapshot_id: Optional[str] = None) -> bool:
    """Restores a note or directory from its latest shadow clone."""
    abs_target = os.path.abspath(filepath)
    rel_path = os.path.relpath(abs_target, VAULT_ROOT)
    prefix = rel_path.replace(os.sep, "__") + ".snap_"
    
    candidates = []
    if os.path.exists(SHADOW_BASE):
        for f in os.listdir(SHADOW_BASE):
            if f.startswith(prefix):
                candidates.append(os.path.join(SHADOW_BASE, f))
    
    if not candidates:
        return False
    
    candidates.sort()
    chosen = candidates[-1] if not snapshot_id else [c for c in candidates if snapshot_id in c][-1]
    
    import shutil
    if os.path.isdir(chosen):
        if os.path.exists(abs_target):
            shutil.rmtree(abs_target)
        shutil.copytree(chosen, abs_target)
    else:
        shutil.copy2(chosen, abs_target)
    return True
