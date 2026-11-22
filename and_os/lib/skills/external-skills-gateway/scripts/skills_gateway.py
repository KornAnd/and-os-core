#!/usr/bin/env python3
"""
skills_gateway.py — External Agent Skills Discovery & Inspection Engine.
Part of AnD os External Skills Gateway (and_os/lib/skills/external-skills-gateway/).

Features:
  - Zero External Dependencies: Pure Python 3 stdlib (urllib, json).
  - Search skills via GitHub API & skills.sh open registry.
  - Ephemeral inspect: fetch raw SKILL.md for review without installing.
  - Anti-Slop Sanitize: automatically checks fetched content against ANTI_SLOP_STANDARD.md.
  - Security Vet (D5, 17.11): runs the security_scan SSoT (S1-S9 + 18 PI
    rule IDs) on a fetched SKILL.md before any register-skill step.
"""

import importlib.util
import os
import sys
import json
import tempfile
import urllib.request
import urllib.error
import urllib.parse
import argparse
from typing import List, Dict, Any, Optional, Tuple

# Five levels up: scripts/ -> external-skills-gateway/ -> skills/ -> lib/
# -> and_os/ -> Vault root. (D5, 17.11: the old 4-level value pointed at
# and_os/ itself, which made every derived absolute path double the
# "and_os" segment.)
VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
ANTI_SLOP_SPEC = os.path.join(VAULT_ROOT, "and_os/docs/specs/ANTI_SLOP_STANDARD.md")
SECURITY_SCAN_SCRIPT = os.path.join(
    VAULT_ROOT, "and_os", "lib", "skills", "system-audit",
    "scripts", "security_scan.py")

# D5 (17.11): import gate classification. BLOCK = payload/exfil classes
# that must never reach a registered skill (exit 1). WARN = hardening
# signals a human must see before adopting, but pinnable/fixable
# (exit 0 with a visible flag).
BLOCKING_PREFIXES = ("S1", "PI-SECRET")
BLOCKING_EXACT = {
    "PI-SANDBOX-BYPASS",   # curl|sh, bash<(, cd $( — remote code execution
    "PI-TOOLS",            # EchoLeak-class: action tools + untrusted ingestion
    "PI-LEAKPHRASE",       # direct prompt-injection phrases
    "PI-ANSI-INJECT",      # raw control bytes, never in a clean doc
}


