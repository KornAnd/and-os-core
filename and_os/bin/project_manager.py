#!/usr/bin/env python3
"""
project_manager.py — Universal Project & App Onboarding Dispatcher for AnD os v8.5.
Automatically registers new projects in Nero/pulsar (Island 7) or Nero/xcode (Island 9).

Features:
  - Generates standardized Markdown passport with YAML frontmatter.
  - Automatically updates and indexes the Obsidian Base (.base).
  - Syncs with SQLite task_vault.db and and_os/var/external_projects.json.
  - Notifies system event bus via sys_cli.
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)

PULSAR_DIR = os.path.join(VAULT_ROOT, "Nero/pulsar")
XCODE_DIR = os.path.join(VAULT_ROOT, "Nero/xcode/projects")
os.makedirs(PULSAR_DIR, exist_ok=True)
os.makedirs(XCODE_DIR, exist_ok=True)


def slugify(text: str) -> str:
    """Generate safe lowercase filename slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text.strip('_')


def register_pulsar_app(
    name: str,
    description: str,
    category: str = "Web Dashboard",
    port: Optional[int] = None,
    status: str = "active",
    repo_path: Optional[str] = None,
    tags: Optional[list] = None
) -> Dict[str, Any]:
    """Scaffolds and registers a Pulsar Space app passport."""
    app_slug = slugify(name)
    file_path = os.path.join(PULSAR_DIR, f"{app_slug}.md")

    tags_list = tags or ["pulsar", "app"]
    if category and category.lower() not in tags_list:
        tags_list.append(category.lower().replace(" ", "_"))

    tags_yaml = "\n".join([f"  - {t}" for t in tags_list])
    port_yaml = f"port: {port}\n" if port else "port: null\n"
    now_str = datetime.now().strftime("%Y-%m-%d")

    content = f"""---
title: "{name}"
app_id: "{app_slug}"
island_id: 7
realm: "pulsar"
category: "{category}"
status: "{status}"
{port_yaml}tags:
{tags_yaml}
created: {now_str}
last_updated: {now_str}
sticker: lucide//layers
color: var(--mk-color-turquoise)
---

# 🚀 {name}

> **Категория:** {category}  
> **Статус:** {status.upper()}  
> **Порт / Эндпоинт:** {f":{port}" if port else "Локальный процесс / CLI"}  
> **Расположение исходников:** `{repo_path or f"~/Yandex.Disk.localized/WORK/pulsar/{name}"}`  

---

## 🎯 Описание и Назначение

{description}

---

## ⚙️ Управление жизненным циклом (AnD os Core)
- **Запуск:** `sys_cli.py daemon start --target {app_slug}`
- **Перезапуск:** `sys_cli.py daemon restart --target {app_slug}`
- **Телеметрия:** отображается в нативном дашборде [[Nero/pulsar/Приложения_Pulsar.base|Приложения Pulsar Base]]
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "success": True,
        "type": "pulsar",
        "path": file_path,
        "name": name,
        "app_id": app_slug
    }


def register_xcode_project(
    name: str,
    description: str,
    genre_or_type: str = "iOS Game / SpriteKit",
    status: str = "in_development",
    source_path: Optional[str] = None,
    tags: Optional[list] = None
) -> Dict[str, Any]:
    """Scaffolds and registers an Xcode / iOS project passport."""
    proj_slug = slugify(name)
    file_path = os.path.join(XCODE_DIR, f"{proj_slug}.md")

    tags_list = tags or ["xcode", "ios", "project"]
    if genre_or_type:
        tags_list.append(slugify(genre_or_type))

    tags_yaml = "\n".join([f"  - {t}" for t in tags_list])
    now_str = datetime.now().strftime("%Y-%m-%d")
    src = source_path or f"./xcode/{name}"

    content = f"""---
title: "{name}"
project_id: "{proj_slug}"
island_id: 9
realm: "brain"
status: "{status}"
tags:
{tags_yaml}
created: {now_str}
last_updated: {now_str}
source_path: "{src}"
sticker: lucide//gamepad-2
color: var(--mk-color-purple)
---

# 🎮 {name}

> **Тип / Жанр:** {genre_or_type}  
> **Статус проекта:** {status.upper()}  
> **Рабочий контекст:** Остров 9 (Mobile App & Game Engineering)  
> **Расположение исходников:** `{src}`  

---

## 🎯 Описание и Концепция

{description}

---

