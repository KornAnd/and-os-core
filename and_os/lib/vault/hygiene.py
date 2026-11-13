#!/usr/bin/env python3
"""
and_os/lib/vault/hygiene.py — File naming standards and WebDAV / FS compatibility validator.
Part of the monolithic and_os.lib.vault package.

Core Invariants:
  - Filename byte length must not exceed MAX_FILENAME_BYTES (default 200) in UTF-8.
  - Filename must never terminate with a period (.) or whitespace ( ) before extension.
  - Filename must not contain cross-platform forbidden characters: < > : " | ? *
"""

import os
from typing import Tuple, List

FORBIDDEN_CHARS = set(['<', '>', ':', '"', '|', '?', '*'])
MAX_FILENAME_BYTES = 200

def validate_name(filename_or_path: str) -> Tuple[bool, List[str]]:
    """
    Validates a filename against WebDAV and cross-platform filesystem constraints.
    Returns (is_valid, list_of_errors).
    """
    basename = os.path.basename(filename_or_path)
    name_no_ext, ext = os.path.splitext(basename)
    errors = []

    # 1. Check trailing dots before extension
    if name_no_ext.endswith('.'):
        errors.append(f"Trailing dot before extension is forbidden by WebDAV: '{basename}'")

    # 2. Check trailing spaces before extension
    if name_no_ext.endswith(' '):
        errors.append(f"Trailing whitespace before extension is forbidden by WebDAV: '{basename}'")

    # 3. Check forbidden characters
    found_forbidden = [c for c in basename if c in FORBIDDEN_CHARS]
    if found_forbidden:
        errors.append(f"Illegal characters {found_forbidden} found in filename: '{basename}'")

    # 4. Check byte length in UTF-8
    byte_len = len(basename.encode('utf-8'))
    if byte_len > MAX_FILENAME_BYTES:
        errors.append(f"Filename byte length exceeds threshold ({byte_len} > {MAX_FILENAME_BYTES} bytes UTF-8): '{basename}'")

    return (len(errors) == 0, errors)

def sanitize_name(filename_or_path: str) -> str:
    """
    Sanitizes a filename into a strictly compliant representation:
    replaces forbidden characters, strips trailing periods and spaces.
    """
    dirname = os.path.dirname(filename_or_path)
    basename = os.path.basename(filename_or_path)
    name_no_ext, ext = os.path.splitext(basename)

    # Replace forbidden characters with underscore
    for c in FORBIDDEN_CHARS:
        name_no_ext = name_no_ext.replace(c, '_')

    # Trim trailing periods and spaces
    name_no_ext = name_no_ext.rstrip('.').rstrip(' ').strip()
    if not name_no_ext:
        name_no_ext = "unnamed_note"

    clean_basename = f"{name_no_ext}{ext}"
    if dirname:
        return os.path.join(dirname, clean_basename)
    return clean_basename
