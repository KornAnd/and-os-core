#!/usr/bin/env python3
"""Генератор контекста для внешних LLM (ChatGPT, Claude, Gemini).

Собирает все CONTEXT.md из хранилища Obsidian в единый файл,
оптимизированный для загрузки в чат-интерфейсы.

Использование:
  python3 gen_context.py              # полный контекст
  python3 gen_context.py --lite       # только Nero (для быстрой загрузки)
  python3 gen_context.py --topic work # контекст конкретного каталога
"""

import os
import sys
import glob
from datetime import datetime

VAULT = os.path.expanduser("~/Documents/Obsidian Vault")
if VAULT not in sys.path:
    sys.path.insert(0, VAULT)
from and_os.lib.core.vault_safe_io import vault_safe_write
OUTPUT = os.path.join(VAULT, "Nero", "ai", "context_export.md")

EXCLUDE_DIRS = {'.trash', '.obsidian', '.smart-env', '.space', '.makemd'}

def collect_context(root: str, exclude: set = None) -> list:
    """Собрать все CONTEXT.md файлы, отсортированные по важности."""
    files = []
    for md in glob.glob(os.path.join(root, "**", "CONTEXT.md"), recursive=True):
        parts = md.replace(root, "").split(os.sep)
        if any(p in (exclude or EXCLUDE_DIRS) for p in parts):
            continue
        priority = 0
        if "Nero/profile" in md:
            priority = 0
        elif "Nero/work" in md:
            priority = 1
        elif "Nero/ta_bu" in md:
            priority = 2
        elif "Nero/ai" in md:
            priority = 3
        elif "Nero" in md:
            priority = 4
        else:
            priority = 5
        files.append((priority, md))
    files.sort(key=lambda x: (x[0], x[1]))
    return [f[1] for f in files]

def read_file(path: str) -> str:
    with open(path, "r") as f:
        content = f.read()
    # Strip secret references
    return "\n".join(
        line for line in content.split("\n")
        if "@@K:" not in line
    )

def generate_full():
    """Полный контекст: карта карт + полный текст ключевых CONTEXT, оглавление остальных."""
    lines = [
        f"# Контекст базы знаний System Architect",
        f"# Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        f"# Для загрузки в ChatGPT/Claude/Gemini",
        f"",
        f"> **Инструкция для LLM:** Это карта базы знаний. Ниже — полный текст глобального контекста, KNOWLEDGE.md и Nero/CONTEXT. Остальные каталоги — оглавление с wiki-ссылками.",
        f"> Для детального разбора каталога запроси его CONTEXT.md отдельно (по `[[wiki-link]]`).",
        f"",
        "---",
        "",
    ]
    files = collect_context(VAULT)
    # Ключевые — полный текст (точное совпадение относительного пути)
    full_keys = {
        "SYSTEM.md",
        "CONTEXT.md",
        "KNOWLEDGE.md",
        os.path.join("Nero", "CONTEXT.md"),
        os.path.join("Nero", "work", "CONTEXT.md"),
        os.path.join("Nero", "ta_bu", "CONTEXT.md"),
        os.path.join("Nero", "profile", "CONTEXT.md"),
        os.path.join("Nero", "profile", "health", "CONTEXT.md"),
        os.path.join("Nero", "finance", "CONTEXT.md"),
        os.path.join("Nero", "cg_core", "CONTEXT.md"),
        os.path.join("Clippings", "CONTEXT.md"),
        os.path.join("Nero", "skills", "CONTEXT.md"),
    }

    for f in files:
        rel = f.replace(VAULT, "").lstrip("/")
        lines.append(f"<!-- {rel} -->")
        if rel in full_keys:
            lines.append(read_file(f))
        else:
            # Оглавление: короткая шапка CONTEXT (назначение)
            content = read_file(f)
            purpose = ""
            for line in content.split("\n"):
                if line.startswith("**Назначение**") or line.startswith("# Контекст"):
                    purpose = line.strip()
                    break
            lines.append(f"→ {purpose or 'Каталог'}. Полный текст: `[[{rel}]]` (запросить при необходимости)")
        lines.append("")
    return "\n".join(lines)

def generate_lite():
    """Лёгкий контекст: только Nero."""
    lines = [
        f"# Контекст базы знаний (NERO)",
        f"# Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        f"",
    ]
    nero_root = os.path.join(VAULT, "Nero")
    files = collect_context(nero_root, set())
    for f in files:
        rel = f.replace(VAULT, "").lstrip("/")
        lines.append(f"<!-- {rel} -->")
        lines.append(read_file(f))
        lines.append("")
    return "\n".join(lines)

def generate_topic(topic: str):
    """Контекст конкретного каталога."""
    nero_dir = os.path.join(VAULT, "Nero", topic)
    vault_dir = os.path.join(VAULT, topic)
    
    lines = [
        f"# Контекст: {topic}/",
        f"# Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        f"",
    ]
    
    # Сначала Nero, потом vault
    for base in [nero_dir, vault_dir]:
        ctx = os.path.join(base, "CONTEXT.md")
        if os.path.exists(ctx):
            content = read_file(ctx)
            lines.append(f"<!-- {ctx.replace(VAULT, '')} -->")
            lines.append(content)
            lines.append("")
    
    if len(lines) <= 3:
        lines.append(f"❌ Каталог '{topic}' не найден.")
    
    return "\n".join(lines)

if __name__ == "__main__":
    if "--lite" in sys.argv:
        content = generate_lite()
        OUTPUT = os.path.join(VAULT, "Nero", "ai", "context_lite.md")
    elif "--topic" in sys.argv:
        idx = sys.argv.index("--topic")
        topic = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
        content = generate_topic(topic)
        OUTPUT = os.path.join(VAULT, "Nero", "ai", f"context_{topic}.md")
    else:
        content = generate_full()
    
    vault_safe_write(OUTPUT, content)
    
    size_kb = len(content) / 1024
    tokens_est = int(len(content) / 3.5)  # rough estimate for Russian
    print(f"✅ Сгенерирован: {OUTPUT}")
    print(f"📏 Размер: {size_kb:.1f} KB (~{tokens_est:,} токенов)")
    print(f"📋 Готов к загрузке в ChatGPT/Claude/Gemini")
