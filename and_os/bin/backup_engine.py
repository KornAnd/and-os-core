#!/usr/bin/env python3
"""
backup_engine.py — Enterprise Backup Engine for AnD os v1.0.0.
Features:
  - 100% Full Obsidian Vault backup (All knowledge domains, configs, core).
  - Cross-Platform & Cloud-Ready universal ZIP format (Deflated level 6, Bit 11 UTF-8).
  - Unicode NFC Normalization: eliminates macOS NFD decomposition and '???' mojibake in Yandex.Disk / Windows / Linux.
  - POSIX file modes (0755/0644) & Unix symlinks preservation.
  - Hard 5.0 GB Quota Enforcer with strict FIFO pruning.
  - Zero Contamination: strictly one-way Source -> Target operations.
  - Pre-flight safety gates, atomic archive creation (.tmp_* -> target), SHA-256 verification.
  - Post-creation 4-phase self-audit: ZIP CRC32 test + Cyrillic integrity probe.
  - Structured telemetry logging (and_os/var/log/backup.jsonl).
  - Health signals & heartbeat check for kernel supervisor watchdog.
"""

import os
import sys
import time
import glob
import json
import shutil
import zipfile
import hashlib
import unicodedata
import stat
from datetime import datetime
from pathlib import Path

# Paths
ENGINE_DIR = Path(__file__).resolve().parent
_default_vault = Path(os.path.expanduser("~/Documents/Obsidian Vault"))
_env_vault = os.getenv("AND_VAULT_ROOT")
if _env_vault and Path(_env_vault).exists():
    VAULT_ROOT = Path(_env_vault).resolve()
elif _default_vault.exists():
    VAULT_ROOT = _default_vault.resolve()
else:
    VAULT_ROOT = ENGINE_DIR.parent.parent.resolve()

TARGET_BACKUP_DIR = Path("~/ExternalDrive/WORK/Backups/Obsidian_Vault")
LOG_FILE = VAULT_ROOT / "and_os" / "var" / "log" / "backup.jsonl"
STATE_FILE = VAULT_ROOT / "and_os" / "var" / "backup_state.json"
LOCK_FILE = Path("/tmp/and_os_backup.lock")
MAX_STORAGE_BYTES = 5 * 1024 * 1024 * 1024  # 5.0 GB Hard Quota (audit R4, P6, R4-BACKUP-1: Andrey's decision 12.11)

# Exclusions (clean transient caches only, preserve all vault content)
EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".smart-env",
    ".pytest_cache",
    ".mypy_cache"
}

def log_event(event_type: str, details: dict):
    """Write structured event to backup.jsonl and state file."""
    record = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        **details
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # Update latest state summary
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
    except (OSError, TypeError) as e:
        sys.stderr.write(f"[backup_engine] Warning saving state: {e}\n")

