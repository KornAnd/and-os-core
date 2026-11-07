#!/usr/bin/env python3
"""
build_native.py — Системный компилятор Python-проектов в нативные бинарники (Правило №32).

Поддерживаемые компиляторы:
  - PyInstaller (основной)
  - Nuitka (высокая производительность C-translation)
  - py2app (нативные macOS .app бандлы)

Использование:
  python3 and_os/bins/build_native.py --app ftrack_gantt_mars --tool pyinstaller
  python3 and_os/bins/build_native.py --app vpn_service_app --tool nuitka --onefile
"""

import sys
import os
import subprocess
import argparse

def check_preflight(source_path: str) -> tuple[bool, str]:
    """Проверяет синтаксис файла и доступное место на диске перед компиляцией."""
    import py_compile, shutil
    # 1. Синтаксис
    try:
        py_compile.compile(source_path, doraise=True)
    except py_compile.PyCompileError as e:
        return False, f"Синтаксическая ошибка: {e}"
        
    # 2. Место на диске (порог 3.0 ГБ согласно Правилу №43)
    free_gb = shutil.disk_usage(os.path.dirname(source_path)).free / (1024**3)
    if free_gb < 3.0:
        return False, f"Недостаточно места на диске: {free_gb:.1f} GB (требуется >= 3.0 GB)"
        
    return True, f"OK (Синтаксис корректен, свободно {free_gb:.1f} GB)"

def resolve_app_path(app_id: str) -> str:
    """Определяет путь к приложению: and_os/opt/apps, Pulsar или прямой абсолютный путь."""
    from and_os.lib.core.root_config import resolve_vault_root
    vault_root = resolve_vault_root()
    from and_os.lib.core.root_config import resolve_pulsar_root
    pulsar_root = resolve_pulsar_root() or os.path.expanduser("~/Yandex.Disk.localized/WORK/pulsar")
    
    candidates = [
        os.path.join(vault_root, "and_os/opt/apps", app_id),
        os.path.join(pulsar_root, app_id),
        app_id
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""

def build_app(app_id, tool="pyinstaller", onefile=True, dry_run=False):
    app_dir = resolve_app_path(app_id)
    if not app_dir:
        print(f"❌ Папка приложения '{app_id}' не найдена в and_os/opt/apps/ или Pulsar!")
        sys.exit(1)
        
    main_py = os.path.join(app_dir, "server.py") if os.path.exists(os.path.join(app_dir, "server.py")) else ""
    if not main_py:
        main_py = os.path.join(app_dir, "main.py")
        if not os.path.exists(main_py):
            main_py = os.path.join(app_dir, "app.py")
            
    if not os.path.exists(main_py):
        print(f"❌ Точка входа (server.py / main.py / app.py) не найдена в {app_dir}!")
        sys.exit(1)
        
    # Pre-flight Gate
    ok, msg = check_preflight(main_py)
    if not ok:
        print(f"❌ [PRE-FLIGHT FAILED] Сборка отклонена: {msg}")
        sys.exit(1)
        
    dist_dir = os.path.join(app_dir, "dist")
    build_dir = os.path.join(app_dir, "build")
    
    print(f"==========================================================")
    print(f"🔨 [NATIVE BUILD] Компиляция приложения: {app_id}")
    print(f"📦 Исходная точка входа: {main_py}")
    print(f"🛠️  Инструмент компиляции: {tool}")
    print(f"🛡️  Pre-flight проверка: {msg}")
    print(f"==========================================================")
    
    if dry_run:
        print("🔍 [DRY-RUN] Пре-компиляционная проверка пройдена успешно. Сборка готова к запуску.")
        return
    
    if tool == "pyinstaller":
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--distpath", dist_dir,
            "--workpath", build_dir,
            "--noconfirm"
        ]
        if onefile:
            cmd.append("--onefile")
        cmd.append(main_py)
        
        try:
            subprocess.run(cmd, check=True)
            print(f"\n✅ Успешная сборка бинарника! Выходной каталог: {dist_dir}")
        except Exception as e:
            print(f"\n❌ Ошибка компиляции PyInstaller: {e}")
            
    elif tool == "nuitka":
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--output-dir=" + dist_dir,
            main_py
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"\n✅ Успешная сборка Nuitka! Выходной каталог: {dist_dir}")
        except Exception as e:
            print(f"\n❌ Ошибка компиляции Nuitka: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Native app builder script")
    parser.add_argument("--app", required=True, help="App ID in and_os/opt/apps/, Pulsar, or full path")
    parser.add_argument("--tool", default="pyinstaller", choices=["pyinstaller", "nuitka"], help="Compiler tool")
    parser.add_argument("--onedir", action="store_true", help="Build as directory instead of single file")
    parser.add_argument("--dry-run", action="store_true", help="Run pre-flight validation and syntax checks without compilation")
    args = parser.parse_args()
    
    build_app(args.app, tool=args.tool, onefile=not args.onedir, dry_run=args.dry_run)

