#!/usr/bin/env python3
"""security_baseline_check.py — release gate: current security findings vs the frozen baseline.

The baseline (and_os/etc/security_baseline.json, frozen 18.11) records every
actionable finding of a full-tree security_scan.py run. At release time this
checker re-runs the same scan (same root, via the same scanner module — no
parallel implementation) and reports the multiset difference:

  NEW      - actionable finding not present in the baseline (release blocker)
  RESOLVED - baseline finding no longer produced (informational only)

Match key: (normalized file, class, context). Line numbers are excluded on
purpose: a one-line drift must not create a false "new" finding.

Usage:
  python3 security_baseline_check.py              # gate mode (exit 0 clean / 1 new findings / 2 usage)
  python3 security_baseline_check.py --update     # re-freeze the baseline from the current scan
  python3 security_baseline_check.py --baseline PATH [--root DIR]

Rule #70: the intersection is a release-time gate, not a per-run gate;
security_scan.py keeps its own exit-code semantics for ad-hoc scans.
"""
import argparse
import datetime
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import security_scan  # noqa: E402  (same directory: reuse, not copy)

VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
DEFAULT_BASELINE = os.path.join(VAULT_ROOT, "and_os", "etc", "security_baseline.json")

EXIT_CLEAN = 0
EXIT_NEW_FINDINGS = 1
EXIT_USAGE = 2


def fail_usage(message: str) -> None:
    sys.stderr.write(f"[security_baseline_check] ERROR: {message}\n")
    sys.exit(EXIT_USAGE)


def finding_key(item: dict) -> tuple:
    """Multiset key, line-number-free (drift tolerant)."""
    path = item["file"]
    if os.path.isabs(path):
        path = os.path.relpath(path, VAULT_ROOT)
    return (os.path.normpath(path), item["class"], item["context"])


def load_baseline(path: str) -> dict:
    if not os.path.exists(path):
        fail_usage(f"baseline not found: {path} (create it with --update)")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            baseline = json.load(fh)
    except json.JSONDecodeError as err:
        fail_usage(f"baseline is not valid JSON: {err}")
    for field in ("version", "created", "root", "actionable_total", "actionable_by_class", "findings"):
        if field not in baseline:
            fail_usage(f"baseline is missing the '{field}' field")
    return baseline


def scan_actionable(root: str, exclude_path: str = "") -> list:
    """Run the shared scanner over root and return actionable findings (JSON rows).

    exclude_path: the baseline file itself, if scanned, would trip its own
    recorded pattern rows (and distort the per-class caps), so it is skipped.
    """
    if not os.path.isdir(root):
        fail_usage(f"scan root is not a directory: {root}")
    exclude_abs = os.path.abspath(exclude_path) if exclude_path else ""
    findings = []
    for path in security_scan.iter_files([root]):
        if exclude_abs and os.path.abspath(path) == exclude_abs:
            continue
        security_scan.scan_file(path, findings)
    for path in security_scan.iter_agent_docs([root]):
        if exclude_abs and os.path.abspath(path) == exclude_abs:
            continue
        security_scan.scan_agent_layer(path, security_scan.read_lines(path), findings)
    security_scan.annotate_self_canaries(findings)
    rows = []
    for path, line, label, ctx in findings:
        if security_scan.is_actionable_finding((path, line, label, ctx)):
            file = os.path.relpath(path, VAULT_ROOT) if os.path.isabs(path) else path
            rows.append({"file": file, "line": line, "class": label, "context": ctx})
    rows.sort(key=lambda r: (r["class"], r["file"], r["line"]))
    return rows


def multiset_diff(current: list, baseline: list) -> tuple:
    """Return (new, resolved): rows in current not covered by baseline and vice versa."""
    remaining = {}
    for row in baseline:
        key = finding_key(row)
        remaining[key] = remaining.get(key, 0) + 1
    new = []
    for row in current:
        key = finding_key(row)
        if remaining.get(key, 0) > 0:
            remaining[key] -= 1
        else:
            new.append(row)
    resolved = []
    for key, count in remaining.items():
        for _ in range(count):
            resolved.append({"file": key[0], "line": 0, "class": key[1], "context": key[2]})
    return new, resolved


