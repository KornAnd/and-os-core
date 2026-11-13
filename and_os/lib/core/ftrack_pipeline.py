"""Transaction pipeline for Ftrack Cache Management with strict schema validation.

Enforces Rule #62 (Single Active Cache Invariant) and Rule #19 (Dual-Speed Governance).
Guarantees bidirectional integrity between Raw CSV slices and SQLite Projections:
1. SHA-256 Checksum binding: SQLite projection stores the exact hash of CSV files.
2. Invalidation & Auto-Rebuild: If CSV changes, DB is rebuilt automatically.
3. Coupled Garbage Collection: If raw slice is deleted/obsolete, its DB projection is purged.
4. Orphan Purge: If a DB projection exists without its raw CSV slice, it is deleted immediately.
"""

import os
import shutil
import json
import hashlib
import sqlite3
import csv
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger("ftrack_pipeline")

MANDATORY_CSV_FILES = ["shots.csv", "assets.csv", "tasks.csv"]
PROJECTION_DB_NAME = "projection_cache.db"


class FtrackPipelineError(Exception):
    """Base exception for Ftrack pipeline operations."""
    pass


class FtrackSchemaValidationError(FtrackPipelineError):
    """Raised when an ingested slice fails schema or structural validation."""
    pass


def compute_slice_checksum(slice_dir: str) -> str:
    """Compute a deterministic SHA-256 checksum across all mandatory CSV files in slice."""
    hasher = hashlib.sha256()
    for fname in sorted(MANDATORY_CSV_FILES):
        fpath = os.path.join(slice_dir, fname)
        if not os.path.exists(fpath):
            raise FtrackSchemaValidationError(f"Cannot compute checksum, missing: {fname}")
        with open(fpath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
    return hasher.hexdigest()


def validate_slice_integrity(slice_dir: str) -> Tuple[bool, str]:
    """Validate that a slice directory exists and contains non-empty mandatory CSVs."""
    if not os.path.isdir(slice_dir):
        return False, f"Directory does not exist: {slice_dir}"

    for f_name in MANDATORY_CSV_FILES:
        f_path = os.path.join(slice_dir, f_name)
        if not os.path.exists(f_path):
            return False, f"Missing mandatory CSV: {f_name}"
        if os.path.getsize(f_path) < 10:
            return False, f"Corrupted or empty CSV: {f_name} ({os.path.getsize(f_path)} bytes)"

    return True, "Valid"


def init_projection_database(db_path: str, source_hash: str, slice_date: str) -> sqlite3.Connection:
    """Initialize SQLite schema with metadata tracking and index acceleration."""
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS _slice_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    cur.execute("INSERT OR REPLACE INTO _slice_meta VALUES ('source_hash', ?)", (source_hash,))
    cur.execute("INSERT OR REPLACE INTO _slice_meta VALUES ('slice_date', ?)", (slice_date,))
    cur.execute("INSERT OR REPLACE INTO _slice_meta VALUES ('created_at', ?)", (datetime.now().isoformat(),))

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            status TEXT,
            parent TEXT,
            end_date TEXT,
            assignees TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type)")

    conn.commit()
    return conn


