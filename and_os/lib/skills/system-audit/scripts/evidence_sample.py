#!/usr/bin/env python3
"""evidence_sample.py — post-flight evidence sampling for audit reports (R11b).

Hallucinations in system reports must be *measurable*, not disciplinary.
This script extracts checkable factual claims from a Markdown report,
samples one (or --all of them), verifies each against a live measurement,
and appends the outcome to and_os/var/health_history.jsonl via the same
writer health_composite.py uses (single rotation path, Rule #72).

Claim classes (measured, not interpreted):
  suite_count   "697/697" / "697 passed"  -> pytest --collect-only total,
                                             canonical scope (and_os/tests +
                                             and_os/lib/core + and_os/opt/apps)
  grid          "Grid 9/9"                -> sys_cli audit probe pass count
  skills        "50 active skills"        -> skill dirs with SKILL.md on disk
  version       "version 1.1.0"           -> etc/system.json SSoT
  rules_index   "77 canonical rules"      -> etc/rules_fast_index.json
             (the corpus-size modifier is mandatory: contextual counts like
              "14 always-active invariants" are NOT corpus claims, 19.11 R-3)
  rule_range    "\u21160\u201372" / "\u21160\u2013\u211672"  -> max integer rule number in rules.md

Determinism: the daily seed (YYYY-MM-DD) picks the sampled claim, so a
same-day re-run samples the same claim; --seed overrides, --all checks
every claim. Exit 0 = all sampled claims PASS, 1 = any FAIL, 2 = usage.
"""
import argparse
import datetime
import json
import os
import random
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import health_composite  # noqa: E402  (same directory: reuse the history writer)

VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
HISTORY_PATH = os.path.join(VAULT_ROOT, "and_os", "var", "health_history.jsonl")
PY = os.path.join(VAULT_ROOT, "and_os", ".venv", "bin", "python3")
SYS_CLI = os.path.join(VAULT_ROOT, "and_os", "bin", "sys_cli.py")

CLAIM_PATTERNS = [
    ("suite_count", re.compile(r"\bsuite\s+(\d{2,4})\s*/\s*(\d{2,4})\b", re.I)),
    ("grid", re.compile(r"\b(?:Grid|grid)\s+(\d+)\s*/\s*(\d+)\b")),
    ("skills", re.compile(r"\b(\d{2,3})\s+(?:active\s+skills|\u0441\u043a\u0438\u043b\u043b\u043e\u0432)\b", re.I)),
    ("version", re.compile(r"\bversion\s+(\d+\.\d+\.\d+)\b", re.I)),
    ("rules_index", re.compile(
        r"\b(\d{2,3})\s+(?:(?:canonical|\u043a\u0430\u043d\u043e\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0445)\s+)"
        r"(?:rules|invariants|\u0438\u043d\u0432\u0430\u0440\u0438\u0430\u043d\u0442\u043e\u0432|\u043f\u0440\u0430\u0432\u0438\u043b)\b",
        re.I)),
    ("rule_range", re.compile(r"\u21160[\u2013\-]\s*\u2116?\s*(\d{1,2})\b")),
]


def fail_usage(message: str) -> None:
    sys.stderr.write(f"[evidence_sample] ERROR: {message}\n")
    sys.exit(2)


def extract_claims(text: str) -> list:
    """Return [(kind, expected, line_no, raw)] for every matched claim."""
    claims = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for kind, pattern in CLAIM_PATTERNS:
            for match in pattern.finditer(line):
                if kind == "suite_count" and match.group(1) != match.group(2):
                    continue  # a mismatch ratio (697/700) is itself the finding
                if kind == "version":
                    expected = match.group(1)
                elif kind in ("suite_count", "grid"):
                    expected = int(match.group(2))
                else:
                    expected = int(match.group(1))
                claims.append({"kind": kind, "expected": expected, "line": line_no,
                               "raw": match.group(0).strip()})
    return claims


