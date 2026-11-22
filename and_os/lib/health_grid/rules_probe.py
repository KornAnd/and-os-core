"""
rules_probe.py — Ring 2: Rules Corpus Integrity Gate (audit 19.11, R-5).

The Health Grid verifies code and reports, but not the rules corpus itself.
This probe closes the blind spot (audit RULES_CORPUS_AUDIT_2026-11-19):
  (a) stub footer count vs the declared registry (drift = error; >0 = warning,
      monthly DoD target is 0 per Rule #34)
  (b) no normative line shared verbatim by two rule sections (SSoT, Rule #55;
      catches the verbatim-duplicate class fixed in R-2)
  (c) numeric claims inside rules.md ("N skills", "N canonical invariants",
      "No.0-No.N" ranges) must match SSoT facts (counters are drift timers, R-3)
  (d) SYSTEM.md domain map: one rule in exactly one domain, every mapped rule
      exists, per-rule "Domain:" fields do not contradict the map
  (e) T0 rule-to-validator mapping from the registry: every always-active
      invariant has a declared machine vector (direct target must exist)
  (f) telemetry mode<->ctx calibration (Rule #9 budgets): strict from the
      declared date, earlier lines are advisory

Registry (declarative config, not code): and_os/etc/rules_probe.json
"""

import json
import os
import re
import sys
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple

from and_os.lib.health_grid import BaseProbeResult

# Rule-number tokens inside the corpus (Rule #3: ASCII-only source, so the
# Russian literals below are unicode escapes).
RULE_SECTION_RE = re.compile(r"^### \u041f\u0440\u0430\u0432\u0438\u043b\u043e \u2116(\d+(?:\.\d+)?)", re.M)
FOOTER_MARKER = "\u043a\u043e\u043d\u0442\u0435\u043d\u0442\u043d\u0430\u044f \u0437\u0430\u0434\u0430\u0447\u0430 backlog"
DOMAIN_MAP_RE = re.compile(r"\*\*\u0414\u041e\u041c\u0415\u041d ([IVX]+):[^\`]*\*\*\s*\`([^\`]+)\`")
RULE_DOMAIN_FIELD_RE = re.compile(r"\*\*\u0414\u043e\u043c\u0435\u043d:\*\* \u0414\u041e\u041c\u0415\u041d ([IVX]+)")
SKILLS_CLAIM_RE = re.compile(r"\b(\d{2,3})\s+(\u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445\s+)?\u0441\u043a\u0438\u043b\u043b(\u043e\u0432|\u0430)\b")
CANON_COUNT_RE = re.compile(r"\b(\d{2,3})\s+\u043a\u0430\u043d\u043e\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0445\s+\u0438\u043d\u0432\u0430\u0440\u0438\u0430\u043d\u0442\u043e\u0432\b")
RANGE_CLAIM_RE = re.compile(r"\u21160[\u2013\-]\s*\u2116?\s*(\d{1,2})\b")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Health Grid probe names (kept in sync with validate_system.probes).
KNOWN_PROBES = {"fs_syntax", "graph", "contract", "clean_code", "manifest",
                "skill", "runtime", "dod_gate", "bin_smoke", "rules"}

# Rule #9 context budgets: mode -> allowed telemetry ctx values.
CTX_BUDGET = {
    "WORK": {"min", "work"},
    "STRATEGIC": {"work", "full"},
    "SYSTEM": {"min", "work", "compressed"},
}


def parse_rule_sections(rules_text: str) -> Dict[str, str]:
    """Map rule number -> full section text (heading to next heading)."""
    matches = list(RULE_SECTION_RE.finditer(rules_text))
    sections: Dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(rules_text)
        sections[m.group(1)] = rules_text[m.start():end]
    return sections


def stub_sections(rules_text: str) -> List[str]:
    """Rule numbers still carrying the 2026-11-11 backlog footer."""
    found = []
    for num, body in parse_rule_sections(rules_text).items():
        if FOOTER_MARKER in body:
            found.append(num)
    return found