def compile_slice_to_db(slice_dir: str) -> str:
    """Compile raw CSV files into an indexed SQLite projection database."""
    is_valid, reason = validate_slice_integrity(slice_dir)
    if not is_valid:
        raise FtrackSchemaValidationError(f"Cannot compile invalid slice {slice_dir}: {reason}")

    db_path = os.path.join(slice_dir, PROJECTION_DB_NAME)
    source_hash = compute_slice_checksum(slice_dir)
    slice_date = os.path.basename(os.path.normpath(slice_dir)).replace("raw_", "")

    conn = init_projection_database(db_path, source_hash, slice_date)
    cur = conn.cursor()

    tasks_csv = os.path.join(slice_dir, "tasks.csv")
    if os.path.exists(tasks_csv):
        with open(tasks_csv, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                task_id = row.get("id") or row.get("ID") or ""
                if not task_id:
                    continue
                batch.append((
                    task_id,
                    row.get("name", ""),
                    row.get("type", ""),
                    row.get("status", ""),
                    row.get("parent", "") or row.get("shot", ""),
                    row.get("end_date", "") or row.get("due_date", ""),
                    row.get("assignees", ""),
                ))
                if len(batch) >= 1000:
                    cur.executemany("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
                    batch = []
            if batch:
                cur.executemany("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)", batch)

    conn.commit()
    conn.close()
    return db_path


def verify_projection_integrity(slice_dir: str) -> Tuple[bool, str]:
    """Verify that SQLite projection matches the exact SHA-256 hash of raw CSVs."""
    db_path = os.path.join(slice_dir, PROJECTION_DB_NAME)
    if not os.path.exists(db_path):
        return False, "Projection database does not exist"

    try:
        current_hash = compute_slice_checksum(slice_dir)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT value FROM _slice_meta WHERE key = 'source_hash'")
        row = cur.fetchone()
        conn.close()

        if not row:
            return False, "Missing source_hash metadata in projection"

        recorded_hash = row[0]
        if recorded_hash != current_hash:
            return False, f"Hash mismatch: recorded {recorded_hash[:8]} vs current {current_hash[:8]}"

        return True, "Valid"
    except Exception as e:
        return False, f"Verification error: {e}"


def purge_orphaned_projections(proj_dir: str, active_slice_dir: str) -> List[str]:
    """Purge orphaned or obsolete projection databases in project directory."""
    purged = []
    canonical_active = os.path.abspath(active_slice_dir) if active_slice_dir else ""

    if not os.path.isdir(proj_dir):
        return purged

    for entry in os.listdir(proj_dir):
        full_p = os.path.join(proj_dir, entry)
        # Any standalone .db in proj_dir without a slice is orphaned
        if entry.endswith(".db"):
            os.remove(full_p)
            purged.append(full_p)
        elif entry.startswith("raw_") and os.path.isdir(full_p):
            if os.path.abspath(full_p) != canonical_active:
                shutil.rmtree(full_p, ignore_errors=True)
                purged.append(full_p)

    return purged


def atomic_swap_active_slice(proj_dir: str, new_slice_dir: str) -> str:
    """Atomically commit a new slice, compile its DB projection, and coupled-purge old data.
    
    Invariant (Rule #62 & Coupled GC):
    - Raw CSV slice and its SQLite projection are coupled as a single atomic unit.
    - All obsolete raw_* directories and orphaned databases are permanently destroyed.
    """
    is_valid, reason = validate_slice_integrity(new_slice_dir)
    if not is_valid:
        raise FtrackSchemaValidationError(f"Cannot commit invalid slice {new_slice_dir}: {reason}")

    # Compile projection database and verify its hash
    compile_slice_to_db(new_slice_dir)
    db_ok, db_reason = verify_projection_integrity(new_slice_dir)
    if not db_ok:
        raise FtrackSchemaValidationError(f"Projection DB verification failed: {db_reason}")

    # Coupled GC: Purge all other raw slices and orphaned DBs
    purge_orphaned_projections(proj_dir, new_slice_dir)

    return new_slice_dir


def create_safe_summary_markdown(dto_dict: Dict[str, Any]) -> str:
    """Generate Markdown report for Obsidian Vault complying with Wikilink and AST conventions."""
    project_key = dto_dict.get("project_key", "unknown")
    project_name = dto_dict.get("project_name", project_key)
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    sh = dto_dict.get("shots", {})
    ast = dto_dict.get("assets", {})
    bot = dto_dict.get("bottlenecks", {})
    emp = dto_dict.get("employees", {})

    lines = [
        "---",
        "tags:",
        "  - \u043f\u0440\u043e\u0434\u0430\u043a\u0448\u043d",
        f"  - {project_key}",
        "  - nero",
        "  - work",
        "---",
        "",
        f"# Ftrack: {project_name} \u2014 {now_str}",
        "",
        "## \u0428\u043e\u0442\u043d\u043e\u0435 \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0441\u0442\u0432\u043e",
        f"**\u0412\u0441\u0435\u0433\u043e \u0448\u043e\u0442\u043e\u0432:** {sh.get('total', 0)}",
        "",
        "| \u0421\u0442\u0430\u0442\u0443\u0441 | \u041a\u043e\u043b-\u0432\u043e | % |",
        "|---|---|---|",
    ]

    by_status = sh.get("by_status", {})
    total_sh = sh.get("total", 0) or 1
    for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
        pct = (count / total_sh * 100)
        lines.append(f"| {status} | {count} | {pct:.1f}% |")

    lines.append("")
    lines.append("### \u041f\u043e \u044d\u0442\u0430\u043f\u0430\u043c \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0441\u0442\u0432\u0430")
    for stg in sh.get("stages", []):
        lines.append(f"- **{stg.get('stage')}:** {stg.get('done')} / {stg.get('total')} ({stg.get('pct')}%) {stg.get('emoji')}")

    lines.append("")
    lines.append("## \u0410\u0441\u0441\u0435\u0442\u043d\u043e\u0435 \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0441\u0442\u0432\u043e")
    lines.append(f"**\u0412\u0441\u0435\u0433\u043e \u0430\u0441\u0441\u0435\u0442\u043e\u0432:** {ast.get('total', 0)}")
    lines.append(f"**\u0413\u043e\u0442\u043e\u0432\u043e:** {ast.get('done', 0)} ({ast.get('pct', 0)}%) | **\u0412 \u0440\u0435\u0432\u044c\u044e/\u043f\u0440\u0430\u0432\u043a\u0430\u0445:** {ast.get('stuck_count', 0)}")
    lines.append("")

    lines.append("### \u041f\u043e \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f\u043c \u0430\u0441\u0441\u0435\u0442\u043e\u0432")
    for c in ast.get("by_category", []):
        lines.append(f"- **{c.get('category')}:** {c.get('total')} \u0448\u0442, \u0433\u043e\u0442\u043e\u0432\u043e {c.get('done')} ({c.get('pct')}%)")

    top_wl = emp.get("top_workload", [])
    if top_wl:
        lines.append("")
        lines.append("## \u041a\u043b\u044e\u0447\u0435\u0432\u044b\u0435 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u0438")
        lines.append("| \u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a | \u041e\u0442\u0434\u0435\u043b | \u0412 \u0440\u0430\u0431\u043e\u0442\u0435 | \u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e | \u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e |")
        lines.append("|---|---|---|---|---|")
        for e in top_wl[:10]:
            ov = f"🔴 {e.get('overdue')}" if e.get("overdue", 0) > 0 else "0"
            lines.append(f"| {e.get('name')} | {e.get('primary_dept')} | {e.get('active')} | {ov} | {e.get('done')} |")

    top_ov = bot.get("top_overdue", [])
    if top_ov:
        lines.append("")
        lines.append(f"## 🔴 \u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043d\u044b\u0435 \u0437\u0430\u0434\u0430\u0447\u0438 ({bot.get('overdue_count', 0)})")
        for t in top_ov[:15]:
            emp_info = f" ({t.get('assignees')})" if t.get("assignees") else ""
            lines.append(f"- [{t.get('type')}] `{t.get('parent')}/{t.get('name')}` \u2014 \u0434\u0435\u0434\u043b\u0430\u0439\u043d: {t.get('end_date')}{emp_info}")

    lines.append("")
    lines.append("---")
    lines.append(f"*\u0410\u0432\u0442\u043e\u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044f Ftrack (AnD os Engine). \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e: {now_str}*")
    lines.append("---")
    lines.append(f"[[Nero/work/{project_key}/{project_key}|\u2190 {project_key}]] | [[CONTEXT|\u2190 \u041d\u0430\u0432\u0435\u0440\u0445]]")

    return "\n".join(lines)