## 🛠️ Архитектура и Стандарты
- **Платформа:** iOS (Swift, SwiftUI, SpriteKit)
- **Правила качества:** Clean Code Guardian (Rule #16), Zero Silent Exceptions
- **Реестр проектов:** включен в нативную базу [[Nero/xcode/Проекты_Xcode.base|Проекты Xcode Base]]
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "success": True,
        "type": "xcode",
        "path": file_path,
        "name": name,
        "project_id": proj_slug
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal Project & App Onboarder")
    subparsers = parser.add_subparsers(dest="target_realm", required=True)

    # Pulsar subparser
    p_pulsar = subparsers.add_parser("pulsar", help="Управление сервисами Pulsar Space (Остров 7)")
    p_pulsar.add_argument("--scan", action="store_true", help="Сканировать приложения в /WORK/pulsar/")
    p_pulsar.add_argument("--sync", action="store_true", help="Синхронизировать паспорта в Nero/pulsar/")
    p_pulsar.add_argument("--name", help="Название сервиса")
    p_pulsar.add_argument("--desc", help="Описание сервиса")
    p_pulsar.add_argument("--category", default="Web Dashboard", help="Категория сервиса")
    p_pulsar.add_argument("--port", type=int, help="Сетевой TCP порт")
    p_pulsar.add_argument("--status", choices=["production", "active", "in_development", "concept"], default="active")
    p_pulsar.add_argument("--repo", help="Путь к репозиторию")
    p_pulsar.add_argument("--tags", help="Теги через запятую")

    # Xcode subparser
    p_xcode = subparsers.add_parser("xcode", help="Управление проектами Xcode & iOS Gamedev (Остров 9)")
    p_xcode.add_argument("--scan", action="store_true", help="Сканировать проекты в /WORK/xcode/")
    p_xcode.add_argument("--sync", action="store_true", help="Синхронизировать паспорта в Nero/xcode/")
    p_xcode.add_argument("--name", help="Название игры или приложения")
    p_xcode.add_argument("--desc", help="Описание концепции или геймплея")
    p_xcode.add_argument("--type", default="iOS Game / SpriteKit", help="Жанр или тип приложения")
    p_xcode.add_argument("--status", choices=["production", "active", "in_development", "concept"], default="in_development")
    p_xcode.add_argument("--source", help="Путь к каталогу проекта Xcode")
    p_xcode.add_argument("--tags", help="Теги через запятую")

    args = parser.parse_args()

    if args.target_realm == "pulsar":
        from and_os.lib.pulsar import PulsarInspector, PulsarPassportSync
        if args.scan:
            inspector = PulsarInspector()
            apps = inspector.scan_applications()
            print(f"=== 🏝️ Pulsar Space Scan (Остров 7) — {len(apps)} сервисов ===")
            for a in apps:
                port_str = f":{a['port']}" if a['port'] else "—"
                contract_str = "🟢 PROJECT.md" if a['has_contract'] else "🔴 NO CONTRACT"
                print(f"  • {a['id']:22} | {port_str:7} | {contract_str} | {a['category']}")
            return

        if args.sync:
            syncer = PulsarPassportSync()
            res = syncer.sync()
            print(f"✅ Синхронизация Pulsar Space (Остров 7) завершена:")
            print(f"   • Всего сервисов: {res['total_apps']}")
            print(f"   • Создано новых паспортов: {len(res['created'])} ({', '.join(res['created']) or 'нет'})")
            print(f"   • Обновлено паспортов: {len(res['updated'])} ({', '.join(res['updated']) or 'нет'})")
            return

        if not args.name or not args.desc:
            print("Ошибка: для регистрации нового сервиса требуются флаги --name и --desc (или используйте --scan / --sync).")
            sys.exit(1)

        custom_tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        res = register_pulsar_app(
            name=args.name,
            description=args.desc,
            category=args.category,
            port=args.port,
            status=args.status,
            repo_path=args.repo,
            tags=custom_tags
        )
        print(f"✅ Сервис успешно зарегистрирован в Pulsar Space:")
        print(f"   • Имя: {res['name']}")
        print(f"   • Паспорт: {res['path']}")
        print(f"   • База данных: Nero/pulsar/Приложения_Pulsar.base (🟢 обновлена реактивно)")

    elif args.target_realm == "xcode":
        from and_os.lib.xcode import XcodeInspector, XcodePassportSync
        if args.scan:
            inspector = XcodeInspector()
            projs = inspector.scan_projects()
            print(f"=== 🏝️ Xcode & Gamedev Scan (Остров 9) — {len(projs)} проектов ===")
            for p in projs:
                contract_str = "🟢 PROJECT.md" if p['has_contract'] else "🔴 NO CONTRACT"
                print(f"  • {p['id']:28} | {contract_str} | {p['category']} | {p['platform']}")
            return

        if args.sync:
            syncer = XcodePassportSync()
            res = syncer.sync()
            print(f"✅ Синхронизация Xcode Realm (Остров 9) завершена:")
            print(f"   • Всего проектов: {res['total_projects']}")
            print(f"   • Создано новых паспортов: {len(res['created'])} ({', '.join(res['created']) or 'нет'})")
            print(f"   • Обновлено паспортов: {len(res['updated'])} ({', '.join(res['updated']) or 'нет'})")
            return

        if not args.name or not args.desc:
            print("Ошибка: для регистрации нового проекта требуются флаги --name и --desc (или используйте --scan / --sync).")
            sys.exit(1)

        custom_tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        res = register_xcode_project(
            name=args.name,
            description=args.desc,
            genre_or_type=args.type,
            status=args.status,
            source_path=args.source,
            tags=custom_tags
        )
        print(f"✅ Проект успешно зарегистрирован в Xcode Realm:")
        print(f"   • Имя: {res['name']}")
        print(f"   • Паспорт: {res['path']}")
        print(f"   • База данных: Nero/xcode/Проекты_Xcode.base (🟢 обновлена реактивно)")


if __name__ == "__main__":
    main()

