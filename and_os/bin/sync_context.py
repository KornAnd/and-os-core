#!/usr/bin/env python3
"""
sync_context.py — автоматизация синхронизации CONTEXT.md в Obsidian Vault.
Принцип: Think in Code (Правило №16).

Использование:
  python3 sync_context.py --check             # Только диагностика всех CONTEXT.md
  python3 sync_context.py --check --path Nero # Проверка конкретного каталога
  python3 sync_context.py --fix               # Автоматическая синхронизация всех CONTEXT.md
  python3 sync_context.py --fix --path Book   # Автоматическая синхронизация конкретного каталога
"""

import os
import sys
import glob
import json
import re
import argparse
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git"}
IGNORE_FILES = {".DS_Store", "CONTEXT.md"}

def get_vault_path(rel_or_abs):
    if os.path.isabs(rel_or_abs):
        return rel_or_abs
    return os.path.join(VAULT_ROOT, rel_or_abs)

def find_context_files(target_dir):
    contexts = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        if "CONTEXT.md" in files:
            contexts.append(root)
    return contexts

def parse_context_links(context_file):
    if not os.path.exists(context_file):
        return set()
    with open(context_file, "r", encoding="utf-8") as f:
        content = f.read()
    # Match [[name|...]] or [[name]]
    wiki_links = re.findall(r"\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]", content)
    parsed = set()
    for link in wiki_links:
        clean = link.strip()
        if clean.endswith(".md"):
            clean = clean[:-3]
        base = os.path.basename(clean)
        parsed.add(base)
        parsed.add(clean)
    return parsed

def get_directory_files(directory):
    files = []
    try:
        entries = os.listdir(directory)
    except OSError:
        return []
    for e in entries:
        if e in IGNORE_FILES or e in IGNORE_DIRS or e.startswith("."):
            continue
        full_path = os.path.join(directory, e)
        if os.path.isfile(full_path) and e.endswith(".md"):
            files.append(e)
    return sorted(files)

def analyze_context(dir_path):
    context_file = os.path.join(dir_path, "CONTEXT.md")
    if not os.path.exists(context_file):
        return {"exists": False, "missing_files": [], "deleted_links": []}
    
    linked_names = parse_context_links(context_file)
    actual_files = get_directory_files(dir_path)
    
    missing_in_context = []
    for f in actual_files:
        base = f[:-3] if f.endswith(".md") else f
        if base not in linked_names and f not in linked_names:
            missing_in_context.append(f)
            
    return {
        "exists": True,
        "context_file": context_file,
        "actual_files": actual_files,
        "missing_in_context": missing_in_context
    }

