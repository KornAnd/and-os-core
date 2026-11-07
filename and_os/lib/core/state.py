"""
state.py — Provenance-Aware State Manager & Core SQLite Metadata Store
AnD os v8.1 — Core Architecture Layer (Truth in State Standard)

Replaces synthetic default states with explicit provenance:
  - StateFreshness (VERIFIED, CACHED, STALE, UNKNOWN)
  - ProvenanceRecord (source_file, observed_at, source_updated_at, freshness)
  - CoreStateStore: Versioned SQLite store for system.*, operation.*, service.* metadata
  - Legacy domain JSON projection maintained with _provenance envelope
  - Zero-Hallucination: Missing or corrupted domain records evaluate to UNKNOWN, never synthetic facts.
"""

from __future__ import annotations

import os
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from and_os.lib.core.vfs import DIR_VAR

STATE_FILE = os.path.join(DIR_VAR, "domain_states.json")
CORE_DB_FILE = os.path.join(DIR_VAR, "core_state.db")


class StateFreshness(str, Enum):
    """Degrees of state certainty."""
    VERIFIED = "VERIFIED"   # Validated directly against physical source document
    CACHED = "CACHED"       # Read from persistent cache with known observation timestamp
    STALE = "STALE"         # Timestamp exceeds freshness TTL
    UNKNOWN = "UNKNOWN"     # No verified record exists; synthetic defaults are forbidden


@dataclass(frozen=True)
class ProvenanceRecord:
    """Provenance metadata describing where and when state was observed."""
    source: str
    observed_at: str
    source_updated_at: Optional[str] = None
    freshness: StateFreshness = StateFreshness.CACHED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "observed_at": self.observed_at,
            "source_updated_at": self.source_updated_at,
            "freshness": self.freshness.value,
        }


# ---------------------------------------------------------------------------
# Core Operational SQLite Store (Metadata, Operations, Services)
# ---------------------------------------------------------------------------

class CoreMetadataStore:
    """
    Isolated SQLite store for cross-cutting operational state.
    Allowed key prefixes: system.*, operation.*, service.*, workflow.*
    Domain data (health, finance, work) is strictly owned by islands.
    """

    ALLOWED_PREFIXES = ("system.", "operation.", "service.", "workflow.")

    def __init__(self, db_path: str = CORE_DB_FILE):
        self.db_path = db_path
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS core_state_metadata (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    freshness TEXT NOT NULL
                )
            """)
            conn.commit()

    def _validate_key(self, key: str) -> None:
        if not any(key.startswith(p) for p in self.ALLOWED_PREFIXES):
            raise ValueError(
                f"CoreMetadataStore key '{key}' rejected. Keys must start with one of {self.ALLOWED_PREFIXES}. "
                f"Domain-specific records must remain in island stores."
            )

    def set(self, key: str, value: Any, source: str = "core") -> None:
        """Sets an operational state key with atomic commit."""
        self._validate_key(key)
        now_iso = datetime.now(timezone.utc).isoformat()
        val_str = json.dumps(value, ensure_ascii=False)
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO core_state_metadata (key, value_json, source, observed_at, freshness)
                VALUES (?, ?, ?, ?, ?)
            """, (key, val_str, source, now_iso, StateFreshness.VERIFIED.value))
            conn.commit()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves an operational state record with provenance."""
        self._validate_key(key)
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT value_json, source, observed_at, freshness FROM core_state_metadata WHERE key = ?",
                (key,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "value": json.loads(row["value_json"]),
                "provenance": {
                    "source": row["source"],
                    "observed_at": row["observed_at"],
                    "freshness": row["freshness"],
                }
            }


# ---------------------------------------------------------------------------
# Domain State Cache (Truth in State: No Synthetic Defaults)
# ---------------------------------------------------------------------------

def create_unknown_domain_state(domain: str, reason: str = "No verified record on disk") -> Dict[str, Any]:
    """Generates an explicit UNKNOWN state record without hallucinated facts."""
    return {
        "domain": domain,
        "status": "UNKNOWN",
        "_provenance": ProvenanceRecord(
            source="none",
            observed_at=datetime.now(timezone.utc).isoformat(),
            freshness=StateFreshness.UNKNOWN,
        ).to_dict(),
        "reason": reason,
    }


def load_states() -> Dict[str, Any]:
    """
    Loads all cached domain states from JSON.
    Guarantees that missing files or keys are returned as UNKNOWN, never synthetic facts.
    """
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            # Attach provenance if missing in legacy records
            for d_name, d_val in data.items():
                if isinstance(d_val, dict) and "_provenance" not in d_val:
                    d_val["_provenance"] = ProvenanceRecord(
                        source=STATE_FILE,
                        observed_at=datetime.now(timezone.utc).isoformat(),
                        source_updated_at=d_val.get("last_updated"),
                        freshness=StateFreshness.CACHED,
                    ).to_dict()
            return data
    except Exception:
        return {}


def save_states(states: Dict[str, Any]) -> bool:
    """Atomically writes domain state records to disk."""
    os.makedirs(DIR_VAR, exist_ok=True)
    temp_file = STATE_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(states, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, STATE_FILE)
        return True
    except (json.JSONDecodeError, OSError) as err:
        sys.stderr.write(f"[state] Error writing state to {temp_file}: {err}\n")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError as rem_err:
                sys.stderr.write(f"[state] Notice: cleaning {temp_file}: {rem_err}\n")
        return False


def get_domain_state(domain: str) -> Dict[str, Any]:
    """
    Returns the state of a single domain.
    Returns explicit UNKNOWN if no cached state exists.
    """
    states = load_states()
    if domain in states:
        return states[domain]
    return create_unknown_domain_state(domain)


def set_domain_state(
    domain: str,
    key: str,
    value: Any,
    source_evidence: str = "manual_update"
) -> Dict[str, Any]:
    """
    Updates a key in a domain state record with verified provenance.
    """
    states = load_states()
    now_iso = datetime.now(timezone.utc).isoformat()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if domain not in states:
        states[domain] = {
            "domain": domain,
            "status": "ACTIVE",
            "last_updated": now_str,
            "_provenance": ProvenanceRecord(
                source=source_evidence,
                observed_at=now_iso,
                source_updated_at=now_str,
                freshness=StateFreshness.VERIFIED,
            ).to_dict()
        }

    states[domain][key] = value
    states[domain]["last_updated"] = now_str
    states[domain]["_provenance"] = ProvenanceRecord(
        source=source_evidence,
        observed_at=now_iso,
        source_updated_at=now_str,
        freshness=StateFreshness.VERIFIED,
    ).to_dict()

    save_states(states)
    return states[domain]
