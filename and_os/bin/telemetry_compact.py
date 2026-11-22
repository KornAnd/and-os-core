#!/usr/bin/env python3
"""
telemetry_compact.py - Monthly compaction of the telemetry journal (audit R4, P10, R4-TEL-2).

The live journal and_os/lib/skills/telemetry.md grows without bound (the
proc_mesh cron appends a line every minute since R4-P2). This script keeps
the newest KEEP_N entry lines in the journal and archives the older
"- YYYY-MM-DD | ..." lines into and_os/var/telemetry_archive_YYYYMM.md
(named by the RUN month, per the approved plan). Both writes are atomic
(tmp + os.replace). The operation is idempotent: below the threshold it is
a no-op. A --dry-run reports what would happen without writing anything.

The frontmatter/title header and the [[CONTEXT|...]] footer are preserved
verbatim. Only the entry lines are moved.
"""

import argparse
import datetime
import os
import re
import shutil
import sys
sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.

ENTRY_RE = re.compile(r"^- \d{4}-\d{2}-\d{2} \|")
DEFAULT_KEEP_N = 300
JOURNAL_REL = os.path.join("and_os", "lib", "skills", "telemetry.md")
ARCHIVE_DIR_REL = os.path.join("and_os", "var")
# 17.11 (Rule #72, data-growth bounding): the monthly archive files are
# themselves a growing channel. Keep the newest ARCHIVE_RETAIN_MONTHS in the
# Vault; older ones are relocated to the system home (outside the Vault and
# outside the 5GB backup quota).
ARCHIVE_RETAIN_MONTHS = 12
ARCHIVE_RELOCATE_DIR = os.path.join(
    os.path.expanduser("~"), ".and_os", "var", "archive", "telemetry")
ARCHIVE_NAME_RE = re.compile(r"^telemetry_archive_(\d{4})(\d{2})\.md$")


def run_month_stamp() -> str:
    """The run month as YYYYMM (the archive file is named by this)."""
    return datetime.datetime.now().strftime("%Y%m")


def _entry_indices(lines):
    return [i for i, line in enumerate(lines) if ENTRY_RE.match(line)]


