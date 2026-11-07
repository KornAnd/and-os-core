#!/usr/bin/env python3
"""mattermost_inspector.py — Анализатор структуры, аудитор и staged-экстрактор срезов Mattermost.

Архитектурный стандарт: AnD os v8.1 (Правило №63: Mattermost Data Pipeline Decoupling).
- Бэкенд Ядра: забор данных из Mattermost REST API v4 (или структурирование существующего оффлайн-кэша),
  очистка шума, формирование сырого канонического среза (raw_YYYYMMDD) и авто-симлинк raw_latest.
- Проекты (Марс, Кот): выступают строго как фронтенд/интерпретаторы готового кэша.

Использование:
  python3 mattermost_inspector.py inspect [--project mars|kot]
  python3 mattermost_inspector.py verify-slice [--project mars|kot]
  python3 mattermost_inspector.py staged-export [--project mars|kot] [--days 30]
  python3 mattermost_inspector.py init-offline-slices
"""

import os
import sys
import re
import json
import time
import argparse
import datetime
import subprocess
import urllib.request
import urllib.parse
import ssl
from collections import defaultdict, Counter

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SERVER = "https://most.Studio.com"
API_BASE = f"{SERVER}/api/v4"

SYSTEM_POST_TYPES = {
    "system_join_channel",
    "system_leave_channel",
    "system_add_to_channel",
    "system_remove_from_channel",
    "system_header_change",
    "system_purpose_change",
    "system_channel_deleted",
}

PROJECT_TEAMS = {
    "mars": ["mars", "mars-management", "mars-freels"],
    "kot": ["kot", "kot-management", "kot-freels"]
}

PROJECT_DIR_MAP = {
    "mars": os.path.join(VAULT_ROOT, "Nero", "work", "mars", "info_mars"),
    "kot": os.path.join(VAULT_ROOT, "Nero", "work", "kot", "info_kot")
}


