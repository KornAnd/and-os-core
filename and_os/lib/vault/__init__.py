#!/usr/bin/env python3
"""
and_os/lib/vault/__init__.py — Monolithic management package for Obsidian Vault.
"""

from .hygiene import validate_name, sanitize_name
from .graph import cascade_rename_links, clean_broken_image_links
from .context import sync_single_context, sync_all_contexts
from .engine import VaultEngine

__all__ = [
    "validate_name",
    "sanitize_name",
    "cascade_rename_links",
    "clean_broken_image_links",
    "sync_single_context",
    "sync_all_contexts",
    "VaultEngine"
]