def _normalize(line: str) -> str:
    # Bracket tags are metadata (rule cross-references, DEV_PROTOCOL, ...),
    # not normative content: strip them all so the same wording under
    # different tags still counts as a verbatim duplicate.
    line = re.sub(r"\[[^\]]*\]", "", line)
    line = re.sub(r"\*+|`+", " ", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip(" \u2014:-\u2192\u2794")


def shared_normative_lines(rules_text: str, min_len: int = 25) -> Dict[str, List[str]]:
    """Bolded/numbered normative lines (the v5.5 invariants class) that appear
    in two or more rule sections after tag/emphasis normalization."""
    owners: Dict[str, Set[str]] = defaultdict(set)
    for num, body in parse_rule_sections(rules_text).items():
        for line in body.splitlines():
            s = line.strip()
            if s.startswith(("- \u274c", "- \u2705")) or re.match(r"^\d+\.\s*\*\*", s):
                key = _normalize(s)
                if len(key) >= min_len:
                    owners[key].add(num)
    return {k: sorted(v) for k, v in owners.items() if len(v) > 1}


def counter_claims(rules_text: str) -> List[Dict[str, Any]]:
    """Numeric SSoT claims inside rules.md: kind/value/line."""
    claims: List[Dict[str, Any]] = []
    for line_no, line in enumerate(rules_text.splitlines(), 1):
        for m in SKILLS_CLAIM_RE.finditer(line):
            claims.append({"kind": "skills", "value": int(m.group(1)), "line": line_no})
        for m in CANON_COUNT_RE.finditer(line):
            claims.append({"kind": "rules_count", "value": int(m.group(1)), "line": line_no})
        for m in RANGE_CLAIM_RE.finditer(line):
            claims.append({"kind": "rule_range", "value": int(m.group(1)), "line": line_no})
    return claims


def domain_map(system_text: str) -> Dict[str, List[str]]:
    """Rule number -> list of domain letters in the SYSTEM.md map.

    Map lines look like: "- X **<domain heading>** `<rule list>`" — the
    rule list (with the brackets) sits inside backticks, so each token is
    stripped of brackets, the No. sign, and whitespace.
    """
    rule_domains: Dict[str, List[str]] = defaultdict(list)
    for m in DOMAIN_MAP_RE.finditer(system_text):
        for token in m.group(2).split(","):
            num = token.strip().strip("[]").replace("\u2116", "").strip()
            if num:
                rule_domains[num].append(m.group(1))
    return rule_domains


def domain_conflicts(system_text: str, sections: Dict[str, str]) -> List[str]:
    """(d) double-listed rules, unknown mapped rules, field/map contradictions."""
    errors: List[str] = []
    rule_domains = domain_map(system_text)
    for num in sorted(rule_domains, key=lambda x: [int(p) for p in x.split(".")]):
        doms = rule_domains[num]
        if len(doms) > 1:
            errors.append(f"Rule No.{num} listed in {len(doms)} domains ({', '.join(doms)}) — one rule = one domain")
        if num not in sections:
            errors.append(f"Rule No.{num} in the domain map but absent from rules.md")
    for num, body in sections.items():
        fm = RULE_DOMAIN_FIELD_RE.search(body)
        if not fm:
            continue
        if num in rule_domains and fm.group(1) not in rule_domains[num]:
            errors.append(
                f"Rule No.{num} 'Domain:' field says DOM {fm.group(1)} but the map lists it in {rule_domains[num]}")
    return errors


def check_t0_mapping(registry: Dict[str, Any], vault_root: str) -> List[str]:
    """(e) every declared T0 rule has a validator entry; direct targets exist."""
    errors: List[str] = []
    t0 = registry.get("t0", {})
    rules = set(t0.get("rules", []))
    mapping = t0.get("mapping", {})
    if set(mapping) != rules:
        errors.append("T0 mapping keys differ from the declared T0 rule set: "
                      f"missing={sorted(rules - set(mapping))}, extra={sorted(set(mapping) - rules)}")
    for num in sorted(set(mapping) & rules, key=lambda x: [int(p) for p in x.split(".")]):
        entry = mapping[num]
        kind = entry.get("kind")
        if kind == "direct":
            target = entry.get("target", "")
            if target.startswith("probe:"):
                name = target.split(":", 1)[1]
                if name not in KNOWN_PROBES:
                    errors.append(f"T0 No.{num}: unknown probe target '{target}'")
            elif not os.path.exists(os.path.join(vault_root, target)):
                errors.append(f"T0 No.{num}: direct target missing on disk: {target}")
            elif not target:
                errors.append(f"T0 No.{num}: empty direct target")
        elif kind == "indirect":
            if not entry.get("via"):
                errors.append(f"T0 No.{num}: indirect entry without 'via' justification")
        else:
            errors.append(f"T0 No.{num}: unknown mapping kind '{kind}'")
    return errors


def telemetry_ctx_findings(telemetry_text: str, strict_from: str) -> Tuple[List[str], List[str]]:
    """(f) mode<->ctx calibration. Returns (strict_errors, advisory_warnings)."""
    errors: List[str] = []
    warnings: List[str] = []
    for line_no, line in enumerate(telemetry_text.splitlines(), 1):
        if not line.startswith("- "):
            continue
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) < 6 or not DATE_RE.match(parts[0]):
            continue
        date, mode, ctx = parts[0], parts[1], parts[5]
        allowed = CTX_BUDGET.get(mode)
        if allowed is None:
            continue
        if ctx in allowed:
            continue
        message = f"telemetry L{line_no} [{date} {mode}] ctx='{ctx}' outside budget {sorted(allowed)}"
        if date >= strict_from:
            errors.append(message)
        else:
            warnings.append(message + " (pre-enforcement, advisory)")
    return errors, warnings


