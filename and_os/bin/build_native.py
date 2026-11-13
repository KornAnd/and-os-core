#!/usr/bin/env python3
"""
build_native.py — System compiler of Python projects into native binaries (Rule #32).

Supported compilers:
  - PyInstaller (primary)
  - Nuitka (high-performance C-translation)
  - py2app (native macOS .app bundles)

Usage:
  python3 and_os/bins/build_native.py --app ftrack_gantt_mars --tool pyinstaller
  python3 and_os/bins/build_native.py --app vpn_service_app --tool nuitka --onefile
"""

import sys
import os
import subprocess
import argparse

def check_preflight(source_path: str) -> tuple[bool, str]:
    """Checks the file syntax and the free disk space before compilation."""
    import py_compile, shutil
    # 1. Syntax
    try:
        py_compile.compile(source_path, doraise=True)
    except py_compile.PyCompileError as e:
        return False, f"Syntax error: {e}"
        
    # 2. Free disk space (the 3.0 GB threshold per Rule #43)
    free_gb = shutil.disk_usage(os.path.dirname(source_path)).free / (1024**3)
    if free_gb < 3.0:
        return False, f"Insufficient disk space: {free_gb:.1f} GB (>= 3.0 GB required)"
        
    return True, f"OK (syntax is correct, {free_gb:.1f} GB free)"

def resolve_app_path(app_id: str) -> str:
    """Resolves the application path: and_os/opt/apps, Pulsar or a direct absolute path."""
    from and_os.lib.core.root_config import resolve_vault_root
    vault_root = resolve_vault_root()
    from and_os.lib.core.root_config import resolve_pulsar_root
    pulsar_root = resolve_pulsar_root() or os.path.expanduser("./pulsar")
    
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
        print(f"❌ Application folder '{app_id}' not found in and_os/opt/apps/ or Pulsar!")
        sys.exit(1)
        
    main_py = os.path.join(app_dir, "server.py") if os.path.exists(os.path.join(app_dir, "server.py")) else ""
    if not main_py:
        main_py = os.path.join(app_dir, "main.py")
        if not os.path.exists(main_py):
            main_py = os.path.join(app_dir, "app.py")
            
    if not os.path.exists(main_py):
        print(f"❌ Entry point (server.py / main.py / app.py) not found in {app_dir}!")
        sys.exit(1)
        
    # Pre-flight Gate
    ok, msg = check_preflight(main_py)
    if not ok:
        print(f"❌ [PRE-FLIGHT FAILED] Build rejected: {msg}")
        sys.exit(1)
        
    dist_dir = os.path.join(app_dir, "dist")
    build_dir = os.path.join(app_dir, "build")
    
    print(f"==========================================================")
    print(f"🔨 [NATIVE BUILD] Compiling application: {app_id}")
    print(f"📦 Source entry point: {main_py}")
    print(f"🛠️  Compilation tool: {tool}")
    print(f"🛡️  Pre-flight check: {msg}")
    print(f"==========================================================")
    
    if dry_run:
        print("🔍 [DRY-RUN] Pre-compilation check passed successfully. Build is ready to start.")
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
            print(f"\n✅ Binary build succeeded! Output catalog: {dist_dir}")
        except Exception as e:
            print(f"\n❌ PyInstaller compilation error: {e}")
            
    elif tool == "nuitka":
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--output-dir=" + dist_dir,
            main_py
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"\n✅ Nuitka build succeeded! Output catalog: {dist_dir}")
        except Exception as e:
            print(f"\n❌ Nuitka compilation error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Native app builder script")
    parser.add_argument("--app", required=True, help="App ID in and_os/opt/apps/, Pulsar, or full path")
    parser.add_argument("--tool", default="pyinstaller", choices=["pyinstaller", "nuitka"], help="Compiler tool")
    parser.add_argument("--onedir", action="store_true", help="Build as directory instead of single file")
    parser.add_argument("--dry-run", action="store_true", help="Run pre-flight validation and syntax checks without compilation")
    args = parser.parse_args()
    
    build_app(args.app, tool=args.tool, onefile=not args.onedir, dry_run=args.dry_run)

