"""
test_root_and_state_provenance.py — Unit Tests for C4A (Roots & Provenance State)
AnD os v8.1 — Core Architecture Verification
"""

import os
import tempfile
import unittest

from and_os.lib.core.root_config import (
    resolve_vault_root,
    resolve_pulsar_root,
    is_valid_vault_root,
    RootResolutionError,
    RootConfig,
)
from and_os.lib.core.state import (
    CoreMetadataStore,
    StateFreshness,
    ProvenanceRecord,
    get_domain_state,
    set_domain_state,
    create_unknown_domain_state,
)


class TestRootAndStateProvenance(unittest.TestCase):

    # -----------------------------------------------------------------------
    # 1. Root Config & Discovery Tests
    # -----------------------------------------------------------------------

    def test_vault_root_discovery(self):
        """Vault root must be discovered by marker files."""
        root = resolve_vault_root()
        self.assertTrue(os.path.isdir(root))
        self.assertTrue(is_valid_vault_root(root))

    def test_invalid_explicit_and_root_fails_closed(self):
        """Explicit invalid AND_ROOT must raise RootResolutionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_val = os.environ.get("AND_ROOT")
            try:
                os.environ["AND_ROOT"] = tmpdir
                with self.assertRaises(RootResolutionError):
                    resolve_vault_root()
            finally:
                if old_val is not None:
                    os.environ["AND_ROOT"] = old_val
                else:
                    os.environ.pop("AND_ROOT", None)

    def test_root_config_container(self):
        """RootConfig container loads all paths immutably."""
        cfg = RootConfig.load()
        self.assertTrue(os.path.exists(cfg.vault_root))
        self.assertTrue(os.path.exists(cfg.and_os_root))
        self.assertEqual(cfg.bin_dir, os.path.join(cfg.and_os_root, "bin"))

    # -----------------------------------------------------------------------
    # 2. State Provenance & Zero-Synthetic-Defaults Tests
    # -----------------------------------------------------------------------

    def test_missing_domain_returns_explicit_unknown(self):
        """Missing domain records must NEVER return fake metrics; returns UNKNOWN."""
        rec = get_domain_state("non_existent_domain_xyz")
        self.assertEqual(rec["domain"], "non_existent_domain_xyz")
        self.assertEqual(rec["status"], "UNKNOWN")
        self.assertEqual(rec["_provenance"]["freshness"], StateFreshness.UNKNOWN.value)

    def test_set_and_get_domain_state_with_provenance(self):
        """Setting domain state attaches verified provenance metadata."""
        updated = set_domain_state(
            domain="test_domain",
            key="test_metric",
            value=100,
            source_evidence="unit_test_run"
        )
        self.assertEqual(updated["test_metric"], 100)
        self.assertIn("_provenance", updated)
        self.assertEqual(updated["_provenance"]["source"], "unit_test_run")
        self.assertEqual(updated["_provenance"]["freshness"], StateFreshness.VERIFIED.value)

    # -----------------------------------------------------------------------
    # 3. Core SQLite Metadata Store Tests
    # -----------------------------------------------------------------------

    def test_core_metadata_store_allowed_prefixes(self):
        """Core metadata store only accepts allowed operational prefixes."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = CoreMetadataStore(db_path=tmp.name)

            # Valid operational keys
            store.set("system.boot_status", {"runlevel": 5}, source="boot_engine")
            res = store.get("system.boot_status")
            self.assertIsNotNone(res)
            self.assertEqual(res["value"]["runlevel"], 5)
            self.assertEqual(res["provenance"]["freshness"], StateFreshness.VERIFIED.value)

            # Forbidden domain key (must fail closed to protect island ownership)
            with self.assertRaises(ValueError):
                store.set("health.vo2max", 52)
            with self.assertRaises(ValueError):
                store.set("work_mars.sprint", "Sprint 42")


if __name__ == "__main__":
    unittest.main()