def _atomic_write(path: str, content: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _archive_content(archive_path: str, archived_lines, run_month: str) -> str:
    block = "\n\n".join(archived_lines) + "\n"
    if os.path.exists(archive_path):
        existing = open(archive_path, encoding="utf-8").read().rstrip("\n")
        return existing + "\n\n" + block
    header = (
        "---\n"
        "tags:\n"
        "  - telemetry\n"
        "  - archive\n"
        "created: {y}-{m}-01\n"
        "---\n"
        "\n"
        "# Telemetry Archive - {rm}\n"
        "\n"
    ).format(y=run_month[:4], m=run_month[4:], rm=run_month)
    return header + block


def retain_archives(archive_dir: str, retain_months: int = ARCHIVE_RETAIN_MONTHS,
                    relocate_dir: str = ARCHIVE_RELOCATE_DIR,
                    dry_run: bool = False) -> dict:
    """Rule #72 (17.11): bound the monthly archive files themselves.

    Keep the newest retain_months of and_os/var/telemetry_archive_YYYYMM.md;
    older ones are relocated (move, not delete) to the system home outside
    the Vault. Idempotent: with nothing old it is a no-op.
    Returns {"relocated": [...], "dry_run": bool, "errors": [...]}.
    """
    summary: dict = {"relocated": [], "dry_run": dry_run, "errors": []}
    if not os.path.isdir(archive_dir):
        return summary
    now = datetime.datetime.now()
    for name in sorted(os.listdir(archive_dir)):
        m = ARCHIVE_NAME_RE.match(name)
        if not m:
            continue
        age_months = (now.year - int(m.group(1))) * 12 + (now.month - int(m.group(2)))
        if age_months < retain_months:
            continue
        if dry_run:
            summary["relocated"].append(name)
            continue
        try:
            os.makedirs(relocate_dir, exist_ok=True)
            shutil.move(os.path.join(archive_dir, name),
                        os.path.join(relocate_dir, name))
            summary["relocated"].append(name)
        except OSError as err:
            summary["errors"].append("%s: %s" % (name, err))
    return summary


def compact(vault_root: str, keep_n: int = DEFAULT_KEEP_N, dry_run: bool = False) -> dict:
    """Compacts the telemetry journal. Returns a result dict (see the module docstring)."""
    vault_root = os.path.abspath(vault_root)
    journal = os.path.join(vault_root, JOURNAL_REL)
    with open(journal, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    idx = _entry_indices(lines)
    if len(idx) <= keep_n:
        return {
            "compacted": False,
            "dry_run": dry_run,
            "reason": "below_threshold",
            "entries": len(idx),
            "keep": keep_n,
        }

    keep_set = set(idx[-keep_n:])
    archived_lines = [lines[i] for i in idx[:-keep_n]]
    first, last = idx[0], idx[-1]

    rebuilt = list(lines[:first])
    prev_kept = False
    for i in range(first, last + 1):
        if not ENTRY_RE.match(lines[i]):
            continue
        if i in keep_set:
            if prev_kept:
                rebuilt.append("")
            rebuilt.append(lines[i])
            prev_kept = True
    rebuilt.extend(lines[last + 1:])

    run_month = run_month_stamp()
    archive_dir = os.path.join(vault_root, ARCHIVE_DIR_REL)
    archive_path = os.path.join(archive_dir, "telemetry_archive_{}.md".format(run_month))

    if dry_run:
        return {
            "compacted": False,
            "dry_run": True,
            "would_archive": len(archived_lines),
            "keep": keep_n,
            "archive_path": archive_path,
        }

    os.makedirs(archive_dir, exist_ok=True)
    _atomic_write(archive_path, _archive_content(archive_path, archived_lines, run_month))
    _atomic_write(journal, "\n".join(rebuilt) + "\n")

    return {
        "compacted": True,
        "dry_run": False,
        "archived": len(archived_lines),
        "kept": keep_n,
        "archive_path": archive_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monthly compaction of the telemetry journal (audit R4, P10)")
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP_N,
                        help="Number of newest entries to keep (default: %(default)s)")
    parser.add_argument("--retain-months", type=int, default=ARCHIVE_RETAIN_MONTHS,
                        help="Number of newest monthly archives to keep in the Vault "
                             "(older ones are relocated, Rule #72; default: %(default)s)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would be archived without writing anything")
    args = parser.parse_args()

    vault_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    try:
        res = compact(vault_root, keep_n=args.keep, dry_run=args.dry_run)
    except (OSError, ValueError) as err:
        sys.stderr.write(f"[telemetry_compact] Error: {err}\n")
        sys.exit(1)

    # 17.11 (Rule #72, data-growth bounding): the monthly archive files are
    # themselves a growing channel - bound them on every run, independently
    # of whether compaction had anything to do.
    rel = retain_archives(os.path.join(vault_root, ARCHIVE_DIR_REL),
                          retain_months=args.retain_months, dry_run=args.dry_run)

    if res.get("reason") == "below_threshold":
        print(f"[telemetry_compact] No-op: {res['entries']} entries <= keep {res['keep']}")
    elif res.get("dry_run"):
        print(f"[telemetry_compact] DRY-RUN: would archive {res['would_archive']} "
              f"entries -> {res['archive_path']} (keep {res['keep']})")
    else:
        print(f"[telemetry_compact] Archived {res['archived']} entries -> {res['archive_path']} "
              f"(kept {res['kept']})")
    if rel["relocated"]:
        mode = "would relocate" if args.dry_run else "relocated"
        print(f"[telemetry_compact] {mode} {len(rel['relocated'])} archive(s) "
              f"older than {args.retain_months} months -> {ARCHIVE_RELOCATE_DIR}")
    for err in rel["errors"]:
        sys.stderr.write(f"[telemetry_compact] relocation error: {err}\n")


if __name__ == "__main__":
    main()