def canonical_suite_scope() -> list:
    """The canonical suite scope as ISOLATED collect root tuples — one
    tuple per pytest process (P11 split, restored 22.11 after the P1b
    top-level `core` package collision; run_tests.py is the SSoT for the
    process model). A single combined process fails collection: the app
    zone (and_os/opt/terminal/core) and the kernel zone (and_os/lib/core)
    both register a top-level `core` under pytest's prepend import mode."""
    import glob
    app_roots = [os.path.join(VAULT_ROOT, "and_os", "tests")] + sorted(glob.glob(
        os.path.join(VAULT_ROOT, "and_os", "opt", "apps", "*", "tests")))
    return [tuple(app_roots), (os.path.join(VAULT_ROOT, "and_os", "lib", "core"),)]


def collect_zone_count(roots: tuple) -> int:
    """Collect-only count of one isolated pytest zone (roots tuple)."""
    proc = subprocess.run(
        [PY, "-m", "pytest"] + list(roots) + ["--collect-only", "-q"],
        cwd=VAULT_ROOT, capture_output=True, text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    if proc.returncode not in (0, 5):
        raise RuntimeError(f"pytest --collect-only failed: {proc.stderr.strip()[:200]}")
    total = 0
    for line in proc.stdout.splitlines():
        m = re.search(r"(\d+)\s+tests?\s+collected", line)
        if m:
            total = int(m.group(1))
    if total == 0:
        m = re.search(r"(\d+)/\d+\s*\[", proc.stdout.strip().splitlines()[-1])
        if m:
            total = int(m.group(1))
    return total


def measure_suite_count() -> int:
    # Canonical suite scope (Rule #11): the app/test zone
    # (and_os/tests + every and_os/opt/apps/*/tests dir) AND the isolated
    # kernel zone (and_os/lib/core). Collecting only and_os/tests
    # under-counts the suite and would fail honest "suite N/N" claims.
    # 22.11 (P1b): summed over the isolated zones of canonical_suite_scope
    # — the old single combined collect fails on the `core` collision.
    return sum(collect_zone_count(roots) for roots in canonical_suite_scope())


def measure_grid() -> int:
    proc = subprocess.run(
        [PY, SYS_CLI, "audit", "--json"],
        cwd=VAULT_ROOT, capture_output=True, text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(f"sys_cli audit failed: {proc.stderr.strip()[:200]}")
    payload = json.loads(proc.stdout)
    probes = payload.get("probes", payload.get("rings", []))
    if isinstance(probes, dict):
        probes = list(probes.values())
    passed = sum(1 for p in probes if isinstance(p, dict) and p.get("passed"))
    return passed


def measure_skill_count() -> int:
    skills_dir = os.path.join(VAULT_ROOT, "and_os", "lib", "skills")
    count = 0
    for entry in os.listdir(skills_dir):
        if os.path.isfile(os.path.join(skills_dir, entry, "SKILL.md")):
            count += 1
    return count


def measure_system_version() -> str:
    with open(os.path.join(VAULT_ROOT, "and_os", "etc", "system.json"), "r", encoding="utf-8") as fh:
        return json.load(fh).get("version", "")


def measure_rules_index_count() -> int:
    with open(os.path.join(VAULT_ROOT, "and_os", "etc", "rules_fast_index.json"), "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    rules = payload.get("rules", payload)
    return len(rules)


def measure_rule_range() -> str:
    """Max integer rule number in .opencode/rules.md (the corpus SSoT).

    Range claims like No.0-No.72 drift silently when rules are added or
    removed; the live maximum integer section number is the ground truth.
    """
    path = os.path.join(VAULT_ROOT, ".opencode", "rules.md")
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    nums = [int(m) for m in re.findall(
        r"^### \u041f\u0440\u0430\u0432\u0438\u043b\u043e \u2116(\d+)(?:\.\d+)?", text, re.M)]
    if not nums:
        raise RuntimeError("no rule sections found in .opencode/rules.md")
    return str(max(nums))


MEASURERS = {
    "suite_count": lambda: str(measure_suite_count()),
    "grid": lambda: str(measure_grid()),
    "skills": lambda: str(measure_skill_count()),
    "version": measure_system_version,
    "rules_index": lambda: str(measure_rules_index_count()),
    "rule_range": measure_rule_range,
}


def verify_claim(claim: dict) -> dict:
    try:
        measured = MEASURERS[claim["kind"]]()
    except (KeyError, OSError, ValueError, RuntimeError, json.JSONDecodeError) as err:
        return {**claim, "measured": None, "verdict": "ERROR", "detail": str(err)[:200]}
    verdict = "PASS" if str(claim["expected"]) == str(measured) else "FAIL"
    return {**claim, "measured": measured, "verdict": verdict}


def latest_claims(claims: list) -> list:
    """Keep the last occurrence per kind: the live claim of record.

    Audit reports are point-in-time documents that get updated; earlier
    lines describe the state at the moment of writing (e.g. the base
    suite count before a batch). The claim verified against the present
    is the newest one per kind; --all checks every occurrence including
    historical context (expected FAILs there are informational).
    """
    latest = {}
    for claim in claims:
        latest[claim["kind"]] = claim
    return [latest[k] for k in sorted(latest)]


def default_report() -> str:
    other_dir = os.path.join(VAULT_ROOT, "Nero", "other")
    candidates = sorted(
        os.path.join(other_dir, f) for f in os.listdir(other_dir)
        if f.startswith("CORE_ARCH_AUDIT") and f.endswith(".md"))
    if not candidates:
        fail_usage("no CORE_ARCH_AUDIT report found in Nero/other/")
    return candidates[-1]


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="Post-flight evidence sampling (R11b)")
    parser.add_argument("--report", default=None,
                        help="Markdown report to sample (default: latest CORE_ARCH_AUDIT)")
    parser.add_argument("--seed", default=None,
                        help="seed override (default: YYYY-MM-DD daily seed)")
    parser.add_argument("--count", type=int, default=1, help="claims to sample (default 1)")
    parser.add_argument("--all", action="store_true", help="verify every claim in the report")
    parser.add_argument("--no-history", action="store_true",
                        help="do not append the outcome to health_history.jsonl")
    args = parser.parse_args(argv)

    report = args.report if args.report else default_report()
    if not os.path.exists(report):
        fail_usage(f"report not found: {report}")
    with open(report, "r", encoding="utf-8") as fh:
        text = fh.read()

    claims = extract_claims(text)
    if not claims:
        fail_usage(f"no checkable claims found in {report}")

    seed = args.seed or datetime.date.today().isoformat()
    if args.all:
        sampled = claims
    else:
        rng = random.Random(seed)
        pool = latest_claims(claims)
        sampled = rng.sample(pool, min(args.count, len(pool)))

    sys.stdout.write(f"evidence sample: {os.path.relpath(report, VAULT_ROOT)} "
                     f"(seed={seed}, {len(sampled)}/{len(claims)} claims)\n")
    rows = []
    for claim in sampled:
        row = verify_claim(claim)
        rows.append(row)
        sys.stdout.write(f"  [{row['verdict']}] L{row['line']} {row['raw']!r} "
                         f"expected={row['expected']} measured={row['measured']}\n")

    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    history_row = {
        "ts": stamp,
        "evidence_sample": {
            "report": os.path.relpath(report, VAULT_ROOT),
            "seed": seed,
            "claims_checked": len(rows),
            "passed": sum(1 for r in rows if r["verdict"] == "PASS"),
            "failed": sum(1 for r in rows if r["verdict"] == "FAIL"),
            "results": rows,
        },
    }
    if not args.no_history:
        health_composite.append_history(HISTORY_PATH, history_row)

    failed = sum(1 for r in rows if r["verdict"] in ("FAIL", "ERROR"))
    sys.stdout.write(f"verdict: {'BLOCKED' if failed else 'CLEAN'} "
                     f"({len(rows) - failed}/{len(rows)} verified)\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
