#!/usr/bin/env python3
"""Анализатор Excel/Google Sheets: чтение формул, связей, структуры.

Запуск: python3 xl_analyze.py <путь к файлу> [--sheet имя] [--formulas] [--structure]
"""

import sys, os, json
try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None

def analyze_workbook(path: str, sheet_name: str = None, show_formulas: bool = False, show_structure: bool = False):
    wb = load_workbook(path, data_only=False)
    
    result = {
        "file": os.path.basename(path),
        "sheets": wb.sheetnames,
        "analysis": {}
    }
    
    sheets_to_analyze = [sheet_name] if sheet_name else wb.sheetnames
    
    for name in sheets_to_analyze[:3]:  # Limit to 3 sheets
        if name not in wb.sheetnames:
            continue
        ws = wb[name]
        sheet_info = {
            "dimensions": f"{ws.dimensions}",
            "rows": ws.max_row,
            "cols": ws.max_column,
            "merged_cells": [str(m) for m in ws.merged_cells.ranges][:10],
        }
        
        if show_structure:
            sheet_info["headers"] = []
            for col in range(1, min(ws.max_column + 1, 20)):
                cell = ws.cell(row=1, column=col)
                if cell.value:
                    sheet_info["headers"].append(f"{cell.coordinate}: {cell.value}")
        
        if show_formulas:
            formulas = []
            for row in ws.iter_rows(max_row=min(ws.max_row, 50)):
                for cell in row:
                    if isinstance(cell.value, str) and cell.value.startswith('='):
                        formulas.append(f"{cell.coordinate}: {cell.value}")
            if formulas:
                sheet_info["formulas_count"] = len(formulas)
                sheet_info["formulas"] = formulas[:20]
        
        result["analysis"][name] = sheet_info
    
    return result

if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    if len(sys.argv) < 2:
        print("Usage: python3 xl_analyze.py <file.xlsx> [--sheet name] [--formulas] [--structure]")
        sys.exit(1)
    
    path = sys.argv[1]
    show_formulas = "--formulas" in sys.argv
    show_structure = "--structure" in sys.argv or len(sys.argv) <= 2
    sheet_name = None
    
    if "--sheet" in sys.argv:
        idx = sys.argv.index("--sheet")
        if idx + 1 < len(sys.argv):
            sheet_name = sys.argv[idx + 1]
    
    result = analyze_workbook(path, sheet_name, show_formulas, show_structure)
    print(json.dumps(result, ensure_ascii=False, indent=2))
