#!/usr/bin/env python3
"""
fs_guard.py -- Canonical Filesystem Map Guard (decision engine).

Single, stateless decision engine behind the canonical FS map
(SSoT data: and_os/etc/fs_map.json). Enforced at every agent tool boundary:

  - OpenCode V2        : plugin fs_map_guard -> native "permission.evaluate" hook
  - Gemini/Antigravity : PreToolUse hook    -> this engine, mode "gemini"

Design invariants:
  * Zero path policy in code: every allow/deny/ask root lives in fs_map.json.
    Adding a zone = editing the JSON, no code change.
  * Statelessness: the map is re-read on every invocation; no cache, no logs
    (Rule #72: no new data channel).
  * Longest-prefix wins, after normalization (expanduser + abspath + realpath),
    so symlinks and ".." traversal cannot escape the map.
  * Fail-closed on engine error: unreadable/invalid map -> deny with reason.
  * Shell checks are two-tier and documented as best effort (per the OpenCode
    V2 scanner docs: directory inference from command text is best effort):
      tier 1 (hard) : any path token inside a deny root -> deny
      tier 2 (soft) : save targets (redirections + unambiguous create-verbs)
                      outside the map -> ask
    Execution tools (python3, node, git, ...) are NOT verb-scanned: their file
    effects cannot be inferred from path arguments without a shell interpreter.

Usage:
  fs_guard.py decide <path> [--action edit|read] [--map PATH]   -> JSON verdict
  fs_guard.py shell  <command> [--map PATH]                     -> JSON verdict
  fs_guard.py gemini [--map PATH]   (stdin: hook payload JSON)   -> {"decision": ...}

Verdict JSON: {"effect": "allow"|"ask"|"deny", "reason": str, "zone": str}
Exit 0 on a normal decision; exit 1 on engine error (the error is still
emitted as a fail-closed JSON verdict on stdout).
"""

import argparse
import json
import os
import re
import shlex
import sys

sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MAP = os.path.normpath(os.path.join(HERE, "..", "etc", "fs_map.json"))
MAP_SCHEMA = "fs-map/v1"

SEVERITY = {"allow": 0, "ask": 1, "deny": 2}

_ABS_RE = re.compile(r"^/[\w.@+~-]+(/[\w.@+~-]+)*$")
_REDIRECT_RE = re.compile(r"^\d*(>>?)$")
_REDIRECT_GLUED_RE = re.compile(r"^\d*(>>?)(\S+)$")
_SEGMENT_SEPARATORS = (";", "&&", "||", "|", "&")

GEMINI_FILE_TOOLS = ("write_to_file", "write_file", "replace_file_content", "edit_file")


class MapError(Exception):
    """Raised when fs_map.json is missing, malformed, or inconsistent."""


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False))


def normalize(raw):
    """expanduser -> abspath -> realpath (symlinks + traversal collapse)."""
    p = os.path.expanduser(str(raw).strip())
    p = os.path.abspath(p)
    return os.path.realpath(p)


