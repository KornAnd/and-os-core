#!/usr/bin/env python3
"""OCR-анализатор изображений через tesseract.

Использует tesseract OCR с языковыми пакетами rus+eng.
Установка: brew install tesseract tesseract-lang

Запуск: python3 image_ocr.py <путь к изображению или папке>
"""

import subprocess
import sys
import os

def ocr_file(path: str) -> str:
    result = subprocess.run(
        ["tesseract", path, "-", "-l", "rus+eng"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 image_ocr.py <path>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if os.path.isfile(path):
        print(f"📷 {os.path.basename(path)}")
        print(ocr_file(path))
    elif os.path.isdir(path):
        for fn in sorted(os.listdir(path)):
            if fn.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                fp = os.path.join(path, fn)
                print(f"\n=== {fn} ===")
                print(ocr_file(fp))
    else:
        print(f"❌ {path} not found")
        sys.exit(1)
