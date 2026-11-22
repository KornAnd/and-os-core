"""
link_scan.py — Deterministic vault-wide wikilink integrity scanner.
AnD os v1.2.0 (R-2, 20.11: closes the dead-link gate-coverage gap found
by the Agent Journey Efficiency Audit — the Grid reported 10/10 while
wikilinks in active docs pointed at moved/removed targets).

Obsidian resolution semantics (in order):
  1. Full path from the vault root (with or without .md) — md index,
     then disk existence (covers non-md assets and notes in hidden dirs).
  2. Path relative to the linking file's directory (same two stages).
  3. Basename match anywhere in the vault ("shortest path"), compared
     case-insensitively (macOS default filesystem). Works for ANY file
     type (Obsidian indexes all attachments), plus the .md stem.

Classification of unresolved links (only the first class blocks):
  - NOTE links (no extension) -> broken_live: BLOCK the audit.
  - ASSET links (file extension: images, pdf, docx, json, base, canvas,
    media) -> asset_broken: ADVISORY. Lost attachments cannot be repaired
    by a link gate; the note text remains readable.
  - HISTORICAL sources (closed dated reports, telemetry journals) and
    SNAPSHOT/ENV targets (var/checkpoints/, .venv/) -> historical_broken:
    ADVISORY (point-in-time records, forward-only, Rule #61).

Also non-blocking:
  - Template placeholders and documentation examples.
  - Targets inside dot-directories never resolve (Obsidian hides dot
    folders from the index — verified against real vault behavior).

Relationship to GraphProbe (graph_probe.py) — 22.11 (external audit
P3.1): GraphProbe's "unresolved_wikilinks" (WARNING) is the WIDER
note-graph metric (every link that is not a resolved note-to-note
edge among visible notes, including attachments, placeholders and
point-in-time records; note-only universe: 2188 files on 22.11).
broken_live here is the NARROWER blocking navigation contract
(2288 files scanned on 22.11). The two counts legitimately differ;
the per-class reconciliation lives in graph_probe.py's docstring.
Actionable dead links for users are this scanner's broken_live list
only — a non-zero GraphProbe unresolved count is not, by itself, a
broken-navigation incident.

Fingerprint-cached: the scan result is reused while the vault file
fingerprint (file count + md count + max mtime + schema) is unchanged,
so the Grid probe is a ~1-2 s fingerprint walk after the first full
pass. SCHEMA_VERSION is part of the fingerprint: any semantic change to
this module invalidates every previously stored cache.
"""

import os
import re
import json
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

IGNORE_DIRS = {
    ".git", ".venv", "venv", ".trash", "Trash", ".archive", ".space",
    ".obsidian", ".makemd", ".smart-env", "node_modules", "__pycache__",
}

# Files/dirs whose wikilinks are a point-in-time record, never a live
# contract (forward-only history). Broken links there warn, never fail.
HISTORICAL_PREFIXES = (
    "Nero/reports/",
    "and_os/var/audits/",
    "and_os/etc/CHANGELOG.md",
    "and_os/lib/skills/telemetry.md",
)
HISTORICAL_NAME_PREFIXES = ("telemetry_archive",)

# Template placeholders / documentation examples that look like wikilinks
# but are syntax illustrations, never navigation targets (Rule #55 example
# in rules.md, clipping-finder path pattern, stem-collision note example).
# Note: \u041f\u0443\u0442\u044c/\u041a_\u0424\u0430\u0439\u043b\u0443 is the RU
# "path/to/file" illustration literal (Rule #3: no Cyrillic literals in .py).
PLACEHOLDER_RE = re.compile(
    r"[<>…]|^\.{2,}$|^Doc_\d|^D-xxx$|^filename$|^wiki-?link$|^Database_Name"
    r"|^…$|^\[\]$|^name$|^\u041f\u0443\u0442\u044c/\u041a_\u0424\u0430\u0439\u043b\u0443$"
    r"|^Clippings/Category/File$")