def load_map(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as err:
        raise MapError("cannot load fs map %s: %s" % (path, err)) from err
    if data.get("schema") != MAP_SCHEMA:
        raise MapError("unsupported schema %r (expected %s)" % (data.get("schema"), MAP_SCHEMA))
    roots = []
    for entry in data.get("roots", []):
        try:
            raw = entry["path"]
            effect = entry["effect"]
        except (KeyError, TypeError):
            raise MapError("root entry without path/effect: %r" % (entry,))
        if effect not in SEVERITY:
            raise MapError("root %r has invalid effect %r" % (raw, effect))
        roots.append(
            {"path": normalize(raw), "effect": effect, "label": str(entry.get("label", ""))}
        )
    default = data.get("default_effect", "ask")
    if default not in SEVERITY:
        raise MapError("invalid default_effect %r" % (default,))
    verbs = [str(v) for v in data.get("shell_write_verbs", [])]
    return {"roots": roots, "default": default, "write_verbs": set(verbs)}


def match_root(roots, path):
    best = None
    for root in roots:
        base = root["path"]
        if path == base or path.startswith(base + "/"):
            if best is None or len(base) > len(best["path"]):
                best = root
    return best


def decide(action, raw, m):
    norm = normalize(raw)
    root = match_root(m["roots"], norm)
    if root is not None:
        effect = root["effect"]
        zone = "root:%s" % root["path"]
        reason = "path is inside %s (%s)" % (root["label"] or root["path"], zone)
    else:
        effect = m["default"]
        zone = "outside-map"
        reason = (
            "path is outside the canonical FS map (SSoT: and_os/etc/fs_map.json) -- "
            "approval required"
        )
    if action == "read":
        # Reads create no artifacts: protected zones escalate to confirmation
        # only; out-of-map reads are left to the native policy (no escalation).
        if effect == "deny":
            effect = "ask"
            reason += " [read of protected zone: confirmation required]"
        elif effect == "ask":
            effect = "allow"
            reason += " [out-of-map read: no escalation, native policy applies]"
    return {"effect": effect, "reason": reason, "zone": zone, "normalized": norm}


def is_path_like(tok):
    if not tok:
        return False
    if tok == "~" or tok.startswith("~/"):
        return True
    if tok == "$HOME" or tok.startswith("$HOME/"):
        return True
    if tok.startswith("/") and _ABS_RE.match(tok):
        return True
    return False


def tokenize_command(command):
    try:
        return shlex.split(str(command), posix=True)
    except ValueError:
        return str(command).split()


def shell_check(command, m):
    tokens = tokenize_command(command)
    worst = [None, None]  # [effect, reason]

    def consider(effect, reason):
        if worst[0] is None or SEVERITY[effect] > SEVERITY[worst[0]]:
            worst[0], worst[1] = effect, reason

    def check_target(target, context):
        if not target or target.startswith("-") or not is_path_like(target):
            return
        d = decide("edit", target, m)
        if d["effect"] == "deny":
            consider("deny", "shell %s protected zone %s: %s" % (context, target, d["reason"]))
        elif d["effect"] == "ask":
            consider("ask", "shell %s outside canonical FS map: %s" % (context, target))

    # Tier 1 (hard): any path token inside a deny root -> deny.
    for tok in tokens:
        if is_path_like(tok):
            d = decide("edit", tok, m)
            if d["effect"] == "deny":
                consider("deny", "shell references protected zone %s: %s" % (tok, d["reason"]))

    # Tier 2 (best effort): save targets outside the map -> ask.
    write_verb = None
    at_segment_start = True
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok in _SEGMENT_SEPARATORS:
            at_segment_start = True
            write_verb = None
            i += 1
            continue
        if at_segment_start:
            at_segment_start = False
            base = os.path.basename(tok)
            write_verb = base if base in m["write_verbs"] else None
        if _REDIRECT_RE.match(tok):
            if i + 1 < n:
                check_target(tokens[i + 1], "redirect to")
                i += 2
            else:
                i += 1
            continue
        if _REDIRECT_GLUED_RE.match(tok):
            check_target(_REDIRECT_GLUED_RE.match(tok).group(2), "redirect to")
            i += 1
            continue
        if write_verb is not None and is_path_like(tok):
            check_target(tok, "%s target" % write_verb)
        i += 1

    if worst[0] is None:
        return {
            "effect": "allow",
            "reason": "no out-of-map save target detected (best-effort scan)",
            "zone": "shell",
        }
    return {"effect": worst[0], "reason": worst[1], "zone": "shell"}


def gemini_check(payload, m):
    tool = payload.get("toolCall") or {}
    name = str(tool.get("name") or (tool.get("function") or {}).get("name") or "")
    args = tool.get("args") or (tool.get("function") or {}).get("arguments") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            args = {}
    if not isinstance(args, dict):
        args = {}

    cmd = args.get("CommandLine") or args.get("command")
    if name == "run_command" and isinstance(cmd, str) and cmd:
        d = shell_check(cmd, m)
        if d["effect"] == "allow":
            return {"decision": "allow"}
        return {
            "decision": "deny",
            "reason": d["reason"]
            + " To approve: add the target root to and_os/etc/fs_map.json or run the command manually.",
        }

    target = args.get("TargetFile") or args.get("target_file") or args.get("path") or args.get("file_path")
    if name in GEMINI_FILE_TOOLS and target:
        d = decide("edit", str(target), m)
        if d["effect"] == "allow":
            return {"decision": "allow"}
        # The Gemini/Antigravity hook protocol on this machine is binary
        # (allow|deny); an "ask" verdict is surfaced as deny + approval path.
        return {
            "decision": "deny",
            "reason": d["reason"]
            + " To approve: add the target root to and_os/etc/fs_map.json or perform the save manually.",
        }

    return {"decision": "allow"}


def main(argv=None):
    # --map is defined per subcommand so it can follow the subcommand token
    # (the calling hooks always pass "mode ... --map PATH").
    parser = argparse.ArgumentParser(prog="fs_guard", description="Canonical FS map decision engine")
    sub = parser.add_subparsers(dest="mode", required=True)
    map_kw = dict(
        default=os.environ.get("FS_GUARD_MAP", DEFAULT_MAP),
        help="path to fs_map.json (default: and_os/etc/fs_map.json)",
    )
    p_decide = sub.add_parser("decide", help="decide a single path")
    p_decide.add_argument("path")
    p_decide.add_argument("--action", choices=("edit", "read"), default="edit")
    p_decide.add_argument("--map", **map_kw)
    p_shell = sub.add_parser("shell", help="best-effort scan of a shell command")
    p_shell.add_argument("command")
    p_shell.add_argument("--map", **map_kw)
    p_gemini = sub.add_parser("gemini", help="PreToolUse payload from stdin (Gemini/Antigravity)")
    p_gemini.add_argument("--map", **map_kw)
    args = parser.parse_args(argv)

    try:
        m = load_map(args.map)
    except MapError as err:
        emit({"effect": "deny", "reason": "fs-map guard error (fail-closed): %s" % err, "zone": "guard-error"})
        return 1

    if args.mode == "decide":
        emit(decide(args.action, args.path, m))
    elif args.mode == "shell":
        emit(shell_check(args.command, m))
    else:
        try:
            payload = json.load(sys.stdin)
            if not isinstance(payload, dict):
                raise ValueError("payload is not an object")
        except ValueError as err:
            # Protocol noise (empty/non-object stdin): pass through, as the
            # vault_guard_hook exemplar does, to avoid IDE lockup.
            emit({"decision": "allow", "reason": "non-object hook payload passed through: %s" % err})
            return 0
        emit(gemini_check(payload, m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
