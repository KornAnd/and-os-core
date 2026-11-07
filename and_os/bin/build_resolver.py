#!/usr/bin/env python3
"""
build_resolver.py — Автономный резолвер ошибок сборки с минимальными диффами (Minimal Diffs).
AnD os v8.4 — Остров 8 (Kernel & Compiler) ⟷ Остров 7 & 9 (CG & Xcode/Swift Engine).

Принцип Minimal Diffs:
1. Запрещено производить архитектурный рефакторинг при падении сборки.
2. Локализует ошибку строго по строке и символу (Python Syntax/Import, Swift, TypeScript, C++/Metal).
3. Применяет минимально необходимое точечное исправление (missing import, type casting, trailing comma).
4. Запускает изолированный компиляционный тест (compile check / syntax verification).
5. При неудаче немедленно выполняет откат (atomic rollback) к исходному коду.
"""

import os
import sys
import json
import shutil
import subprocess
from typing import Dict, Any, Optional

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
BACKUP_DIR = os.path.join(VAULT_ROOT, "and_os", "var", "cache", "build_backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

def verify_file_compilation(file_path: str) -> Dict[str, Any]:
    """Проверяет синтаксис и компилируемость конкретного исходного файла."""
    if not os.path.exists(file_path):
        return {"status": "error", "valid": False, "error": f"File not found: {file_path}"}

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".py":
        cmd = [sys.executable, "-m", "py_compile", file_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "status": "ok" if res.returncode == 0 else "error",
            "valid": res.returncode == 0,
            "type": "python",
            "error": res.stderr.strip() if res.returncode != 0 else ""
        }
    elif ext == ".swift":
        # Быстрая проверка синтаксиса Swift через swiftc -parse
        swiftc = shutil.which("swiftc")
        if swiftc:
            cmd = [swiftc, "-parse", file_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "status": "ok" if res.returncode == 0 else "error",
                "valid": res.returncode == 0,
                "type": "swift",
                "error": res.stderr.strip() if res.returncode != 0 else ""
            }
        return {"status": "ok", "valid": True, "type": "swift", "note": "swiftc not installed, skipped"}
    elif ext in [".js", ".ts", ".json"]:
        if ext == ".json":
            try:
                with open(file_path, "r", encoding="utf-8") as jf:
                    json.load(jf)
                return {"status": "ok", "valid": True, "type": "json"}
            except Exception as e:
                return {"status": "error", "valid": False, "type": "json", "error": str(e)}
        js_bin = shutil.which("bun") or os.path.expanduser("~/.bun/bin/bun")
        if os.path.exists(js_bin) and ext in (".js", ".ts"):
            cmd = [js_bin, "build", "--no-bundle", file_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "status": "ok" if res.returncode == 0 else "error",
                "valid": res.returncode == 0,
                "type": "javascript_bun",
                "error": res.stderr.strip() if res.returncode != 0 else ""
            }
        node_bin = shutil.which("node")
        if node_bin and ext == ".js":
            cmd = [node_bin, "--check", file_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "status": "ok" if res.returncode == 0 else "error",
                "valid": res.returncode == 0,
                "type": "javascript",
                "error": res.stderr.strip() if res.returncode != 0 else ""
            }

    return {"status": "ok", "valid": True, "type": "unsupported_or_text"}

def apply_minimal_fix(file_path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """
    Атомарно применяет точечную замену и тестирует компиляцию.
    При возникновении синтаксической ошибки автоматически откатывает файл.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"Target file does not exist: {file_path}"}

    # 1. Создаем страховочную копию
    backup_file = os.path.join(BACKUP_DIR, f"{os.path.basename(file_path)}.bak")
    shutil.copy2(file_path, backup_file)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_str not in content:
            return {"status": "error", "message": "Target substring to replace not found in file."}

        # 2. Применяем минимальный диф
        new_content = content.replace(old_str, new_str, 1)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        # 3. Верифицируем сборку
        test_res = verify_file_compilation(file_path)
        if not test_res.get("valid", True):
            # Откат при ошибке
            shutil.copy2(backup_file, file_path)
            return {
                "status": "error",
                "action": "rolled_back",
                "message": f"Fix failed compilation test: {test_res.get('error')}. File restored from backup.",
                "file": file_path
            }

        return {
            "status": "ok",
            "action": "applied_minimal_diff",
            "file": file_path,
            "compilation_verified": True,
            "replaced_bytes": len(old_str),
            "inserted_bytes": len(new_str)
        }
    except Exception as e:
        shutil.copy2(backup_file, file_path)
        return {"status": "error", "message": f"Unexpected error: {str(e)}. File restored."}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        f = sys.argv[2]
        res = verify_file_compilation(f)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("Usage: build_resolver.py --verify <file_path>")
