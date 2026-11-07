#!/usr/bin/env python3
"""
system_tools_map.py — Автоматический Генератор Единого Системного Паспорта Инструментария и Рантаймов (Toolchain & Runtime Engine).
Принцип: Zero-Token Routing Map, Think in Code (Правило №16), Регламент сред исполнения AnD os v8.1.

Назначение:
  1. Сканирует рантаймы ОС: Python (версия, путь, установленные пакеты), Node.js, Git, OS Architecture.
  2. Сканирует все 50 скиллов (SKILL.md) и скрипты ядра в and_os/bin/.
  3. Генерирует машиночитаемый JSON и Markdown файл:
     - `and_os/etc/SYSTEM_TOOLCHAIN.json`
     - `and_os/etc/SYSTEM_TOOLCHAIN.md`
  4. Обновляет виртуальный статус в /proc mesh (`proc/env.stat`).

Использование:
  python3 system_tools_map.py --build
"""

import os
import sys
from pathlib import Path
_vroot = str(Path(__file__).resolve().parents[2])
if _vroot not in sys.path:
    sys.path.insert(0, _vroot)
from and_os.lib.core.vault_safe_io import vault_safe_write

import sys
import glob
import json
import shutil
import platform
import argparse
import subprocess
import importlib.metadata
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SCRIPT_DIR = os.path.join(VAULT_ROOT, "and_os/bin")
SKILLS_DIR = os.path.join(VAULT_ROOT, "and_os/lib/skills")
JSON_OUTPUT = os.path.join(VAULT_ROOT, "and_os/etc/SYSTEM_TOOLCHAIN.json")
MD_OUTPUT = os.path.join(VAULT_ROOT, "and_os/etc/SYSTEM_TOOLCHAIN.md")
PROC_DIR = os.path.join(VAULT_ROOT, "and_os/proc")

def get_cli_version(cmd_list):
    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:{env.get('PATH', '')}"
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True, env=env, timeout=3)
        if res.returncode == 0:
            out = res.stdout.strip().split("\n")[0]
            return out if out else "ACTIVE"
        return "NOT_AVAILABLE"
    except Exception:
        return "NOT_AVAILABLE"

def get_app_plist_version(plist_path):
    import plistlib
    if os.path.exists(plist_path):
        try:
            with open(plist_path, "rb") as f:
                pl = plistlib.load(f)
                return pl.get("CFBundleShortVersionString") or pl.get("CFBundleVersion") or "INSTALLED"
        except Exception:
            return "INSTALLED"
    return "NOT_INSTALLED"

