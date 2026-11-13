#!/usr/bin/env python3
"""
and_os/lib/vault/engine.py — Unified facade for Obsidian Vault management.
Part of the monolithic and_os.lib.vault package.

Exposes atomic, high-level operations:
  - move_note: Safe relocation/renaming with WebDAV hygiene validation, filesystem move,
    and atomic cascade refactoring of all incoming wikilinks.
  - audit_hygiene: Fast and deep hygiene audits (filenames, 0-byte notes, WebDAV limits).
"""

import os
from typing import Dict, Any, Tuple, List, Optional
from .hygiene import validate_name, sanitize_name
from .graph import cascade_rename_links, clean_broken_image_links, scan_markdown_files
from .context import sync_single_context, sync_all_contexts

class VaultEngine:
    def __init__(self, vault_root: Optional[str] = None):
        if vault_root:
            self.vault_root = os.path.abspath(vault_root)
        else:
            self.vault_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

    def move_note(self, src_rel_path: str, dst_rel_path: str, auto_sanitize: bool = True) -> Dict[str, Any]:
        """
        Atomically relocates or renames a markdown note:
        1. Validates destination name against WebDAV constraints.
        2. Relocates file on disk.
        3. Cascades incoming wikilinks across all vault notes.
        4. Synchronizes source and destination CONTEXT.md maps.
        """
        src_full = os.path.join(self.vault_root, src_rel_path)
        if not os.path.exists(src_full):
            return {"success": False, "error": f"Source note not found: {src_rel_path}"}

        # 1. Validate destination name
        target_path = dst_rel_path
        is_valid, errors = validate_name(os.path.basename(target_path))
        if not is_valid:
            if auto_sanitize:
                target_path = sanitize_name(target_path)
            else:
                return {"success": False, "error": f"Invalid WebDAV filename: {errors}"}

        dst_full = os.path.join(self.vault_root, target_path)
        os.makedirs(os.path.dirname(dst_full), exist_ok=True)

        if os.path.exists(dst_full) and os.path.abspath(src_full) != os.path.abspath(dst_full):
            return {"success": False, "error": f"Destination file already exists: {target_path}"}

        # 2. Relocate file on disk
        try:
            os.rename(src_full, dst_full)
        except OSError as e:
            return {"success": False, "error": f"Filesystem rename error: {e}"}

        # 3. Cascade refactor wikilinks
        updated_links_count = cascade_rename_links(self.vault_root, src_rel_path, target_path)

        # 4. Synchronize source and destination contexts
        src_dir = os.path.dirname(src_full)
        dst_dir = os.path.dirname(dst_full)
        sync_single_context(src_dir, fix=True)
        if src_dir != dst_dir:
            sync_single_context(dst_dir, fix=True)

        return {
            "success": True,
            "src": src_rel_path,
            "dst": target_path,
            "updated_link_files": updated_links_count,
            "message": f"Note successfully relocated to '{target_path}', updated {updated_links_count} files with wikilinks."
        }

    def audit_hygiene(self, deep: bool = False) -> Dict[str, Any]:
        """
        Audits vault naming standards (WebDAV limits, trailing dots/spaces, empty files).
        """
        violations = []
        zero_byte_files = []

        for root, dirs, files in os.walk(self.vault_root):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'and_os', 'Trash', '.trash'}]
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), self.vault_root)
                ok, errs = validate_name(f)
                if not ok:
                    violations.append({"file": rel, "errors": errs})
                full_p = os.path.join(root, f)
                if f.endswith('.md') and os.path.getsize(full_p) == 0:
                    zero_byte_files.append(rel)

        return {
            "clean": len(violations) == 0 and len(zero_byte_files) == 0,
            "violations_count": len(violations),
            "violations": violations,
            "zero_byte_count": len(zero_byte_files),
            "zero_byte_files": zero_byte_files
        }
