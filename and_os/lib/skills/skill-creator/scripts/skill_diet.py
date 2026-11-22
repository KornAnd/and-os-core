#!/usr/bin/env python3
"""
skill_diet.py — Skill Diet & Drift Auditor for AnD os.
Part of Ring 0 Meta-Skill Infrastructure (and_os/lib/skills/skill-creator/).

Three deterministic checks across the skill base:

  1. BILL: size per level (SKILL.md / references/ / scripts/) and a cost
     class. SKILL.md is the primary context cost (loaded into the
     conversation on every skill invocation); references and scripts are
     loaded on demand.
  2. DRIFT: every `and_os/...` path referenced in SKILL.md or references/
     must exist in the vault (extension-tolerant: `ROUTING` resolves to
     `ROUTING.md`, the Obsidian wikilink convention). Templates containing
     placeholders (`*`, `<...>`, `YYYY`) are skipped. A missing file inside
     an existing directory is reported as an "example path" (documentation
     example, review class); a missing directory, or a file whose parent
     directory is missing, is a hard drift finding. Every
     `sys_cli.py <subcommand>` invocation must be a registered subcommand
     (parsed from `sys_cli.py --help`, fail-closed on an incomplete parse).
  3. GROWTH: delta of the SKILL.md bill against the last diet baseline
     (state lives in and_os/var/skill_diet_baseline.json per Rule #50 —
     never inside the skill folder). Use --reset-baseline after a diet.

Bloat advisories (never fail the audit): SKILL.md above the line
threshold, description above the routing-cost threshold, duplicated
code fences.

Usage:
  python3 skill_diet.py [skills-root]
  python3 skill_diet.py --skill <name>
  python3 skill_diet.py --reset-baseline

Exit codes: 0 clean (no drift), 1 drift or unreadable skill found,
2 usage or environment error.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
DEFAULT_SKILLS_ROOT = SCRIPT_PATH.parents[2]
VAULT_ROOT = SCRIPT_PATH.parents[5]
BASELINE_FILE = VAULT_ROOT / "and_os" / "var" / "skill_diet_baseline.json"

# Cost thresholds (lines for SKILL.md, characters for description).
SKILL_MD_LINE_THRESHOLD = 120
DESCRIPTION_CHAR_THRESHOLD = 500

# Path references in the form `and_os/...`. The lookbehind rejects
# dot-prefixed names such as `~/.and_os/...` (outside the vault); the
# character class includes glob/template markers so whole template
# tokens are captured and then skipped instead of truncated.
PATH_REF_RE = re.compile(r"(?<![\w.])and_os/[A-Za-z0-9_./\-*<>]+")
SYSCLI_REF_RE = re.compile(r"\bsys_cli\.py\s+([a-z][a-z0-9_-]*)")
SKIP_NAMES = {"references", "audits", "__pycache__", ".git"}
# Tokens that mark a reference as a template/placeholder, not a real
# path (globs, bracket placeholders, date-format placeholders).
TEMPLATE_TOKENS = ("*", "<", ">", "YYYY")
# Extensions tried in order when a reference omits its file extension
# (Obsidian wikilink convention: [[path]] resolves to path.md).
EXTRA_EXTENSIONS = (".md", ".py", ".json")


def fail_usage(message: str) -> None:
    sys.stderr.write(f"[skill_diet] ERROR: {message}\n")
    sys.exit(2)


def iter_skill_dirs(skills_root: Path):
    """Yields skill directories in the skills root (templates excluded)."""
    for item in sorted(skills_root.iterdir()):
        if item.is_dir() and not item.name.startswith(".") and item.name not in SKIP_NAMES:
            yield item


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def skill_bill(skill_dir: Path) -> dict:
    """Computes the size bill per level for one skill."""
    skill_md = skill_dir / "SKILL.md"
    md_lines = len(read_text(skill_md).splitlines()) if skill_md.exists() else 0

    def level_lines(level: str) -> int:
        level_dir = skill_dir / level
        if not level_dir.is_dir():
            return 0
        total = 0
        for root, dirs, files in os.walk(level_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_NAMES]
            for name in files:
                if name.endswith((".md", ".py", ".json", ".txt")):
                    total += len(read_text(Path(root) / name).splitlines())
        return total

    ref_lines = level_lines("references")
    script_lines = level_lines("scripts")
    return {
        "skill": skill_dir.name,
        "skill_md_lines": md_lines,
        "reference_lines": ref_lines,
        "script_lines": script_lines,
        "total_lines": md_lines + ref_lines + script_lines,
    }


def description_of(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ""
    text = read_text(skill_md)
    match = re.search(r"^description:\s*[\"']?(.*?)[\"']?\s*$", text, re.MULTILINE)
    return match.group(1) if match else ""


def collect_path_refs(skill_dir: Path):
    """Collects and_os/... path references from markdown docs."""
    refs = set()
    docs = [skill_dir / "SKILL.md"]
    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        docs.extend(sorted(references_dir.rglob("*.md")))
    for path in docs:
        if not path.exists():
            continue
        for match in PATH_REF_RE.finditer(read_text(path)):
            ref = match.group(0).rstrip(".,)")
            if any(token in ref for token in TEMPLATE_TOKENS):
                continue
            refs.add(ref)
    return refs


def classify_path_ref(ref: str) -> str:
    """Classifies a vault-relative path reference.

    Returns:
      "ok"      — the path (or its extension-tolerant form) exists.
      "drift"   — a real reference to a path that does not exist:
                  a directory reference (trailing slash) is missing,
                  or a file reference whose parent directory is missing.
      "example" — a file reference whose parent directory exists:
                  documentation examples and expected-output names
                  (review class, never a drift failure).
    """
    candidate = VAULT_ROOT / ref
    if ref.endswith("/"):
        return "ok" if candidate.is_dir() else "drift"
    if candidate.exists():
        return "ok"
    if any((candidate.parent / (candidate.name + ext)).exists()
           for ext in EXTRA_EXTENSIONS):
        return "ok"
    return "example" if candidate.parent.exists() else "drift"


def _fast_path_subcommands() -> set:
    """Fast-path subsystem commands (SUBSYSTEM_MAP in cli_subsystems).

    The UNIX Git-style fast path registers these top-level commands
    outside the monolithic argparse parser, so `sys_cli.py --help`
    never lists them (C10c: false drift for `sys_cli ops` references).
    Reads the SUBSYSTEM_MAP literal — deterministic, no import side effects.
    """
    registry = VAULT_ROOT / "and_os" / "bin" / "cli_subsystems" / "__init__.py"
    if not registry.exists():
        return set()
    try:
        text = registry.read_text(encoding="utf-8")
    except OSError as err:
        sys.stderr.write(f"[skill_diet] notice reading cli_subsystems registry: {err}\n")
        return set()
    return set(re.findall(
        r'^\s*"([A-Za-z0-9-]+)"\s*:\s*\(\s*"and_os\.bin\.cli_subsystems\.',
        text, re.M))


def registered_sys_cli_subcommands() -> set:
    """Parses `sys_cli.py --help` for the registered subcommand names.

    The authoritative source is the subparser choices line that argparse
    renders as ``{cmd1,cmd2,...}``. The per-command help lines (exactly
    four-space indented) serve as a fallback. Fails closed when neither
    yields a plausible registry, so an unparseable CLI can never turn a
    real drift finding into a false negative. The fast-path subsystem
    registry (SUBSYSTEM_MAP) is merged in as the second registration plane.
    """
    sys_cli = VAULT_ROOT / "and_os" / "bin" / "sys_cli.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(sys_cli), "--help"],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        fail_usage(f"cannot parse sys_cli.py --help: {err}")
    commands = set()
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            commands = set(stripped[1:-1].split(","))
            break
    if not commands:
        in_positional = False
        for line in proc.stdout.splitlines():
            if line.strip() == "positional arguments":
                in_positional = True
                continue
            if in_positional:
                if line.startswith("    ") and not line.startswith("     "):
                    commands.add(line.strip().split(" ")[0])
                elif line.strip() and not line.startswith("  "):
                    break
    if len(commands) < 5:
        fail_usage(
            "sys_cli.py --help parse yielded "
            f"{len(commands)} subcommand(s); refusing to audit against "
            "an incomplete subcommand registry")
    return commands | _fast_path_subcommands()


def collect_sys_cli_refs(skill_dir: Path) -> set:
    """Collects `sys_cli.py <sub>` references from markdown docs."""
    refs = set()
    docs = [skill_dir / "SKILL.md"]
    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        docs.extend(sorted(references_dir.rglob("*.md")))
    for path in docs:
        if not path.exists():
            continue
        for match in SYSCLI_REF_RE.finditer(read_text(path)):
            refs.add(match.group(1))
    return refs


def duplicated_fences(skill_dir: Path) -> int:
    """Counts duplicated non-trivial code fences in SKILL.md (bloat signal)."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return 0
    fences = re.findall(r"```[a-z]*\n(.*?)```", read_text(skill_md), re.DOTALL)
    seen = set()
    dups = 0
    for fence in fences:
        body = fence.strip()
        if len(body) < 20:
            continue
        if body in seen:
            dups += 1
        seen.add(body)
    return dups


