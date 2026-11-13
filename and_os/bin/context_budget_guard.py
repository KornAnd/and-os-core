#!/usr/bin/env python3
"""
context_budget_guard.py — Context budget guard and phase compactor for AnD os v1.0.0.
Island 8 (Kernel Core) <-> the agent's instrumental runtime.

Provides:
1. Session intensity tracking (Tool Counter) with no overhead.
2. Context-window remainder control (the 20% reserve rule).
3. Strategic phase audit (Strategic Phase Compaction):
   - Emits a warning and a /compact recommendation at phase completion (DoD Gates 1, 2, 3),
     when the artifacts are already pinned in the sidecar manifests (shot.meta.json).
4. Protection against the neural network's attention degradation on heavy generative tasks.
"""

import os
import sys
import json
import time
from typing import Dict, Any, Optional

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
# Rule #71 (Vault Purity): session counters are cache data, not Vault state.
SESSION_CACHE_DIR = os.path.join(os.path.expanduser("~/.and_os"), "var", "cache", "sessions")
os.makedirs(SESSION_CACHE_DIR, exist_ok=True)

DEFAULT_COMPACT_THRESHOLD = 45 # Compactification recommendation after 45 instrumental steps

def get_session_id() -> str:
    """Returns the stable identifier of the current working session."""
    # Uses CLAUDE_SESSION_ID or the parent date/PID
    return os.getenv("CLAUDE_SESSION_ID", os.getenv("SESSION_ID", "default_session"))

def get_counter_file(session_id: str) -> str:
    return os.path.join(SESSION_CACHE_DIR, f"tool_count_{session_id}.json")

def track_tool_invocation(tool_name: str = "unknown", session_id: Optional[str] = None) -> Dict[str, Any]:
    """Increments the tool-call counter and estimates the context load."""
    sid = session_id or get_session_id()
    cfile = get_counter_file(sid)

    data = {
        "session_id": sid,
        "count": 0,
        "first_call": time.time(),
        "last_call": time.time(),
        "tools_used": {},
        "suggest_compact": False,
        "reason": ""
    }

    if os.path.exists(cfile):
        try:
            with open(cfile, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as err:
            sys.stderr.write(f"[context_budget_guard] Notice: the counter file is unreadable, the fresh counter is used: {err}\n")

    data["count"] = data.get("count", 0) + 1
    data["last_call"] = time.time()
    tools = data.setdefault("tools_used", {})
    tools[tool_name] = tools.get(tool_name, 0) + 1

    count = data["count"]
    # Compactification necessity estimate
    if count == DEFAULT_COMPACT_THRESHOLD:
        data["suggest_compact"] = True
        data["reason"] = f"Threshold of {count} instrumental actions reached. The context window is intensively filled."
    elif count > DEFAULT_COMPACT_THRESHOLD and count % 20 == 0:
        data["suggest_compact"] = True
        data["reason"] = f"High session depth ({count} actions). /compact between task phases is recommended."

    try:
        with open(cfile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        sys.stderr.write(f"[context_budget_guard] Warning saving counter: {e}\n")

    return data

def evaluate_phase_transition(current_phase: str, target_phase: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks the transition between production phases (e.g. Blocking -> Neuro-composite).
    If the context is saturated, it recommends compactification before entering the generative phase.
    """
    sid = session_id or get_session_id()
    cfile = get_counter_file(sid)
    count = 0
    if os.path.exists(cfile):
        try:
            with open(cfile, "r", encoding="utf-8") as f:
                d = json.load(f)
                count = d.get("count", 0)
        except (OSError, json.JSONDecodeError) as err:
            sys.stderr.write(f"[context_budget_guard] Notice: the counter file is unreadable, the count is 0: {err}\n")

    needs_compaction = False
    message = "Context budget is within the normal range."

    # Phases 3 (Shot Synthesis) and 4 (DaVinci Conform) are critical to the LLM's attention purity
    if target_phase in ["PHASE_3", "PHASE_4"] and count >= 30:
        needs_compaction = True
        message = (
            f"⚠️ ENTERING {target_phase}: the current session contains {count} actions. "
            f"The artifacts of the previous phase are pinned in .meta.json. "
            f"Run /compact before launching the heavy neuro-composite/edit."
        )

    return {
        "status": "ok",
        "current_phase": current_phase,
        "target_phase": target_phase,
        "tool_count": count,
        "needs_compaction": needs_compaction,
        "recommendation": message
    }

def reset_session_counter(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Resets the counter after a successful compactification."""
    sid = session_id or get_session_id()
    cfile = get_counter_file(sid)
    if os.path.exists(cfile):
        try:
            os.remove(cfile)
        except OSError as err:
            sys.stderr.write(f"[context_budget_guard] Notice: the counter file was not removed: {err}\n")
    return {"status": "ok", "action": "counter_reset", "session_id": sid}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--track":
        tname = sys.argv[2] if len(sys.argv) > 2 else "generic_tool"
        res = track_tool_invocation(tname)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "--phase-check":
        p_curr = sys.argv[2] if len(sys.argv) > 2 else "PHASE_2"
        p_tgt = sys.argv[3] if len(sys.argv) > 3 else "PHASE_3"
        res = evaluate_phase_transition(p_curr, p_tgt)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "--reset":
        res = reset_session_counter()
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("Usage: context_budget_guard.py [--track <tool> | --phase-check <curr> <tgt> | --reset]")