def print_rows(rows: list, label: str) -> None:
    sys.stdout.write(f"{label}: {len(rows)}\n")
    for row in rows[:security_scan.FINDING_CAP_PER_CLASS]:
        sys.stdout.write(f"   {row['file']}:{row['line']}  [{row['class']}]  {row['context']}\n")
    if len(rows) > security_scan.FINDING_CAP_PER_CLASS:
        sys.stdout.write(f"   ... and {len(rows) - security_scan.FINDING_CAP_PER_CLASS} more\n")


def write_baseline(path: str, root: str, rows: list) -> None:
    by_class = {}
    for row in rows:
        by_class[row["class"]] = by_class.get(row["class"], 0) + 1
    # Root is stored Vault-relative so the baseline stays portable (19.11:
    # an absolutized root broke the file-shape contract after a re-freeze).
    root_rel = root
    vault_abs = os.path.abspath(VAULT_ROOT)
    if root == vault_abs or root.startswith(vault_abs + os.sep):
        root_rel = os.path.relpath(root, vault_abs)
    # Curated annotations survive a re-freeze: a new scan must not silently
    # drop the human review of known-benign rows (19.11 mutation finding).
    benign = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            benign = json.load(fh).get("benign_annotations", {}) or {}
    except (OSError, json.JSONDecodeError):
        benign = {}
    payload = {
        "version": 1,
        "created": datetime.date.today().isoformat(),
        "root": root_rel,
        "source": "security_scan.py (root: %s/), re-frozen by security_baseline_check.py --update" % root_rel,
        "actionable_total": len(rows),
        "actionable_by_class": dict(sorted(by_class.items(), key=lambda kv: (-kv[1], kv[0]))),
        "findings": rows,
        "benign_annotations": benign,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    sys.stdout.write(f"[security_baseline_check] baseline re-frozen: {path} ({len(rows)} actionable)\n")


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="Security baseline release gate")
    parser.add_argument("--update", action="store_true",
                        help="re-freeze the baseline from the current scan (release-time only)")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE,
                        help=f"baseline JSON path (default: {DEFAULT_BASELINE})")
    parser.add_argument("--root", default=None,
                        help="scan root override (default: the root stored in the baseline)")
    args = parser.parse_args(argv)

    baseline_path = os.path.abspath(args.baseline)
    baseline = load_baseline(baseline_path)
    root = args.root if args.root else baseline["root"]
    if not os.path.isabs(root):
        root = os.path.join(VAULT_ROOT, root)
    if args.root and args.root != baseline["root"]:
        sys.stdout.write(f"[security_baseline_check] WARNING: root override '{args.root}' != baseline root '{baseline['root']}'\n")

    rows = scan_actionable(root, exclude_path=baseline_path)

    if args.update:
        write_baseline(baseline_path, root, rows)
        return EXIT_CLEAN

    new, resolved = multiset_diff(rows, baseline["findings"])
    sys.stdout.write("=" * 68 + "\n")
    sys.stdout.write(f"SECURITY BASELINE GATE  (baseline: {baseline['created']}, root: {baseline['root']})\n")
    sys.stdout.write("=" * 68 + "\n")
    sys.stdout.write(f"baseline actionable: {baseline['actionable_total']}\n")
    sys.stdout.write(f"current actionable:  {len(rows)}\n")
    print_rows(new, "NEW (release blockers)")
    print_rows(resolved, "RESOLVED (informational)")
    if new:
        sys.stdout.write(f"\nVERDICT: BLOCKED - {len(new)} new actionable finding(s) vs baseline.\n")
        sys.stdout.write("Repair them or re-freeze the baseline with --update at release time (Rule #70).\n")
        return EXIT_NEW_FINDINGS
    sys.stdout.write("\nVERDICT: CLEAN - no new actionable findings vs baseline.\n")
    return EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