# Targets that are point-in-time records (checkpoint snapshots) or
# environment artifacts (venv package files), never a live navigation
# contract. Broken links to them are reported, never blocking.
TARGET_NONBLOCKING_PREFIXES = ("and_os/var/checkpoints/", "and_os/.venv/")

LINK_RE = re.compile(r"\[\[([^\]\[]+?)\]\]")

# Bump whenever scan semantics change: the fingerprint carries it, so a
# code change can never serve a stale cache written by the old logic.
SCHEMA_VERSION = 4


def is_historical(rel_path: str) -> bool:
    return any(rel_path.startswith(p) for p in HISTORICAL_PREFIXES) or any(
        os.path.basename(rel_path).startswith(p) for p in HISTORICAL_NAME_PREFIXES)


def _is_asset(target: str) -> bool:
    """True for file-attachment targets (basename carries an extension)."""
    base = os.path.basename(target)
    return "." in base and not base.startswith(".")


def _prune_dirs(dirs: List[str]) -> None:
    """Drop ignored dirs and dot-dirs in place (Obsidian hides dot folders
    from its index, so links into/into-them never resolve)."""
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]


def _safe_mtime(path: str) -> float:
    """File mtime, or 0.0 when it cannot be read (deleted mid-walk)."""
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def _read_cache(cache_path: str) -> Optional[Dict[str, Any]]:
    """Returns the cached scan dict, or None when unreadable/corrupt."""
    try:
        with open(cache_path, "r", encoding="utf-8") as cf:
            return json.load(cf)
    except (OSError, ValueError):
        return None


def _write_cache(cache_path: str, result: Dict[str, Any]) -> bool:
    """Atomically persists the cache (tmp + os.replace). Returns False on any
    FS error — the cache is an optimization, never a gate dependency."""
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        tmp = cache_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as cf:
            json.dump(result, cf, ensure_ascii=False)
        os.replace(tmp, cache_path)
        return True
    except OSError:
        return False


def _iter_md_files(vault_root: str):
    for root, dirs, files in os.walk(vault_root):
        _prune_dirs(dirs)
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(root, f)


def _build_indexes(vault_root: str, skip_paths: Optional[set] = None):
    """Returns (md_path_set, basename->paths dict, fingerprint).

    The basename index covers EVERY file type (Obsidian shortest-path
    resolves attachments by name); .md files additionally register their
    stem. The fingerprint spans all files so any file add/delete/change
    invalidates the cache — except the cache file itself (self-reference:
    writing the cache must not change the fingerprint it stores).
    """
    skip_abs = {os.path.abspath(s) for s in (skip_paths or set())}
    all_paths = set()
    basename_index: Dict[str, List[str]] = defaultdict(list)
    md_count = 0
    file_count = 0
    max_mtime = 0.0
    for root, dirs, files in os.walk(vault_root):
        _prune_dirs(dirs)
        for f in files:
            p = os.path.join(root, f)
            if os.path.abspath(p) in skip_abs:
                continue
            rel = os.path.relpath(p, vault_root).replace(os.sep, "/")
            file_count += 1
            max_mtime = max(max_mtime, _safe_mtime(p))
            if f.endswith(".md"):
                md_count += 1
                all_paths.add(rel)
            basename_index[f.casefold()].append(rel)
            if f.endswith(".md"):
                basename_index[f[:-3].casefold()].append(rel)
    fingerprint = {
        "schema": SCHEMA_VERSION,
        "file_count": file_count,
        "md_count": md_count,
        "max_mtime": round(max_mtime, 3),
    }
    return all_paths, basename_index, fingerprint


def _crosses_hidden_dir(rel: str) -> bool:
    """True when the path passes through a dot-directory (Obsidian hides
    dot folders from its index: such links are red even if the file
    exists on disk)."""
    return any(part.startswith(".") and part not in (".", "..")
               for part in rel.split("/"))