def fix_context(dir_path, analysis):
    context_file = analysis["context_file"]
    missing = analysis["missing_in_context"]
    if not missing:
        return False
        
    with open(context_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = content.splitlines()
    today_str = datetime.now().strftime("%d.%m.%Y")
    
    new_entries = []
    for f in missing:
        base = f[:-3] if f.endswith(".md") else f
        new_entries.append(f"- [[{base}|{f}]] — добавлен автоматически")
        
    insert_idx = -1
    for i, line in enumerate(lines):
        if re.search(r"^##\s*(?:Файлы|Карта|Структура)", line, re.IGNORECASE):
            insert_idx = i + 1
            break
            
    if insert_idx != -1:
        lines = lines[:insert_idx] + [""] + new_entries + lines[insert_idx:]
    else:
        lines.extend(["", "## Файлы (добавлены)", ""] + new_entries)
        
    updated_timestamp = False
    for i in range(len(lines) - 1, -1, -1):
        if "Обновлено:" in lines[i]:
            lines[i] = f"*Обновлено: {today_str}*"
            updated_timestamp = True
            break
    if not updated_timestamp:
        lines.append(f"\n*Обновлено: {today_str}*")
        
    with open(context_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
        
    return True

def parse_competence_matrix():
    comp_path = os.path.join(VAULT_ROOT, "Clippings", "competence_matrix.md")
    competence_map = {}
    if os.path.exists(comp_path):
        try:
            with open(comp_path, "r", encoding="utf-8") as f:
                for line in f:
                    m = re.findall(r"\|\s*\[\[(?:Clippings/)?([^\|\]]+)(?:\|([^\]]+))?\]\]\s*\|\s*([^\|]+)\|\s*([^\|]+)\|\s*([^\|]+)\|", line)
                    if m:
                        path, label, comp, skill, tasks = m[0]
                        clean_path = path.strip().replace(".md", "").rstrip("\\")
                        bn = os.path.basename(clean_path).lower().replace(" ", "_")
                        competence_map[bn] = {
                            "competence": comp.strip(),
                            "skill": skill.strip(),
                            "tasks": tasks.strip()
                        }
        except (OSError, UnicodeDecodeError) as e:
            sys.stderr.write(f"[sync_context] Warning reading competence map {matrix_path}: {e}\n")
    return competence_map

def extract_clipping_meta(filepath, competence_map):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    
    bn = os.path.basename(filepath).replace(".md", "")
    rel_path = os.path.relpath(filepath, VAULT_ROOT)
    folder = os.path.dirname(os.path.relpath(filepath, os.path.join(VAULT_ROOT, "Clippings"))).replace("Clippings/", "").replace("Clippings", "Общее")
    
    fm_match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    tags = []
    if fm_match:
        tag_lines = re.findall(r"-\s*([^\n]+)", fm_match.group(1))
        for t in tag_lines:
            clean_t = t.strip().strip("\"'").lstrip("#")
            if clean_t and not any(k in clean_t for k in ["color:", "updated:", "created:", "tags:"]):
                tags.append(clean_t)
                
    h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = bn
    if h1_match:
        h1 = h1_match.group(1).strip()
        h1_clean = re.sub(r"[\*\_#]", "", h1).strip()
        if h1_clean and len(h1_clean) > 2:
            title = h1_clean
            
    summary = ""
    m = re.search(r"\*\*(?:Суть|Главная мысль):\*\*\s*([^\n]+)", text, re.IGNORECASE)
    if m:
        summary = m.group(1).strip()
    if not summary:
        m = re.search(r"(?:##\s*О чем книга|\*\*О чем книга\*\*)\s*\n+([^\n#]+)", text, re.IGNORECASE)
        if m:
            summary = m.group(1).strip()
    if not summary:
        m = re.search(r"(?:##\s*(?:\d+\.\s*)?Главная идея книги|\*\*Главная идея книги:\*\*)\s*\n+([^\n#>]+(?:\n[^\n#>]+)?)", text, re.IGNORECASE)
        if m:
            summary = m.group(1).strip()
    if not summary:
        m = re.search(r"(?:##\s*(?:\d+\.\s*)?Контекст|\*\*Контекст:\*\*)\s*\n+([^\n#]+)", text, re.IGNORECASE)
        if m:
            summary = m.group(1).strip()
    if not summary:
        body = text
        if fm_match:
            body = text[fm_match.end():]
        clean_lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("#")]
        if clean_lines:
            summary = " ".join(clean_lines[:3])

    summary = re.sub(r"[\*\_#>`]", "", summary).strip()
    if len(summary) > 250:
        summary = summary[:247] + "..."

    target_match = re.search(r"\*\*(?:Для кого|Кому читать):\*\*\s*([^\n]+)", text, re.IGNORECASE)
    target = target_match.group(1).strip() if target_match else ""
    target_clean = re.sub(r"[\*\_#>`]", "", target).strip()

    cid = bn.lower().replace(" ", "_")
    comp_info = competence_map.get(cid, {})

    return {
        "id": cid,
        "title": title,
        "filename": bn,
        "category": folder if folder else "Общее",
        "source": f"[[{rel_path}|{bn}]]",
        "summary": summary,
        "target_audience": target_clean,
        "tags": tags[:8],
        "competence": comp_info.get("competence", ""),
        "tasks": comp_info.get("tasks", ""),
        "skill": comp_info.get("skill", "")
    }

def update_quick_db():
    clippings_dir = os.path.join(VAULT_ROOT, "Clippings")
    knowledge_dir = os.path.join(VAULT_ROOT, "Nero", "knowledge")
    db_path = os.path.join(clippings_dir, "quick_knowledge_db.json")

    md_files = []
    if os.path.exists(clippings_dir):
        md_files.extend([
            f for f in glob.glob(os.path.join(clippings_dir, "**/*.md"), recursive=True)
            if not f.endswith("CONTEXT.md")
            and not f.endswith("competence_matrix.md")
            and not f.endswith("summary.md")
            and not f.endswith("Clippings.md")
            and not f.endswith("quick_knowledge_db.md")
        ])

    # HARD GUARD: Automatically index learned empirical patterns from Nero/knowledge/
    if os.path.exists(knowledge_dir):
        md_files.extend([
            f for f in glob.glob(os.path.join(knowledge_dir, "**/*.md"), recursive=True)
            if not f.endswith("CONTEXT.md")
            and not f.endswith("knowledge.md")
        ])

    c_map = parse_competence_matrix()
    knowledge_entries = []
    for f in md_files:
        try:
            entry = extract_clipping_meta(f, c_map)
            knowledge_entries.append(entry)
        except (OSError, UnicodeDecodeError, ValueError) as e:
            sys.stderr.write(f"[sync_context] Warning extracting clipping meta {f}: {e}\n")

    with open(db_path, "w", encoding="utf-8") as out:
        json.dump(knowledge_entries, out, ensure_ascii=False, indent=2)
    print(f"⚡ Обновлена быстрая база знаний: Clippings/quick_knowledge_db.json ({len(knowledge_entries)} записей)")

def sync_all_contexts(fix=True, target_path=""):
    target = get_vault_path(target_path) if target_path else VAULT_ROOT
    if not os.path.exists(target):
        return False
    contexts = find_context_files(target)
    dirs_with_missing = []
    for c_dir in contexts:
        res = analyze_context(c_dir)
        if res.get("missing_in_context"):
            dirs_with_missing.append((c_dir, res))
    if fix:
        for c_dir, res in dirs_with_missing:
            fix_context(c_dir, res)
        update_quick_db()
    return len(dirs_with_missing) == 0

def main():
    parser = argparse.ArgumentParser(description="Автоматическая синхронизация CONTEXT.md")
    parser.add_argument("--check", action="store_true", help="Проверить актуальность без изменения файлов")
    parser.add_argument("--fix", action="store_true", help="Автоматически добавить недостающие файлы в CONTEXT.md")
    parser.add_argument("--path", type=str, default="", help="Относительный или абсолютный путь каталога для проверки")
    args = parser.parse_args()
    
    target = get_vault_path(args.path) if args.path else VAULT_ROOT
    if not os.path.exists(target):
        print(f"Ошибка: каталог {target} не существует.")
        sys.exit(1)
        
    contexts = find_context_files(target)
    print(f"Сканирование хранилища: {target}")
    print(f"Найдено CONTEXT.md файлов: {len(contexts)}")
    print("-" * 60)
    
    total_missing = 0
    dirs_with_missing = []
    
    for c_dir in contexts:
        rel_dir = os.path.relpath(c_dir, VAULT_ROOT)
        rel_dir_label = "корень" if rel_dir == "." else rel_dir
        res = analyze_context(c_dir)
        missing = res.get("missing_in_context", [])
        if missing:
            total_missing += len(missing)
            dirs_with_missing.append((c_dir, res))
            print(f"⚠️  [{rel_dir_label}] Не отражено в CONTEXT.md ({len(missing)} шт.):")
            for m in missing[:5]:
                print(f"    + {m}")
            if len(missing) > 5:
                print(f"    ... и ещё {len(missing) - 5} файлов")
                
    if not dirs_with_missing:
        print("✅ Все проверенные CONTEXT.md полностью синхронизированы!")
        if args.fix:
            update_quick_db()
        return
        
    print("-" * 60)
    print(f"Итого несинхронизированных файлов: {total_missing} в {len(dirs_with_missing)} каталогах.")
    
    if args.fix:
        print("\nЗапуск автоматического исправления (--fix)...")
        fixed_count = 0
        for c_dir, res in dirs_with_missing:
            if fix_context(c_dir, res):
                rel_dir = os.path.relpath(c_dir, VAULT_ROOT)
                print(f"✅ Обновлён CONTEXT.md: {rel_dir}")
                fixed_count += 1
        print(f"\nГотово! Синхронизировано каталогов: {fixed_count}.")
        update_quick_db()
    elif not args.check:
        print("\nДля автоматического исправления запустите с флагом --fix:")
        print(f"python3 \"{os.path.abspath(__file__)}\" --fix")

if __name__ == "__main__":
    import glob, json
    main()
