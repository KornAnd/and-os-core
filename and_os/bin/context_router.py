#!/usr/bin/env python3
"""
context_router.py — Умная быстрая БД и маршрутизатор контекстных файлов ANDREY OS (v1.0.0).
Индексирует все CONTEXT.md в Vault, ведет реестр в SQLite (task_vault.db) и JSON (context_map.json),
предоставляет быструю маршрутизацию задач к нужным контекстам за 0.005 сек.
"""

import os
import sys
import json
import sqlite3
import re
from pathlib import Path
from datetime import datetime

try:
    from and_os.lib.core.root_config import RootConfig
    VAULT_ROOT = Path(RootConfig.load().vault_root)
except Exception:
    VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(VAULT_ROOT))
DB_PATH = VAULT_ROOT / "and_os" / "var" / "task_vault.db"
JSON_SNAPSHOT = VAULT_ROOT / "Nero" / "ai" / "scratch" / "context_map.json"

EXCLUDE_DIRS = {".git", ".obsidian", ".pdf_archive", "node_modules", "__pycache__", ".venv", "Trash", ".trash"}

def extract_context_info(context_path):
    """Extracts summary and title from a CONTEXT.md file."""
    try:
        content = context_path.read_text(encoding="utf-8", errors="ignore")
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        
        title = context_path.parent.name
        summary_lines = []
        
        in_fm = False
        for l in lines:
            if l == "---":
                in_fm = not in_fm
                continue
            if in_fm:
                continue
            if l.startswith("#"):
                t_match = re.sub(r"^#+\s*", "", l)
                if t_match and title == context_path.parent.name:
                    title = t_match
                continue
            summary_lines.append(l)
            if len(summary_lines) >= 3:
                break
                
        summary = " ".join(summary_lines)[:250] if summary_lines else "Контекстный файл каталога."
        return title, summary
    except Exception as e:
        return context_path.parent.name, f"Ошибка чтения: {str(e)}"

def count_child_md_files(directory):
    """Counts .md files inside directory (excluding CONTEXT.md)."""
    count = 0
    try:
        for f in directory.iterdir():
            if f.is_file() and f.suffix.lower() == ".md" and f.name != "CONTEXT.md":
                count += 1
    except OSError as e:
        sys.stderr.write(f"[context_router] Warning accessing directory {directory}: {e}\n")
    return count

def sync_context_registry():
    """Scans all CONTEXT.md files in Vault and updates SQLite + JSON snapshot."""
    print("🔍 Сканирование и индексация всех CONTEXT.md файлов...")
    context_entries = []

    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        if "CONTEXT.md" in files:
            ctx_file = Path(root) / "CONTEXT.md"
            rel_ctx = str(ctx_file.relative_to(VAULT_ROOT))
            rel_dir = str(Path(root).relative_to(VAULT_ROOT))
            if rel_dir == ".":
                rel_dir = "корень"
                
            title, summary = extract_context_info(ctx_file)
            md_count = count_child_md_files(Path(root))
            
            entry = {
                "directory": rel_dir,
                "context_path": rel_ctx,
                "title": title,
                "summary": summary,
                "md_file_count": md_count,
                "updated_at": datetime.now().isoformat()
            }
            context_entries.append(entry)

    # Save JSON Snapshot
    JSON_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with open(JSON_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_contexts": len(context_entries),
            "contexts": context_entries
        }, f, ensure_ascii=False, indent=2)

    # Save SQLite
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS context_registry (
            directory TEXT PRIMARY KEY,
            context_path TEXT,
            title TEXT,
            summary TEXT,
            md_file_count INTEGER,
            updated_at TEXT
        )
    """)
    cursor.execute("DELETE FROM context_registry")
    for c in context_entries:
        cursor.execute("""
            INSERT INTO context_registry (directory, context_path, title, summary, md_file_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (c["directory"], c["context_path"], c["title"], c["summary"], c["md_file_count"], c["updated_at"]))
    conn.commit()
    conn.close()

    print(f"✅ База данных контекстов обновлена! Учтено {len(context_entries)} CONTEXT.md файлов.")
    print(f"📁 Файл снимка сохранен: and_os/var/context_map.json")
    return context_entries

