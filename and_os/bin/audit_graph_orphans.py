#!/usr/bin/env python3
"""
audit_graph_orphans.py — Точный сканер графовой связности Obsidian Vault.
Находит файлы, которые в визуальном графе Obsidian отображаются сиротами:
1. Имеют 0 входящих ссылок из видимых .md файлов (исключая игнорируемые CONTEXT.md)
2. Имеют 0 исходящих ссылок на видимые .md файлы (или только обратные ссылки на скрытый CONTEXT.md)
"""

import os
import sys
import re
import json
from collections import defaultdict

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".cache", "repo"}
IGNORE_FILES = {".DS_Store"}

# Файлы, которые Obsidian скрывает по userIgnoreFilters в app.json
HIDDEN_FROM_GRAPH = {"CONTEXT.md", "context_export.md", "context_lite.md"}

def is_hidden_file(filename):
    bn = os.path.basename(filename)
    if bn in HIDDEN_FROM_GRAPH or bn.startswith("context_"):
        return True
    return False

import unicodedata

def extract_wikilinks(content):
    # [[target|alias]] or [[target]]
    matches = re.findall(r"\[\[([^\|\]\r\n]+)(?:\|[^\]\r\n]+)?\]\]", content)
    links = []
    for m in matches:
        clean = unicodedata.normalize('NFC', m.strip())
        if clean.endswith(".md"):
            clean = clean[:-3]
        links.append(clean)
    return links

def main():
    all_files = {} # rel_path -> { "basename": str, "name_no_ext": str, "outgoing": list }
    
    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if not f.endswith(".md") or f in IGNORE_FILES:
                continue
            full_path = os.path.join(root, f)
            rel_path = unicodedata.normalize('NFC', os.path.relpath(full_path, VAULT_ROOT))
            
            # Скрытые из графа файлы не учитываются как узлы
            if is_hidden_file(rel_path):
                continue
                
            bn = unicodedata.normalize('NFC', os.path.basename(rel_path))
            name_no_ext = bn[:-3]
            
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                outgoing = extract_wikilinks(content)
            except Exception:
                outgoing = []
                
            all_files[rel_path] = {
                "full_path": full_path,
                "basename": bn,
                "name_no_ext": name_no_ext,
                "outgoing": outgoing
            }

    # Построение матрицы входящих связей
    # Ссылка может вести по относительному пути (Folder/Name) или чисто по basename (Name)
    in_degree = defaultdict(int)
    out_degree_visible = defaultdict(int)

    # Быстрый индекс имен файлов
    basename_map = defaultdict(list)
    for rel_path, data in all_files.items():
        basename_map[data["name_no_ext"]].append(rel_path)
        basename_map[data["basename"]].append(rel_path)
        basename_map[rel_path].append(rel_path)
        if rel_path.endswith(".md"):
            basename_map[rel_path[:-3]].append(rel_path)

    for src_rel, data in all_files.items():
        for target in data["outgoing"]:
            # Проверяем, ведет ли ссылка на существующий видимый файл
            target_clean = os.path.basename(target)
            if target in basename_map or target_clean in basename_map:
                # Нашли валидную цель в графе
                target_paths = basename_map.get(target) or basename_map.get(target_clean)
                for tp in target_paths:
                    if tp != src_rel: # петли на себя не считаем
                        in_degree[tp] += 1
                        out_degree_visible[src_rel] += 1

    # Сироты в терминах Obsidian:
    # Узел в графе изолирован, если у него in_degree == 0 И out_degree == 0 (нет ни одного видимого ребра)
    isolated_orphans = []
    # Слабосвязанные: входящих 0 (тупик на входе, на него никто не ссылается)
    zero_in = []

    for rel_path, data in all_files.items():
        in_c = in_degree[rel_path]
        out_c = out_degree_visible[rel_path]
        if in_c == 0 and out_c == 0:
            isolated_orphans.append((rel_path, in_c, out_c))
        elif in_c == 0:
            zero_in.append((rel_path, in_c, out_c))

    print(f"📊 Всего видимых Markdown-файлов в графе: {len(all_files)}")
    print(f"🔴 Полностью изолированные сироты (0 входящих, 0 исходящих): {len(isolated_orphans)}")
    print(f"🟡 Односторонние заметки (0 входящих, но есть исходящие): {len(zero_in)}")

    # Группировка изолированных сирот по корневым каталогам
    by_folder = defaultdict(list)
    for p, inc, outc in isolated_orphans:
        root_folder = p.split(os.sep)[0]
        by_folder[root_folder].append(p)

    print("\n📂 Распределение изолированных сирот по каталогам:")
    for folder, files in sorted(by_folder.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  • {folder}/ : {len(files)} сирот")

    # Сохраняем отчет для работы
    report_file = os.path.join(VAULT_ROOT, "and_os/var/graph_orphans_report.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as rf:
        json.dump({
            "total_visible": len(all_files),
            "isolated_count": len(isolated_orphans),
            "zero_in_count": len(zero_in),
            "isolated_by_folder": {k: len(v) for k, v in by_folder.items()},
            "isolated_files": [p for p, _, _ in isolated_orphans]
        }, rf, ensure_ascii=False, indent=2)

    print(f"\n💾 Полный отчет сохранен: and_os/var/graph_orphans_report.json")

if __name__ == "__main__":
    main()
