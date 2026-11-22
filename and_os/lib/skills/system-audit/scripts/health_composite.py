#!/usr/bin/env python3
"""
health_composite.py — Health Composite 0-10 for AnD os (system-audit v1.2).

Computes a single weighted health score over four captured components,
appends one JSONL row to the history file, and reports the trend versus
the previous row ONLY when the coverage (the set of captured components)
is equal. A component that fails to capture is N/A (null) — the score is
renormalized over the captured set, never padded with a guessed value.

Components (weights documented in WEIGHTS):
  suite  0.40  last full run_tests.py result (passed/total)
  grid   0.25  health-grid cache (probes passed/total, max age 24h)
  gates  0.20  gate_integrity_probe.py weakened-gate findings
  diet   0.15  skill_diet.py bloat advisories

History row (JSONL, one per run):
  {"ts": iso, "composite": float|null, "coverage": [...],
   "components": {...}, "notes": [...]}

Usage:
  python3 health_composite.py [--no-suite] [--grid PATH]
                              [--max-grid-age SECS] [--out-jsonl PATH]
                              [--history N] [--json]

Exit codes: 0 computed (or nothing captured at all) · 2 usage error.
Read-only except the history file. No network. Standard library only.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

EXIT_OK = 0
EXIT_USAGE = 2

WEIGHTS = {"suite": 0.40, "grid": 0.25, "gates": 0.20, "diet": 0.15}
GATE_FINDINGS_BUDGET = 10
DIET_FINDINGS_BUDGET = 5
TREND_BAND = 0.5
DEFAULT_MAX_GRID_AGE = 86400
# 17.11 (Rule #72, data-growth bounding): health_history.jsonl is append-only;
# keep the newest N rows in the live journal (~1000 daily rows = ~3 years).
MAX_HISTORY_LINES = 1000
# 17.11 (Rule #72, Andrey decision): rotate, do not burn - the oldest rows
# are replaced by the monthly archive health_history_YYYYMM.jsonl (preserved
# next to the journal), and archives older than the horizon are relocated to
# the system home (outside the Vault and the 5GB backup quota).
HEALTH_HISTORY_RETAIN_MONTHS = 12
HEALTH_HISTORY_RELOCATE_DIR = os.path.join(
    os.path.expanduser("~"), ".and_os", "var", "archive", "health_history")
HEALTH_ARCHIVE_RE = re.compile(r"^health_history_(\d{4})(\d{2})\.jsonl$")

VAULT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "..", "..", "..", ".."))
DEFAULT_GRID_PATH = os.path.join(VAULT_ROOT, "and_os", "var",
                                 "system_health.json")
DEFAULT_HISTORY_PATH = os.path.join(VAULT_ROOT, "and_os", "var",
                                    "health_history.jsonl")
RUN_TESTS = os.path.join(VAULT_ROOT, "and_os", "bin", "run_tests.py")
GATE_PROBE = os.path.join(VAULT_ROOT, "and_os", "lib", "skills",
                          "system-audit", "scripts", "gate_integrity_probe.py")
SKILL_DIET = os.path.join(VAULT_ROOT, "and_os", "lib", "skills",
                          "skill-creator", "scripts", "skill_diet.py")
VENV_PYTHON = os.path.join(VAULT_ROOT, "and_os", ".venv", "bin", "python")


def composite_score(components: Dict[str, Optional[float]]) -> Optional[float]:
    """Weighted 0-10 score over the captured components.

    Weights are renormalized over the captured set; all-missing returns
    None (a health score with zero coverage would be a fabrication).
    """
    captured = {k: v for k, v in components.items() if v is not None}
    if not captured:
        return None
    weight_sum = sum(WEIGHTS.get(k, 0.0) for k in captured)
    if weight_sum <= 0:
        return None
    total = sum(WEIGHTS.get(k, 0.0) * v for k, v in captured.items())
    return round(total / weight_sum * 10.0, 1)


def coverage(components: Dict[str, Optional[float]]) -> Tuple[str, ...]:
    """Sorted tuple of captured component names (coverage of the score)."""
    return tuple(sorted(k for k, v in components.items() if v is not None))


def trend(prev: Optional[dict], curr: Optional[dict]) -> Optional[str]:
    """up/down/flat versus the previous row, or None when not comparable.

    Comparable only at equal coverage: a score computed over a different
    component set is not the same measurement.
    """
    if not prev or not curr:
        return None
    if prev.get("composite") is None or curr.get("composite") is None:
        return None
    if tuple(prev.get("coverage", ())) != tuple(curr.get("coverage", ())):
        return None
    delta = curr["composite"] - prev["composite"]
    if delta >= TREND_BAND:
        return "up"
    if delta <= -TREND_BAND:
        return "down"
    return "flat"


def _history_archive_month(line: str, fallback: str) -> str:
    """YYYYMM from the 'ts' field of the oldest rotated row (fallback: run month)."""
    try:
        ts = json.loads(line).get("ts", "")
        if isinstance(ts, str) and len(ts) >= 7:
            return ts[:4] + ts[5:7]
    except (ValueError, AttributeError) as err:
        sys.stderr.write(
            f"[health_composite] Notice: archive month unparseable from history row, "
            f"using fallback month: {err}\n")
    return fallback


def _relocate_old_history_archives(history_dir: str) -> None:
    """Relocate health_history_YYYYMM.jsonl archives older than
    HEALTH_HISTORY_RETAIN_MONTHS to the system home."""
    now = datetime.now()
    for name in sorted(os.listdir(history_dir)):
        m = HEALTH_ARCHIVE_RE.match(name)
        if not m:
            continue
        age = (now.year - int(m.group(1))) * 12 + (now.month - int(m.group(2)))
        if age < HEALTH_HISTORY_RETAIN_MONTHS:
            continue
        try:
            os.makedirs(HEALTH_HISTORY_RELOCATE_DIR, exist_ok=True)
            shutil.move(os.path.join(history_dir, name),
                        os.path.join(HEALTH_HISTORY_RELOCATE_DIR, name))
        except OSError as err:
            sys.stderr.write(f"[health_composite] archive relocation failed: {name}: {err}\n")


def rotate_history(path: str) -> None:
    """Rule #72 (17.11): bounded rotation of the health history journal.
    When the journal exceeds MAX_HISTORY_LINES, the oldest rows are NOT
    burned - they are replaced by (moved into) the monthly archive
    health_history_YYYYMM.jsonl, so the full history stays available;
    archives older than the retention horizon are relocated to the system
    home. health_composite.py and evidence_sample.py (delegating through
    append_history) are the writers (audit runs are serialized by their
    lock), so temp+replace is safe."""
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.readlines()
    if len(lines) <= MAX_HISTORY_LINES:
        return
    old = lines[: len(lines) - MAX_HISTORY_LINES]
    newest = lines[len(lines) - MAX_HISTORY_LINES:]
    month = _history_archive_month(old[0], datetime.now().strftime("%Y%m"))
    with open(os.path.join(os.path.dirname(path), f"health_history_{month}.jsonl"),
              "a", encoding="utf-8") as handle:
        handle.writelines(old)
    tmp = path + ".rot.tmp"
    with open(tmp, "w", encoding="utf-8") as tf:
        tf.writelines(newest)
    os.replace(tmp, path)
    _relocate_old_history_archives(os.path.dirname(path))


def append_history(path: str, row: dict) -> None:
    """Append a row, then keep the journal bounded by rotation (oldest rows
    are replaced by the monthly archive - preserved, not burned; Rule #72)."""
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    try:
        rotate_history(path)
    except OSError as err:
        sys.stderr.write(f"[health_composite] history rotation failed: {err}\n")


def read_history(path: str) -> List[dict]:
    """Parses the JSONL history; malformed lines are skipped, not fatal."""
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except (ValueError, TypeError):
                continue
    return rows


# 18.11 F2 fix: the old regex `(\d+) passed in ` only matched the bare form
# "N passed in Xs". As soon as pytest added "warnings"/"subtests" segments
# ("641 passed, 3 warnings, 5 subtests passed in 52.57s") the suite component
# (weight 0.40 — the heaviest) went systematically N/A. The summary line is
# now detected structurally: a count word (passed/failed/error) plus the
# " in <time>s" tail, scanned from the end of the output.
SUITE_SUMMARY_RE = re.compile(r"\d+ (?:passed|failed|error).* in \d")
SUITE_PASS_RE = re.compile(r"(\d+) passed")
SUITE_FAIL_RE = re.compile(r"(\d+) failed")
SUITE_ERR_RE = re.compile(r"(\d+) error")


def _first_int(pattern: "re.Pattern[str]", line: str) -> int:
    match = pattern.search(line)
    return int(match.group(1)) if match else 0


def parse_suite_output(text: str) -> Optional[Tuple[int, int]]:
    """(passed, total) from the pytest summary line, or None when absent."""
    for line in reversed(text.splitlines()):
        if not SUITE_SUMMARY_RE.search(line):
            continue
        passed = _first_int(SUITE_PASS_RE, line)
        failed = _first_int(SUITE_FAIL_RE, line)
        errors = _first_int(SUITE_ERR_RE, line)
        total = passed + failed + errors
        if total <= 0:
            continue
        return (passed, total)
    return None


def parse_grid_rings(data: dict) -> Optional[Tuple[int, int]]:
    """(passed, total) health-grid probes, or None when the cache is
    structurally absent (a stale cache is a freshness problem, handled
    by the caller, not a parser problem)."""
    probes = data.get("probes") if isinstance(data, dict) else None
    if not isinstance(probes, dict) or not probes:
        return None
    total = len(probes)
    passed = sum(1 for entry in probes.values()
                 if isinstance(entry, dict) and entry.get("passed"))
    return (passed, total)


GATE_SUMMARY_RE = re.compile(r"SUMMARY:\s*(\d+)\s*weakened-gate")
GATE_CLEAN_RE = re.compile(r"clean:\s*no weakened gates")


def parse_gate_summary(text: str) -> Optional[int]:
    """Weakened-gate finding count: N from the SUMMARY line, 0 from the
    clean marker, None when neither is present (capture failed)."""
    match = GATE_SUMMARY_RE.search(text)
    if match:
        return int(match.group(1))
    if GATE_CLEAN_RE.search(text):
        return 0
    return None


DIET_ADVISORY_RE = re.compile(r"bloat advisories:\s*(\d+)")


def parse_diet_summary(text: str) -> Optional[int]:
    """Bloat-advisory count from the skill_diet SUMMARY line, or None."""
    match = DIET_ADVISORY_RE.search(text)
    if match:
        return int(match.group(1))
    return None


def score_suite(passed: int, total: int) -> Optional[float]:
    if total <= 0:
        return None
    return passed / total


def score_grid(passed: int, total: int) -> Optional[float]:
    if total <= 0:
        return None
    return passed / total


def score_findings(count: int, budget: int) -> float:
    """1.0 at zero findings, linear decay to 0.0 at the budget."""
    if count <= 0:
        return 1.0
    return max(0.0, 1.0 - count / budget)


def _python() -> str:
    if os.path.exists(VENV_PYTHON):
        return VENV_PYTHON
    return sys.executable


def _run_captured(command: list, timeout: int) -> Optional[str]:
    """Runs a subprocess and returns its stdout, or None on failure."""
    try:
        proc = subprocess.run(
            command, capture_output=True, text=True, cwd=VAULT_ROOT,
            timeout=timeout)
        return proc.stdout
    except (OSError, subprocess.SubprocessError):
        return None


def capture_suite(timeout: int = 600) -> Tuple[Optional[float], str]:
    """Runs the full test suite and returns (score, note-or-None)."""
    output = _run_captured([_python(), RUN_TESTS], timeout)
    if output is None:
        return None, "suite capture failed (runner error or timeout)"
    parsed = parse_suite_output(output)
    if parsed is None:
        return None, "suite capture failed (no pytest summary line)"
    score = score_suite(parsed[0], parsed[1])
    return score, f"suite {parsed[0]}/{parsed[1]} passed"


def capture_grid(grid_path: str, max_age: int) -> Tuple[Optional[float], str]:
    """Health-grid cache: probe pass ratio if fresh, else N/A."""
    if not os.path.exists(grid_path):
        return None, "grid N/A (no cache)"
    try:
        age = os.path.getmtime(grid_path)
    except OSError:
        return None, "grid N/A (stat failed)"
    if time.time() - age > max_age:
        return None, f"grid N/A (cache older than {max_age}s)"
    try:
        with open(grid_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None, "grid N/A (cache unreadable)"
    parsed = parse_grid_rings(data)
    if parsed is None:
        return None, "grid N/A (no probes in cache)"
    score = score_grid(parsed[0], parsed[1])
    note = f"grid {parsed[0]}/{parsed[1]} probes passed"
    advisory_count = data.get("advisory_count")
    if isinstance(advisory_count, int) and advisory_count > 0:
        note += f"; advisories: {advisory_count} (non-blocking)"
    return score, note


def capture_gates() -> Tuple[Optional[float], str]:
    output = _run_captured([_python(), GATE_PROBE], timeout=300)
    if output is None:
        return None, "gates capture failed"
    count = parse_gate_summary(output)
    if count is None:
        return None, "gates capture failed (no SUMMARY line)"
    score = score_findings(count, GATE_FINDINGS_BUDGET)
    return score, f"gates: {count} weakened-gate finding(s)"


def capture_diet() -> Tuple[Optional[float], str]:
    output = _run_captured([_python(), SKILL_DIET], timeout=300)
    if output is None:
        return None, "diet capture failed"
    count = parse_diet_summary(output)
    if count is None:
        return None, "diet capture failed (no SUMMARY line)"
    score = score_findings(count, DIET_FINDINGS_BUDGET)
    return score, f"diet: {count} bloat advisory(ies)"


def build_components(run_suite: bool, grid_path: str,
                     max_age: int) -> Tuple[Dict[str, Optional[float]], List[str]]:
    components = {}
    notes = []
    if run_suite:
        score, note = capture_suite()
        components["suite"] = score
    else:
        components["suite"] = None
        notes.append("suite N/A (capture skipped by --no-suite)")
    score, note = capture_grid(grid_path, max_age)
    components["grid"] = score
    notes.append(note)
    score, note = capture_gates()
    components["gates"] = score
    notes.append(note)
    score, note = capture_diet()
    components["diet"] = score
    notes.append(note)
    return components, notes


def render_report(composite, components, notes, trend_value,
                  history_rows, history_path) -> str:
    lines = ["=" * 68,
             "\U0001f49a  Health Composite (system-audit v1.2)",
             "=" * 68]
    if composite is None:
        lines.append("composite: N/A (no component captured — no score is "
                     "a better answer than a fabricated one)")
    else:
        lines.append(f"composite: {composite} / 10  "
                     f"(coverage: {', '.join(coverage(components)) or '-'})")
        for name in ("suite", "grid", "gates", "diet"):
            value = components.get(name)
            if value is None:
                lines.append(f"  {name:<6}: N/A                  "
                             f"w={WEIGHTS[name]:.2f}")
            else:
                lines.append(f"  {name:<6}: {value:.2f}             "
                             f"w={WEIGHTS[name]:.2f}")
    if trend_value is None:
        lines.append("trend: n/a (first measurement or coverage changed)")
    else:
        lines.append(f"trend: {trend_value} (vs previous at equal coverage)")
    lines.append(f"history: {history_path} ({history_rows} row(s))")
    for note in notes:
        lines.append(f"note: {note}")
    lines.append("=" * 68)
    return "\n".join(lines)


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="Health composite 0-10 with JSONL history")
    parser.add_argument("--no-suite", action="store_true",
                        help="skip the full test-suite capture")
    parser.add_argument("--grid", default=DEFAULT_GRID_PATH,
                        help="health-grid cache path")
    parser.add_argument("--max-grid-age", type=int,
                        default=DEFAULT_MAX_GRID_AGE,
                        help="max cache age in seconds (default 86400)")
    parser.add_argument("--out-jsonl", default=DEFAULT_HISTORY_PATH,
                        help="history file to append the row to")
    parser.add_argument("--history", type=int, default=0,
                        help="print the last N history rows")
    parser.add_argument("--json", action="store_true",
                        help="machine-readable output")
    args = parser.parse_args(argv)

    try:
        components, notes = build_components(
            not args.no_suite, args.grid, args.max_grid_age)
    except Exception as err:  # noqa: BLE001 - last-resort capture guard
        components = {k: None for k in WEIGHTS}
        notes = [f"capture aborted: {err}"]

    composite = composite_score(components)
    history = read_history(args.out_jsonl)
    prev = history[-1] if history else None
    row = {"ts": datetime.now().isoformat(timespec="seconds"),
           "composite": composite,
           "coverage": list(coverage(components)),
           "components": {k: components.get(k) for k in WEIGHTS},
           "notes": notes}
    trend_value = trend(prev, row)
    append_history(args.out_jsonl, row)

    if args.json:
        payload = {"ts": row["ts"], "composite": composite,
                   "coverage": row["coverage"],
                   "components": row["components"], "trend": trend_value,
                   "history_rows": len(history) + 1, "notes": notes}
        sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False)
                         + "\n")
    else:
        sys.stdout.write(
            render_report(composite, components, notes, trend_value,
                          len(history) + 1, args.out_jsonl) + "\n")

    if args.history > 0:
        for old in history[-args.history:]:
            sys.stdout.write(json.dumps(old, ensure_ascii=False) + "\n")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
