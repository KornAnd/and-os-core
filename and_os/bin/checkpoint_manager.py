#!/usr/bin/env python3
"""
checkpoint_manager.py - High-Performance APFS CoW & Git State Checkpoint Engine for AnD os.
Combines Apple File System instantaneous copy-on-write cloning (0 extra disk space, 1-2 ms)
with Git SHA and working-tree delta analysis for bulletproof rollback and progress tracking.

Commands:
  create <name>   - Take instant CoW snapshot and record git delta
  verify <name>   - Compare current workspace with named checkpoint
  list            - Show active checkpoints and metadata
  rollback <name> - Restore workspace files from CoW snapshot
  clear           - Remove old checkpoints (keeps last N)
"""

import os
import sys
import json
import time
import ctypes
import shutil
import argparse
import subprocess
from typing import Dict, Any, List, Optional

sys.dont_write_bytecode = True

# Load native macOS clonefile syscall
try:
    libc = ctypes.cdll.LoadLibrary("/usr/lib/libSystem.B.dylib")
    _clonefile = libc.clonefile
    _clonefile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    _clonefile.restype = ctypes.c_int
except Exception:
    _clonefile = None


def apfs_cow_clone(src: str, dst: str) -> bool:
    """Performs instant APFS Copy-on-Write clone of file or directory."""
    if os.path.exists(dst):
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        else:
            os.remove(dst)

    if _clonefile:
        res = _clonefile(src.encode("utf-8"), dst.encode("utf-8"), 0)
        if res == 0:
            return True

    # Fallback to copytree/copy2 if not APFS or syscall failed
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return True