def _resolves(target: str, file_dir: str, all_paths: set,
              basename_index: dict, vault_root: str) -> bool:
    # 1-2. Full / relative path candidates: md index first (fast),
    # then disk existence — Obsidian resolves links to any file type
    # (.canvas, .base, .json, images), but never through dot-directories.
    for cand in (target, target + ".md"):
        if cand in all_paths:
            return True
        if not _crosses_hidden_dir(cand) and os.path.exists(os.path.join(vault_root, cand)):
            return True
    for cand in (target, target + ".md"):
        rel = os.path.join(file_dir, cand).replace(os.sep, "/")
        if rel in all_paths:
            return True
        if not _crosses_hidden_dir(rel) and os.path.exists(os.path.join(vault_root, rel)):
            return True
    # 3. Basename "shortest path" — any file type, case-insensitive.
    base_cf = os.path.basename(target).casefold()
    if base_cf in basename_index:
        return True
    if base_cf.endswith(".md") and base_cf[:-3] in basename_index:
        return True
    return False


def scan_vault(vault_root: str, use_cache: bool = True,
               cache_path: Optional[str] = None) -> Dict[str, Any]:
    """Scans every wikilink in the vault.

    Returns:
        {
          "files_scanned": int, "links_scanned": int,
          "broken": [{"file": rel, "link": raw, "target": resolved}, ...],
          "historical_broken": int, "asset_broken": int, "cached": bool,
          "elapsed_sec": float,
          "fingerprint": {"schema", "file_count", "md_count", "max_mtime"}
        }
        "broken" holds BLOCKING findings only (live note links, live docs).
    """
    t0 = time.time()
    if cache_path is None:
        cache_path = os.path.join(vault_root, "and_os", "var", "link_scan_cache.json")

    # Fingerprint walk (cheap: names + mtimes only, no content reads).
    # The cache file (and its .tmp) is excluded — writing it must not
    # change the fingerprint it stores (self-reference).
    skip = {cache_path, cache_path + ".tmp"}
    _, _, fingerprint = _build_indexes(vault_root, skip)
    if use_cache and os.path.exists(cache_path):
        cached = _read_cache(cache_path)
        if cached is not None and cached.get("fingerprint") == fingerprint:
            cached["cached"] = True
            cached["elapsed_sec"] = round(time.time() - t0, 3)
            return cached

    all_paths, basename_index, _ = _build_indexes(vault_root, skip)
    broken: List[Dict[str, str]] = []
    historical_broken = 0
    artifact_broken = 0
    asset_broken = 0
    files_scanned = 0
    links_scanned = 0
    for p in _iter_md_files(vault_root):
        rel = os.path.relpath(p, vault_root).replace(os.sep, "/")
        files_scanned += 1
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue
        fdir = os.path.dirname(rel)
        for raw in set(LINK_RE.findall(text)):
            links_scanned += 1
            target = re.split(r"\||\\", raw)[0].split("#")[0].strip()
            if not target or PLACEHOLDER_RE.search(target):
                continue
            # Trailing slash = folder-note style notation; Obsidian users
            # write [[folder/note/]] meaning the note — normalize.
            target = target.rstrip("/")
            if not target:
                continue
            if _resolves(target, fdir, all_paths, basename_index, vault_root):
                continue
            if is_historical(rel) or target.startswith(TARGET_NONBLOCKING_PREFIXES):
                historical_broken += 1
                if target.startswith(TARGET_NONBLOCKING_PREFIXES):
                    artifact_broken += 1
            elif _is_asset(target):
                asset_broken += 1
            else:
                broken.append({"file": rel, "link": raw, "target": target})

    result = {
        "files_scanned": files_scanned,
        "links_scanned": links_scanned,
        "broken": broken,
        "historical_broken": historical_broken,
        "artifact_broken": artifact_broken,
        "asset_broken": asset_broken,
        "cached": False,
        "elapsed_sec": round(time.time() - t0, 3),
        "fingerprint": fingerprint,
    }
    _write_cache(cache_path, result)
    return result
