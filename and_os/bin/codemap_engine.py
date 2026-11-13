#!/usr/bin/env python3
"""
codemap_engine.py — Ultra-lightweight architectural code map generator (Codemaps Engine).
AnD os v1.0.0 — Island 8 (Kernel & System Compiler).

Provides ~95% token economy when studying project structure:
1. Scans the AST (Abstract Syntax Tree) of Python (.py) and Swift (.swift) sources.
2. Extracts only class and struct headers, exported functions, methods and their signatures.
3. Ignores function bodies and implementation details.
4. Builds a compact hierarchical Markdown map (Codemap) for:
   - `and_os/opt/apps/cg_workspace/` (3D/CG modules);
   - `Nero/xcode/EscPlanet/` (game Swift architecture);
   - `and_os/bin/` (kernel system facades).
"""

import os
import sys
import ast
import json
import re
from typing import Dict, Any, List

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def parse_python_file(file_path: str) -> Dict[str, Any]:
    """Extracts classes and functions from a Python file without reading the implementation."""
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
    """Extracts structs, classes and functions from a Swift file via regex."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        classes = []
        # Find class/struct
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
    """Generates a compact Markdown architecture map of a directory."""
    lines = [f"# 🗺️ Architecture Map (Codemap): {title}\n"]
    lines.append(f"> **Directory**: `{target_dir}` | **Status**: 🟢 Auto-Generated (0-Token)\n")

    for root, dirs, files in sorted(os.walk(target_dir)):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "node_modules", "Tests"]]
        rel_dir = os.path.relpath(root, target_dir)
        header = f"### 📂 {rel_dir}" if rel_dir != "." else "### 📂 Project root"
        
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
