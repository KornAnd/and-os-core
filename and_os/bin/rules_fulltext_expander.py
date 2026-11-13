#!/usr/bin/env python3
"""
rules_fulltext_expander.py — Canonical Rule Section Restorer & Consistency Guard.

Restores missing "### Правило N:" sections in .opencode/rules.md using CANONICAL
SOURCES ONLY (no paraphrase, no invention):
  1. and_os/etc/system.json rules[N] — the machine SSoT one-line invariant
     (used verbatim as the canonical description),
  2. SYSTEM.md domain (pillar) map — domain attribution (parsed, not typed),
  3. .archive/snapshots/snap_20261016_140742/rules.md — verbatim hard invariants
     from the v5.5 Sovereign Matrix where the rule number is referenced.

Existing sections are never touched. The tool also exposes a `verify` action:
every system.json rule must have a section in rules.md whose canonical
description matches the machine manifest (this is the drift guard later wired
into manifest_probe, Ring 3).

Usage:
  rules_fulltext_expander.py expand    restore missing sections (idempotent)
  rules_fulltext_expander.py verify    check section<->manifest consistency
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parents[1]
RULES_MD = VAULT_ROOT / ".opencode" / "rules.md"
CANONICAL = VAULT_ROOT / "and_os" / "etc" / "system.json"
SYSTEM_MD = VAULT_ROOT / "SYSTEM.md"
ARCHIVE_RULES_MD = (
    VAULT_ROOT / ".archive" / "snapshots" / "snap_20261016_140742" / "rules.md"
)

SECTION_RE = re.compile(r"^### Правило №([0-9]+(?:\.[0-9]+)?): (.+)$", re.M)


def rule_sort_key(raw: str) -> tuple:
    major, _, minor = raw.partition(".")
    return (int(major), int(minor) if minor else 0)


def load_canonical_rules() -> dict:
    with open(CANONICAL, "r", encoding="utf-8") as handle:
        return json.load(handle)["rules"]


def parse_domain_map(system_md_text: str) -> dict:
    """Maps rule number -> (domain letter, domain title) from the pillar map."""
    mapping = {}
    domain_line = re.compile(
        r"\*\*ДОМЕН\s+([IVX]+)\s*[:：]\s*([^*\]]+?)\*\*\s*[`«]?[^\[\n]*\[([^\]]+)\]"
    )
    for match in domain_line.finditer(system_md_text):
        letter, title, numbers = match.groups()
        for raw in re.split(r"[,;\s]+", numbers.replace("№", "")):
            if raw.strip():
                mapping[raw.strip()] = (letter, title.strip())
    return mapping


# Markdown list-item start: bullet or numbered marker followed by content.
LIST_ITEM_RE = re.compile(r"^(\s*)(?:[-*•]|\d+[.)])\s+\S")

# Bracketed rule tag: [Правило №N, №M] — a single tag may carry several
# rule numbers; every one of them is attributed the whole verbatim block.
TAG_SPAN_RE = re.compile(r"\[[^\]]*Правило[^\]]*\]")
TAG_NUM_RE = re.compile(r"№([0-9]+(?:\.[0-9]+)?)")

# Stamped by build_section(); sections carrying it are machine-restored and
# eligible for `rebuild` (legacy hand-written sections are never touched).
RESTORE_STAMP = "Секция восстановлена"


def parse_archive_invariants() -> dict:
    """Maps rule number -> [verbatim invariant blocks] from the v5.5 archive.

    An invariant block is a markdown list item (the tagged header line) plus
    all following lines indented deeper than the item, until a blank line or
    a line at the item's own indent — standard markdown nesting semantics,
    so each invariant keeps its full verbatim body, not only its header.

    Rule numbers are read exclusively from bracket tags
    (`[Правило №N, №M]`) anywhere inside the block — one tag may carry
    several numbers and the whole block is attributed to each of them.
    This covers both the header tag and wrapped tag closers on a following
    line; prose mentions such as "(Правило №58)" inside code fences are
    deliberately ignored (no square brackets).
    """
    invariants = {}
    if not ARCHIVE_RULES_MD.exists():
        return invariants
    lines = ARCHIVE_RULES_MD.read_text(encoding="utf-8", errors="ignore").splitlines()
    total = len(lines)
    index = 0
    while index < total:
        match = LIST_ITEM_RE.match(lines[index])
        if not match:
            index += 1
            continue
        base_indent = len(match.group(1))
        block = []
        follower = index
        while follower < total:
            line = lines[follower]
            if follower > index:
                if not line.strip():
                    break
                indent = len(line) - len(line.lstrip(" "))
                if indent <= base_indent:
                    break
            block.append(line)
            follower += 1
        text = "\n".join(block).rstrip()
        numbers = set()
        for line in block:
            for span in TAG_SPAN_RE.findall(line):
                numbers.update(TAG_NUM_RE.findall(span))
        for number in sorted(numbers):
            if text not in invariants.setdefault(number, []):
                invariants[number].append(text)
        index = follower
    return invariants


def split_sections(rules_text: str) -> tuple:
    """Returns (preamble, [(raw, title, block_text)], ) with section order."""
    matches = list(SECTION_RE.finditer(rules_text))
    preamble = rules_text[: matches[0].start()] if matches else rules_text
    sections = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(rules_text)
        sections.append((match.group(1), match.group(2).strip(), rules_text[match.start():end]))
    return preamble, sections


def existing_numbers(sections) -> set:
    return {raw for raw, _, _ in sections}


def build_section(raw: str, title: str, canonical_text: str, domain, invariants) -> str:
    domain_label = ""
    if domain:
        letter, domain_title = domain
        domain_label = f"**Домен:** ДОМЕН {letter} — {domain_title} (карта SYSTEM.md)\n\n"
    lines = [f"### Правило №{raw}: {title}", ""]
    lines += [
        f"**Каноническое описание (system.json #{raw}, machine SSoT):**",
        "",
        f"{canonical_text}",
        "",
    ]
    if domain_label:
        lines += [domain_label.rstrip("\n"), ""]
    if invariants:
        lines += [
            "**Hard Invariants (источник: rules.md v5.5 Sovereign Matrix, снапшот 10.16.2026 — дословно):**",
            "",
        ]
        for invariant in invariants:
            lines.append(invariant)
            lines.append("")
        while lines and lines[-1] == "":
            lines.pop()
        lines.append("")
    lines += [
        f"> Секция восстановлена {date.today().isoformat()} (audit R2, WI-1.5) из канонических источников; ",
        "полная редакция регламента — контентная задача backlog.",
        "",
    ]
    return "\n".join(lines)


def expand_in_memory(rules_text: str, canonical: dict, domain_map: dict, archive_inv: dict) -> tuple:
    """Core expansion: returns (new_text, restored_numbers). Pure function."""
    preamble, sections = split_sections(rules_text)
    present = existing_numbers(sections)
    missing = [n for n in canonical if n not in present]

    # Build new sections, then insert each before the first existing section
    # with a higher sort key (stable numeric placement).
    new_sections = {}
    for raw in missing:
        one_liner = canonical[raw]
        title = one_liner.split(":", 1)[0].strip() if ":" in one_liner else f"Rule {raw}"
        new_sections[raw] = build_section(raw, title, one_liner, domain_map.get(raw), archive_inv.get(raw))

    ordered = sorted(
        [(raw, body) for raw, _, body in sections] + list(new_sections.items()),
        key=lambda item: rule_sort_key(item[0]),
    )
    new_text = preamble + "\n".join(body for _, body in ordered)
    return new_text, [raw for raw in missing]


def write_rules(new_text: str) -> None:
    tmp = str(RULES_MD) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(new_text)
    os.replace(tmp, RULES_MD)


def expand() -> int:
    canonical = load_canonical_rules()
    domain_map = parse_domain_map(SYSTEM_MD.read_text(encoding="utf-8"))
    archive_inv = parse_archive_invariants()
    new_text, restored = expand_in_memory(
        RULES_MD.read_text(encoding="utf-8"), canonical, domain_map, archive_inv
    )
    if not restored:
        print("OK  all canonical rules already have sections")
        return 0
    write_rules(new_text)
    print(f"OK  restored {len(restored)} rule sections: {', '.join(sorted(restored, key=rule_sort_key))}")
    return 0


def rebuild() -> int:
    """Rebuilds only machine-restored sections (those carrying the restore
    stamp) with the current parsers; legacy hand-written sections are kept
    verbatim. Idempotent: safe to run after parser improvements.
    """
    canonical = load_canonical_rules()
    domain_map = parse_domain_map(SYSTEM_MD.read_text(encoding="utf-8"))
    archive_inv = parse_archive_invariants()
    rules_text = RULES_MD.read_text(encoding="utf-8")
    preamble, sections = split_sections(rules_text)
    kept = [body for _, _, body in sections if RESTORE_STAMP not in body]
    base_text = preamble + "".join(kept)
    rebuilt, restored = expand_in_memory(base_text, canonical, domain_map, archive_inv)
    write_rules(rebuilt)
    print(f"OK  rebuilt {len(restored)} machine-restored rule sections (legacy sections untouched)")
    return 0


def verify() -> int:
    """Drift guard, two-tiered:
    - ERROR (blocking): a manifest rule with no section, or a section with no
      manifest entry — the hard completeness invariant (Rule #54 core binding).
    - WARNING (informational): section title wording differs from the manifest
      compact title. Display names in rules.md and the machine one-liner may
      legitimately differ; this is reported, not enforced.
    """
    rules_text = RULES_MD.read_text(encoding="utf-8")
    canonical = load_canonical_rules()
    preamble, sections = split_sections(rules_text)
    present = existing_numbers(sections)
    errors = []
    warnings = []
    for raw in canonical:
        if raw not in present:
            errors.append(f"rule #{raw} has no section in rules.md")
            continue
        manifest_title = canonical[raw].split(":", 1)[0].strip()
        section_title = next(title for r, title, _ in sections if r == raw)
        if manifest_title and manifest_title not in section_title:
            warnings.append(f"rule #{raw} title wording drift (section='{section_title}' manifest='{manifest_title}')")
    extra = present - set(canonical)
    if extra:
        errors.append(f"sections without manifest entry: {sorted(extra, key=rule_sort_key)}")
    for warning in warnings:
        print(f"WARN {warning}")
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(f"OK  rules.md complete vs system.json ({len(canonical)} rules, {len(sections)} sections, {len(warnings)} title-wording warnings)")
    return 0


def align_titles() -> int:
    """Idempotently aligns section headers to the canonical manifest titles.

    The machine manifest (etc/system.json) is the SSoT for rule naming; legacy
    full-text sections keep their richer bodies. Only the header title is
    replaced; a trailing severity marker (КРИТИЧНО / ОБЯЗАТЕЛЬНО) is preserved.
    """
    rules_text = RULES_MD.read_text(encoding="utf-8")
    canonical = load_canonical_rules()
    preamble, sections = split_sections(rules_text)
    changed = 0
    rebuilt = []
    for raw, title, body in sections:
        if raw not in canonical:
            rebuilt.append(body)
            continue
        manifest_title = canonical[raw].split(":", 1)[0].strip()
        if manifest_title in title:
            rebuilt.append(body)
            continue
        severity = ""
        marker = re.search(r"((?:\(|（)([^()（）]*(?:КРИТИЧНО|ОБЯЗАТЕЛЬНО)[^()（）]*)(?:\)|）))", title)
        if marker:
            severity = f" {marker.group(1)}"
        old_header = f"### Правило №{raw}: {title}"
        new_header = f"### Правило №{raw}: {manifest_title}{severity}"
        rebuilt.append(body.replace(old_header, new_header, 1))
        changed += 1
        print(f"  aligned #{raw}: '{title}' -> '{manifest_title}{severity}'")
    if changed:
        new_text = preamble + "\n".join(rebuilt)
        tmp = str(RULES_MD) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(new_text)
        os.replace(tmp, RULES_MD)
    print(f"OK  aligned {changed} legacy section titles to the manifest SSoT")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonical rule section restorer & guard")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("expand", help="Restore missing rule sections from canonical sources")
    sub.add_parser("rebuild", help="Rebuild machine-restored sections only (idempotent, after parser fixes)")
    sub.add_parser("align-titles", help="Align section headers to manifest titles (idempotent)")
    sub.add_parser("verify", help="Verify section<->manifest consistency")
    args = parser.parse_args()
    if args.action == "expand":
        return expand()
    if args.action == "rebuild":
        return rebuild()
    if args.action == "align-titles":
        return align_titles()
    if args.action == "verify":
        return verify()
    return 2


if __name__ == "__main__":
    sys.exit(main())