def _load_security_scan():
    """Loads the security_scan SSoT module (stage-1 scanner)."""
    if not os.path.exists(SECURITY_SCAN_SCRIPT):
        raise FileNotFoundError(
            f"security_scan SSoT not found: {SECURITY_SCAN_SCRIPT}")
    spec = importlib.util.spec_from_file_location("security_scan_gateway",
                                                  SECURITY_SCAN_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def security_scan_skill(content: str) -> Tuple[List[tuple], List[tuple]]:
    """Runs the full security_scan SSoT over fetched skill content.

    The content is written to a temporary SKILL.md (the absence rules
    apply to SKILL.md instruction docs only) and scanned in place; the
    temp file is removed in all paths. Returns (blocking, advisory).
    Raises FileNotFoundError if the SSoT scanner is unavailable,
    OSError on temp-file failure — the gate fails closed.
    """
    scanner = _load_security_scan()
    tmp_dir = tempfile.mkdtemp(prefix="skills_gateway_vet_")
    tmp_path = os.path.join(tmp_dir, "SKILL.md")
    try:
        with open(tmp_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        findings = []
        scanner.scan_file(tmp_path, findings)
    finally:
        for name in os.listdir(tmp_dir):
            os.remove(os.path.join(tmp_dir, name))
        os.rmdir(tmp_dir)

    blocking = [f for f in findings
                if f[2].startswith(BLOCKING_PREFIXES)
                or f[2] in BLOCKING_EXACT]
    advisory = [f for f in findings
                if not (f[2].startswith(BLOCKING_PREFIXES)
                        or f[2] in BLOCKING_EXACT)]
    return blocking, advisory


def search_github_skills(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for agent skills across GitHub repositories."""
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}+in:name,description+skill&per_page={limit}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AnD-os-SkillsGateway/8.3"}
    )
    results = []
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("items", []):
                results.append({
                    "name": item.get("name"),
                    "full_name": item.get("full_name"),
                    "description": item.get("description") or "No description",
                    "url": item.get("html_url"),
                    "stars": item.get("stargazers_count", 0)
                })
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as err:
        sys.stderr.write(f"[skills_gateway] Search warning: {err}\n")
    return results


def fetch_skill_raw(repo_or_url: str, branch: str = "main") -> Optional[str]:
    """Fetch raw SKILL.md from a GitHub repository."""
    if repo_or_url.startswith("http"):
        # Direct raw link
        url = repo_or_url
    else:
        # User/repo shorthand
        repo = repo_or_url.strip("/")
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/SKILL.md"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AnD-os-SkillsGateway/8.3"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as he:
        if he.code == 404 and branch == "main":
            return fetch_skill_raw(repo_or_url, branch="master")
        sys.stderr.write(f"[skills_gateway] HTTP error {he.code} fetching {url}\n")
        return None
    except (urllib.error.URLError, OSError) as err:
        sys.stderr.write(f"[skills_gateway] Network error: {err}\n")
        return None


def print_security_section(blocking: List[tuple], advisory: List[tuple]) -> None:
    """Prints the D5 vet section; shared by inspect and vet."""
    print("\n" + "=" * 60)
    print("🔒 SECURITY VET (security_scan SSoT, D5 17.11)")
    print("=" * 60)
    for _path, line_no, label, context in blocking:
        print(f"  🔴 BLOCK  [{label}] line {line_no}: {context}")
    for _path, line_no, label, context in advisory:
        print(f"  🟡 ADVISORY [{label}] line {line_no}: {context}")
    if not blocking and not advisory:
        print("  🟢 clean: no deterministic findings")
    elif not blocking:
        print(f"  ⚠️ {len(advisory)} advisory finding(s): fix or justify before adoption")
    else:
        print(f"  ⛔ {len(blocking)} blocking finding(s): DO NOT register this skill")


def inspect_skill(repo: str) -> None:
    """Inspect and format raw skill content for ephemeral agent use."""
    content = fetch_skill_raw(repo)
    if not content:
        print(f"⚪ Could not locate SKILL.md in repository '{repo}'.")
        return

    print("=" * 60)
    print(f"📦 EPHEMERAL INSPECT: {repo}")
    print("=" * 60)
    lines = content.splitlines()
    print("\n".join(lines[:60]))
    if len(lines) > 60:
        print(f"\n... [Truncated {len(lines) - 60} lines. Fetch full content via script if required] ...")
    try:
        blocking, advisory = security_scan_skill(content)
    except (FileNotFoundError, OSError) as err:
        print(f"\n⛔ SECURITY VET unavailable — fail closed: {err}")
        return
    print_security_section(blocking, advisory)


def vet_skill(repo: str) -> int:
    """D5 import gate: fetch + full security scan before register-skill.

    Returns the process exit code: 0 = clean or advisory-only,
    1 = blocking findings (or the skill could not be fetched).
    """
    content = fetch_skill_raw(repo)
    if not content:
        print(f"⛔ Could not locate SKILL.md in repository '{repo}' — vet FAILED (unverifiable).")
        return 1
    try:
        blocking, advisory = security_scan_skill(content)
    except (FileNotFoundError, OSError) as err:
        print(f"⛔ SECURITY VET unavailable — fail closed: {err}")
        return 1

    print("=" * 60)
    print(f"🔎 SECURITY VET: {repo}")
    print("=" * 60)
    print_security_section(blocking, advisory)
    if blocking:
        print("\nVERDICT: FAIL — blocking findings; do not register.")
        return 1
    if advisory:
        print("\nVERDICT: PASS WITH ADVISORIES — review before register-skill.")
    else:
        print("\nVERDICT: PASS — no deterministic findings.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="External Agent Skills Gateway (AnD os v1.2.0)")
    subparsers = parser.add_subparsers(dest="command")

    p_search = subparsers.add_parser("search", help="Search open skills repository")
    p_search.add_argument("query", type=str, help="Search query (e.g. 'ffmpeg', 'react', 'git')")
    p_search.add_argument("--limit", type=int, default=5, help="Result limit")

    p_inspect = subparsers.add_parser("inspect", help="Fetch and inspect a skill without installing")
    p_inspect.add_argument("repo", type=str, help="Repository 'owner/repo' or raw URL")

    p_vet = subparsers.add_parser(
        "vet", help="D5 import gate: security_scan SSoT before register-skill")
    p_vet.add_argument("repo", type=str, help="Repository 'owner/repo' or raw URL")

    args = parser.parse_args()

    if args.command == "search":
        items = search_github_skills(args.query, limit=args.limit)
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0
    if args.command == "inspect":
        inspect_skill(args.repo)
        return 0
    if args.command == "vet":
        return vet_skill(args.repo)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