def load_baseline() -> dict:
    if not BASELINE_FILE.exists():
        return {}
    try:
        return json.loads(read_text(BASELINE_FILE))
    except json.JSONDecodeError as err:
        sys.stderr.write(f"[skill_diet] WARNING: unreadable baseline, ignoring: {err}\n")
        return {}


def save_baseline(bills: list) -> None:
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {name: bill["skill_md_lines"] for name, bill in
               ((b["skill"], b) for b in bills)}
    BASELINE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True),
                             encoding="utf-8")


def audit_skill(skill_dir: Path, subcommands: set, baseline: dict) -> dict:
    """Runs bill + drift + growth + bloat checks for one skill."""
    bill = skill_bill(skill_dir)
    path_refs = collect_path_refs(skill_dir)
    missing_paths = []
    example_paths = []
    for ref in path_refs:
        kind = classify_path_ref(ref)
        if kind == "drift":
            missing_paths.append(ref)
        elif kind == "example":
            example_paths.append(ref)
    missing_paths.sort()
    example_paths.sort()
    cli_refs = collect_sys_cli_refs(skill_dir)
    unknown_cmds = sorted(c for c in cli_refs if c not in subcommands)

    growth = None
    if skill_dir.name in baseline:
        growth = bill["skill_md_lines"] - baseline[skill_dir.name]

    advisories = []
    if bill["skill_md_lines"] > SKILL_MD_LINE_THRESHOLD:
        advisories.append(
            f"SKILL.md {bill['skill_md_lines']} lines > {SKILL_MD_LINE_THRESHOLD} "
            f"(offload detail to references/)")
    desc_len = len(description_of(skill_dir))
    if desc_len > DESCRIPTION_CHAR_THRESHOLD:
        advisories.append(
            f"description {desc_len} chars > {DESCRIPTION_CHAR_THRESHOLD} "
            f"(routing cost)")
    dups = duplicated_fences(skill_dir)
    if dups:
        advisories.append(f"{dups} duplicated code fence(s) in SKILL.md")

    bill["missing_paths"] = missing_paths
    bill["example_paths"] = example_paths
    bill["unknown_subcommands"] = unknown_cmds
    bill["growth_since_baseline"] = growth
    bill["advisories"] = advisories
    return bill


