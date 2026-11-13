#!/usr/bin/env python3
"""
script_chunker.py — the tool of the smart extraction of the fragments from the large texts/scripts/books.
The principle: Think in Code (Rule #16) & the Context Budget (Rule #9).

The economy: up to 90% of the tokens by providing the exactly needed Episode, Act, Chapter or Scene.

Usage:
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
        print(f"❌ The file was not found: {abs_p}")
        return

    with open(abs_p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lines = content.splitlines()
    print(f"📄 The extraction from: {os.path.basename(abs_p)} (The total lines: {len(lines)})")
    print("=" * 60)

    matched_lines = []
    
    # The filter by the Act
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

    # The filter by the Episode / the Series
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

    # The filter by the Chapter
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

    # The filter by the Scene / the Shot
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

    # The contextual search by the keyword
    elif search is not None:
        pattern = re.compile(re.escape(search), re.IGNORECASE)
        for idx, l in enumerate(lines):
            if pattern.search(l):
                start = max(0, idx - 5)
                end = min(len(lines), idx + 15)
                matched_lines.append(f"--- [The line {idx+1}] ---")
                matched_lines.extend(lines[start:end])
                matched_lines.append("...")

    # The fallback: if nothing was passed, provide the first N lines
    if not matched_lines:
        if act or episode or chapter or scene:
            print(f"⚠️ The requested block (the Act {act} / the Episode {episode} / the Chapter {chapter} / the Scene {scene}) was not found by the headers. The printing of the first {max_lines} lines:")
        matched_lines = lines[:max_lines]

    print("\n".join(matched_lines[:max_lines]))
    if len(matched_lines) > max_lines:
        print(f"\n... [The output was trimmed: shown the {max_lines} of the {len(matched_lines)} lines]")

def main():
    parser = argparse.ArgumentParser(description="The smart chunking of the scripts and the books files")
    parser.add_argument("--file", required=True, help="The path to the script or the book file")
    parser.add_argument("--act", type=int, help="The number of the Act")
    parser.add_argument("--episode", type=int, help="The number of the Episode/the Series")
    parser.add_argument("--chapter", type=int, help="The number of the Chapter")
    parser.add_argument("--scene", type=str, help="The number or the ID of the Scene/the Shot")
    parser.add_argument("--search", type=str, help="The keyword or the character for the search")
    parser.add_argument("--lines", type=int, default=150, help="The maximum count of the printed lines")
    
    args = parser.parse_args()
    extract_chunk(args.file, act=args.act, episode=args.episode, chapter=args.chapter, search=args.search, max_lines=args.lines)

if __name__ == "__main__":
    main()
