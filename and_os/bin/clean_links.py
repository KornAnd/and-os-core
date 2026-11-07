#!/usr/bin/env python3
"""
clean_links.py — безопасная нормализация ссылок на несуществующие картинки.
Proxy-shim к монолитной библиотеке and_os.lib.vault.
"""
import os
import sys

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)

from and_os.lib.vault import clean_broken_image_links

def main() -> None:
    fixed = clean_broken_image_links(VAULT_ROOT)
    print(f"Готово. Обработано файлов: {fixed}")

if __name__ == "__main__":
    main()
