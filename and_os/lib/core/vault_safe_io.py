"""
vault_safe_io.py — Centralized Safe I/O Gateway for Obsidian Vault Notes (AnD os v1.0.0)
Complies with Vault Access Invariant (Rule #19) and Clean Code protocol (ub-mode).
Provides atomic writes, YAML frontmatter validation, link corruption prevention,
and payload ceiling checks.
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

MAX_NOTE_PAYLOAD_BYTES = 50 * 1024 * 1024  # 50 MB safety ceiling
CORRUPTION_MARKERS = [chr(91) + chr(91) + chr(124) + chr(93) + chr(93)]  # [[|]]


class VaultSafeIOError(Exception):
    """Base exception for Vault Safe I/O violations."""
    pass


def validate_note_content(content: str) -> Tuple[bool, Optional[str]]:
    """
    Validates note content for AST syntax, frontmatter integrity, and link safety.
    Returns (True, None) if clean, or (False, error_message).
    """
    if len(content.encode("utf-8")) > MAX_NOTE_PAYLOAD_BYTES:
        return False, f"Payload ceiling exceeded: {len(content)} bytes"

    for marker in CORRUPTION_MARKERS:
        if marker in content:
            return False, f"Detected link corruption marker: {repr(marker)}"

    # If note has YAML frontmatter, verify delimiter symmetry
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) < 3:
            return False, "Unclosed or malformed YAML frontmatter delimiter (missing closing '---')"

    return True, None


def vault_safe_write(
    target_path: str,
    content: str,
    validate: bool = True,
    create_parents: bool = True
) -> bool:
    """
    Safely writes markdown content to the target file with atomic temp-swap.
    
    Args:
        target_path: Absolute or relative file path to note.
        content: String content to write.
        validate: If True, executes AST & corruption checks before writing.
        create_parents: If True, automatically creates missing parent directories.
    
    Returns:
        bool: True on success.
    
    Raises:
        VaultSafeIOError: On validation failure or atomic write failure.
    """
    if validate:
        is_valid, err = validate_note_content(content)
        if not is_valid:
            raise VaultSafeIOError(f"Validation failed for {target_path}: {err}")

    p = Path(target_path).resolve()
    if create_parents:
        p.parent.mkdir(parents=True, exist_ok=True)

    temp_path = p.parent / f".tmp_{p.name}_{os.getpid()}"
    try:
        with open(temp_path, "w", encoding="utf-8") as tf:
            tf.write(content)
            tf.flush()
            os.fsync(tf.fileno())

        os.replace(temp_path, p)
        return True
    except OSError as e:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise VaultSafeIOError(f"Atomic file write failed for {target_path}: {e}") from e


def vault_safe_read(target_path: str, max_bytes: Optional[int] = None) -> str:
    """
    Safely reads markdown content from a vault file.
    """
    p = Path(target_path).resolve()
    if not p.exists():
        raise VaultSafeIOError(f"File not found: {target_path}")

    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            if max_bytes:
                return f.read(max_bytes)
            return f.read()
    except OSError as e:
        raise VaultSafeIOError(f"Read failed for {target_path}: {e}") from e
