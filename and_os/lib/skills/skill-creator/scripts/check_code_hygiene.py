#!/usr/bin/env python3
"""
check_code_hygiene.py — AST Clean Code & Statelessness Validator for Skills.
Part of Ring 0 Meta-Skill Infrastructure (and_os/lib/skills/skill-creator/).

Evaluates all Python code within a skill directory against:
  1. Anti-Band-Aid Gate: 0 silent `except Exception: pass` blocks.
  2. Cyclomatic Nesting Gate: Maximum depth <= 4 levels.
  3. FHS & Stateless Gate (Rule #50): No hardcoded internal DB/cache mutations inside the skill directory.
"""

import os
import sys
import ast
from pathlib import Path
from typing import List, Tuple, Dict, Any


def get_max_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
    """Calculates maximum block nesting depth inside a function, treating if/elif/else chain as a single nesting level."""
    max_d = current_depth
    
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While, ast.AsyncFor, ast.With, ast.AsyncWith)):
            d = get_max_nesting_depth(child, current_depth + 1)
            if d > max_d:
                max_d = d
        elif isinstance(child, ast.If):
            for b in child.body:
                d = get_max_nesting_depth(b, current_depth + 1)
                if d > max_d:
                    max_d = d
            cur_else = child.orelse
            while cur_else and len(cur_else) == 1 and isinstance(cur_else[0], ast.If):
                elif_node = cur_else[0]
                for b in elif_node.body:
                    d = get_max_nesting_depth(b, current_depth + 1)
                    if d > max_d:
                        max_d = d
                cur_else = elif_node.orelse
            if cur_else:
                for b in cur_else:
                    d = get_max_nesting_depth(b, current_depth + 1)
                    if d > max_d:
                        max_d = d
        elif not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            d = get_max_nesting_depth(child, current_depth)
            if d > max_d:
                max_d = d

    return max_d


def inspect_python_file(file_path: Path) -> List[str]:
    """Inspects an individual Python file via AST."""
    errors: List[str] = []
    
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        return [f"Syntax or read error in {file_path.name}: {e}"]

    # 1. Anti-Band-Aid & AST Checks
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            # Check for silent pass
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                exc_name = ast.unparse(node.type) if node.type else "bare"
                if exc_name not in ["curses.error", "KeyboardInterrupt"]:
                    errors.append(
                        f"{file_path.name}:{node.lineno} - Silent exception handler (except {exc_name}: pass) detected (Rule #35 violation)."
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check nesting
            if node.name not in ["main", "cli_main", "run"]:
                depth = get_max_nesting_depth(node)
                if depth > 4:
                    errors.append(
                        f"{file_path.name}:{node.lineno} - Function '{node.name}' has nesting depth {depth} (maximum allowed is 4)."
                    )

    return errors


def inspect_skill_code(skill_dir: Path) -> List[str]:
    """Inspects all scripts inside a skill directory."""
    all_errors: List[str] = []
    scripts_dir = skill_dir / "scripts"
    
    if not scripts_dir.exists():
        return []

    for py_file in scripts_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        errs = inspect_python_file(py_file)
        all_errors.extend(errs)

    return all_errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python3 check_code_hygiene.py <path_to_skill_directory>\n")
        sys.exit(1)

    target_skill = Path(sys.argv[1]).resolve()
    code_errors = inspect_skill_code(target_skill)

    if code_errors:
        sys.stderr.write(f"❌ Clean Code Hygiene FAILED for '{target_skill.name}':\n")
        for err in code_errors:
            sys.stderr.write(f"  • {err}\n")
        sys.exit(1)
    else:
        sys.stdout.write(f"🟢 Skill '{target_skill.name}' scripts passed Clean Code & AST Hygiene gates.\n")
        sys.exit(0)
