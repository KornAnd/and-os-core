#!/usr/bin/env python3
"""
doc_analyze.py — The universal analyzer of the documents, the tables, the PDF and the images.
Implements the Think in Code principle (Rule #16) and the Context Budget (Rule #9).

The supported formats:
  - PDF (.pdf): the structure, the pages, the extraction of the tables into the Markdown (via the pdfplumber / pdftotext)
  - Excel (.xlsx, .xls): the sheets, the formulas, the structure, the conversion into the Markdown (via the openpyxl)
  - Word (.docx): the structure of the sections, the paragraphs, the tables (via the embedded zip/xml)
  - The images (.png, .jpg, .webp): the metadata, the sizes, the OCR recognition of the text (tesseract rus+eng)

Usage:
  python3 doc_analyze.py <file>                          # The compact passport of the file (< 250 tokens)
  python3 doc_analyze.py <file.pdf> --pages 1-3          # The extraction of the text of the specific pages
  python3 doc_analyze.py <file.pdf> --tables             # The extraction of all the tables into the Markdown
  python3 doc_analyze.py <file.pdf> --search "term"      # The search of the pages with the matches
  python3 doc_analyze.py <file.xlsx> --sheet "Budget"    # The preview of the specific sheet in the Markdown
  python3 doc_analyze.py <file.xlsx> --formulas          # The search of the formulas and the links
  python3 doc_analyze.py <picture> --ocr                 # The OCR recognition of the text
  python3 doc_analyze.py <file.docx> --text              # The extraction of the structured text
"""

import os
import sys
import argparse
import subprocess
import json
import logging
import xml.etree.ElementTree as ET
import zipfile

logging.getLogger("pdfminer").setLevel(logging.ERROR)

