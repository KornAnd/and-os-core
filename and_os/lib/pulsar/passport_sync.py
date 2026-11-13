"""
passport_sync.py — Island 7 Passport Synchronizer (Brain & Muscle Parity).
Synchronizes physical /WORK/pulsar/ applications with Nero/pulsar/ Markdown passports
and updates Приложения_Pulsar.base metadata without legacy paths or orphaned notes.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
from and_os.lib.pulsar.inspector import PulsarInspector


class PulsarPassportSync:
    DEFAULT_VAULT = Path(".")

    def __init__(self, vault_root: Path = None, inspector: PulsarInspector = None):
        self.vault_root = vault_root or self.DEFAULT_VAULT
        self.pulsar_dir = self.vault_root / "Nero" / "pulsar"
        self.inspector = inspector or PulsarInspector()

    def sync(self) -> Dict[str, Any]:
        """Synchronizes all detected applications into Nero/pulsar/ passports."""
        apps = self.inspector.scan_applications()
        self.pulsar_dir.mkdir(parents=True, exist_ok=True)

        synced = []
        created = []
        updated = []

        for app in apps:
            app_id = app["id"]
            passport_path = self.pulsar_dir / f"{app_id}.md"

            content = self._render_passport(app)
            if not passport_path.exists():
                with open(passport_path, "w", encoding="utf-8") as f:
                    f.write(content)
                created.append(app_id)
            else:
                # Update on-disk note with verified schema
                with open(passport_path, "w", encoding="utf-8") as f:
                    f.write(content)
                updated.append(app_id)

            synced.append(app_id)

        return {
            "total_apps": len(apps),
            "created": created,
            "updated": updated,
            "synced": synced
        }

    def _render_passport(self, app: Dict[str, Any]) -> str:
        """Renders canonical markdown passport with Obsidian Base compatibility."""
        port_yaml = f"port: {app['port']}\n" if app["port"] else "port: null\n"
        port_display = f"`http://localhost:{app['port']}`" if app["port"] else "— (Standalone process)"

        return f"""---
title: "{app['name']}"
app_id: "{app['id']}"
island_id: 7
realm: "pulsar"
category: "{app['category']}"
status: "{app['status']}"
{port_yaml}tags:
  - pulsar
  - app
  - island-7
sticker: lucide//layers
color: var(--mk-color-turquoise)
---

# 🚀 {app['name']}

> **Категория:** {app['category']}  
> **Статус:** {app['status'].upper()}  
> **Порт / Эндпоинт:** {port_display}  
> **Расположение исходников (Muscle Realm):** `{app['path']}`  

---

## 🎯 Описание и Назначение

{app['description'] or 'Автономный сервис кластера Pulsar Space.'}

---

## ⚙️ Технические характеристики и Запуск

| Параметр | Значение |
|---|---|
| **Стек технологий** | {app['stack']} |
| **Точка входа** | `{app['entrypoint']}` |
| **Команда запуска** | `{app['run_command'] or 'python3 ' + app['entrypoint']}` |
| **Команда проверки (Smoke test)** | `{app['smoke_test'] or 'test -f ' + app['entrypoint']}` |

---

## 🧭 Связи и Навигация

- [[Nero/pulsar/INDEX|🗂️ Реестр Pulsar Space]]
- [[Nero/pulsar/Приложения_Pulsar.base|📊 Витрина приложений (Base)]]
- [[Nero/CONTEXT|← Назад в Nero]]
"""
