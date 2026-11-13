#!/usr/bin/env python3
"""
task_db_engine.py — Local Task Database and Vault Indexing Engine (SQLite Engine).
Principle: Think in Code (Rule #16), Zero-Token Querying.

Features:
  1. Scans the Obsidian Vault (the Tasks/, Nero/, Product/, Story/, Ta-Bu/ catalogs).
  2. Extracts the checkboxes (- [ ] / - [x]), the tags #task, #deadline, #urgent and the dates.
  3. Indexes them into the hidden local database and_os/var/task_vault.db.
  4. Generates the native visual canvas Nero/Dashboard.canvas.

Usage:
  python3 task_db_engine.py --index               # Full-text indexing of the vault into SQLite
  python3 task_db_engine.py --query-pending        # Fast JSON output of the unfinished tasks
  python3 task_db_engine.py --build-canvas         # Generation of the visual Canvas dashboard
"""

import os
import sys
import re
import json
import sqlite3
import argparse
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DB_PATH = os.path.join(VAULT_ROOT, "and_os/var/task_vault.db")
CANVAS_PATH = os.path.join(VAULT_ROOT, "Nero/Dashboard.canvas")

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".pdf_archive"}

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            task_text TEXT NOT NULL,
            is_completed INTEGER DEFAULT 0,
            tag TEXT,
            due_date TEXT,
            domain TEXT,
            last_indexed TEXT
        )
    """)
    conn.commit()
    return conn

def index_vault():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")  # Re-index

    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    indexed_count = 0

    task_pattern = re.compile(r"^\s*-\s*\[([ xX])\]\s+(.+)$")
    tag_pattern = re.compile(r"#([a-zA-Z0-9_\-\/]+)")
    date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if not f.endswith(".md") or f == "CONTEXT.md":
                continue
            fpath = os.path.join(root, f)
            rel_path = os.path.relpath(fpath, VAULT_ROOT)

            # Determine domain
            domain = "general"
            if rel_path.startswith("Nero/work/mars") or "mars" in rel_path.lower():
                domain = "mars"
            elif rel_path.startswith("Nero/work/kot") or "kot" in rel_path.lower():
                domain = "kot"
            elif "health" in rel_path.lower() or "sport" in rel_path.lower():
                domain = "health"
            elif rel_path.startswith("Ta-Bu") or "ta_bu" in rel_path.lower():
                domain = "ta_bu"

            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as file:
                    lines = file.readlines()
                for line in lines:
                    match = task_pattern.match(line)
                    if match:
                        completed = 1 if match.group(1).lower() == "x" else 0
                        t_text = match.group(2).strip()

                        tags = tag_pattern.findall(t_text)
                        tag_str = ",".join(tags) if tags else None

                        dates = date_pattern.findall(t_text)
                        due = dates[0] if dates else None

                        cursor.execute("""
                            INSERT INTO tasks (file_path, file_name, task_text, is_completed, tag, due_date, domain, last_indexed)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (rel_path, f, t_text, completed, tag_str, due, domain, today_str))
                        indexed_count += 1
            except (sqlite3.Error, OSError) as e:
                sys.stderr.write(f"[task_db_engine] Warning indexing tasks in {rel_path}: {e}\n")

    conn.commit()
    conn.close()
    return indexed_count

def query_pending_tasks(domain=None):
    if not os.path.exists(DB_PATH):
        index_vault()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if domain:
        cursor.execute("SELECT id, file_name, task_text, tag, due_date, domain FROM tasks WHERE is_completed = 0 AND domain = ? LIMIT 50", (domain,))
    else:
        cursor.execute("SELECT id, file_name, task_text, tag, due_date, domain FROM tasks WHERE is_completed = 0 LIMIT 50")
    
    rows = cursor.fetchall()
    conn.close()

    tasks = []
    for r in rows:
        tasks.append({
            "id": r[0],
            "file": r[1],
            "task": r[2],
            "tags": r[3],
            "due_date": r[4],
            "domain": r[5]
        })
    return tasks

def generate_dashboard_canvas():
    pending = query_pending_tasks()
    
    # Group by domain
    domains = {"mars": [], "kot": [], "health": [], "ta_bu": [], "general": []}
    for t in pending:
        d = t["domain"] if t["domain"] in domains else "general"
        domains[d].append(t)

    canvas_nodes = []
    canvas_edges = []

    # Title node
    canvas_nodes.append({
        "id": "node_title",
        "type": "text",
        "text": "# 🚀 ANDREY OS — Live Executive Dashboard\n> Автоматически обновляемый дашборд состояния задач и проектов.",
        "x": 0, "y": 0, "width": 800, "height": 120
    })

    x_offsets = {"mars": 0, "kot": 420, "health": 840, "ta_bu": 1260, "general": 1680}
    colors = {"mars": "1", "kot": "2", "health": "3", "ta_bu": "4", "general": "5"}
    titles = {
        "mars": "🔴 Проект Марс (Задачи)",
        "kot": "🟡 Проект Кот Ученый",
        "health": "🟢 Здоровье & Спорт",
        "ta_bu": "🔵 Стартап Ta-Bu",
        "general": "⚪ Общие Задачи Vault"
    }

    for dom, task_list in domains.items():
        x_pos = x_offsets[dom]
        text_lines = [f"## {titles[dom]}\n"]
        if not task_list:
            text_lines.append("_Все задачи выполнены или не найдены._")
        else:
            for t in task_list[:8]:
                text_lines.append(f"- [ ] {t['task']} `[[{t['file']}]]`")

        canvas_nodes.append({
            "id": f"node_{dom}",
            "type": "text",
            "text": "\n".join(text_lines),
            "x": x_pos, "y": 180,
            "width": 380, "height": 450,
            "color": colors[dom]
        })

    canvas_data = {"nodes": canvas_nodes, "edges": canvas_edges}
    with open(CANVAS_PATH, "w", encoding="utf-8") as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)

    return CANVAS_PATH

def main():
    parser = argparse.ArgumentParser(description="Task DB & Canvas Engine")
    parser.add_argument("--index", action="store_true", help="Index all Vault tasks into SQLite")
    parser.add_argument("--query-pending", action="store_true", help="Print the unfinished tasks as JSON")
    parser.add_argument("--domain", type=str, help="Filter by domain")
    parser.add_argument("--build-canvas", action="store_true", help="Generate the Dashboard.canvas")

    args = parser.parse_args()

    if args.index:
        count = index_vault()
        print(json.dumps({"status": "SUCCESS", "indexed_tasks": count}, ensure_ascii=False, indent=2))
    elif args.query_pending:
        tasks = query_pending_tasks(args.domain)
        print(json.dumps({"status": "SUCCESS", "count": len(tasks), "tasks": tasks}, ensure_ascii=False, indent=2))
    elif args.build_canvas:
        c_path = generate_dashboard_canvas()
        print(json.dumps({"status": "SUCCESS", "canvas_path": c_path}, ensure_ascii=False, indent=2))
    else:
        # Default run indexing only
        c = index_vault()
        print(json.dumps({"status": "SUCCESS", "indexed_tasks": c}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