def get_token():
    """Извлечь токен доступа из macOS Keychain или переменной окружения."""
    tok = os.environ.get("MATTERMOST_TOKEN")
    if not tok:
        res = subprocess.run(
            ["security", "find-generic-password", "-s", "mattermost-token", "-w"],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            tok = res.stdout.strip()
    return tok


def api_request(endpoint, method="GET", data=None, token=None):
    """Выполнить HTTP-запрос к Mattermost REST API v4."""
    if not token:
        token = get_token()
    if not token:
        raise RuntimeError("Токен Mattermost не найден в Keychain (сервис 'mattermost-token')")

    url = f"{API_BASE}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_msg)
            err_text = err_json.get("message", err_msg)
        except Exception:
            err_text = err_msg
        raise RuntimeError(f"HTTP {e.code}: {err_text}")


def get_project_dir(project_key):
    return PROJECT_DIR_MAP.get(project_key.lower())


def run_verify_slice(project_key):
    """Проверить целостность локальных срезов для проекта."""
    proj_dir = get_project_dir(project_key)
    if not proj_dir or not os.path.exists(proj_dir):
        print(f"❌ Каталог проекта '{project_key}' не найден: {proj_dir}")
        return False

    print(f"\n📂 [VERIFY-SLICE] Проверка локальных срезов Mattermost для проекта '{project_key}'...")
    slices = [d for d in os.listdir(proj_dir) if d.startswith("raw_") and os.path.isdir(os.path.join(proj_dir, d))]
    print(f"Найдено локальных срезов: {len(slices)}")

    if not slices:
        print(f"   ⚠️ Срезы raw_* отсутствуют в {proj_dir}")
        return False

    all_ok = True
    for s in sorted(slices):
        s_path = os.path.join(proj_dir, s)
        is_link = os.path.islink(s_path)
        real_target = os.path.realpath(s_path) if is_link else s_path

        posts_file = os.path.join(s_path, "posts.json")
        threads_file = os.path.join(s_path, "threads.json")
        manifest_file = os.path.join(s_path, "export_manifest.json")
        summary_file = os.path.join(s_path, "summary.json")

        def count_json(path):
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return len(data) if isinstance(data, (list, dict)) else 1
                except Exception:
                    return -1
            return 0

        posts_count = count_json(posts_file)
        threads_count = count_json(threads_file)
        manifest_ok = os.path.exists(manifest_file)
        summary_ok = os.path.exists(summary_file)

        status_posts = f"{posts_count:5} записей 🟢" if posts_count > 0 else "🔴 ОТСУТСТВУЕТ"
        status_threads = f"{threads_count:5} тредов  🟢" if threads_count > 0 else "🔴 ОТСУТСТВУЕТ"

        link_mark = f" ➔ {os.path.basename(real_target)}" if is_link else ""
        print(f"\n📁 Срез: {s}{link_mark}")
        print(f"   • posts.json:          {status_posts}")
        print(f"   • threads.json:        {status_threads}")
        print(f"   • export_manifest.json: {'✓' if manifest_ok else '✗'}")
        print(f"   • summary.json:        {'✓' if summary_ok else '✗'}")

        if posts_count <= 0 or not manifest_ok:
            all_ok = False

    return all_ok


def parse_markdown_to_posts(file_path, channel_name):
    """Извлечь структурированные посты из имеющихся исторических Markdown-заметок."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Паттерн сообщений: Автор \n [HH:MM](url) \n Текст
    pattern = r'([^\n]+)\n+\[(\d{1,2}:\d{2})\]\((https://most\.Studio\.com/[^/]+/pl/([a-zA-Z0-9]+))\)\n+(.*?)(?=(?:[^\n]+\n+\[\d{1,2}:\d{2}\]\(https://most\.Studio\.com)|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    posts = []
    for author, tm, url, pid, body in matches:
        author = author.strip("# -* \t\n\r")
        body = body.strip()
        posts.append({
            "id": pid,
            "root_id": "",
            "author_name": author,
            "time_str": tm,
            "url": url,
            "channel_name": channel_name,
            "message": body,
            "length": len(body),
            "create_at": 1788800000000  # Базовый timestamp эпохи 2026-09
        })
    return posts


def build_threads(posts):
    """Группировка постов по тредам и выявление решений."""
    threads = defaultdict(list)
    for p in posts:
        rid = p.get("root_id") or p.get("id")
        threads[rid].append(p)
    return dict(threads)


def build_summary(project_key, posts, threads):
    """Построить компактную машиночитаемую и человекочитаемую сводку."""
    channels = Counter(p.get("channel_name", "unknown") for p in posts)
    authors = Counter(p.get("author_name", "unknown") for p in posts)

    return {
        "project": project_key,
        "total_posts": len(posts),
        "total_threads": len(threads),
        "channels_distribution": dict(channels),
        "top_authors": dict(authors.most_common(10)),
        "updated_at": datetime.datetime.now().isoformat()
    }


def create_slice(project_key, posts, date_str=None, source_mode="offline_migration"):
    """Создать герметичный срез raw_YYYYMMDD с манифестом и обновить raw_latest."""
    proj_dir = get_project_dir(project_key)
    if not proj_dir:
        raise ValueError(f"Неизвестный проект: {project_key}")
    os.makedirs(proj_dir, exist_ok=True)

    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y%m%d")

    target_dir = os.path.join(proj_dir, f"raw_{date_str}")
    os.makedirs(target_dir, exist_ok=True)

    threads = build_threads(posts)
    summary = build_summary(project_key, posts, threads)

    # 1. posts.json
    with open(os.path.join(target_dir, "posts.json"), "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    # 2. threads.json
    with open(os.path.join(target_dir, "threads.json"), "w", encoding="utf-8") as f:
        json.dump(threads, f, ensure_ascii=False, indent=2)

    # 3. summary.json
    with open(os.path.join(target_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 4. export_manifest.json
    manifest = {
        "manifest_version": "1.0",
        "service": "mattermost",
        "project": project_key,
        "slice_date": date_str,
        "created_at": datetime.datetime.now().isoformat(),
        "source_mode": source_mode,
        "schema": {
            "entity": "Mattermost Post & Thread Tree",
            "version": "v1.0"
        },
        "counts": {
            "posts": len(posts),
            "threads": len(threads),
            "channels": len(summary["channels_distribution"])
        }
    }
    with open(os.path.join(target_dir, "export_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 5. Симлинк raw_latest
    symlink_path = os.path.join(proj_dir, "raw_latest")
    try:
        if os.path.islink(symlink_path) or os.path.exists(symlink_path):
            os.remove(symlink_path)
        os.symlink(os.path.basename(target_dir), symlink_path)
    except Exception as e:
        print(f"   ⚠️ Не удалось обновить симлинк raw_latest: {e}")

    print(f"✅ [SLICE CREATED] {project_key.upper()} ➔ {target_dir} (symlink: raw_latest)")
    print(f"   • Постов: {len(posts)} | Тредов: {len(threads)} | Каналы: {list(summary['channels_distribution'].keys())}")
    return target_dir


def init_offline_slices():
    """Сформировать стартовые локальные срезы из существующих файлов проекта."""
    print("🔄 Инициализация базовых офлайн-срезов Mattermost...")

    # Марс
    m_follow = parse_markdown_to_posts(
        os.path.join(VAULT_ROOT, "Nero/work/mars/info_mars/follow_up/follow_up (mars).md"),
        "mm_follow_up"
    )
    m_stand = parse_markdown_to_posts(
        os.path.join(VAULT_ROOT, "Nero/work/mars/info_mars/stend_up/stend_up (mars).md"),
        "mm_stand_up"
    )
    all_mars = m_follow + m_stand
    if all_mars:
        create_slice("mars", all_mars, date_str="20260908", source_mode="offline_vault_archive")

    # Кот
    k_follow = parse_markdown_to_posts(
        os.path.join(VAULT_ROOT, "Nero/work/kot/info_kot/follow_up/follow_up (kot).md"),
        "kt_follow-up"
    )
    k_stand = parse_markdown_to_posts(
        os.path.join(VAULT_ROOT, "Nero/work/kot/info_kot/stend_up/stend_up (kot).md"),
        "kt_stand_up"
    )
    all_kot = k_follow + k_stand
    if all_kot:
        create_slice("kot", all_kot, date_str="20260908", source_mode="offline_vault_archive")


def run_inspect(project_key):
    """Аудит структуры и каналов проекта (через API при наличии токена, иначе по локальному кэшу)."""
    tok = get_token()
    proj_dir = get_project_dir(project_key)
    print(f"\n🔍 [INSPECT] Аудит каналов Mattermost для проекта '{project_key}'...")

    if not tok:
        print("ℹ️ Токен Mattermost отсутствует в Keychain. Работа в режиме [OFFLINE / LOCAL CACHE].")
        run_verify_slice(project_key)
        return

    # Если токен есть — опрашиваем живой API
    try:
        teams = api_request("users/me/teams")
        target_teams = PROJECT_TEAMS.get(project_key.lower(), [project_key])
        found_teams = [t for t in teams if t.get("name", "").lower() in target_teams]
        print(f"Найдено доступных команд для {project_key}: {len(found_teams)}")
        for t in found_teams:
            print(f"  • {t.get('display_name')} [ID: {t.get('id')}]")
            channels = api_request(f"users/me/teams/{t['id']}/channels")
            named = [c for c in channels if c.get("type") in ("O", "P")]
            print(f"    Каналов: {len(named)}")
            for c in named[:10]:
                print(f"      - #{c.get('display_name')} ({c.get('name')})")
    except Exception as e:
        print(f"❌ Ошибка сетевого запроса к Mattermost API: {e}")
        print("Переключение в офлайн-режим проверки среза:")
        run_verify_slice(project_key)


def run_staged_export(project_key, days=30):
    """Поэтапный бережный забор постов из ключевых каналов через API."""
    tok = get_token()
    if not tok:
        print("❌ Ошибка: для онлайн staged-export требуется токен в Keychain ('mattermost-token').")
        print("   Используйте существующий локальный кэш: raw_latest / verify-slice")
        return None

    print(f"🚀 [STAGED-EXPORT] Запуск забора данных Mattermost для проекта '{project_key}'...")
    # Режим онлайн-экспорта при наличии токена
    # Будет вызван сетевой сборщик
    pass


def main():
    parser = argparse.ArgumentParser(description="Mattermost Inspector & Slice Manager (AnD os v8.1)")
    subparsers = parser.add_subparsers(dest="command", help="Команда для выполнения")

    p_inspect = subparsers.add_parser("inspect", help="Аудит каналов и структуры Mattermost")
    p_inspect.add_argument("--project", default="mars", choices=["mars", "kot"], help="Проект")

    p_verify = subparsers.add_parser("verify-slice", help="Проверка целостности локального среза")
    p_verify.add_argument("--project", default="mars", choices=["mars", "kot"], help="Проект")

    p_init = subparsers.add_parser("init-offline-slices", help="Инициализация базовых срезов из локального архива")

    p_export = subparsers.add_parser("staged-export", help="Сбор свежего среза из Mattermost API")
    p_export.add_argument("--project", default="mars", choices=["mars", "kot"], help="Проект")
    p_export.add_argument("--days", type=int, default=30, help="Период в днях")

    args = parser.parse_args()

    if args.command == "inspect":
        run_inspect(args.project)
    elif args.command == "verify-slice":
        run_verify_slice(args.project)
    elif args.command == "init-offline-slices":
        init_offline_slices()
    elif args.command == "staged-export":
        run_staged_export(args.project, args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
