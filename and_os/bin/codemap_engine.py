#!/usr/bin/env python3
"""
codemap_engine.py — Генератор сверхлегких архитектурных карт кода (Codemaps Engine).
AnD os v8.4 — Остров 8 (Kernel & System Compiler).

Обеспечивает 95% токеноэкономию при изучении структуры проектов:
1. Сканирует AST (Abstract Syntax Tree) исходников Python (.py) и Swift (.swift).
2. Извлекает только заголовки классов, структуры, экспортируемые функции, методы и их сигнатуры.
3. Игнорирует тела функций и детали реализации.
4. Формирует компактную иерархическую Markdown-карту (Codemap) для:
   - `and_os/opt/apps/cg_workspace/` (3D/CG-модули);
   - `Nero/xcode/EscPlanet/` (Swift-архитектура игры);
   - `and_os/bin/` (Системные фасады ядра).
"""

import os
import sys
import ast
import json
import re
from typing import Dict, Any, List

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def parse_python_file(file_path: str) -> Dict[str, Any]:
    """Извлекает классы и функции из Python файла без чтения реализации."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)

        classes = []
        functions = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                classes.append({"name": node.name, "methods": methods})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)

        return {"classes": classes, "functions": functions}
    except Exception as e:
        return {"classes": [], "functions": [], "error": str(e)}

def parse_swift_file(file_path: str) -> Dict[str, Any]:
    """Извлекает структуры, классы и функции из Swift файла через regex."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        classes = []
        # Находим class/struct
        for match in re.finditer(r'(?:public\s+|final\s+)?(class|struct|enum)\s+([A-Za-z0-9_]+)', content):
            entity_type, name = match.group(1), match.group(2)
            classes.append({"name": f"{entity_type} {name}", "methods": []})

        functions = []
        for match in re.finditer(r'(?:public\s+|override\s+|private\s+)?func\s+([A-Za-z0-9_]+)\s*\(', content):
            functions.append(match.group(1))

        return {"classes": classes, "functions": functions}
    except Exception as e:
        return {"classes": [], "functions": [], "error": str(e)}

def generate_codemap(target_dir: str, title: str = "Codemap") -> str:
    """Генерирует компактную Markdown карту архитектуры каталога."""
    lines = [f"# 🗺️ Архитектурная Карта (Codemap): {title}\n"]
    lines.append(f"> **Каталог**: `{target_dir}` | **Статус**: 🟢 Auto-Generated (0-Token)\n")

    for root, dirs, files in sorted(os.walk(target_dir)):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "node_modules", "Tests"]]
        rel_dir = os.path.relpath(root, target_dir)
        header = f"### 📂 {rel_dir}" if rel_dir != "." else "### 📂 Корень проекта"
        
        dir_content = []
        for f in sorted(files):
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                info = parse_python_file(fpath)
                cls_str = ", ".join([f"class {c['name']}" for c in info["classes"]])
                fn_str = ", ".join([f"{fn}()" for fn in info["functions"]])
                summary = []
                if cls_str: summary.append(cls_str)
                if fn_str: summary.append(fn_str)
                dir_content.append(f"- **`{f}`**: {'; '.join(summary) if summary else 'entry/script'}")
            elif f.endswith(".swift"):
                fpath = os.path.join(root, f)
                info = parse_swift_file(fpath)
                cls_str = ", ".join([c["name"] for c in info["classes"]])
                fn_str = ", ".join([f"{fn}()" for fn in info["functions"]])
                summary = []
                if cls_str: summary.append(cls_str)
                if fn_str: summary.append(fn_str)
                dir_content.append(f"- **`{f}`**: {'; '.join(summary) if summary else 'swift_module'}")

        if dir_content:
            lines.append(header)
            lines.extend(dir_content)
            lines.append("")

    return "\n".join(lines)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--dir":
        tdir = sys.argv[2]
        title = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(tdir)
        print(generate_codemap(tdir, title))
    else:
        print("Usage: codemap_engine.py --dir <target_dir> [title]")