def sync_knowledge_clippings_db():
    """Syncs Clippings/quick_knowledge_db.json into SQLite task_vault.db."""
    json_db = VAULT_ROOT / "Clippings" / "quick_knowledge_db.json"
    if not json_db.exists():
        return
    try:
        data = json.loads(json_db.read_text(encoding="utf-8"))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_clippings (
                id TEXT PRIMARY KEY,
                title TEXT,
                category TEXT,
                source TEXT,
                summary TEXT
            )
        """)
        cursor.execute("DELETE FROM knowledge_clippings")
        for item in data:
            cursor.execute("""
                INSERT OR REPLACE INTO knowledge_clippings (id, title, category, source, summary)
                VALUES (?, ?, ?, ?, ?)
            """, (item.get("id"), item.get("title"), item.get("category"), item.get("source"), item.get("summary")))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Ошибка синхронизации знаний в SQLite: {e}")

def sync_graph_registry_db():
    """Syncs and_os/etc/SYSTEM_GRAPH_REGISTRY.json into SQLite task_vault.db."""
    reg_file = VAULT_ROOT / "Nero" / "ai" / "reference" / "SYSTEM_GRAPH_REGISTRY.json"
    if not reg_file.exists():
        return
    try:
        data = json.loads(reg_file.read_text(encoding="utf-8"))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_manifest_graph (
                file_path TEXT PRIMARY KEY,
                role TEXT,
                description TEXT,
                island TEXT,
                depends_on TEXT,
                affects TEXT
            )
        """)
        cursor.execute("DELETE FROM system_manifest_graph")
        for fpath, meta in data.get("manifests", {}).items():
            cursor.execute("""
                INSERT OR REPLACE INTO system_manifest_graph (file_path, role, description, island, depends_on, affects)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                fpath,
                meta.get("role", ""),
                meta.get("desc", ""),
                meta.get("island", ""),
                json.dumps(meta.get("depends_on", []), ensure_ascii=False),
                json.dumps(meta.get("affects", []), ensure_ascii=False)
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Ошибка синхронизации графа зависимостей: {e}")

def route_task_to_context(query):
    """Fast unified routing across CONTEXT.md, Knowledge Clippings, and System Manifest Graph."""
    if not DB_PATH.exists():
        sync_context_registry()
        
    sync_knowledge_clippings_db()
    sync_graph_registry_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    raw_keywords = [k.strip().lower() for k in query.split() if len(k.strip()) > 2]
    try:
        from and_os.lib.core.bilingual_lexicon import expand_tokens
        keywords = list(expand_tokens(raw_keywords))
    except Exception:
        keywords = raw_keywords
    
    # 1. Search Context Registry
    cursor.execute("SELECT * FROM context_registry")
    ctx_rows = cursor.fetchall()
    
    # 2. Search Knowledge Clippings
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_clippings'")
    has_know = cursor.fetchone()
    know_rows = []
    if has_know:
        cursor.execute("SELECT * FROM knowledge_clippings")
        know_rows = cursor.fetchall()
        
    # 3. Search External Projects Registry
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='external_projects'")
    has_proj = cursor.fetchone()
    proj_rows = []
    if has_proj:
        cursor.execute("SELECT * FROM external_projects")
        proj_rows = cursor.fetchall()

    # 4. Search System Manifest Graph
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_manifest_graph'")
    has_graph = cursor.fetchone()
    graph_rows = []
    if has_graph:
        cursor.execute("SELECT * FROM system_manifest_graph")
        graph_rows = cursor.fetchall()

    conn.close()
    
    # Dual-Track Invariant Routing Boosters
    query_l = query.lower()
    is_Studio = any(k in query_l for k in ["кот", "марc", "марcа", "mars", "kot", "ftrack", "weeek", "субстанс", "substance", "renderman", "рендерман", "unreal", "ue5", "департамент"])
    is_tabu = any(k in query_l for k in ["та-бу", "ta-bu", "tabu", "комфи", "comfy", "comfyui", "controlnet", "давинчи", "davinci", "блокаут", "чудобус", "chbs", "greybox"])
    is_xcode = any(k in query_l for k in ["xcode", "swift", "swiftui", "spritekit", "ios", "iphone", "ipad", "геймдев", "игра", "игры", "gamedev"])

    ctx_results = []
    for r in ctx_rows:
        score = 0
        dir_l = (r["directory"] or "").lower()
        title_l = (r["title"] or "").lower()
        sum_l = (r["summary"] or "").lower()

        # Strict Domain Affinity
        if is_Studio and any(k in dir_l for k in ["product", "depart", "kot", "mars", "tasks"]):
            score += 50
        elif is_Studio and "ta-bu" in dir_l:
            score -= 100
            
        if is_tabu and any(k in dir_l for k in ["ta-bu", "pulsar", "montage"]):
            score += 50
        elif is_tabu and any(k in dir_l for k in ["product", "depart"]):
            score -= 100

        if is_xcode and any(k in dir_l for k in ["xcode", "ios"]):
            score += 60

        for kw in keywords:
            if kw in dir_l:
                score += 10
            elif kw in title_l:
                score += 5
            elif kw in sum_l:
                score += 1
        if score > 0 or not keywords:
            ctx_results.append({
                "directory": r["directory"],
                "context_path": r["context_path"],
                "title": r["title"],
                "summary": r["summary"],
                "score": score
            })
    ctx_results.sort(key=lambda x: x["score"], reverse=True)

    know_results = []
    for r in know_rows:
        score = 0
        text = f"{r['title']} {r['category']} {r['summary']}".lower()
        for kw in keywords:
            if kw in text:
                score += 1
        if score > 0:
            know_results.append({
                "title": r["title"],
                "category": r["category"],
                "source": r["source"],
                "summary": r["summary"],
                "score": score
            })
    know_results.sort(key=lambda x: x["score"], reverse=True)

    proj_results = []
    for r in proj_rows:
        score = 0
        text = f"{r['name']} {r['category']} {r['stack']} {r['description']}".lower()
        for kw in keywords:
            if kw in text:
                score += 1
        if score > 0:
            proj_results.append({
                "name": r["name"],
                "category": r["category"],
                "stack": r["stack"],
                "local_port": r["local_port"],
                "run_command": r["run_command"],
                "description": r["description"],
                "score": score
            })
    proj_results.sort(key=lambda x: x["score"], reverse=True)

    manifest_results = []
    for r in graph_rows:
        score = 0
        text = f"{r['file_path']} {r['role']} {r['description']} {r['island']}".lower()
        for kw in keywords:
            if kw in text:
                score += 1
        if score > 0:
            manifest_results.append({
                "file_path": r["file_path"],
                "role": r["role"],
                "description": r["description"],
                "island": r["island"],
                "depends_on": json.loads(r["depends_on"]),
                "affects": json.loads(r["affects"]),
                "score": score
            })
    manifest_results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "contexts": ctx_results,
        "knowledge": know_results,
        "external_projects": proj_results,
        "manifests": manifest_results
    }

def find_related_notes(note_path: str, limit: int = 4):
    """Find top semantically related notes and knowledge clippings for a given document (inspired by Smart Connections)."""
    target_p = Path(note_path)
    if not target_p.is_absolute():
        target_p = VAULT_ROOT / target_p
    if not target_p.exists():
        return []

    try:
        content = target_p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    words = re.findall(r"[\w]{3,}", content.lower())
    if not words:
        return []

    stopwords = {"the", "and", "for", "with", "this", "that", "from", "есть", "для", "это", "что", "как", "или", "все", "при", "после", "быть", "date", "project", "status", "tags", "focus", "island", "bridge"}
    freqs = {}
    for w in words:
        if w not in stopwords and not w.isdigit():
            freqs[w] = freqs.get(w, 0) + 1

    top_terms = sorted(freqs.items(), key=lambda x: x[1], reverse=True)[:15]
    search_keywords = [w for w, _ in top_terms]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT directory, context_path, title, summary FROM context_registry")
    candidates = []
    rel_target = str(target_p.relative_to(VAULT_ROOT)) if str(target_p).startswith(str(VAULT_ROOT)) else str(target_p)

    for r in cursor.fetchall():
        if r["context_path"] == rel_target:
            continue
        text = f"{r['directory']} {r['title']} {r['summary']}".lower()
        score = sum(freqs[w] for w in search_keywords if w in text)
        if score > 0:
            candidates.append({
                "type": "context",
                "title": r["title"],
                "path": r["context_path"],
                "score": score,
                "snippet": r["summary"][:160]
            })

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_clippings'")
    if cursor.fetchone():
        cursor.execute("SELECT title, category, source, summary FROM knowledge_clippings")
        for r in cursor.fetchall():
            text = f"{r['title']} {r['category']} {r['summary']}".lower()
            score = sum(freqs[w] for w in search_keywords if w in text)
            if score > 0:
                candidates.append({
                    "type": "clipping",
                    "title": r["title"],
                    "path": r["source"],
                    "score": score,
                    "snippet": r["summary"][:160]
                })

    conn.close()
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:limit]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "relate":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        rel = find_related_notes(target)
        print(f"🔗 СЕМАНТИЧЕСКИ СВЯЗАННЫЕ ЗАМЕТКИ ДЛЯ: '{target}'")
        print("=" * 60)
        for i, item in enumerate(rel, 1):
            print(f"{i}. [{item['type'].upper()}] {item['title']} (Score: {item['score']})")
            print(f"   Путь: {item['path']}")
            print(f"   Сниппет: {item['snippet']}...\n")
    elif len(sys.argv) > 1 and sys.argv[1] == "route":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        res = route_task_to_context(query)
        print(f"🎯 ЕДИНАЯ МАРШРУТИЗАЦИЯ ДЛЯ ЗАДАЧИ: '{query}'")
        print("=" * 60)
        
        if res.get("manifests"):
            print("📜 Манифесты, Правила и Регламенты (Зависимости):")
            for m in res["manifests"][:2]:
                print(f"  • [{m['island']}] {m['file_path']} ({m['role']})")
                print(f"    Суть: {m['description']}")
                if m["affects"]:
                    print(f"    ⚠️ Требует синхронного обновления: {', '.join(m['affects'])}")
                print()

        print("📍 Релевантные Контексты (CONTEXT.md):")
        for r in res["contexts"][:3]:
            print(f"  • [{r['directory']}] -> {r['context_path']}")
            print(f"    {r['title']}: {r['summary'][:100]}...\n")
        
        if res.get("knowledge"):
            print("📚 Релевантные Статьи и Конспекты Базы Знаний (Остров 1):")
            for k in res["knowledge"][:3]:
                print(f"  • [{k['category']}] {k['title']}")
                print(f"    Источник: [[{k['source']}]]")
                print(f"    Суть: {k['summary'][:120]}...\n")

        if res.get("external_projects"):
            print("🌐 Зарегистрированные Внешние Веб-Приложения / Проекты:")
            for p in res["external_projects"][:3]:
                print(f"  • [{p['category']}] {p['name']} (Порт: :{p['local_port']})")
                print(f"    Стек: {p['stack']} | Команда: `{p['run_command']}`")
                print(f"    {p['description']}\n")
    else:
        sync_context_registry()
        sync_knowledge_clippings_db()
        sync_graph_registry_db()


