#!/usr/bin/env python3
"""
telemetry_logger.py — telemetry journal writer (Rule #11, IPC Bus).

Appends validated records to and_os/lib/skills/telemetry.md without
loading the whole file into the LLM context.

Canonical task row (11 fields, contract: system-audit/references/metrics.md):
  - DATE | MODE | skill | task | route(ok|manual) | ctx | iter | rework | result(new|reused) | K(+|-) | D(+|-)

Auto-invocation rows (CLI invocations, not significant tasks) carry one
extra trailing field:
  ... | invoke
and are excluded from the task metrics (metrics 1-4, 7, 11) by the
system-audit pipeline.

Legacy alias values for --result (success, fail, completed, deployed,
done, ok) normalize to "new" and force the invoke marker, so the
pre-R5 auto callers (sys_cli auto_log_telemetry, closed_loop
telemetry_guard) keep working unchanged (Audit R5, decision R1,
2026-11-16: the old template hardcoded iter/rework/result/K and put
the result text into the route column).

Usage:
  python3 telemetry_logger.py --task "Task name" --mode SYSTEM --skill "system-audit" \
      --ctx work --route ok --result new --k + --d -
"""

import argparse
import fcntl
import json
import os
import sys
sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.
from datetime import datetime
from pathlib import Path

_vroot = str(Path(__file__).resolve().parents[2])
if _vroot not in sys.path:
    sys.path.insert(0, _vroot)
from and_os.lib.core.vault_safe_io import VaultSafeIOError, vault_safe_write

VAULT_ROOT = _vroot
TELEMETRY_PATH = os.path.join(VAULT_ROOT, "and_os", "lib", "skills", "telemetry.md")
LOCK_PATH = os.path.join(VAULT_ROOT, "and_os", "var", "locks", "telemetry.lock")
FOOTER = "[[and_os/lib/skills/CONTEXT|← Наверх]]"
# Canonical footer is path-qualified (audit 17.11 stage B): a bare
# '[[CONTEXT|...]]' is ambiguous in the graph (63 CONTEXT.md files share
# the name) and renders as an unresolved link in Obsidian. The legacy
# bare variant is still recognized so a journal that predates this change
# is migrated to the canonical form on the next append.
_FOOTER_VARIANTS = (FOOTER, "[[CONTEXT|← Наверх]]")

MODES = ("QUICK", "WORK", "STRATEGIC", "SYSTEM")
CTX_LEVELS = ("min", "work", "full", "compressed")
ROUTES = ("ok", "manual")
RESULTS = ("new", "reused")
FLAGS = ("+", "-")
KINDS = ("task", "invoke")
LEGACY_RESULTS = {"success", "fail", "completed", "deployed", "done", "ok"}
# 18.11 R8 (F8): pre-contract journals wrote result text into the route
# column (4 345 of 6 325 historical rows carry route="success"). The
# routing information those rows actually had was "the router picked the
# primary skill" — the documented meaning of "ok". Normalize on the way
# in (build_row) and offer the same mapping as a journal migration.
LEGACY_ROUTES = {"success": "ok", "route(ok)": "ok", "route=ok": "ok"}


def _normalize_result(result: str, kind):
    """Map pre-R5 legacy result values onto the documented enum.

    Legacy auto callers pass free-form status text ('success', ...);
    such rows are invocation rows, never task rows.
    """
    if result in RESULTS:
        return result, kind
    if result in LEGACY_RESULTS:
        return "new", ("invoke" if kind is None else kind)
    raise ValueError(
        "invalid --result %r: expected one of %s (legacy aliases: %s)"
        % (result, ", ".join(RESULTS), ", ".join(sorted(LEGACY_RESULTS)))
    )


def normalize_route(route: str) -> str:
    """Map pre-contract route spellings onto the ok/manual enum."""
    return LEGACY_ROUTES.get(route, route)


def normalize_journal_rows(content: str) -> tuple:
    """Migrate a journal to the route enum, column by column.

    Only touches the route field (column 5) of data rows whose value is
    exactly a known legacy spelling. Corrupted rows (shifted columns) and
    the YYYY-MM-DD format example are left byte-identical.

    Returns (new_content, changed_rows).
    """
    out = []
    changed = 0
    for line in content.splitlines():
        if line.startswith("- ") and line.count(" | ") >= 9:
            head, sep, rest = line[2:].partition(" | ")
            if head[0:4].isdigit():  # a data row (date first), not the example
                parts = rest.split(" | ")
                if len(parts) >= 4 and parts[3] in LEGACY_ROUTES:
                    parts[3] = LEGACY_ROUTES[parts[3]]
                    # NB: the leading "- " is the list bullet, not a column.
                    line = f"- {head} | " + " | ".join(parts)
                    changed += 1
        out.append(line)
    return "\n".join(out) + ("\n" if content.endswith("\n") else ""), changed


