#!/usr/bin/env python3
"""
clean_links.py — safe normalization of links to missing images.
Proxy-shim to the monolithic and_os.lib.vault library.
"""
import os
import sys

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)

from and_os.lib.vault import clean_broken_image_links

def main() -> None:
    fixed = clean_broken_image_links(VAULT_ROOT)
    print(f"Done. Files processed: {fixed}")

if __name__ == "__main__":
    main()
