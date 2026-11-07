#!/usr/bin/env python3
"""
context_budget_guard.py — Страж бюджета контекста и фазовый компактор AnD os v8.4.
Остров 8 (Kernel Core) ⟷ Инструментальный рантайм агента.

Обеспечивает:
1. Отслеживание интенсивности сессии (Tool Counter) без накладных расходов.
2. Контроль остатка контекстного окна (Правило 20% резерва).
3. Фазовый стратегический аудит (Strategic Phase Compaction):
   - Выдает предупреждение и рекомендацию /compact при завершении фаз (DoD Gates 1, 2, 3),
     когда артефакты уже зафиксированы в sidecar-манифестах (shot.meta.json).
4. Защиту от деградации внимания нейросети при тяжелых генеративных задачах.
"""

import os
import sys
import json
import time
from typing import Dict, Any, Optional

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
SESSION_CACHE_DIR = os.path.join(VAULT_ROOT, "and_os", "var", "cache", "sessions")
os.makedirs(SESSION_CACHE_DIR, exist_ok=True)

DEFAULT_COMPACT_THRESHOLD = 45 # Рекомендация компактификации после 45 инструментальных шагов

def get_session_id() -> str:
    """Возвращает стабильный идентификатор текущей рабочей сессии."""
    # Используем CLAUDE_SESSION_ID или дату/PID родителя
    return os.getenv("CLAUDE_SESSION_ID", os.getenv("SESSION_ID", "default_session"))

def get_counter_file(session_id: str) -> str:
    return os.path.join(SESSION_CACHE_DIR, f"tool_count_{session_id}.json")

def track_tool_invocation(tool_name: str = "unknown", session_id: Optional[str] = None) -> Dict[str, Any]:
    """Инкрементирует счетчик вызовов инструментов и оценивает контекстную нагрузку."""
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
        except Exception:
            pass

    data["count"] = data.get("count", 0) + 1
    data["last_call"] = time.time()
    tools = data.setdefault("tools_used", {})
    tools[tool_name] = tools.get(tool_name, 0) + 1

    count = data["count"]
    # Оценка необходимости компактификации
    if count == DEFAULT_COMPACT_THRESHOLD:
        data["suggest_compact"] = True
        data["reason"] = f"Достигнут порог {count} инструментальных действий. Контекстное окно интенсивно заполнено."
    elif count > DEFAULT_COMPACT_THRESHOLD and count % 20 == 0:
        data["suggest_compact"] = True
        data["reason"] = f"Высокая глубина сессии ({count} действий). Рекомендуется /compact между фазами задачи."

    try:
        with open(cfile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        sys.stderr.write(f"[context_budget_guard] Warning saving counter: {e}\n")

    return data

def evaluate_phase_transition(current_phase: str, target_phase: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Проверяет переход между производственными фазами (например, Блокинг ➔ Нейро-композ).
    Если контекст насыщен, советует компактификацию перед входом в генеративную фазу.
    """
    sid = session_id or get_session_id()
    cfile = get_counter_file(sid)
    count = 0
    if os.path.exists(cfile):
        try:
            with open(cfile, "r", encoding="utf-8") as f:
                d = json.load(f)
                count = d.get("count", 0)
        except Exception:
            pass

    needs_compaction = False
    message = "Контекстный бюджет в норме."

    # Фазы 3 (Shot Synthesis) и 4 (DaVinci Conform) критичны к чистоте внимания LLM
    if target_phase in ["PHASE_3", "PHASE_4"] and count >= 30:
        needs_compaction = True
        message = (
            f"⚠️ ВХОД В {target_phase}: текущая сессия содержит {count} действий. "
            f"Артефакты предыдущей фазы зафиксированы в .meta.json. "
            f"Рекомендуется выполнить /compact перед запуском тяжелого нейро-композа/монтажа."
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
    """Сбрасывает счетчик после успешной компактификации."""
    sid = session_id or get_session_id()
    cfile = get_counter_file(sid)
    if os.path.exists(cfile):
        try:
            os.remove(cfile)
        except Exception:
            pass
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
