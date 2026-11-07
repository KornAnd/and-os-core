#!/usr/bin/env python3
"""
doc_analyze.py — универсальный анализатор документов, таблиц, PDF и изображений.
Реализует принцип Think in Code (Правило №16) и Context Budget (Правило №9).

Поддерживаемые форматы:
  - PDF (.pdf): структура, страницы, извлечение таблиц в Markdown (через pdfplumber / pdftotext)
  - Excel (.xlsx, .xls): листы, формулы, структура, конвертация в Markdown (через openpyxl)
  - Word (.docx): структура разделов, параграфы, таблицы (через встроенный zip/xml)
  - Изображения (.png, .jpg, .webp): метаданные, размеры, OCR-распознавание текста (tesseract rus+eng)

Использование:
  python3 doc_analyze.py <файл>                          # Компактный паспорт файла (< 250 токенов)
  python3 doc_analyze.py <файл.pdf> --pages 1-3          # Извлечение текста конкретных страниц
  python3 doc_analyze.py <файл.pdf> --tables             # Извлечение всех таблиц в Markdown
  python3 doc_analyze.py <файл.pdf> --search "термин"    # Поиск страниц с совпадениями
  python3 doc_analyze.py <файл.xlsx> --sheet "Смета"     # Превью конкретного листа в Markdown
  python3 doc_analyze.py <файл.xlsx> --formulas          # Поиск формул и связей
  python3 doc_analyze.py <картинка> --ocr                # OCR-распознавание текста
  python3 doc_analyze.py <файл.docx> --text              # Извлечение структурированного текста
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
                print(f"📄 [PDF Паспорт] {os.path.basename(path)}")
                print(f"• Размер: {format_size(os.path.getsize(path))}")
                print(f"• Страниц: {total_pages}")
                if meta.get("Title"): print(f"• Заголовок: {meta.get('Title')}")
                if meta.get("Author"): print(f"• Автор: {meta.get('Author')}")
                if meta.get("CreationDate"): print(f"• Создан: {meta.get('CreationDate')}")
                
                # Sample first page header / outline
                p1_text = pdf.pages[0].extract_text() or ""
                first_lines = [line.strip() for line in p1_text.splitlines() if line.strip()][:5]
                if first_lines:
                    print("• Начало документа:")
                    for l in first_lines:
                        print(f"    {l[:100]}")
                print("\n💡 Для извлечения: --pages 1-3, --tables или --search 'текст'")
                return

            # 2. Search
            if args.search:
                query = args.search.lower()
                matches = []
                for idx, page in enumerate(pdf.pages, 1):
                    txt = page.extract_text() or ""
                    if query in txt.lower():
                        matches.append(idx)
                print(f"🔍 Поиск '{args.search}' в {os.path.basename(path)}: найдено на страницах: {matches or 'не найдено'}")
                return

            # 3. Extract text from pages
            if args.pages:
                pages_to_extract = parse_page_range(args.pages, total_pages)
                print(f"=== Выжимка текста (стр. {', '.join(map(str, pages_to_extract))}) ===")
                for p_num in pages_to_extract:
                    page = pdf.pages[p_num - 1]
                    txt = page.extract_text() or "(нет текста / скан)"
                    print(f"\n--- [Страница {p_num} / {total_pages}] ---")
                    print(txt.strip())

            # 4. Extract tables to Markdown
            if args.tables:
                print(f"=== Таблицы из {os.path.basename(path)} ===")
                table_found = False
                target_pages = parse_page_range(args.pages, total_pages) if args.pages else range(1, total_pages + 1)
                for p_num in target_pages:
                    page = pdf.pages[p_num - 1]
                    tables = page.extract_tables()
                    for t_idx, tbl in enumerate(tables, 1):
                        table_found = True
                        print(f"\n📊 [Таблица {t_idx} на стр. {p_num}]:")
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
                    print("Таблицы не обнаружены.")
    except Exception as e:
        print(f"❌ Ошибка анализа PDF: {e}")

# ── EXCEL ANALYZER ──────────────────────────────────────────────────────
def analyze_xlsx(path, args):
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=False)
        
        # 1. Info / Passport
        if not args.sheet and not args.formulas and not args.tables:
            print(f"📊 [Excel Паспорт] {os.path.basename(path)}")
            print(f"• Размер: {format_size(os.path.getsize(path))}")
            print(f"• Листы ({len(wb.sheetnames)}): {', '.join(wb.sheetnames)}")
            for name in wb.sheetnames[:3]:
                ws = wb[name]
                print(f"  - Лист '{name}': {ws.max_row} строк × {ws.max_column} колонок")
            print("\n💡 Для извлечения: --sheet '<имя>' [--tables] или --formulas")
            return

        # 2. Formulas inspection
        if args.formulas:
            print(f"=== Формулы в {os.path.basename(path)} ===")
            target_sheets = [args.sheet] if args.sheet else wb.sheetnames
            for sname in target_sheets:
                if sname not in wb.sheetnames: continue
                ws = wb[sname]
                formulas = []
                for row in ws.iter_rows(max_row=min(ws.max_row or 1, 100)):
                    for cell in row:
                        if isinstance(cell.value, str) and cell.value.startswith('='):
                            formulas.append(f"{cell.coordinate}: {cell.value}")
                print(f"\nЛист '{sname}': найдено формул: {len(formulas)}")
                for f in formulas[:15]:
                    print(f"  • {f}")
            return

        # 3. Sheet tables to Markdown
        if args.sheet or args.tables:
            sheet_name = args.sheet if args.sheet else wb.sheetnames[0]
            if sheet_name not in wb.sheetnames:
                print(f"❌ Лист '{sheet_name}' не найден в файле.")
                return
            ws = wb[sheet_name]
            max_r = min(ws.max_row or 1, 50)
            max_c = min(ws.max_column or 1, 15)
            print(f"=== Лист '{sheet_name}' ({max_r} строк × {max_c} колонок в Markdown) ===")
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
                print(f"\n⚠️ Превью обрезано до {max_r} строк × {max_c} колонок (всего {ws.max_row}×{ws.max_column}).")
    except Exception as e:
        print(f"❌ Ошибка анализа Excel: {e}")

# ── IMAGE / OCR ANALYZER ────────────────────────────────────────────────
def analyze_image(path, args):
    try:
        from PIL import Image
        with Image.open(path) as img:
            w, h = img.size
            fmt = img.format
            mode = img.mode
        
        print(f"🖼️ [Изображение] {os.path.basename(path)}")
        print(f"• Размер: {w} × {h} px | Формат: {fmt} ({mode}) | Вес: {format_size(os.path.getsize(path))}")
        
        # Run OCR if requested or by default if image
        if args.ocr or not args.info_only:
            print("\n📝 [OCR Текст (tesseract rus+eng)]:")
            res = subprocess.run(
                ["tesseract", path, "-", "-l", "rus+eng"],
                capture_output=True, text=True, timeout=30
            )
            out = res.stdout.strip()
            if out:
                lines = out.splitlines()
                print(f"(Распознано {len(lines)} строк):")
                for l in lines:
                    if l.strip():
                        print(f"  {l}")
            else:
                print("(Текст на изображении не обнаружен)")
    except Exception as e:
        print(f"❌ Ошибка анализа изображения: {e}")

# ── WORD (.docx) ANALYZER ───────────────────────────────────────────────
def analyze_docx(path, args):
    try:
        if not zipfile.is_zipfile(path):
            print(f"❌ Файл {path} не является корректным docx.")
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
        
        print(f"📑 [Word Документ] {os.path.basename(path)}")
        print(f"• Размер: {format_size(os.path.getsize(path))}")
        print(f"• Параграфов: {len(paragraphs)}")
        
        if args.text or len(paragraphs) <= 20:
            print("\n=== Текст документа ===")
            for p in paragraphs:
                print(p)
        else:
            print("\n=== Начало документа (первые 10 параграфов) ===")
            for p in paragraphs[:10]:
                print(f"• {p}")
            print("\n💡 Для полной выгрузки укажите флаг --text")
    except Exception as e:
        print(f"❌ Ошибка анализа docx: {e}")

# ── MAIN DISPATCHER ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Universal Document & Image Analyzer (Think in Code)")
    parser.add_argument("path", help="Путь к файлу")
    parser.add_argument("--pages", help="Диапазон страниц для PDF (напр. 1-3 или 1,5)")
    parser.add_argument("--tables", action="store_true", help="Извлечь таблицы в Markdown")
    parser.add_argument("--sheet", help="Имя листа для Excel")
    parser.add_argument("--formulas", action="store_true", help="Показать формулы Excel")
    parser.add_argument("--ocr", action="store_true", help="Запустить OCR для картинки")
    parser.add_argument("--text", action="store_true", help="Полное извлечение текста (docx/pdf)")
    parser.add_argument("--search", help="Поиск текста в PDF")
    parser.add_argument("--info-only", action="store_true", help="Только метаданные")
    
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    path = os.path.abspath(args.path)
    
    if not os.path.exists(path):
        print(f"❌ Файл не найден: {path}")
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
        print(f"📄 [Файл {ext}] {os.path.basename(path)} ({format_size(os.path.getsize(path))})")
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [f.readline() for _ in range(20)]
            print("".join(lines))
        except Exception as e:
            print(f"Двоичный файл: {e}")

if __name__ == "__main__":
    main()
