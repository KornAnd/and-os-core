#!/usr/bin/env python3
"""
project_manager.py — Universal Project & App Onboarding Dispatcher for AnD os v1.0.0.
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

> **Category:** {category}  
> **Status:** {status.upper()}  
> **Port / Endpoint:** {f":{port}" if port else "Local process / CLI"}  
> **The sources location:** `{repo_path or f"./pulsar/{name}"}`  

---

## 🎯 The Description and the Purpose

{description}

---

## ⚙️ The Lifecycle Control (AnD os Core)
- **The launch:** `sys_cli.py daemon start --target {app_slug}`
- **The restart:** `sys_cli.py daemon restart --target {app_slug}`
- **The telemetry:** displayed in the native dashboard [[Nero/pulsar/Приложения_Pulsar.base|Приложения Pulsar Base]]
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

> **The Type / Genre:** {genre_or_type}  
> **The project status:** {status.upper()}  
> **The working context:** the Island 9 (Mobile App & Game Engineering)  
> **The sources location:** `{src}`  

---

## 🎯 The Description and the Concept

{description}

---

## 🛠️ The Architecture and the Standards
- **The Platform:** iOS (Swift, SwiftUI, SpriteKit)
- **The quality rules:** Clean Code Guardian (Rule #16), Zero Silent Exceptions
- **The projects registry:** included in the native base [[Nero/xcode/Проекты_Xcode.base|Проекты Xcode Base]]
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
    p_pulsar = subparsers.add_parser("pulsar", help="The control of the Pulsar Space services (the Island 7)")
    p_pulsar.add_argument("--scan", action="store_true", help="Scan the applications in /WORK/pulsar/")
    p_pulsar.add_argument("--sync", action="store_true", help="Synchronize the passports in Nero/pulsar/")
    p_pulsar.add_argument("--name", help="The name of the service")
    p_pulsar.add_argument("--desc", help="The description of the service")
    p_pulsar.add_argument("--category", default="Web Dashboard", help="The category of the service")
    p_pulsar.add_argument("--port", type=int, help="The network TCP port")
    p_pulsar.add_argument("--status", choices=["production", "active", "in_development", "concept"], default="active")
    p_pulsar.add_argument("--repo", help="The path to the repository")
    p_pulsar.add_argument("--tags", help="The tags separated by a comma")

    # Xcode subparser
    p_xcode = subparsers.add_parser("xcode", help="The control of the Xcode & iOS Gamedev projects (the Island 9)")
    p_xcode.add_argument("--scan", action="store_true", help="Scan the projects in /WORK/xcode/")
    p_xcode.add_argument("--sync", action="store_true", help="Synchronize the passports in Nero/xcode/")
    p_xcode.add_argument("--name", help="The name of the game or the application")
    p_xcode.add_argument("--desc", help="The description of the concept or the gameplay")
    p_xcode.add_argument("--type", default="iOS Game / SpriteKit", help="The genre or the type of the application")
    p_xcode.add_argument("--status", choices=["production", "active", "in_development", "concept"], default="in_development")
    p_xcode.add_argument("--source", help="The path to the Xcode project catalog")
    p_xcode.add_argument("--tags", help="The tags separated by a comma")

    args = parser.parse_args()

    if args.target_realm == "pulsar":
        from and_os.lib.pulsar import PulsarInspector, PulsarPassportSync
        if args.scan:
            inspector = PulsarInspector()
            apps = inspector.scan_applications()
            print(f"=== 🏝️ Pulsar Space Scan (the Island 7) — {len(apps)} services ===")
            for a in apps:
                port_str = f":{a['port']}" if a['port'] else "—"
                contract_str = "🟢 PROJECT.md" if a['has_contract'] else "🔴 NO CONTRACT"
                print(f"  • {a['id']:22} | {port_str:7} | {contract_str} | {a['category']}")
            return

        if args.sync:
            syncer = PulsarPassportSync()
            res = syncer.sync()
            print(f"✅ The Pulsar Space synchronization (the Island 7) was completed:")
            print(f"   • Total services: {res['total_apps']}")
            print(f"   • The new passports were created: {len(res['created'])} ({', '.join(res['created']) or 'none'})")
            print(f"   • The passports were updated: {len(res['updated'])} ({', '.join(res['updated']) or 'none'})")
            return

        if not args.name or not args.desc:
            print("Error: for the registration of the new service the --name and the --desc flags are required (or use the --scan / the --sync).")
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
        print(f"✅ The service was successfully registered in the Pulsar Space:")
        print(f"   • Name: {res['name']}")
        print(f"   • Passport: {res['path']}")
        print(f"   • The database: Nero/pulsar/Приложения_Pulsar.base (🟢 updated reactively)")

    elif args.target_realm == "xcode":
        from and_os.lib.xcode import XcodeInspector, XcodePassportSync
        if args.scan:
            inspector = XcodeInspector()
            projs = inspector.scan_projects()
            print(f"=== 🏝️ Xcode & Gamedev Scan (the Island 9) — {len(projs)} projects ===")
            for p in projs:
                contract_str = "🟢 PROJECT.md" if p['has_contract'] else "🔴 NO CONTRACT"
                print(f"  • {p['id']:28} | {contract_str} | {p['category']} | {p['platform']}")
            return

        if args.sync:
            syncer = XcodePassportSync()
            res = syncer.sync()
            print(f"✅ The Xcode Realm synchronization (the Island 9) was completed:")
            print(f"   • Total projects: {res['total_projects']}")
            print(f"   • The new passports were created: {len(res['created'])} ({', '.join(res['created']) or 'none'})")
            print(f"   • The passports were updated: {len(res['updated'])} ({', '.join(res['updated']) or 'none'})")
            return

        if not args.name or not args.desc:
            print("Error: for the registration of the new project the --name and the --desc flags are required (or use the --scan / the --sync).")
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
        print(f"✅ The project was successfully registered in the Xcode Realm:")
        print(f"   • Name: {res['name']}")
        print(f"   • Passport: {res['path']}")
        print(f"   • The database: Nero/xcode/Проекты_Xcode.base (🟢 updated reactively)")


if __name__ == "__main__":
    main()