def format_size(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def parse_page_range(range_str, max_pages):
    pages = set()
    parts = range_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                for p in range(max(1, start), min(max_pages, end) + 1):
                    pages.add(p)
            except ValueError as e:
                sys.stderr.write(f"[doc_analyze] Invalid page range format '{part}': {e}\n")
        else:
            try:
                p = int(part)
                if 1 <= p <= max_pages:
                    pages.add(p)
            except ValueError as e:
                sys.stderr.write(f"[doc_analyze] Invalid page number '{part}': {e}\n")
    return sorted(pages)

# ── PDF ANALYZER ────────────────────────────────────────────────────────
def analyze_pdf(path, args):
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            meta = pdf.metadata or {}
            
            # 1. Info / Passport
            if not args.pages and not args.tables and not args.search:
                print(f"📄 [PDF Passport] {os.path.basename(path)}")
                print(f"• Size: {format_size(os.path.getsize(path))}")
                print(f"• Pages: {total_pages}")
                if meta.get("Title"): print(f"• Title: {meta.get('Title')}")
                if meta.get("Author"): print(f"• Author: {meta.get('Author')}")
                if meta.get("CreationDate"): print(f"• Created: {meta.get('CreationDate')}")
                
                # Sample first page header / outline
                p1_text = pdf.pages[0].extract_text() or ""
                first_lines = [line.strip() for line in p1_text.splitlines() if line.strip()][:5]
                if first_lines:
                    print("• The beginning of the document:")
                    for l in first_lines:
                        print(f"    {l[:100]}")
                print("\n💡 For the extraction: --pages 1-3, --tables or --search 'text'")
                return

            # 2. Search
            if args.search:
                query = args.search.lower()
                matches = []
                for idx, page in enumerate(pdf.pages, 1):
                    txt = page.extract_text() or ""
                    if query in txt.lower():
                        matches.append(idx)
                print(f"🔍 The search of '{args.search}' in {os.path.basename(path)}: found on the pages: {matches or 'not found'}")
                return

            # 3. Extract text from pages
            if args.pages:
                pages_to_extract = parse_page_range(args.pages, total_pages)
                print(f"=== The text extract (p. {', '.join(map(str, pages_to_extract))}) ===")
                for p_num in pages_to_extract:
                    page = pdf.pages[p_num - 1]
                    txt = page.extract_text() or "(no text / scan)"
                    print(f"\n--- [Page {p_num} / {total_pages}] ---")
                    print(txt.strip())

            # 4. Extract tables to Markdown
            if args.tables:
                print(f"=== The tables from {os.path.basename(path)} ===")
                table_found = False
                target_pages = parse_page_range(args.pages, total_pages) if args.pages else range(1, total_pages + 1)
                for p_num in target_pages:
                    page = pdf.pages[p_num - 1]
                    tables = page.extract_tables()
                    for t_idx, tbl in enumerate(tables, 1):
                        table_found = True
                        print(f"\n📊 [Table {t_idx} on the p. {p_num}]:")
                        # Format as markdown
                        cleaned_rows = []
                        for row in tbl:
                            cleaned_rows.append([str(c or '').replace('\n', ' ').strip() for c in row])
                        if cleaned_rows:
                            headers = cleaned_rows[0]
                            print("| " + " | ".join(headers) + " |")
                            print("| " + " | ".join(["---"] * len(headers)) + " |")
                            for r in cleaned_rows[1:]:
                                print("| " + " | ".join(r) + " |")
                if not table_found:
                    print("The tables were not detected.")
    except Exception as e:
        print(f"❌ The PDF analysis error: {e}")

# ── EXCEL ANALYZER ──────────────────────────────────────────────────────
def analyze_xlsx(path, args):
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=False)
        
        # 1. Info / Passport
        if not args.sheet and not args.formulas and not args.tables:
            print(f"📊 [Excel Passport] {os.path.basename(path)}")
            print(f"• Size: {format_size(os.path.getsize(path))}")
            print(f"• Sheets ({len(wb.sheetnames)}): {', '.join(wb.sheetnames)}")
            for name in wb.sheetnames[:3]:
                ws = wb[name]
                print(f"  - Sheet '{name}': {ws.max_row} rows x {ws.max_column} columns")
            print("\n💡 For the extraction: --sheet '<name>' [--tables] or --formulas")
            return

        # 2. Formulas inspection
        if args.formulas:
            print(f"=== The formulas in {os.path.basename(path)} ===")
            target_sheets = [args.sheet] if args.sheet else wb.sheetnames
            for sname in target_sheets:
                if sname not in wb.sheetnames: continue
                ws = wb[sname]
                formulas = []
                for row in ws.iter_rows(max_row=min(ws.max_row or 1, 100)):
                    for cell in row:
                        if isinstance(cell.value, str) and cell.value.startswith('='):
                            formulas.append(f"{cell.coordinate}: {cell.value}")
                print(f"\nSheet '{sname}': the formulas were found: {len(formulas)}")
                for f in formulas[:15]:
                    print(f"  • {f}")
            return

        # 3. Sheet tables to Markdown
        if args.sheet or args.tables:
            sheet_name = args.sheet if args.sheet else wb.sheetnames[0]
            if sheet_name not in wb.sheetnames:
                print(f"❌ The sheet '{sheet_name}' was not found in the file.")
                return
            ws = wb[sheet_name]
            max_r = min(ws.max_row or 1, 50)
            max_c = min(ws.max_column or 1, 15)
            print(f"=== The sheet '{sheet_name}' ({max_r} rows x {max_c} columns in the Markdown) ===")
            rows = []
            for row in ws.iter_rows(max_row=max_r, max_col=max_c, values_only=True):
                r_vals = [str(c if c is not None else '').replace('\n', ' ').strip() for c in row]
                if any(r_vals):
                    rows.append(r_vals)
            if rows:
                headers = rows[0]
                print("| " + " | ".join(headers) + " |")
                print("| " + " | ".join(["---"] * len(headers)) + " |")
                for r in rows[1:]:
                    print("| " + " | ".join(r) + " |")
            if (ws.max_row or 0) > max_r or (ws.max_column or 0) > max_c:
                print(f"\n⚠️ The preview was trimmed to {max_r} rows x {max_c} columns (total {ws.max_row}x{ws.max_column}).")
    except Exception as e:
        print(f"❌ The Excel analysis error: {e}")

