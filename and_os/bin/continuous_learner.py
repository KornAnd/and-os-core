#!/usr/bin/env python3
"""
continuous_learner.py — Интеллектуальный компилятор опыта сессий для AnD os v8.4.
Остров 8 (Kernel & Compiler) ⟷ Остров 1 & 6 (Knowledge Realm).

Анализирует транскрипты/логи завершенных сессий или атомарные пользовательские решения:
1. Выявляет решенные технические проблемы (error_resolution, tool_hacks).
2. Выявляет явные корректировки и предпочтения пользователя (user_corrections).
3. Формирует структурированные стандартизированные заметки в:
   - `Nero/knowledge/engineers/` (инженерные решения Blender, ComfyUI, DaVinci, Swift, macOS);
   - `Nero/CONTEXT.md` / `Nero/profile/` (пользовательские стандарты и предпочтения);
4. Автоматически регистрирует новые знания в `Clippings/quick_knowledge_db.json`.
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
KNOWLEDGE_ENGINEERS_DIR = os.path.join(VAULT_ROOT, "Nero", "knowledge", "engineers")
QUICK_DB_PATH = os.path.join(VAULT_ROOT, "Clippings", "quick_knowledge_db.json")
LEARNED_LOG_DIR = os.path.join(VAULT_ROOT, "and_os", "var", "learned")

os.makedirs(KNOWLEDGE_ENGINEERS_DIR, exist_ok=True)
os.makedirs(LEARNED_LOG_DIR, exist_ok=True)

def slugify(text: str) -> str:
    """Генерирует безопасное имя файла из заголовка."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text[:60]

def record_learned_pattern(
    topic: str,
    domain: str, # "blender" | "comfyui" | "davinci" | "swift" | "core" | "user"
    problem: str,
    solution: str,
    source: str = "interactive_session",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Создает стандартизированную каноническую заметку в Obsidian Knowledge Base
    и регистрирует ее в быстром индексе quick_knowledge_db.json.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_tag = datetime.now().strftime("%Y-%m-%d")
    clean_slug = slugify(topic)
    filename = f"{clean_slug}.md"
    target_path = os.path.join(KNOWLEDGE_ENGINEERS_DIR, filename)

    tags_list = ["knowledge", "learned", domain, "and_os"]
    if tags:
        tags_list.extend(tags)
    tags_formatted = "\n".join([f"  - {t}" for t in sorted(set(tags_list))])

    content = f"""---
created: {now_str}
updated: {now_str}
tags:
{tags_formatted}
project: and_os
status: VERIFIED
domain: {domain}
source: {source}
---

# 🧠 База Опыта: {topic}

> **Дата**: {date_tag} | **Домен**: `{domain}` | **Статус**: 🟢 VERIFIED
> **Контекст**: Решение извлечено автоматическим компилятором опыта AnD os v8.4.

---

## 1. Проблема / Симптом
{problem.strip()}

---

## 2. Верифицированное Решение
{solution.strip()}

---

## 3. Инвариант для Агента (Правило применения)
- При работе в домене `{domain}` строго соблюдать данный паттерн во избежание регрессий.

---
[[CONTEXT|← Наверх в атлас]]
"""

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Обновление quick_knowledge_db.json
    db_updated = False
    if os.path.exists(QUICK_DB_PATH):
        try:
            with open(QUICK_DB_PATH, "r", encoding="utf-8") as qf:
                quick_db = json.load(qf)

            new_entry = {
                "id": clean_slug,
                "title": topic,
                "filename": filename.replace(".md", ""),
                "category": f"Knowledge_{domain.capitalize()}",
                "source": f"[[Nero/knowledge/engineers/{filename}|{topic}]]",
                "summary": f"{problem[:150]} -> {solution[:150]}",
                "target_audience": "LLM Agents & Engineers",
                "tags": tags_list,
                "competence": f"Engineering_{domain}",
                "tasks": "Troubleshooting & Optimization",
                "skill": "continuous-learning"
            }

            if isinstance(quick_db, list):
                quick_db = [item for item in quick_db if item.get("id") != clean_slug]
                quick_db.append(new_entry)
            elif isinstance(quick_db, dict) and "articles" in quick_db:
                articles = [a for a in quick_db["articles"] if a.get("id") != clean_slug]
                articles.append(new_entry)
                quick_db["articles"] = articles
                quick_db["total_count"] = len(articles)

            with open(QUICK_DB_PATH, "w", encoding="utf-8") as qf:
                json.dump(quick_db, qf, indent=2, ensure_ascii=False)
            db_updated = True
        except Exception as e:
            sys.stderr.write(f"[continuous_learner] Warning updating quick DB: {e}\n")


    return {
        "status": "ok",
        "action": "pattern_recorded",
        "topic": topic,
        "domain": domain,
        "note_path": target_path,
        "quick_db_updated": db_updated
    }

def evaluate_session_transcript(transcript_path: str) -> Dict[str, Any]:
    """Анализирует JSONL/лог сессии на наличие исправлений и решений."""
    if not os.path.exists(transcript_path):
        return {"status": "error", "message": f"Transcript not found: {transcript_path}"}

    try:
        user_messages = 0
        error_lines = []
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("source") == "USER_EXPLICIT" or data.get("type") == "USER_INPUT":
                        user_messages += 1
                    if "error" in line.lower() or "traceback" in line.lower():
                        error_lines.append(line[:200])
                except Exception:
                    pass

        return {
            "status": "ok",
            "user_messages_count": user_messages,
            "detected_error_signals": len(error_lines),
            "worthy_of_eval": user_messages >= 5 or len(error_lines) > 0
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        res = record_learned_pattern(
            topic="Blender Headless Playblast OpenGL Audio Context",
            domain="blender",
            problem="При фоновом рендере bpy.ops.render.opengl(animation=True) без аудио-устройства падала ошибка context incorrect.",
            solution="Устанавливать scene.render.image_settings.file_format = 'FFMPEG' и video codec до вызова OpenGL оператора.",
            source="unit_test"
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("Usage: continuous_learner.py --test")