class CheckpointManager:
    def __init__(self, vault_root: str):
        self.vault_root = os.path.abspath(vault_root)
        self.storage_dir = os.path.join(self.vault_root, "and_os", "var", "checkpoints")
        self.metadata_file = os.path.join(self.storage_dir, "checkpoints.json")
        os.makedirs(self.storage_dir, exist_ok=True)

    def _load_metadata(self) -> Dict[str, Any]:
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"checkpoints": []}

    def _save_metadata(self, data: Dict[str, Any]):
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_git_info(self) -> Dict[str, Any]:
        info = {"sha": "SOVEREIGN_VAULT", "branch": "MAIN", "dirty_files": []}
        git_dir = os.path.join(self.vault_root, ".git")
        if os.path.exists(git_dir):
            try:
                p_sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=self.vault_root, stdout=subprocess.PIPE, text=True)
                if p_sha.returncode == 0:
                    info["sha"] = p_sha.stdout.strip()
                p_br = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.vault_root, stdout=subprocess.PIPE, text=True)
                if p_br.returncode == 0:
                    info["branch"] = p_br.stdout.strip()
                p_st = subprocess.run(["git", "status", "--porcelain"], cwd=self.vault_root, stdout=subprocess.PIPE, text=True)
                if p_st.returncode == 0:
                    info["dirty_files"] = [line[3:].strip() for line in p_st.stdout.splitlines() if len(line) > 3]
            except Exception:
                pass
        return info

    def create(self, name: str, targets: Optional[List[str]] = None) -> Dict[str, Any]:
        t0 = time.time()
        meta = self._load_metadata()
        git_info = self._get_git_info()

        safe_name = name.replace(" ", "_").replace("/", "-")
        snap_dir = os.path.join(self.storage_dir, safe_name)
        os.makedirs(snap_dir, exist_ok=True)

        target_dirs = targets or [
            "and_os/bin",
            "and_os/lib",
            "and_os/etc",
            "and_os/opt",
            "and_os/docs",
            "Nero/xcode"
        ]
        cloned_paths = []
        for td in target_dirs:
            src = os.path.join(self.vault_root, td)
            if os.path.exists(src):
                dst = os.path.join(snap_dir, td.replace("/", "__"))
                if apfs_cow_clone(src, dst):
                    cloned_paths.append(td)

        elapsed = round(time.time() - t0, 3)

        cp_record = {
            "name": name,
            "safe_name": safe_name,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": time.time(),
            "git_sha": git_info["sha"],
            "git_branch": git_info["branch"],
            "dirty_count": len(git_info["dirty_files"]),
            "cloned_targets": cloned_paths,
            "elapsed_seconds": elapsed
        }

        # Replace existing or append
        existing_idx = next((i for i, c in enumerate(meta["checkpoints"]) if c["name"] == name), -1)
        if existing_idx >= 0:
            meta["checkpoints"][existing_idx] = cp_record
        else:
            meta["checkpoints"].insert(0, cp_record)

        self._save_metadata(meta)
        return cp_record

    def verify(self, name: str) -> Dict[str, Any]:
        meta = self._load_metadata()
        record = next((c for c in meta["checkpoints"] if c["name"] == name), None)
        if not record:
            return {"error": f"Checkpoint '{name}' not found"}

        current_git = self._get_git_info()
        snap_dir = os.path.join(self.storage_dir, record["safe_name"])

        # Check file deltas across cloned targets
        modified = []
        added = []
        for target in record["cloned_targets"]:
            original_dir = os.path.join(self.vault_root, target)
            cloned_dir = os.path.join(snap_dir, target.replace("/", "__"))
            if os.path.exists(original_dir) and os.path.exists(cloned_dir):
                for root, _, files in os.walk(original_dir):
                    if any(ig in root for ig in [".git", "var/checkpoints", "__pycache__"]):
                        continue
                    for f in files:
                        curr_file = os.path.join(root, f)
                        rel = os.path.relpath(curr_file, original_dir)
                        snap_file = os.path.join(cloned_dir, rel)
                        if not os.path.exists(snap_file):
                            added.append(os.path.relpath(curr_file, self.vault_root))
                        else:
                            try:
                                if os.path.getmtime(curr_file) != os.path.getmtime(snap_file):
                                    modified.append(os.path.relpath(curr_file, self.vault_root))
                            except OSError:
                                pass

        return {
            "checkpoint_name": name,
            "created_at": record["created_at"],
            "baseline_sha": record["git_sha"],
            "current_sha": current_git["sha"],
            "sha_match": record["git_sha"] == current_git["sha"],
            "files_added": added,
            "files_modified": modified,
            "total_deltas": len(added) + len(modified)
        }

    def rollback(self, name: str) -> Dict[str, Any]:
        meta = self._load_metadata()
        record = next((c for c in meta["checkpoints"] if c["name"] == name), None)
        if not record:
            return {"error": f"Checkpoint '{name}' not found"}

        snap_dir = os.path.join(self.storage_dir, record["safe_name"])
        restored = []
        for target in record["cloned_targets"]:
            src_snap = os.path.join(snap_dir, target.replace("/", "__"))
            dst_live = os.path.join(self.vault_root, target)
            if os.path.exists(src_snap):
                if apfs_cow_clone(src_snap, dst_live):
                    restored.append(target)

        return {
            "checkpoint_name": name,
            "status": "RESTORED",
            "restored_targets": restored
        }

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        meta = self._load_metadata()
        return meta.get("checkpoints", [])

    def clear(self, keep_last: int = 5) -> int:
        meta = self._load_metadata()
        cps = meta.get("checkpoints", [])
        if len(cps) > keep_last:
            to_remove = cps[keep_last:]
            meta["checkpoints"] = cps[:keep_last]
            for r in to_remove:
                snap_dir = os.path.join(self.storage_dir, r["safe_name"])
                if os.path.exists(snap_dir):
                    shutil.rmtree(snap_dir)
            self._save_metadata(meta)
            return len(to_remove)
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="AnD os APFS CoW & Git Checkpoint Engine")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # create
    p_c = subparsers.add_parser("create", help="Создать мгновенный APFS CoW снимок")
    p_c.add_argument("name", help="Название контрольной точки")
    p_c.add_argument("--targets", nargs="*", help="Целевые подкаталоги для клонирования")

    # verify
    p_v = subparsers.add_parser("verify", help="Проверить дельту с момента контрольной точки")
    p_v.add_argument("name", help="Название контрольной точки")

    # rollback
    p_r = subparsers.add_parser("rollback", help="Откатить состояние до контрольной точки")
    p_r.add_argument("name", help="Название контрольной точки")

    # list
    subparsers.add_parser("list", help="Список активных контрольных точек")

    # clear
    p_cl = subparsers.add_parser("clear", help="Очистить старые контрольные точки")
    p_cl.add_argument("--keep", type=int, default=5, help="Сколько последних снимков сохранить")

    args = parser.parse_args()
    vault_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    mgr = CheckpointManager(vault_root)

    if args.subcommand == "create":
        res = mgr.create(args.name, targets=args.targets)
        print(f"✅ Checkpoint '{res['name']}' created in {res['elapsed_seconds']}s (Git SHA: {res['git_sha']}, Targets: {', '.join(res['cloned_targets'])})")
    elif args.subcommand == "verify":
        res = mgr.verify(args.name)
        if "error" in res:
            print(f"❌ {res['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"🔍 CHECKPOINT DELTA: {res['checkpoint_name']} ({res['created_at']})")
        print(f"  • Git Baseline SHA : {res['baseline_sha']} -> Current: {res['current_sha']}")
        print(f"  • Files Modified   : {len(res['files_modified'])}")
        print(f"  • Files Added      : {len(res['files_added'])}")
        if res["files_modified"]:
            for f in res["files_modified"][:5]:
                print(f"     ~ {f}")
        if res["files_added"]:
            for f in res["files_added"][:5]:
                print(f"     + {f}")
    elif args.subcommand == "rollback":
        res = mgr.rollback(args.name)
        if "error" in res:
            print(f"❌ {res['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"🔄 Checkpoint '{res['checkpoint_name']}' successfully restored targets: {', '.join(res['restored_targets'])}")
    elif args.subcommand == "list":
        cps = mgr.list_checkpoints()
        if not cps:
            print("ℹ️ Нет активных контрольных точек.")
        else:
            print(f"📋 АКТИВНЫЕ КОНТРОЛЬНЫЕ ТОЧКИ ({len(cps)}):")
            for c in cps:
                print(f"  • [{c['created_at']}] {c['name']:<20} | SHA: {c['git_sha']} | Cloned: {', '.join(c['cloned_targets'])}")
    elif args.subcommand == "clear":
        removed = mgr.clear(keep_last=args.keep)
        print(f"🧹 Очищено устаревших контрольных точек: {removed}")


if __name__ == "__main__":
    main()