# ── IMAGE / OCR ANALYZER ────────────────────────────────────────────────
def analyze_image(path, args):
    try:
        from PIL import Image
        with Image.open(path) as img:
            w, h = img.size
            fmt = img.format
            mode = img.mode
        
        print(f"🖼️ [Image] {os.path.basename(path)}")
        print(f"• Size: {w} x {h} px | Format: {fmt} ({mode}) | Weight: {format_size(os.path.getsize(path))}")
        
        # Run OCR if requested or by default if image
        if args.ocr or not args.info_only:
            print("\n📝 [OCR Text (tesseract rus+eng)]:")
            res = subprocess.run(
                ["tesseract", path, "-", "-l", "rus+eng"],
                capture_output=True, text=True, timeout=30
            )
            out = res.stdout.strip()
            if out:
                lines = out.splitlines()
                print(f"(The lines were recognized: {len(lines)}):")
                for l in lines:
                    if l.strip():
                        print(f"  {l}")
            else:
                print("(The text on the image was not detected)")
    except Exception as e:
        print(f"❌ The image analysis error: {e}")

# ── WORD (.docx) ANALYZER ───────────────────────────────────────────────
def analyze_docx(path, args):
    try:
        if not zipfile.is_zipfile(path):
            print(f"❌ The file {path} is not a correct docx.")
            return
        with zipfile.ZipFile(path) as z:
            xml_content = z.read("word/document.xml")
        
        tree = ET.fromstring(xml_content)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        paragraphs = []
        for p in tree.iterfind('.//w:p', ns):
            texts = [node.text for node in p.iterfind('.//w:t', ns) if node.text]
            if texts:
                paragraphs.append("".join(texts).strip())
        
        print(f"📑 [Word Document] {os.path.basename(path)}")
        print(f"• Size: {format_size(os.path.getsize(path))}")
        print(f"• Paragraphs: {len(paragraphs)}")
        
        if args.text or len(paragraphs) <= 20:
            print("\n=== The text of the document ===")
            for p in paragraphs:
                print(p)
        else:
            print("\n=== The beginning of the document (the first 10 paragraphs) ===")
            for p in paragraphs[:10]:
                print(f"• {p}")
            print("\n💡 For the full export specify the --text flag")
    except Exception as e:
        print(f"❌ The docx analysis error: {e}")

# ── MAIN DISPATCHER ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Universal Document & Image Analyzer (Think in Code)")
    parser.add_argument("path", help="The path to the file")
    parser.add_argument("--pages", help="The range of the pages for the PDF (e.g. 1-3 or 1,5)")
    parser.add_argument("--tables", action="store_true", help="Extract the tables into the Markdown")
    parser.add_argument("--sheet", help="The name of the sheet for the Excel")
    parser.add_argument("--formulas", action="store_true", help="Show the formulas of the Excel")
    parser.add_argument("--ocr", action="store_true", help="Launch the OCR for the picture")
    parser.add_argument("--text", action="store_true", help="The full extraction of the text (docx/pdf)")
    parser.add_argument("--search", help="The text search in the PDF")
    parser.add_argument("--info-only", action="store_true", help="The metadata only")
    
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    path = os.path.abspath(args.path)
    
    if not os.path.exists(path):
        print(f"❌ The file was not found: {path}")
        sys.exit(1)
        
    ext = os.path.splitext(path)[1].lower()
    
    if ext == ".pdf":
        analyze_pdf(path, args)
    elif ext in [".xlsx", ".xls"]:
        analyze_xlsx(path, args)
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"]:
        analyze_image(path, args)
    elif ext in [".docx"]:
        analyze_docx(path, args)
    else:
        # Fallback text preview
        print(f"📄 [File {ext}] {os.path.basename(path)} ({format_size(os.path.getsize(path))})")
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [f.readline() for _ in range(20)]
            print("".join(lines))
        except Exception as e:
            print(f"The binary file: {e}")

if __name__ == "__main__":
    main()
