#!/usr/bin/env python3
"""
code_ast_shrinker.py — AST-based Python Code & Token Compressor (AnD os v8.1).
Core subsystem (and_os/lib/core/).
Rule #16: Think in Code, Rule #44: Task Context Bundling.

Transforms Python code into compact signatures (classes, methods, parameters, return types, docstrings)
omitting internal implementation bodies. Yields 80–90% prompt token reduction.
"""

import os
import ast
import sys
import json
from typing import Dict, Any, List

def shrink_python_code(code_text: str, filepath: str = "") -> str:
    """Extract compact structural signature from Python AST."""
    try:
        tree = ast.parse(code_text)
    except SyntaxError as e:
        return f"# [Syntax Error parsing {filepath}: {e}]"

    output_lines = [f"# Code Signature: {os.path.basename(filepath) or 'in-memory'}"]
    
    # Module docstring
    mod_doc = ast.get_docstring(tree)
    if mod_doc:
        first_line = mod_doc.strip().split("\n")[0]
        output_lines.append(f'"""{first_line}"""')

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            args_str = ", ".join(a.arg for a in node.args.args)
            returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
            doc = ast.get_docstring(node)
            doc_str = f' """{doc.strip().split(chr(10))[0]}"""' if doc else ""
            output_lines.append(f"def {node.name}({args_str}){returns}:{doc_str} ...")

        elif isinstance(node, ast.ClassDef):
            bases = ", ".join(ast.unparse(b) for b in node.bases)
            base_str = f"({bases})" if bases else ""
            output_lines.append(f"\nclass {node.name}{base_str}:")
            cdoc = ast.get_docstring(node)
            if cdoc:
                output_lines.append(f'    """{cdoc.strip().split(chr(10))[0]}"""')
            
            methods_found = False
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods_found = True
                    margs = ", ".join(a.arg for a in item.args.args)
                    mret = f" -> {ast.unparse(item.returns)}" if item.returns else ""
                    mdoc = ast.get_docstring(item)
                    mdoc_str = f' """{mdoc.strip().split(chr(10))[0]}"""' if mdoc else ""
                    output_lines.append(f"    def {item.name}({margs}){mret}:{mdoc_str} ...")
            if not methods_found:
                output_lines.append("    pass")

    return "\n".join(output_lines)

def shrink_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        return f"# Error: File {filepath} not found"
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    orig_chars = len(content)
    compressed = shrink_python_code(content, filepath)
    new_chars = len(compressed)
    ratio = round((1 - new_chars / max(orig_chars, 1)) * 100, 1)
    header = f"# [AST Shrink: {orig_chars} -> {new_chars} chars | Token Savings: -{ratio}%]\n"
    return header + compressed

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Python AST Code Shrinker (Token Optimizer)")
    parser.add_argument("file", help="Target Python file")
    args = parser.parse_args()

    print(shrink_file(args.file))

if __name__ == "__main__":
    main()
