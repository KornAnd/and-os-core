"""
passport_sync.py — Island 9 Passport Synchronizer (Brain & Muscle Parity).
Synchronizes physical /WORK/xcode/ projects with Nero/xcode/ Markdown passports
and updates Проекты_Xcode.base metadata.
"""

from pathlib import Path
from typing import Dict, Any, List
from and_os.lib.xcode.inspector import XcodeInspector


class XcodePassportSync:
    DEFAULT_VAULT = Path(".")

    def __init__(self, vault_root: Path = None, inspector: XcodeInspector = None):
        self.vault_root = vault_root or self.DEFAULT_VAULT
        self.xcode_dir = self.vault_root / "Nero" / "xcode" / "projects"
        self.inspector = inspector or XcodeInspector()

    def sync(self) -> Dict[str, Any]:
        """Synchronizes all detected Xcode projects into Nero/xcode/projects/ passports."""
        projects = self.inspector.scan_projects()
        self.xcode_dir.mkdir(parents=True, exist_ok=True)

        synced = []
        created = []
        updated = []

        for proj in projects:
            proj_id = proj["id"]
            passport_path = self.xcode_dir / f"{proj_id}.md"

            content = self._render_passport(proj)
            if not passport_path.exists():
                with open(passport_path, "w", encoding="utf-8") as f:
                    f.write(content)
                created.append(proj_id)
            else:
                with open(passport_path, "w", encoding="utf-8") as f:
                    f.write(content)
                updated.append(proj_id)

            synced.append(proj_id)

        return {
            "total_projects": len(projects),
            "created": created,
            "updated": updated,
            "synced": synced
        }

    def _render_passport(self, proj: Dict[str, Any]) -> str:
        """Renders canonical markdown passport for Island 9."""
        return f"""---
title: "{proj['name']}"
project_id: "{proj['id']}"
island_id: 9
realm: "brain"
category: "{proj['category']}"
status: "{proj['status']}"
source_path: "{proj['path']}"
tags:
  - xcode
  - ios
  - project
  - island-9
sticker: lucide//gamepad-2
color: var(--mk-color-purple)
---

# 🎮 {proj['name']}

> **Категория:** {proj['category']}  
> **Статус:** {proj['status'].upper()}  
> **Платформа:** {proj['platform']}  
> **Расположение исходников (Muscle Realm):** `{proj['path']}`  

---

## 🎯 Описание и Концепция

{proj['description'] or 'Мобильный проект / игра для экосистемы Apple.'}

---

## 🛠️ Архитектура и Сборка

| Параметр | Значение |
|---|---|
| **Стек технологий** | {proj['stack']} |
| **Xcode проект (.xcodeproj)** | `{'Да' if proj['has_xcodeproj'] else 'Нет'}` |
| **Swift Package Manager** | `{'Да (Package.swift)' if proj['has_package_swift'] else 'Нет'}` |
| **Команда сборки** | `{proj['build_command']}` |
| **Команда тестов** | `{proj['test_command'] or '—'}` |

---

## 🧭 Связи и Навигация

- [[Nero/xcode/PROJECTS|📂 Реестр проектов Xcode]]
- [[Nero/xcode/Проекты_Xcode.base|📊 База проектов (Base)]]
- [[Nero/xcode/CONTEXT|← Назад в MOC Острова 9]]
"""
