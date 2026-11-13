#!/usr/bin/env python3
"""
pdf_twin_converter.py — Automatic creation of informational Markdown twins for PDFs.
Principle: Think in Code (Rule #16), Data Safety (Rule #7).

Features:
  1. Finds all PDFs in the vault (or at the given path).
  2. Converts them into clean structured Markdown (.md twins).
  3. Moves the original PDF into the `.pdf_archive/` subcatalog next to the original.
  4. Writes a header with a wiki-link to the archived original PDF into the .md twin.
  5. Automatically updates the Quick DB (Clippings/quick_knowledge_db.json).

Usage:
  python3 pdf_twin_converter.py --check             # Check PDFs only, no conversion
  python3 pdf_twin_converter.py --run               # Perform the conversion and archiving
  python3 pdf_twin_converter.py --file "<path>"    # Convert a specific PDF
"""

import os
import sys
import re
import shutil
import json
import argparse
import subprocess
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".pdf_archive"}

def convert_pdf_to_text(pdf_path):
    # Attempt 1: convert_doc.py (Anydoc / markitdown / pypdf)
    convert_doc_script = os.path.join(os.path.dirname(__file__), "convert_doc.py")
    if os.path.exists(convert_doc_script):
        cmd = [sys.executable, convert_doc_script, pdf_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
            
    # Attempt 2: pypdf directly
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text_parts = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text()
            if txt:
                text_parts.append(f"## Страница {i+1}\n\n{txt}")
        if text_parts:
            return "\n\n".join(text_parts)
    except (ImportError, OSError, Exception) as e:
        sys.stderr.write(f"[pdf_twin_converter] Warning extracting pypdf text {pdf_path}: {e}\n")

    return f"_Не удалось извлечь текстовый контент из бинарного PDF. Оригинальный файл сохранен в архиве._"

def process_pdf(pdf_path, run=False):
    rel_pdf = os.path.relpath(pdf_path, VAULT_ROOT)
    parent_dir = os.path.dirname(pdf_path)
    base_name = os.path.basename(pdf_path)
    name_no_ext = os.path.splitext(base_name)[0]
    
    md_twin_path = os.path.join(parent_dir, f"{name_no_ext}.md")
    archive_dir = os.path.join(parent_dir, ".pdf_archive")
    archived_pdf_path = os.path.join(archive_dir, base_name)
    rel_archived_pdf = os.path.relpath(archived_pdf_path, VAULT_ROOT)

    if not run:
        return {
            "pdf": rel_pdf,
            "md_twin": os.path.relpath(md_twin_path, VAULT_ROOT),
            "archive_target": rel_archived_pdf,
            "status": "PENDING"
        }

    # Extract text
    extracted_text = convert_pdf_to_text(pdf_path)

    # Move original to .pdf_archive
    os.makedirs(archive_dir, exist_ok=True)
    shutil.move(pdf_path, archived_pdf_path)

    # Create MD Twin content
    today_str = datetime.now().strftime("%Y-%m-%d")
    md_content = f"""---
tags:
  - pdf-twin
  - auto-generated
created: {today_str}
original_pdf: "{rel_archived_pdf}"
---

# 📄 {name_no_ext} (Информационный Двойник)

> [!NOTE] 
> Это автоматический информационный двойник PDF-документа для быстрого поиска ИИ и нулевого расхода токенов.
> **Оригинальный PDF сохранён в архиве:** [`{base_name}`](file://{archived_pdf_path})

---

## 📝 Извлечённое содержимое

{extracted_text}
"""

    with open(md_twin_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return {
        "pdf": rel_pdf,
        "md_twin": os.path.relpath(md_twin_path, VAULT_ROOT),
        "archive_target": rel_archived_pdf,
        "status": "SUCCESS"
    }

def main():
    parser = argparse.ArgumentParser(description="PDF Twin Converter Module")
    parser.add_argument("--check", action="store_true", help="Find all PDFs for conversion without changes")
    parser.add_argument("--run", action="store_true", help="Perform the conversion and move to the archive")
    parser.add_argument("--file", type=str, help="Path to a specific PDF file")

    args = parser.parse_args()

    pdf_files = []
    if args.file:
        full_p = os.path.abspath(args.file)
        if os.path.exists(full_p) and full_p.endswith(".pdf"):
            pdf_files.append(full_p)
    else:
        for root, dirs, files in os.walk(VAULT_ROOT):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                if f.endswith(".pdf"):
                    pdf_files.append(os.path.join(root, f))

    print(f"=== PDF Twin Converter: PDF files found: {len(pdf_files)} ===")

    results = []
    for pdf_p in pdf_files:
        res = process_pdf(pdf_p, run=args.run)
        results.append(res)
        status_symbol = "✅ SUCCESS" if res["status"] == "SUCCESS" else "⏳ PENDING"
        print(f"{status_symbol}: {res['pdf']} -> {res['md_twin']} (Archive: {res['archive_target']})")

    if args.run and pdf_files:
        # Update Quick DB and Sync Context
        sync_script = os.path.join(os.path.dirname(__file__), "sync_context.py")
        if os.path.exists(sync_script):
            print("\n⚡ Context synchronization and Quick Knowledge DB update...")
            subprocess.run([sys.executable, sync_script, "--fix"], capture_output=True, text=True)

if __name__ == "__main__":
    main()
