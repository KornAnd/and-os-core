#!/usr/bin/env python3
"""
audit_tags_links.py — проверка и доставка тегов каталога и навигационных ссылок CONTEXT.
Принцип: Think in Code (Правило №16) и Правило №1 (режим «проверять и доставлять»).

Использование:
  python3 audit_tags_links.py --check             # Диагностика по всему хранилищу
  python3 audit_tags_links.py --check --path Nero # Диагностика одного каталога
  python3 audit_tags_links.py --fix --path Tasks  # Доставка тегов и линков в каталоге Tasks
"""

import os
import sys
from pathlib import Path
_vroot = str(Path(__file__).resolve().parents[2])
if _vroot not in sys.path:
    sys.path.insert(0, _vroot)
from and_os.lib.core.vault_safe_io import vault_safe_write

import re
import sys
import argparse

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git"}
IGNORE_FILES = {"CONTEXT.md", "Vault.md", ".DS_Store"}
SYSTEM_TAGS = {"root", "system", "контекст", "vault", "манифест", "точка входа", "база", "навигация", "other"}

def extract_context_tags(context_path):
    if not os.path.exists(context_path):
        return []
    with open(context_path, "r", encoding="utf-8", errors="ignore") as f:
        c = f.read()
    
    tags = []
    # Match frontmatter tags:
    fm_match = re.search(r"^---\s*\n(.*?)\n---", c, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        in_tags = False
        for line in fm.splitlines():
            line_str = line.strip()
            if line_str.startswith("tags:"):
                in_tags = True
                continue
            if in_tags:
                if line_str.startswith("- "):
                    tag = line_str[2:].strip().strip("\"'")
                    if tag.lower() not in SYSTEM_TAGS and not tag.startswith("#"):
                        tags.append(tag)
                elif re.match(r"^[a-zA-Z0-9_-]+:", line_str):
                    break

    # Also match inline #хештеги
    hash_match = re.search(r"\*\*Хештеги:\*\*\s*(.+)", c)
    if hash_match:
        for t in hash_match.group(1).split():
            t_clean = t.lstrip("#").strip()
            if t_clean and t_clean.lower() not in SYSTEM_TAGS and t_clean not in tags:
                tags.append(t_clean)

    return tags

def find_parent_context(dir_path):
    curr = dir_path
    while curr.startswith(VAULT_ROOT):
        c_path = os.path.join(curr, "CONTEXT.md")
        if os.path.exists(c_path):
            return c_path
        if curr == VAULT_ROOT:
            break
        curr = os.path.dirname(curr)
    return None

def analyze_file(file_path):
    dir_path = os.path.dirname(file_path)
    context_file = find_parent_context(dir_path)
    if not context_file:
        return None

    dir_tags = extract_context_tags(context_file)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 1. Check tags
    file_tags = []
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    has_fm = bool(fm_match)
    if fm_match:
        fm = fm_match.group(1)
        in_tags = False
        for line in fm.splitlines():
            l_str = line.strip()
            if l_str.startswith("tags:"):
                in_tags = True
                continue
            if in_tags:
                if l_str.startswith("- "):
                    file_tags.append(l_str[2:].strip().strip("\"'"))
                elif re.match(r"^[a-zA-Z0-9_-]+:", l_str):
                    break

    missing_tags = [t for t in dir_tags if t not in file_tags and f"#{t}" not in content]

    # 2. Check backlink to context/index
    has_backlink = bool(re.search(r"\[\[(?:[^\|\]]+/)?CONTEXT(?:\|[^\]]+)?\]\]", content, re.IGNORECASE))
    if not has_backlink:
        parent_name = os.path.basename(dir_path)
        has_backlink = f"[[{parent_name}]]" in content or f"[[{parent_name}/" in content

    return {
        "file_path": file_path,
        "has_fm": has_fm,
        "existing_tags": file_tags,
        "missing_tags": missing_tags,
        "has_backlink": has_backlink
    }

def fix_file(analysis):
    fp = analysis["file_path"]
    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    changed = False
    new_content = content

    # Add missing tags if any and dir has tags
    if analysis["missing_tags"]:
        tags_to_add = analysis["missing_tags"][:2] # add up to 2 primary directory tags
        if analysis["has_fm"]:
            # insert into tags: or add tags:
            fm_match = re.search(r"^---\s*\n(.*?)\n---", new_content, re.DOTALL)
            if fm_match:
                fm = fm_match.group(1)
                if "tags:" in fm:
                    # insert after tags:
                    lines = []
                    for l in fm.splitlines():
                        lines.append(l)
                        if l.strip().startswith("tags:"):
                            for t in tags_to_add:
                                lines.append(f"  - {t}")
                    new_fm = "\n".join(lines)
                    new_content = re.sub(r"^---\s*\n(.*?)\n---", lambda m: f"---\n{new_fm}\n---", new_content, count=1, flags=re.DOTALL)
                    changed = True
                else:
                    tag_block = "tags:\n" + "\n".join(f"  - {t}" for t in tags_to_add)
                    new_fm = f"{tag_block}\n{fm}"
                    new_content = re.sub(r"^---\s*\n(.*?)\n---", lambda m: f"---\n{new_fm}\n---", new_content, count=1, flags=re.DOTALL)
                    changed = True
        else:
            tag_block = "---\ntags:\n" + "\n".join(f"  - {t}" for t in tags_to_add) + "\n---\n\n"
            new_content = tag_block + new_content
            changed = True

    # Add backlink if missing
    if not analysis["has_backlink"]:
        new_content = new_content.rstrip() + "\n\n---\n[[CONTEXT|← Наверх]]\n"
        changed = True

    if changed:
        with open(fp, "w", encoding="utf-8") as f:
            f.write(new_content)

    return changed

def main():
    parser = argparse.ArgumentParser(description="Аудит и доставка тегов и обратных навигационных ссылок")
    parser.add_argument("--check", action="store_true", help="Только проверка")
    parser.add_argument("--fix", action="store_true", help="Применить автоматическую доставку")
    parser.add_argument("--path", type=str, default="", help="Ограничить каталогом")
    args = parser.parse_args()

    target = os.path.join(VAULT_ROOT, args.path) if args.path else VAULT_ROOT
    if not os.path.exists(target):
        print(f"Ошибка: {target} не существует.")
        sys.exit(1)

    print(f"Сканирование заметок в: {target}")
    total_files = 0
    missing_links_count = 0
    missing_tags_count = 0
    to_fix = []

    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if f.endswith(".md") and f not in IGNORE_FILES and not f.startswith("."):
                fp = os.path.join(root, f)
                total_files += 1
                res = analyze_file(fp)
                if res:
                    if not res["has_backlink"] or res["missing_tags"]:
                        to_fix.append(res)
                        if not res["has_backlink"]:
                            missing_links_count += 1
                        if res["missing_tags"]:
                            missing_tags_count += 1

    print(f"Всего проверено заметок: {total_files}")
    print(f"Файлов без обратной ссылки на CONTEXT/индекс: {missing_links_count}")
    print(f"Файлов с неполными тегами каталога: {missing_tags_count}")
    print(f"Всего файлов, требующих нормализации: {len(to_fix)}")

    if args.fix:
        print("\nЗапуск доставки тегов и навигационных ссылок (--fix)...")
        fixed_count = 0
        for item in to_fix:
            if fix_file(item):
                fixed_count += 1
        print(f"Готово! Успешно обновлено заметок: {fixed_count}.")
    elif not args.check:
        print("\nДля автоматического исправления запустите с флагом --fix:")
        print(f"python3 \"{os.path.abspath(__file__)}\" --fix [--path <каталог>]")

if __name__ == "__main__":
    main()
