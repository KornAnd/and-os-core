#!/usr/bin/env python3
"""
project_registry.py — Единый Реестр Внешних Программных Систем и Веб-Сервисов ANDREY OS (v1.0.0).
Каталогизирует все автономные внешние сервисы, веб-приложения (React, Vite, Python, Streamlit),
их порты запуска, команды, стеки и схемы данных в SQLite (task_vault.db).
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

try:
    from and_os.lib.core.root_config import RootConfig
    VAULT_ROOT = Path(RootConfig.load().vault_root)
except Exception:
    VAULT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = VAULT_ROOT / "and_os" / "var" / "task_vault.db"
JSON_SNAPSHOT = VAULT_ROOT / "and_os" / "var" / "external_projects.json"

DEFAULT_PROJECTS = [
    {
        "id": "mars_gantt",
        "name": "Pulsar Mars Gantt Dashboard (Мотомарс: Большая гонка)",
        "category": "Web Dashboard",
        "stack": "Python Web / Master Supervisor / Ftrack API",
        "local_port": 8087,
        "repo_path": "and_os/opt/apps/ftrack_gantt_mars",
        "data_source": "~/.pulsar_cache/ftrack_gantt/ftrack_gantt_mars.json",
        "run_command": "sys_cli.py daemon restart --target mars_gantt",
        "description": "Интерактивный дашборд готовности эпизодов, шотов и ассетов проекта Марс.",
        "status": "PRODUCTION"
    },
    {
        "id": "kot_gantt",
        "name": "Pulsar Kot Gantt Dashboard (Кот ученый / Лукоморье)",
        "category": "Web Dashboard",
        "stack": "Python Web / Master Supervisor / Ftrack API",
        "local_port": 8092,
        "repo_path": "and_os/opt/apps/ftrack_gantt_kot",
        "data_source": "~/.pulsar_cache/ftrack_gantt/ftrack_gantt_kot.json",
        "run_command": "sys_cli.py daemon restart --target kot_gantt",
        "description": "Интерактивный дашборд производства сериала Кот ученый.",
        "status": "PRODUCTION"
    },
    {
        "id": "and_terminal",
        "name": "AND_Terminal Web GUI",
        "category": "System Terminal",
        "stack": "Python Web / AnD os Kernel Bus",
        "local_port": 8099,
        "repo_path": "~/Yandex.Disk.localized/WORK/pulsar/AND_Terminal",
        "data_source": "http://localhost:8099",
        "run_command": "python3 ~/Yandex.Disk.localized/WORK/pulsar/AND_Terminal/server.py",
        "description": "Графический веб-терминал и операционный пульт управления AnD os.",
        "status": "STANDBY"
    },
    {
        "id": "omniroute_gateway",
        "name": "Omniroute Local Gateway",
        "category": "AI Gateway",
        "stack": "Python / Node Proxy",
        "local_port": 20128,
        "repo_path": "System/Omniroute",
        "data_source": "http://localhost:20128",
        "run_command": "omniroute start",
        "description": "Локальный AI-шлюз и прокси-маршрутизатор запросов к LLM.",
        "status": "STANDBY"
    }
]

def init_external_projects_db():
    """Ensures external_projects table exists in task_vault.db and populates defaults."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS external_projects (
            id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            stack TEXT,
            local_port INTEGER,
            repo_path TEXT,
            data_source TEXT,
            run_command TEXT,
            description TEXT,
            status TEXT,
            updated_at TEXT
        )
    """)
    
    today_str = datetime.now().isoformat()
    for p in DEFAULT_PROJECTS:
        cursor.execute("""
            INSERT OR REPLACE INTO external_projects 
            (id, name, category, stack, local_port, repo_path, data_source, run_command, description, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (p["id"], p["name"], p["category"], p["stack"], p["local_port"], p["repo_path"], p["data_source"], p["run_command"], p["description"], p["status"], today_str))
    
    conn.commit()
    conn.close()

    # Dump JSON snapshot
    with open(JSON_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump({"updated_at": today_str, "projects": DEFAULT_PROJECTS}, f, ensure_ascii=False, indent=2)

def register_project(project_dict):
    """Registers or updates a new external project in the system registry."""
    init_external_projects_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today_str = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT OR REPLACE INTO external_projects 
        (id, name, category, stack, local_port, repo_path, data_source, run_command, description, status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        project_dict.get("id"),
        project_dict.get("name"),
        project_dict.get("category", "General Web App"),
        project_dict.get("stack", "Fullstack"),
        project_dict.get("local_port", 0),
        project_dict.get("repo_path", ""),
        project_dict.get("data_source", ""),
        project_dict.get("run_command", ""),
        project_dict.get("description", ""),
        project_dict.get("status", "ACTIVE"),
        today_str
    ))
    conn.commit()
    conn.close()
    print(f"✅ Внешний проект '{project_dict.get('name')}' зарегистрирован в SQLite реестре!")

def get_registered_projects():
    """Returns all registered external projects."""
    if not DB_PATH.exists():
        init_external_projects_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM external_projects")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

if __name__ == "__main__":
    init_external_projects_db()
    projects = get_registered_projects()
    print(f"🌐 [Project Registry] Проиндексировано внешних веб-приложений и сервисов: {len(projects)}")
    for p in projects:
        print(f"  • [{p['id']}] {p['name']} ({p['category']})")
        print(f"    Стек: {p['stack']} | Порт: :{p['local_port']} | Команда: `{p['run_command']}`\n")