def collect_runtime_environment():
    """Сбор информации о версиях языков программирования, установленных модулях, DCC и прикладных системах."""
    python_ver = platform.python_version()
    python_path = sys.executable
    os_name = f"{platform.system()} {platform.release()} ({platform.machine()})"

    node_ver = get_cli_version(["node", "--version"])
    git_ver = get_cli_version(["git", "--version"])
    deno_ver = get_cli_version(["deno", "--version"])
    go_ver = get_cli_version(["go", "version"])
    swift_ver = get_cli_version(["swift", "--version"])
    ffmpeg_ver = get_cli_version(["ffmpeg", "-version"])
    tesseract_ver = get_cli_version(["tesseract", "--version"])
    ytdlp_ver = get_cli_version(["yt-dlp", "--version"])
    uv_ver = get_cli_version(["uv", "--version"])
    gh_ver = get_cli_version(["gh", "--version"])
    jq_ver = get_cli_version(["jq", "--version"])
    sqlite_ver = get_cli_version(["sqlite3", "--version"])
    tmux_ver = get_cli_version(["tmux", "-V"])

    # DCC & Creative Software
    blender_ver = get_cli_version(["/Applications/Blender.app/Contents/MacOS/Blender", "--version"])
    xcode_ver = get_app_plist_version("/Applications/Xcode.app/Contents/Info.plist")
    davinci_ver = get_app_plist_version("/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Info.plist")
    comfy_ver = get_app_plist_version("/Applications/Comfy Desktop.app/Contents/Info.plist")
    unity_hub_ver = get_app_plist_version("/Applications/Unity Hub.app/Contents/Info.plist")
    docker_ver = get_app_plist_version("/Applications/Docker.app/Contents/Info.plist")
    obsidian_ver = get_app_plist_version("/Applications/Obsidian.app/Contents/Info.plist")
    mattermost_ver = get_app_plist_version("/Applications/Mattermost.app/Contents/Info.plist")
    telegram_ver = get_app_plist_version("/Applications/Telegram.app/Contents/Info.plist")

    # Houdini check
    houdini_ver = "NOT_INSTALLED"
    if os.path.exists("/Applications/Houdini/Current"):
        h_target = os.path.realpath("/Applications/Houdini/Current")
        houdini_ver = os.path.basename(h_target).replace("Houdini", "")

    # Collect Python Packages safely
    packages = []
    try:
        dists = importlib.metadata.distributions()
        for d in dists:
            try:
                name = d.metadata.get("Name")
                if name:
                    packages.append({
                        "name": name,
                        "version": d.version or "unknown"
                    })
            except Exception:
                continue
        packages.sort(key=lambda x: x["name"].lower())
    except (ImportError, Exception) as e:
        sys.stderr.write(f"[system_tools_map] Warning inspecting packages: {e}\n")

    # Group packages by domain
    categories = {
        "Data & Document Processing": ["pdfplumber", "pdfminer.six", "pypdfium2", "openpyxl", "markdown-it-py", "docutils", "rich", "numpy", "pillow", "jinja2", "markupsafe"],
        "Network, API & Integration": ["requests", "urllib3", "websocket-client", "curl_cffi", "telemetry_syncconnect", "ftrack-python-api", "youtube-transcript-api", "ua-generator"],
        "Security, Crypto & System": ["cryptography", "cffi", "pycparser", "defusedxml", "platformdirs", "certifi"],
        "Build & Core Infrastructure": ["pip", "wheel", "packaging", "pybind11", "sphinx", "pygments", "setuptools", "virtualenv"]
    }

    categorized_packages = {}
    known_names = set()
    for cat, pkgs in categories.items():
        categorized_packages[cat] = []
        for p in packages:
            if p["name"].lower() in [x.lower() for x in pkgs]:
                categorized_packages[cat].append(p)
                known_names.add(p["name"].lower())

    other_pkgs = [p for p in packages if p["name"].lower() not in known_names]
    if other_pkgs:
        categorized_packages["Other Utilities"] = other_pkgs

    return {
        "os": os_name,
        "python": {
            "version": python_ver,
            "executable": python_path,
            "standard_target": ">=3.11 (Recommended 3.14.x)",
            "total_packages": len(packages),
            "packages_categorized": categorized_packages,
            "packages_all": packages
        },
        "runtimes": {
            "node": node_ver,
            "deno": deno_ver,
            "go": go_ver,
            "swift": swift_ver,
            "git": git_ver
        },
        "cli_tools": {
            "ffmpeg": ffmpeg_ver,
            "tesseract": tesseract_ver,
            "yt_dlp": ytdlp_ver,
            "uv": uv_ver,
            "gh": gh_ver,
            "jq": jq_ver,
            "sqlite": sqlite_ver,
            "tmux": tmux_ver
        },
        "creative_and_dcc": {
            "blender": blender_ver,
            "houdini": houdini_ver,
            "davinci_resolve": davinci_ver,
            "xcode": xcode_ver,
            "unity_hub": unity_hub_ver,
            "comfy_desktop": comfy_ver
        },
        "apps": {
            "obsidian": obsidian_ver,
            "mattermost": mattermost_ver,
            "telegram": telegram_ver,
            "docker": docker_ver
        }
    }