def print_report(bills: list) -> None:
    sys.stdout.write("\n" + "=" * 66 + "\n")
    sys.stdout.write("🥗 Skill Diet & Drift Auditor (skill-creator v1.1)\n")
    sys.stdout.write("=" * 66 + "\n")
    header = (f"{'skill':<28} {'SKILL.md':>8} {'refs':>6} {'scripts':>8} "
              f"{'Δbase':>6}")
    sys.stdout.write(header + "\n" + "-" * len(header) + "\n")
    for bill in bills:
        growth = bill["growth_since_baseline"]
        growth_s = "n/a" if growth is None else f"{growth:+d}"
        sys.stdout.write(
            f"{bill['skill']:<28} {bill['skill_md_lines']:>8} "
            f"{bill['reference_lines']:>6} {bill['script_lines']:>8} "
            f"{growth_s:>6}\n")
    sys.stdout.write("-" * len(header) + "\n")
    for bill in bills:
        if bill["missing_paths"]:
            sys.stdout.write(f"❌ {bill['skill']}: drifted paths:\n")
            for ref in bill["missing_paths"]:
                sys.stdout.write(f"   • {ref}\n")
        if bill["example_paths"]:
            sys.stdout.write(f"🟡 {bill['skill']}: example paths "
                             "(file absent, parent dir exists — likely doc examples):\n")
            for ref in bill["example_paths"]:
                sys.stdout.write(f"   • {ref}\n")
        if bill["unknown_subcommands"]:
            sys.stdout.write(f"❌ {bill['skill']}: unknown sys_cli subcommands: "
                             f"{', '.join(bill['unknown_subcommands'])}\n")
        for advisory in bill["advisories"]:
            sys.stdout.write(f"🟡 {bill['skill']}: {advisory}\n")
    drift = sum(len(b["missing_paths"]) + len(b["unknown_subcommands"])
                for b in bills)
    examples = sum(len(b["example_paths"]) for b in bills)
    advisory = sum(len(b["advisories"]) for b in bills)
    sys.stdout.write(f"\nSUMMARY: {len(bills)} skills | drift findings: {drift} "
                     f"| bloat advisories: {advisory} | example paths: {examples}\n")
    sys.stdout.write("=" * 66 + "\n")


def main(argv) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("target", nargs="?", default=None,
                        help="skills root dir (default: the skills root "
                             "this script lives in)")
    parser.add_argument("--skill", help="audit a single skill by name")
    parser.add_argument("--reset-baseline", action="store_true",
                        help="save the current SKILL.md bills as the baseline")
    args = parser.parse_args(argv)

    if args.skill and args.target:
        fail_usage("--skill takes a name; positional argument must be a dir")
    skills_root = (Path(args.target).resolve() if args.target
                   else DEFAULT_SKILLS_ROOT)
    if not skills_root.is_dir():
        fail_usage(f"skills root is not a directory: {skills_root}")

    skill_dirs = list(iter_skill_dirs(skills_root))
    if args.skill:
        skill_dirs = [d for d in skill_dirs if d.name == args.skill]
        if not skill_dirs:
            fail_usage(f"skill not found: {args.skill}")

    bills = [audit_skill(d, set(), {}) for d in skill_dirs]
    if args.reset_baseline:
        save_baseline(bills)
        sys.stdout.write(f"✅ Baseline saved for {len(bills)} skill(s) "
                         f"-> {BASELINE_FILE}\n")
        return 0

    subcommands = registered_sys_cli_subcommands()
    baseline = load_baseline()
    bills = [audit_skill(d, subcommands, baseline) for d in skill_dirs]
    print_report(bills)
    drift = sum(len(b["missing_paths"]) + len(b["unknown_subcommands"])
                for b in bills)
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
