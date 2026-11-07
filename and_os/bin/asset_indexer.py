#!/usr/bin/env python3
"""
Asset Indexer for ANDREY OS (v1.0.0)
Scans non-MD assets (images, archives, audio, binaries, code exports),
maps them to parent context files, Obsidian wiki-links, file size/hashes,
and builds and_os/var/asset_manifest.json + SQLite integration.
"""

import os
import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime

try:
    from and_os.lib.core.root_config import RootConfig
    VAULT_ROOT = Path(RootConfig.load().vault_root)
except Exception:
    VAULT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_JSON = VAULT_ROOT / "Nero" / "ai" / "scratch" / "asset_manifest.json"
DB_PATH = VAULT_ROOT / "and_os" / "var" / "task_vault.db"

ASSET_EXTENSIONS = {
    # Media
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".mp3", ".wav", ".m4a", ".mp4", ".mov",
    # Archives & Binaries
    ".zip", ".tar", ".gz", ".7z", ".rar", ".pdf",
    # Code & Data Exports
    ".ajson", ".py", ".html", ".tsx", ".jsx", ".json", ".csv", ".db"
}

EXCLUDE_DIRS = {".git", ".obsidian", ".pdf_archive", "node_modules", "__pycache__", ".venv"}

def _extract_md_targets(md_path: Path, pattern: re.Pattern) -> List[str]:
    """Reads markdown file and extracts all wikilink target basenames."""
    targets: List[str] = []
    try:
        content = md_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as err:
        sys.stderr.write(f"[AssetIndexer] Warning reading {md_path}: {err}\n")
        return targets

    for match in pattern.findall(content):
        target = match[0] or match[1]
        if target:
            targets.append(Path(target).name)
    return targets

def scan_md_backlinks() -> Dict[str, List[str]]:
    """Scans all .md files to build a reverse link map: asset_filename -> list of md_paths."""
    link_map: Dict[str, List[str]] = {}
    pattern = re.compile(r'\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]|!\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]')

    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if not f.endswith(".md"):
                continue
            md_path = Path(root) / f
            rel_md = str(md_path.relative_to(VAULT_ROOT))
            targets = _extract_md_targets(md_path, pattern)
            for target_name in targets:
                link_map.setdefault(target_name, [])
                if rel_md not in link_map[target_name]:
                    link_map[target_name].append(rel_md)
    return link_map

def run_asset_indexing():
    """Main indexing logic."""
    print("🔍 Сканирование ассетов и сбор контекстных связей...")
    backlinks = scan_md_backlinks()

    assets = []
    stats_by_ext = {}

    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in ASSET_EXTENSIONS and not f.endswith(".md"):
                file_path = Path(root) / f
                rel_path = str(file_path.relative_to(VAULT_ROOT))
                size_bytes = file_path.stat().st_size
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()

                # Find nearest CONTEXT.md
                parent_dir = file_path.parent
                nearest_context = None
                curr = parent_dir
                while curr >= VAULT_ROOT:
                    ctx_file = curr / "CONTEXT.md"
                    if ctx_file.exists():
                        nearest_context = str(ctx_file.relative_to(VAULT_ROOT))
                        break
                    if curr == VAULT_ROOT:
                        break
                    curr = curr.parent

                asset_entry = {
                    "filename": f,
                    "path": rel_path,
                    "extension": ext,
                    "size_kb": round(size_bytes / 1024, 2),
                    "mtime": mtime,
                    "nearest_context": nearest_context,
                    "linked_in_md": backlinks.get(f, []),
                    "is_orphan": len(backlinks.get(f, [])) == 0
                }

                assets.append(asset_entry)
                stats_by_ext[ext] = stats_by_ext.get(ext, 0) + 1

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "total_assets": len(assets),
        "total_orphans": sum(1 for a in assets if a["is_orphan"]),
        "extension_counts": stats_by_ext,
        "assets": assets
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump(manifest, out, ensure_ascii=False, indent=2)

    # Sync into SQLite
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_index (
                path TEXT PRIMARY KEY,
                filename TEXT,
                extension TEXT,
                size_kb REAL,
                nearest_context TEXT,
                is_orphan INTEGER,
                linked_md_count INTEGER
            )
        """)
        cursor.execute("DELETE FROM asset_index")
        for a in assets:
            cursor.execute("""
                INSERT INTO asset_index (path, filename, extension, size_kb, nearest_context, is_orphan, linked_md_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (a["path"], a["filename"], a["extension"], a["size_kb"], a["nearest_context"], 1 if a["is_orphan"] else 0, len(a["linked_in_md"])))
        conn.commit()
        conn.close()

    print(f"✅ Успешно проиндексировано {len(assets)} ассетов!")
    print(f"📊 Найдено 'сиротских' ассетов без ссылок: {manifest['total_orphans']}")
    print(f"📁 Файл манифеста сохранен: and_os/var/asset_manifest.json")
    return manifest

if __name__ == "__main__":
    run_asset_indexing()