def _extract_script_docstring(pf: str) -> str:
    """Extract first docstring from a python script file."""
    try:
        with open(pf, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except OSError:
        return ""

    in_doc = False
    doc_lines = []
    for line in lines[:25]:
        if '"""' in line or "'''" in line:
            if in_doc:
                break
            in_doc = True
            doc_lines.append(line.replace('"""', '').replace("'''", '').strip())
        elif in_doc:
            doc_lines.append(line.strip())
    return " ".join([l for l in doc_lines if l])


def _extract_skill_description(sf: str) -> str:
    """Extract description from a skill SKILL.md file."""
    try:
        with open(sf, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return ""

    if "description:" not in content:
        return ""

    for line in content.splitlines():
        if line.startswith("description:"):
            return line.replace("description:", "").strip().strip('"').strip("'")
    return ""


def _render_packages_markdown(packages_categorized: dict) -> str:
    """Render python packages categorized markdown table."""
    role_map = {
        "ftrack-python-api": "Ftrack Studio API integration (Mars & Kot Gantt engines)",
        "telemetry_syncconnect": "telemetry_sync biometric and athletic performance synchronization",
        "openpyxl": "Excel workbook calculation and analysis (budgets, schedules)",
        "markdown-it-py": "Markdown document parsing and processing",
        "rich": "Terminal formatting and CLI syntax highlighting",
        "requests": "HTTP client for system APIs and gateway connections",
        "numpy": "Numerical mathematics and scientific array computation",
        "pillow": "Image and asset texture validation/processing",
        "cryptography": "Cryptographic primitives and secret key protection",
        "youtube-transcript-api": "YouTube transcript and summary extraction",
        "jinja2": "Document and report templating engine",
    }
    lines = []
    for category, pkgs in packages_categorized.items():
        if not pkgs:
            continue
        lines.append(f"#### 🔹 {category}\n\n")
        lines.append("| Package / Module | Version | Architectural Role in AnD os |\n")
        lines.append("| :--- | :--- | :--- |\n")
        for p in pkgs:
            pname = p["name"]
            pver = p["version"]
            note = role_map.get(pname, "PDF parsing and text twin extraction (MarkItDown engine)" if pname in ["pdfplumber", "pdfminer.six", "pypdfium2"] else "System utility")
            lines.append(f"| `{pname}` | `{pver}` | {note} |\n")
        lines.append("\n")
    return "".join(lines)


def build_toolchain_map():
    # 0. Collect Runtime Environment
    runtime_env = collect_runtime_environment()

    # 1. Collect Scripts
    py_files = sorted(glob.glob(os.path.join(SCRIPT_DIR, "*.py")))
    scripts_info = []
    for pf in py_files:
        fname = os.path.basename(pf)
        docstring = _extract_script_docstring(pf)
        scripts_info.append({
            "name": fname,
            "path": f"and_os/bin/{fname}",
            "description": docstring[:140] if docstring else "Python CLI Automation Script"
        })

    # 2. Collect Active Skills
    skill_files = sorted(glob.glob(os.path.join(SKILLS_DIR, "*/SKILL.md")))
    skills_info = []
    for sf in skill_files:
        sfolder = os.path.basename(os.path.dirname(sf))
        desc = _extract_skill_description(sf)
        skills_info.append({
            "name": sfolder,
            "path": f"and_os/lib/skills/{sfolder}/SKILL.md",
            "description": desc[:150] if desc else "System Skill Definition"
        })

    toolchain_data = {
        "version": "4.0.0",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "runtime": runtime_env,
        "total_scripts": len(scripts_info),
        "total_skills": len(skills_info),
        "scripts": scripts_info,
        "skills": skills_info
    }

    # Save JSON
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(toolchain_data, f, ensure_ascii=False, indent=2)

    # Save MD
    md_header = f"""---
tags:
  - system
  - toolchain
  - context
  - runtime
created: {toolchain_data['updated_at']}
---

# 🛠️ SYSTEM TOOLCHAIN — Runtime Standard & Toolchain Specification AnD os v8.1

> **Specification for AI Agents and Developers:** Canonical specification of programming language versions, installed libraries, {len(scripts_info)} core scripts, and {len(skills_info)} active skills.  
> **Automated Refresh:** `python3 and_os/bin/sys_cli.py env` or `python3 and_os/bin/system_tools_map.py --build`

---

## ⚙️ 0. Runtime Environment Standard

| Language / Runtime | Current Version | Target Standard | Executable Path | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Python** | `{runtime_env['python']['version']}` | `{runtime_env['python']['standard_target']}` | `{runtime_env['python']['executable']}` | 🟢 Active |
| **Node.js** | `{runtime_env['runtimes']['node']}` | `>=20.x LTS` | `Node Runtime (Homebrew)` | 🟢 Active |
| **Deno** | `{runtime_env['runtimes']['deno']}` | Modern TS/JS Runtime | `Deno (Homebrew)` | 🟢 Active |
| **Go** | `{runtime_env['runtimes']['go']}` | Compiled Backend Runtime | `Go (Homebrew)` | 🟢 Active |
| **Swift** | `{runtime_env['runtimes']['swift']}` | Native Apple Ecosystem | `Apple Swift 6 Toolchain` | 🟢 Active |
| **Git** | `{runtime_env['runtimes']['git']}` | `>= 2.40.x` | Apple Git | 🟢 Active |
| **Platform** | `{runtime_env['os']}` | macOS Darwin Apple Silicon | Darwin Kernel | 🟢 Active |

---

## 🛠️ 1. CLI Tools & System Utilities

| Tool | Version / Status | Role & Purpose |
| :--- | :--- | :--- |
| **FFmpeg** | `{runtime_env['cli_tools']['ffmpeg']}` | Декодирование, нарезка видео/аудио, конформ таймлайнов |
| **Tesseract OCR** | `{runtime_env['cli_tools']['tesseract']}` | Оптическое распознавание текста со сканов и скриншотов |
| **yt-dlp** | `{runtime_env['cli_tools']['yt_dlp']}` | Загрузка медиа и транскриптов YouTube (`yt_analyze.py`) |
| **uv** | `{runtime_env['cli_tools']['uv']}` | Ультрабыстрый менеджер пакетов и виртуальных окружений Python |
| **GitHub CLI (gh)** | `{runtime_env['cli_tools']['gh']}` | Управление репозиториями, PR и релизами GitHub |
| **jq** | `{runtime_env['cli_tools']['jq']}` | Потоковая фильтрация и парсинг JSON в терминале |
| **SQLite3** | `{runtime_env['cli_tools']['sqlite']}` | Встроенное хранилище индексов и задач (`task_vault.db`) |
| **tmux** | `{runtime_env['cli_tools']['tmux']}` | Мультиплексор терминальных сессий |

---

## 🎨 2. DCC, 3D & Creative Suites (Muscle Realm)

| Software / Suite | Version / Status | Production Domain / Role |
| :--- | :--- | :--- |
| **Blender** | `{runtime_env['creative_and_dcc']['blender']}` | 3D-моделирование, процедурные ассеты, рендер (`cg_workspace`) |
| **Houdini** | `{runtime_env['creative_and_dcc']['houdini']}` | Процедурный FX/динамика, Solaris, USD пайплайн |
| **DaVinci Resolve** | `{runtime_env['creative_and_dcc']['davinci_resolve']}` | Цветокоррекция, финальный монтаж, конформ шотов (`openmontage-builder`) |
| **Xcode** | `{runtime_env['creative_and_dcc']['xcode']}` | Нативная разработка iOS/macOS игр и приложений (Остров 9) |
| **Comfy Desktop** | `{runtime_env['creative_and_dcc']['comfy_desktop']}` | Нейросетевая генерация и стилизация шотов (ComfyUI / ControlNet) |
| **Unity Hub** | `{runtime_env['creative_and_dcc']['unity_hub']}` | Менеджер игровых движков Unity (Standby / Cross-platform) |

---

## 📱 3. Desktop Applications & System Bridges

| Application | Version / Status | System Interaction |
| :--- | :--- | :--- |
| **Obsidian** | `{runtime_env['apps']['obsidian']}` | Суверенное когнитивное пространство (Brain Realm) |
| **Mattermost** | `{runtime_env['apps']['mattermost']}` | Корпоративный мессенджер Production Studio (`mattermost_sync.py`) |
| **Telegram** | `{runtime_env['apps']['telegram']}` | Каналы, боты и оперативная коммуникация (`tg_bot_app`) |
| **Docker** | `{runtime_env['apps']['docker']}` | Контейнеризация микросервисов и баз данных |

---

### 📦 Installed Python Packages & Modules ({runtime_env['python']['total_packages']} total)

"""
    pkg_tables = _render_packages_markdown(runtime_env['python']['packages_categorized'])

    md_scripts = f"""---

## ⚡ 4. Core Executable Scripts (and_os/bin/ & sbin/ — {len(scripts_info)} scripts)

| Script | Purpose & Description |
| :--- | :--- |
"""
    for s in scripts_info:
        md_scripts += f"| `{s['name']}` | {s['description']} |\n"

    md_skills = f"""
---

## 🧠 5. Declarative Skills (and_os/lib/skills/ — {len(skills_info)} skills)

| Skill | Purpose & Routing |
| :--- | :--- |
"""
    for sk in skills_info:
        md_skills += f"| `[[and_os/lib/skills/{sk['name']}/SKILL|{sk['name']}]]` | {sk['description']} |\n"

    md_skills += "\n---\n[[SYSTEM_MAP|← Master Atlas SYSTEM_MAP.md]] | [[SYSTEM|← Master Manifest SYSTEM.md]]\n"

    with open(MD_OUTPUT, "w", encoding="utf-8") as f:
        f.write(md_header + pkg_tables + md_scripts + md_skills)

    # 3. Update /proc virtual mesh file
    os.makedirs(PROC_DIR, exist_ok=True)
    with open(os.path.join(PROC_DIR, "env.stat"), "w", encoding="utf-8") as pf:
        pf.write(f"PYTHON_VER={runtime_env['python']['version']}\n")
        pf.write(f"PYTHON_PACKAGES_COUNT={runtime_env['python']['total_packages']}\n")
        pf.write(f"NODE_VER={runtime_env['runtimes']['node']}\n")
        pf.write(f"GIT_VER={runtime_env['runtimes']['git']}\n")
        pf.write(f"SCRIPTS_COUNT={len(scripts_info)}\n")
        pf.write(f"SKILLS_COUNT={len(skills_info)}\n")
        pf.write(f"UPDATED={toolchain_data['updated_at']}\n")

    return toolchain_data

def main():
    parser = argparse.ArgumentParser(description="System Toolchain & Runtime Map Generator")
    parser.add_argument("--build", action="store_true", default=True, help="Сгенерировать карту инструментария и рантаймов")
    parser.add_argument("--json", action="store_true", help="Вывод только в формате JSON")
    args = parser.parse_args()

    data = build_toolchain_map()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"⚡ [Toolchain & Runtime Engine] Успешно актуализировано!")
        print(f"  • Python: {data['runtime']['python']['version']} ({data['runtime']['python']['total_packages']} пакетов)")
        print(f"  • Node.js: {data['runtime']['runtimes']['node']} | Deno: {data['runtime']['runtimes']['deno']} | Swift: {data['runtime']['runtimes']['swift']}")
        print(f"  • DCC: Blender ({data['runtime']['creative_and_dcc']['blender']}), Houdini ({data['runtime']['creative_and_dcc']['houdini']}), Resolve ({data['runtime']['creative_and_dcc']['davinci_resolve']}), Xcode ({data['runtime']['creative_and_dcc']['xcode']})")
        print(f"  • Скриптов ядра: {data['total_scripts']} | Скиллов: {data['total_skills']}")
        print(f"  • Паспорт: and_os/etc/SYSTEM_TOOLCHAIN.md")
        print(f"  • Машиночитаемый JSON: and_os/etc/SYSTEM_TOOLCHAIN.json")
        print(f"  • Виртуальный статус: and_os/proc/env.stat")

if __name__ == "__main__":
    main()
