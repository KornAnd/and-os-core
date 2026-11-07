#!/usr/bin/env python3
"""
obsidian_blueprint_generator.py — Генератор эталонного паспорта архитектуры и плагинов Obsidian.
AnD os v8.1 — Production Environment Blueprint

Создает или обновляет единый файл `OBSIDIAN_STRUCTURE_BLUEPRINT.md` в корне / в and_os/etc/,
содержащий 100% спецификацию:
  1. Архитектура хранилища и каталогов (контуры, контексты, базы знаний).
  2. Базовые настройки Obsidian (app.json, core-plugins, appearance).
  3. Полный реестр комьюнити-плагинов (версии, назначение, ключевые конфиги).
  4. Инструкция по 1-клик / headless развертыванию на новом компьютере для любой LLM.

Периодичность обновления: раз в месяц при запуске нейросети или по флагу --force.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OBSIDIAN_DIR = os.path.join(VAULT_ROOT, ".obsidian")
TARGET_MD = os.path.join(VAULT_ROOT, "and_os/etc/OBSIDIAN_STRUCTURE_BLUEPRINT.md")
TARGET_JSON = os.path.join(VAULT_ROOT, "and_os/etc/obsidian_blueprint.json")

# Ключевые плагины и их бизнес-роль в системе ANDREY OS
PLUGIN_ROLES = {
    "remotely-save": "Синхронизация через WebDAV (Mail.ru Cloud), отказоустойчивость, лимит файлов 1GB",
    "dataview": "DQL/JS запросы к метаданным, трекинг задач и динамические таблицы",
    "make-md": "Пространства (Spaces), Folder Notes, контекстное управление каталогами",
    "obsidian-tasks-plugin": "Глобальный трекинг задач, дедлайнов, тегов и приоритетов",
    "task-gantt": "Визуализация графиков Ганта для проектов студии (Studio / Ta-Bu / Mars)",
    "cmdr": "Пользовательские горячие клавиши, кастомные макросы и тулбары",
    "obsidian-kanban": "Канбан-доски для спринтов и фаз продакшна",
    "obsidian-excalidraw-plugin": "Интерактивные архитектурные схемы, эскизы и скетчи",
    "advanced-canvas": "Расширенные бесконечные холсты для декомпозиции сюжетов и майндмапов",
    "calendar": "Календарное представление и привязка ежедневных/еженедельных заметок",
    "obsidian-full-calendar": "Полноэкранный календарь встреч и дедлайнов",
    "obsidian-day-planner": "Почасовое планирование рабочего дня",
    "obsidian-tracker": "Трекер привычек, здоровья и спортивных метрик",
    "templater-obsidian": "Шаблонизатор с исполнением скриптов при создании заметок",
    "sheet-plus": "Интерактивные таблицы и формулы внутри заметок",
    "table-editor-obsidian": "Продвинутый редактор Markdown-таблиц (Advanced Tables)",
    "data-files-editor": "Редактирование JSON, YAML и CSV файлов прямо внутри интерфейса",
    "code-styler": "Подсветка синтаксиса, нумерация строк и оформление блоков кода",
    "obsidian-icon-folder": "Иконки и эмодзи на папках и заметках (Iconize)",
    "editing-toolbar": "Визуальная плавающая панель форматирования текста",
    "obsidian-minimal-settings": "Тонкая настройка темы оформления Minimal",
    "obsidian-style-settings": "Глобальная настройка CSS-переменных и типографики",
    "obsidian-languagetool-plugin": "Проверка орфографии и грамматики через LanguageTool",
    "obsidian-image-toolkit": "Инструменты масштабирования и просмотра изображений",
    "automatic-table-of-contents": "Автоматическая генерация оглавлений (TOC)",
    "url-into-selection": "Быстрая вставка гиперссылок поверх выделенного текста",
    "obsidian-auto-link-title": "Автоподтягивание заголовков веб-страниц при вставке ссылок",
    "obsidian-outliner": "Поведение списков как в Workflowy / Roam Research",
    "pdf-plus": "Продвинутая аннотация и цитирование PDF-документов",
    "jotbird": "Быстрый шеринг и экспорт заметок через JotBird",
    "markwhen": "Таймлайны из текстового формата Markwhen",
    "obsidian-checklist-plugin": "Боковая панель агрегации всех чек-боксов хранилища",
    "obsidian-enhancing-mindmap": "Интеллект-карты на базе Mindmap",
    "vscode-editor": "Встроенный редактор Monaco / VS Code для кода и скриптов",
    "opencode-obsidian": "Интеграция с локальными AI-агентами OpenCode",
    "obsidian-opencode": "Интеграция с локальными AI-агентами OpenCode"
}

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def should_update(force=False):
    if force or not os.path.exists(TARGET_MD):
        return True
    
    # Проверка давности обновления (раз в месяц = 30 дней)
    mtime = os.path.getmtime(TARGET_MD)
    last_update = datetime.fromtimestamp(mtime)
    if datetime.now() - last_update > timedelta(days=30):
        return True
    return False

def generate_blueprint():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 1. Сбор базовых настроек Obsidian
    app_cfg = load_json(os.path.join(OBSIDIAN_DIR, "app.json"))
    appearance_cfg = load_json(os.path.join(OBSIDIAN_DIR, "appearance.json"))
    core_plugins = load_json(os.path.join(OBSIDIAN_DIR, "core-plugins.json"))
    comm_plugins = load_json(os.path.join(OBSIDIAN_DIR, "community-plugins.json"))
    
    # 2. Сканирование папок плагинов
    plugins_dir = os.path.join(OBSIDIAN_DIR, "plugins")
    installed_plugins = []
    
    if os.path.exists(plugins_dir):
        for item in sorted(os.listdir(plugins_dir)):
            p_dir = os.path.join(plugins_dir, item)
            if not os.path.isdir(p_dir) or item.startswith('.'):
                continue
            
            m_path = os.path.join(p_dir, "manifest.json")
            manifest = load_json(m_path)
            
            data_json_path = os.path.join(p_dir, "data.json")
            has_custom_data = os.path.exists(data_json_path)
            
            installed_plugins.append({
                "id": item,
                "name": manifest.get("name", item),
                "version": manifest.get("version", "unknown"),
                "description": manifest.get("description", ""),
                "author": manifest.get("author", ""),
                "enabled": item in comm_plugins,
                "has_config": has_custom_data,
                "role": PLUGIN_ROLES.get(item, "Расширение интерфейса и функционала")
            })

    # 3. Структура каталогов хранилища
    vault_folders = [
        {"path": "Nero/", "role": "Центральный мозг системы, AI-ядро, скиллы (54), скрипты (64), контекст пользователя"},
        {"path": "Clippings/", "role": "База знаний, конспекты книг, управленческие фреймворки, Quick Knowledge DB"},
        {"path": "Tasks/", "role": "Оперативное управление, спринты, трекинг задач и проектные бэклог-листы"},
        {"path": "Product/", "role": "Продуктовая разработка, спецификации, архитектура сервисов"},
        {"path": "Story/", "role": "Сценарная разработка, персонажи, синопсисы, логлайны"},
        {"path": "CG_core/", "role": "База знаний компьютерной графики, статьи, стандарты пайплайнов"},
        {"path": "Ta-Bu/", "role": "Проекты, коммерческие пайплайны и клиенты студии Ta-Bu"},
        {"path": "Studio/", "role": "Продакшн проекты анимационной Production Studio"},
        {"path": "Industry/", "role": "Анализ индустрии, студии, вендоры, рынок CG и анимации"},
        {"path": "Book/", "role": "Книжные проекты и авторские материалы"},
        {"path": "Resource/", "role": "Медиа-ассеты, шаблоны, вложения и графические материалы"}
    ]

    # Генерация Markdown
    md = []
    md.append("---")
    md.append("tags:")
    md.append("  - nero")
    md.append("  - system")
    md.append("  - architecture")
    md.append("  - obsidian")
    md.append("  - blueprint")
    md.append("sticker: lucide//layers")
    md.append("color: var(--mk-color-purple)")
    md.append(f"updated: {datetime.now().strftime('%Y-%m-%d')}")
    md.append("---")
    md.append("")
    md.append("# 🏛️ OBSIDIAN_STRUCTURE_BLUEPRINT — Эталонный Паспорт Архитектуры и Плагинов")
    md.append("")
    md.append("> 💡 **TL;DR:** Единый эталонный паспорт полной структуры Obsidian Vault System Architect (AnD os v8.1). "
              "Содержит 100% спецификацию каталогов, базовых настроек, ядра и 35 комьюнити-плагинов с их ролью и конфигурацией. "
              "Позволяет любой LLM на любом новом компьютере мгновенно воссоздать точную копию рабочей среды.")
    md.append(f"> 📅 **Дата генерации / актуализации:** `{now_str}`  ")
    md.append("> 🔄 **Регламент обновления:** Автоматически раз в 30 дней при инициализации сессии (`sys_cli.py sync/audit`).  ")
    md.append("> 🔗 **Кросс-связи:** [[SYSTEM|SYSTEM.md]] | [[system.json]] | [[and_os/etc/SYSTEM_MAP|SYSTEM_MAP.md]]")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🗺️ 1. Архитектурный Контур Хранилища (Vault Folder Topology)")
    md.append("")
    md.append("Хранилище организовано по принципу **Семантического Зонирования**:")
    md.append("")
    md.append("| Каталог | Назначение и Контур | Роль для ИИ-Агента |")
    md.append("| :--- | :--- | :--- |")
    for fld in vault_folders:
        md.append(f"| `{fld['path']}` | {fld['role']} | Read / Reference |" if fld['path'] != "Nero/" else f"| `{fld['path']}` | {fld['role']} | **Primary Storage (Правило №7)** |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## ⚙️ 2. Базовые Настройки Obsidian (Core Engine Config)")
    md.append("")
    md.append("```json")
    core_summary = {
        "app": app_cfg,
        "appearance": appearance_cfg,
        "active_core_plugins": [k for k, v in core_plugins.items() if v]
    }
    md.append(json.dumps(core_summary, indent=2, ensure_ascii=False))
    md.append("```")
    md.append("")
    md.append("- **Тема оформления:** `AnuPpuccin` (тёмный режим, акцентный цвет `#b900ff`).")
    md.append("- **Поведение ссылок:** `alwaysUpdateLinks: true` (автообновление ссылок при переименовании).")
    md.append("- **Вложения:** `./` (сохранение вложений рядом с текущей заметкой).")
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"## 🧩 3. Реестр Комьюнити-Плагинов ({len(installed_plugins)} плагинов)")
    md.append("")
    md.append("| ID плагина | Название | Версия | Статус | Роль в системе ANDREY OS |")
    md.append("| :--- | :--- | :---: | :---: | :--- |")
    for p in installed_plugins:
        status_icon = "🟢 Включен" if p["enabled"] else "⚪ Отключен"
        md.append(f"| `{p['id']}` | **{p['name']}** | `v{p['version']}` | {status_icon} | {p['role']} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🔒 4. Критические Настройки Ключевых Плагинов")
    md.append("")
    md.append("### 1. Remotely Save (`remotely-save`) — Защита синхронизации WebDAV")
    md.append("- **Метод:** WebDAV (Mail.ru Cloud).")
    md.append("- **Лимит размера файла (`skipSizeLargerThan`):** `1 000 000 000` байт (1 GB) — предотвращает сбои 505 при синхронизации больших файлов.")
    md.append("- **Конкурентность (`concurrency`):** `2` параллельных потока (защита от разрыва сокетов).")
    md.append("- **Игнорируемые пути (`ignorePaths`):** `['.trash', '.git', '.smart-env', '.opencode', '__pycache__', 'and_os/opt/apps', 'and_os/var', 'and_os/lib/skills/openmontage-builder/repo']`.")
    md.append("")
    md.append("### 2. Make.md (`make-md`) — Организация пространств")
    md.append("- **Folder Notes:** Включены, привязаны к каталогам.")
    md.append("- **Spaces:** Изолированная навигация без загрязнения дерева заметок фантомными MDB.")
    md.append("")
    md.append("### 3. Dataview (`dataview`) — Запросы к данным")
    md.append("- **JavaScript Queries:** Включены (`enableDataviewJs: true`).")
    md.append("- **Inline JS:** Включен.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🚀 5. Инструкция для ИИ: Как развернуть это окружение на новом ПК")
    md.append("")
    md.append("Если ты агент, работающий на чистой машине, выполни следующие шаги:")
    md.append("1. **Установка Obsidian:** Скачай и установи приложение с официального сайта (`obsidian.md`).")
    md.append("2. **Клонирование / Копирование хранилища:** Разверни содержимое Vault в целевую папку.")
    md.append("3. **Каталог `.obsidian`:**")
    md.append("   - Скопируй файлы конфигурации `app.json`, `appearance.json`, `community-plugins.json`, `core-plugins.json`.")
    md.append("   - Убедись, что список в `community-plugins.json` активирован.")
    md.append("4. **Установка плагинов:** Для каждого плагина из реестра скопируй папку в `.obsidian/plugins/<id>/` (файлы `manifest.json`, `main.js`, `styles.css`, `data.json`).")
    md.append("5. **Симлинки Скиллов:** Запусти системную линковку:")
    md.append("   ```bash")
    md.append("   python3 and_os/bin/sys_cli.py sync --fix")
    md.append("   ```")
    md.append("6. **Проверка целостности:** Запусти 13-векторную проверку:")
    md.append("   ```bash")
    md.append("   python3 and_os/bin/sys_cli.py audit")
    md.append("   ```")
    md.append("")
    md.append("---")
    md.append("[[SYSTEM|← Мастер-Манифест]] | [[and_os/etc/SYSTEM_MAP|← Генеральный Атлас]] | [[REGISTRY|← Реестр Скиллов]]")
    
    content = "\n".join(md) + "\n"
    
    os.makedirs(os.path.dirname(TARGET_MD), exist_ok=True)
    with open(TARGET_MD, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Сохраняем машиночитаемую версию
    blueprint_json = {
        "updated": now_str,
        "vault_folders": vault_folders,
        "core_config": core_summary,
        "plugins": installed_plugins
    }
    with open(TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(blueprint_json, f, indent=2, ensure_ascii=False)
        
    return {
        "status": "ok",
        "target_md": TARGET_MD,
        "target_json": TARGET_JSON,
        "plugins_count": len(installed_plugins),
        "updated": now_str
    }

if __name__ == "__main__":
    force_run = "--force" in sys.argv
    if should_update(force=force_run):
        res = generate_blueprint()
        print(f"✅ Obsidian Blueprint успешно сгенерирован/обновлен: {res['target_md']} ({res['plugins_count']} плагинов)")
    else:
        print("ℹ️ Obsidian Blueprint актуален (обновление требуется не чаще 1 раза в 30 дней). Используйте --force для принудительного обновления.")