def build_row(task, mode, skill, ctx, route, iter_n, rework, result, k, d, kind) -> str:
    route = normalize_route(route)
    if mode not in MODES:
        raise ValueError("invalid mode %r" % mode)
    if ctx not in CTX_LEVELS:
        raise ValueError("invalid ctx %r" % ctx)
    if route not in ROUTES:
        raise ValueError("invalid route %r" % route)
    if k not in FLAGS or d not in FLAGS:
        raise ValueError("K/D must be '+' or '-'")
    if kind not in (None, *KINDS):
        raise ValueError("invalid kind %r" % kind)
    if iter_n < 1 or rework < 0:
        raise ValueError("iter >= 1 and rework >= 0 required")
    line = (
        f"- {datetime.now():%Y-%m-%d} | {mode} | {skill} | {task} | {route} | {ctx}"
        f" | {iter_n} | {rework} | {result} | {k} | {d}"
    )
    if kind is not None:
        line += f" | {kind}"
    return line + "\n"


def _insert_row(content: str, row: str) -> str:
    """Insert a validated row before the footer (17.11 hardening).

    Self-heals rows a pre-fix appender left below the footer: the
    orphaned '- ' lines are moved back above the canonical footer, and
    a fully-qualified footer variant is normalized to the canonical
    form. Fails closed on any unexpected non-row content after the
    footer (never corrupts the journal silently).
    """
    for variant in _FOOTER_VARIANTS:
        if variant not in content:
            continue
        head, tail = content.rsplit(variant, 1)
        tail_lines = [l for l in tail.splitlines() if l.strip()]
        orphans = [l for l in tail_lines if l.startswith("- ")]
        junk = [l for l in tail_lines if not l.startswith("- ")]
        if junk:
            raise ValueError(
                "unexpected content after the telemetry footer: %r" % junk[:3])
        healed = head + "".join(l + "\n" for l in orphans)
        return healed + row + FOOTER + "\n"
    # No footer at all: append at the end; the live-journal shape test
    # flags the missing footer, so the loss cannot stay silent.
    return content + row


def log_telemetry(task, mode, skill, ctx="min", route="ok", iter_n=1, rework=0,
                  result="new", k="-", d="-", kind=None) -> str:
    """Validate, append and persist one telemetry row. Returns the row.

    Raises ValueError on schema violation, VaultSafeIOError on a failed
    safe write, OSError on I/O failure. Never swallows errors.
    """
    result, kind = _normalize_result(result, kind)
    row = build_row(task, mode, skill, ctx, route, iter_n, rework, result, k, d, kind)

    # Exclusive flock around the read-modify-write: concurrent CLI
    # invocations must not lose each other's rows (same pattern as
    # vfs/context_projector.py owner lock).
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    with open(LOCK_PATH, "w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            content = Path(TELEMETRY_PATH).read_text(encoding="utf-8")
            new_content = _insert_row(content, row)
            vault_safe_write(TELEMETRY_PATH, new_content, validate=True)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Telemetry journal writer (Rule #11)")
    parser.add_argument("--task", type=str, required=True, help="The task description")
    parser.add_argument("--mode", type=str, choices=MODES, default="WORK")
    parser.add_argument("--skill", type=str, required=True, help="The primary skill / module used")
    parser.add_argument("--ctx", type=str, choices=CTX_LEVELS, default="min")
    parser.add_argument("--route", type=str, default="ok",
                        help="ok = the router picked the right primary skill; "
                             "legacy spellings (success, route=ok) normalize to ok")
    parser.add_argument("--iter", dest="iter_n", type=int, default=1)
    parser.add_argument("--rework", type=int, default=0)
    parser.add_argument("--result", type=str, default="new", help="new | reused (legacy aliases map to an invoke row)")
    parser.add_argument("--k", type=str, choices=FLAGS, default="-",
                        help="+ only when knowledge was actually promoted")
    parser.add_argument("--d", type=str, choices=FLAGS, default="-",
                        help="+ only when a decision-log entry was created")
    parser.add_argument("--kind", type=str, choices=KINDS, default=None,
                        help="task | invoke (legacy --result values force invoke)")
    args = parser.parse_args()

    try:
        row = log_telemetry(
            task=args.task, mode=args.mode, skill=args.skill, ctx=args.ctx,
            route=args.route, iter_n=args.iter_n, rework=args.rework,
            result=args.result, k=args.k, d=args.d, kind=args.kind,
        )
    except (ValueError, VaultSafeIOError, OSError) as err:
        sys.stderr.write(f"[telemetry_logger] ERROR: {err}\n")
        return 1

    print(json.dumps({"status": "SUCCESS", "logged_entry": row.strip()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