class RulesProbe:
    """Ring 2: rules-corpus integrity (see module docstring for the checks)."""

    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 2: Rules Corpus Integrity Gate", ring=2)
        issues = 0
        registry_path = os.path.join(vault_root, "and_os", "etc", "rules_probe.json")
        try:
            with open(registry_path, "r", encoding="utf-8") as fh:
                registry = json.load(fh)
        except (OSError, ValueError) as err:
            issues += 1
            result.errors.append(f"rules_probe registry unreadable ({err}) — probe cannot validate")
            result.passed = False
            result.issues_count = issues
            return result

        rules_path = os.path.join(vault_root, ".opencode", "rules.md")
        system_path = os.path.join(vault_root, "SYSTEM.md")
        telemetry_path = os.path.join(vault_root, "and_os", "lib", "skills", "telemetry.md")
        try:
            with open(rules_path, "r", encoding="utf-8") as fh:
                rules_text = fh.read()
            with open(system_path, "r", encoding="utf-8") as fh:
                system_text = fh.read()
            with open(telemetry_path, "r", encoding="utf-8") as fh:
                telemetry_text = fh.read()
        except OSError as err:
            issues += 1
            result.errors.append(f"rules corpus input unreadable: {err}")
            result.passed = False
            result.issues_count = issues
            return result

        sections = parse_rule_sections(rules_text)

        # (a) stub registry drift
        actual_stubs = sorted(stub_sections(rules_text), key=lambda x: [int(p) for p in x.split(".")])
        declared_stubs = set(registry.get("stubs", {}).get("rules", []))
        if set(actual_stubs) != declared_stubs:
            missing = sorted(set(actual_stubs) - declared_stubs)
            extra = sorted(declared_stubs - set(actual_stubs))
            issues += 1
            result.errors.append(
                f"stub registry drift: unexpected restored={missing}, missing from disk={extra} "
                f"(actual={len(actual_stubs)}, declared={len(declared_stubs)})")
        if len(actual_stubs) > 0:
            result.warnings.append(
                f"{len(actual_stubs)} rules still carry the 2026-11-11 backlog footer "
                f"(monthly DoD per Rule #34: 0) — advisory, tracked in the registry")

        # (b) verbatim duplicate normative lines
        shared = shared_normative_lines(rules_text)
        if shared:
            for key, nums in list(shared.items())[:5]:
                issues += 1
                result.errors.append(f"normative line shared by {nums}: {key[:90]}")

        # (c) counters inside rules.md vs SSoT
        skills_dir = os.path.join(vault_root, "and_os", "lib", "skills")
        skill_count = 0
        for entry in os.listdir(skills_dir):
            if os.path.isfile(os.path.join(skills_dir, entry, "SKILL.md")):
                skill_count += 1
        max_rule = max((int(n.split(".")[0]) for n in sections), default=0)
        facts = {"skills": skill_count, "rules_count": len(sections), "rule_range": max_rule}
        for claim in counter_claims(rules_text):
            if claim["value"] != facts[claim["kind"]]:
                issues += 1
                result.errors.append(
                    f"stale counter at rules.md L{claim['line']}: '{claim['kind']}'={claim['value']}, "
                    f"SSoT fact={facts[claim['kind']]}")

        # (d) domain map integrity
        for err in domain_conflicts(system_text, sections):
            issues += 1
            result.errors.append(f"domain map: {err}")

        # (e) T0 rule-to-validator mapping
        for err in check_t0_mapping(registry, vault_root):
            issues += 1
            result.errors.append(f"T0 mapping: {err}")

        # (f) telemetry ctx calibration
        strict_from = str(registry.get("ctx_strict_from", ""))
        ctx_errors, ctx_warnings = telemetry_ctx_findings(telemetry_text, strict_from)
        for err in ctx_errors:
            issues += 1
            result.errors.append(f"ctx budget: {err}")
        result.warnings.extend(ctx_warnings)

        result.issues_count = issues
        result.passed = issues == 0
        result.details = {
            "rules_sections": len(sections),
            "stub_sections": len(actual_stubs),
            "shared_lines": len(shared),
            "counter_claims": len(counter_claims(rules_text)),
            "t0_rules": len(registry.get("t0", {}).get("rules", [])),
        }
        return result