def calculate_sha256(filepath: Path) -> str:
    """Compute SHA-256 checksum in chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def preflight_check() -> tuple[bool, str]:
    """Execute pre-flight safety gates."""
    target_work = Path("~/ExternalDrive/WORK")
    if not target_work.exists() or not os.access(target_work, os.W_OK):
        return False, "Target backup path /WORK is not mounted or not writable."
    
    try:
        free_bytes = shutil.disk_usage(VAULT_ROOT).free
        if free_bytes < 10 * 1024 * 1024 * 1024:
            return False, f"Host disk space too low: {free_bytes // (1024**3)} GB free."
    except Exception as e:
        return False, f"Failed checking host disk space: {e}"
        
    return True, "Pre-flight OK"

def should_exclude(rel_path: Path) -> bool:
    """Filter out transient caches while preserving all content."""
    parts = rel_path.parts
    for p in parts:
        if p in EXCLUDE_DIRS:
            return True
        if p == ".DS_Store" or p.endswith(".pyc"):
            return True
    if len(parts) >= 2 and parts[0] == ".obsidian" and parts[1].startswith("workspace"):
        return True
    return False

def enforce_quota(target_dir: Path) -> list[str]:
    """Prune oldest backups strictly when total size exceeds 5.0 GB."""
    pruned = []
    while True:
        archives = sorted(
            [p for p in target_dir.glob("vault_*") if p.name.endswith(".zip") or p.name.endswith(".tar.gz")],
            key=lambda p: p.stat().st_mtime
        )
        total_size = sum(a.stat().st_size for a in archives)
        if total_size <= MAX_STORAGE_BYTES or not archives:
            break
        
        # Remove oldest archive and its corresponding sha256 checksum
        oldest = archives[0]
        base_stem = oldest.name.split(".")[0]
        sha_file = oldest.parent / f"{base_stem}.sha256"
        try:
            oldest_size_mb = oldest.stat().st_size / (1024 * 1024)
            oldest.unlink(missing_ok=True)
            if sha_file.exists():
                sha_file.unlink(missing_ok=True)
            pruned.append(f"{oldest.name} ({oldest_size_mb:.1f} MB)")
        except Exception as e:
            log_event("PRUNE_ERROR", {"error": str(e), "file": oldest.name})
            break
            
    return pruned

def verify_archive(archive_path: Path) -> tuple[bool, str, int]:
    """Phase 4 Self-Audit: test ZIP CRC32 integrity and verify Cyrillic NFC encoding."""
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            # Check CRC32 of all members
            bad_crc = zf.testzip()
            if bad_crc is not None:
                return False, f"Corrupted file found in archive: {bad_crc}", 0
            
            infolist = zf.infolist()
            total_members = len(infolist)
            if total_members == 0:
                return False, "Archive is empty", 0

            # Probe Cyrillic filenames for NFC normalization and UTF-8 Bit 11
            cyrillic_checked = 0
            for info in infolist:
                # Check for Cyrillic letters
                if any('\u0400' <= char <= '\u04FF' for char in info.filename):
                    cyrillic_checked += 1
                    if not unicodedata.is_normalized('NFC', info.filename):
                        return False, f"File name is not NFC normalized: {info.filename}", total_members
                    if not (info.flag_bits & 0x800):
                        return False, f"UTF-8 Bit 11 flag not set for: {info.filename}", total_members
                    if cyrillic_checked >= 25:
                        break

            return True, f"Integrity verified (tested CRC32, checked {cyrillic_checked} Cyrillic names)", total_members
    except Exception as e:
        return False, f"Archive verification exception: {e}", 0

def run_backup() -> dict:
    """Run full atomic vault backup with universal ZIP format and 5GB quota."""
    start_time = time.time()
    
    # Check Lock
    if LOCK_FILE.exists():
        try:
            lock_age = time.time() - LOCK_FILE.stat().st_mtime
            if lock_age < 3600:
                return {"status": "ABORTED", "reason": "Another backup process is currently running."}
        except OSError as e:
            sys.stderr.write(f"[backup_engine] Warning checking lock file: {e}\n")
    LOCK_FILE.write_text(str(os.getpid()))

    try:
        ok, msg = preflight_check()
        if not ok:
            log_event("PREFLIGHT_FAILED", {"reason": msg})
            return {"status": "FAILED", "error": msg}

        TARGET_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Clean stalled .tmp files older than 6 hours
        for tmp_f in TARGET_BACKUP_DIR.glob(".tmp_*"):
            if time.time() - tmp_f.stat().st_mtime > 6 * 3600:
                tmp_f.unlink(missing_ok=True)

        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        final_filename = f"vault_{timestamp_str}.zip"
        final_archive_path = TARGET_BACKUP_DIR / final_filename
        temp_archive_path = TARGET_BACKUP_DIR / f".tmp_{final_filename}"
        sha_path = TARGET_BACKUP_DIR / f"vault_{timestamp_str}.sha256"

        print(f"📦 [AnD os Backup] Creating atomic universal ZIP archive: {final_filename}...")
        archived_count = 0

        with zipfile.ZipFile(temp_archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for root, dirs, files in os.walk(VAULT_ROOT):
                rel_root = Path(root).relative_to(VAULT_ROOT)
                if should_exclude(rel_root):
                    dirs[:] = []
                    continue

                # Filter out excluded subdirectories in place
                dirs[:] = [d for d in dirs if not should_exclude(rel_root / d)]

                for f in files:
                    full_path = Path(root) / f
                    rel_path = full_path.relative_to(VAULT_ROOT)
                    if should_exclude(rel_path):
                        continue

                    try:
                        lst = full_path.lstat()
                    except OSError:
                        continue

                    # Filter out Unix domain sockets, FIFOs, character/block devices
                    if stat.S_ISSOCK(lst.st_mode) or stat.S_ISFIFO(lst.st_mode) or stat.S_ISBLK(lst.st_mode) or stat.S_ISCHR(lst.st_mode):
                        continue

                    # Unicode NFC normalization for cross-platform fidelity
                    nfc_rel = unicodedata.normalize("NFC", str(rel_path))
                    
                    if full_path.is_symlink():
                        # Preserve Unix symlinks
                        link_target = os.readlink(full_path)
                        zinfo = zipfile.ZipInfo(nfc_rel)
                        zinfo.create_system = 3  # Unix
                        zinfo.external_attr = 0o120777 << 16  # S_IFLNK | 0777
                        zinfo.flag_bits |= 0x800  # Language encoding flag (UTF-8)
                        zf.writestr(zinfo, link_target)
                    else:
                        st = full_path.stat()
                        mtime = time.localtime(st.st_mtime)[:6]
                        zinfo = zipfile.ZipInfo(filename=nfc_rel, date_time=mtime)
                        zinfo.compress_type = zipfile.ZIP_DEFLATED
                        zinfo.create_system = 3  # Unix
                        # Preserve POSIX mode (0755/0644 etc.)
                        zinfo.external_attr = (st.st_mode & 0xFFFF) << 16
                        zinfo.flag_bits |= 0x800  # Language encoding flag (UTF-8)
                        with open(full_path, "rb") as f_in, zf.open(zinfo, "w") as f_out:
                            shutil.copyfileobj(f_in, f_out, length=64 * 1024)

                    archived_count += 1

        # Post-creation integrity self-audit
        print("🔍 [AnD os Backup] Verifying archive integrity & Unicode NFC encoding...")
        is_valid, audit_msg, total_verified = verify_archive(temp_archive_path)
        if not is_valid:
            temp_archive_path.unlink(missing_ok=True)
            raise ValueError(f"Self-Audit Verification Failed: {audit_msg}")

        checksum = calculate_sha256(temp_archive_path)
        sha_path.write_text(f"{checksum}  {final_filename}\n", encoding="utf-8")
        
        # Atomic promotion
        temp_archive_path.replace(final_archive_path)
        archive_size_mb = final_archive_path.stat().st_size / (1024 * 1024)

        # Enforce 5.0 GB quota via FIFO
        pruned_files = enforce_quota(TARGET_BACKUP_DIR)
        
        # Total remaining size calculation
        all_archives = [p for p in TARGET_BACKUP_DIR.glob("vault_*") if p.name.endswith(".zip") or p.name.endswith(".tar.gz")]
        total_quota_used_mb = sum(a.stat().st_size for a in all_archives) / (1024 * 1024)

        elapsed = round(time.time() - start_time, 2)
        summary = {
            "status": "SUCCESS",
            "format": "universal_zip_nfc",
            "archive": final_filename,
            "size_mb": round(archive_size_mb, 2),
            "files_archived": archived_count,
            "sha256": checksum,
            "pruned_archives": pruned_files,
            "total_quota_used_mb": round(total_quota_used_mb, 2),
            "max_quota_mb": MAX_STORAGE_BYTES / (1024 * 1024),
            "elapsed_sec": elapsed
        }
        
        log_event("BACKUP_SUCCESS", summary)
        print(f"✅ [AnD os Backup] Complete in {elapsed}s | Size: {archive_size_mb:.1f} MB | Quota: {total_quota_used_mb:.1f}/{MAX_STORAGE_BYTES / (1024 * 1024):.0f} MB")
        if pruned_files:
            print(f"🗑️ [AnD os Backup] FIFO Pruned (exceeded 5GB): {', '.join(pruned_files)}")
            
        return summary

    except Exception as e:
        err_msg = str(e)
        log_event("BACKUP_FAILED", {"error": err_msg})
        print(f"❌ [AnD os Backup] Error: {err_msg}", file=sys.stderr)
        return {"status": "ERROR", "error": err_msg}
    finally:
        LOCK_FILE.unlink(missing_ok=True)

def get_backup_health() -> dict:
    """Check health signals for supervisor daemon & health grid."""
    if not STATE_FILE.exists():
        return {
            "healthy": False,
            "status": "NO_BACKUP_YET",
            "message": "No backup has been recorded yet."
        }
        
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            last_state = json.load(f)
            
        last_time_str = last_state.get("timestamp")
        last_time = datetime.fromisoformat(last_time_str)
        days_since = (datetime.now() - last_time).total_seconds() / 86400
        
        # Weekly backup threshold: unhealthy if older than 8 days
        is_stale = days_since > 8.0
        status_ok = last_state.get("status") == "SUCCESS"
        
        return {
            "healthy": status_ok and not is_stale,
            "days_since_last": round(days_since, 1),
            "last_archive": last_state.get("archive"),
            "size_mb": last_state.get("size_mb"),
            "total_quota_used_mb": last_state.get("total_quota_used_mb"),
            "is_stale": is_stale,
            "status": last_state.get("status")
        }
    except Exception as e:
        return {
            "healthy": False,
            "status": "CORRUPT_STATE",
            "message": f"Error reading state: {e}"
        }

if __name__ == "__main__":
    if "--status" in sys.argv:
        health = get_backup_health()
        print(json.dumps(health, indent=2, ensure_ascii=False))
    else:
        res = run_backup()
        sys.exit(0 if res.get("status") == "SUCCESS" else 1)
