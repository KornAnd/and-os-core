#!/usr/bin/env python3
"""
script_chunker.py — инструмент умного извлечения фрагментов из крупных текстов/сценариев/книг.
Принцип: Think in Code (Правило №16) & Context Budget (Правило №9).

Экономия: до 90% токенов за счёт выдачи ровно нужного Эпизода, Акта, Главы или Сцены.

Использование:
  python3 script_chunker.py --file "Book/Страшный Сон/Сон (book).md" --act 1
  python3 script_chunker.py --file "Product/Projects/Kot/Сценарий (Kot).md" --episode 5
  python3 script_chunker.py --file "Book/Лидерство в CG Искусство вдохновлять!/Лидерство в CG.md" --chapter 3
  python3 script_chunker.py --file "Product/Projects/Kot/Сценарий (Kot).md" --search "Баба Яга"
"""

import os
import sys
import re
import argparse

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

def get_abs_path(path_str):
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(VAULT_ROOT, path_str)

def extract_chunk(filepath, act=None, episode=None, chapter=None, scene=None, search=None, max_lines=150):
    abs_p = get_abs_path(filepath)
    if not os.path.exists(abs_p):
        print(f"❌ Файл не найден: {abs_p}")
        return

    with open(abs_p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lines = content.splitlines()
    print(f"📄 Извлечение из: {os.path.basename(abs_p)} (Всего строк: {len(lines)})")
    print("=" * 60)

    matched_lines = []
    
    # Фильтр по Акту
    if act is not None:
        pattern = re.compile(rf"(#+\s*.*(акт|act)\s*{act}\b|#+\s*{act}\s*акт)", re.IGNORECASE)
        recording = False
        for l in lines:
            if pattern.search(l):
                recording = True
            elif recording and re.match(r"#+\s*.*(акт|act)\s*\d+", l, re.IGNORECASE):
                break
            if recording:
                matched_lines.append(l)

    # Фильтр по Эпизоду / Серии
    elif episode is not None:
        pattern = re.compile(rf"(#+\s*.*(эпизод|серия|ep|episode)\s*{episode}\b)", re.IGNORECASE)
        recording = False
        for l in lines:
            if pattern.search(l):
                recording = True
            elif recording and re.match(r"#+\s*.*(эпизод|серия|ep|episode)\s*\d+", l, re.IGNORECASE):
                break
            if recording:
                matched_lines.append(l)

    # Фильтр по Главе
    elif chapter is not None:
        pattern = re.compile(rf"(#+\s*.*(глава|chapter)\s*{chapter}\b)", re.IGNORECASE)
        recording = False
        for l in lines:
            if pattern.search(l):
                recording = True
            elif recording and re.match(r"#+\s*.*(глава|chapter)\s*\d+", l, re.IGNORECASE):
                break
            if recording:
                matched_lines.append(l)

    # Фильтр по Сцене / Шоту
    elif scene is not None:
        pattern = re.compile(rf"(#+\s*.*(сцена|scene|эпизод|шot|shot)\s*{scene}\b)", re.IGNORECASE)
        recording = False
        for l in lines:
            if pattern.search(l):
                recording = True
            elif recording and re.match(r"#+\s*.*(сцена|scene|шot|shot)\s*\d+", l, re.IGNORECASE):
                break
            if recording:
                matched_lines.append(l)

    # Контекстный поиск по ключевому слову
    elif search is not None:
        pattern = re.compile(re.escape(search), re.IGNORECASE)
        for idx, l in enumerate(lines):
            if pattern.search(l):
                start = max(0, idx - 5)
                end = min(len(lines), idx + 15)
                matched_lines.append(f"--- [Строка {idx+1}] ---")
                matched_lines.extend(lines[start:end])
                matched_lines.append("...")

    # Фоллбэк: если ничего не передано, отдаем первых N строк
    if not matched_lines:
        if act or episode or chapter or scene:
            print(f"⚠️ Запрошенный блок (Акт {act} / Эпизод {episode} / Глава {chapter} / Сцена {scene}) не найден по заголовкам. Вывод первых {max_lines} строк:")
        matched_lines = lines[:max_lines]

    print("\n".join(matched_lines[:max_lines]))
    if len(matched_lines) > max_lines:
        print(f"\n... [Вывод обрезан: показано {max_lines} из {len(matched_lines)} строк]")

def main():
    parser = argparse.ArgumentParser(description="Умный чанкинг файлов сценариев и книг")
    parser.add_argument("--file", required=True, help="Путь к файлу сценария или книги")
    parser.add_argument("--act", type=int, help="Номер Акта")
    parser.add_argument("--episode", type=int, help="Номер Эпизода/Серии")
    parser.add_argument("--chapter", type=int, help="Номер Главы")
    parser.add_argument("--scene", type=str, help="Номер или ID Сцены/Шота")
    parser.add_argument("--search", type=str, help="Ключевое слово или персонаж для поиска")
    parser.add_argument("--lines", type=int, default=150, help="Максимальное количество выводимых строк")
    
    args = parser.parse_args()
    extract_chunk(args.file, act=args.act, episode=args.episode, chapter=args.chapter, search=args.search, max_lines=args.lines)

if __name__ == "__main__":
    main()
