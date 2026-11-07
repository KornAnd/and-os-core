"""
test_event_journal.py — Comprehensive Unit Tests for C4B Canonical Event Journal
AnD os v8.1 — Core Architecture Verification
"""

import os
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from and_os.lib.core.bus import (
    emit_event,
    get_recent_events,
    clear_events,
    BUS_FILE,
    LOCK_FILE,
)


class TestEventJournal(unittest.TestCase):

    def setUp(self):
        clear_events()

    def tearDown(self):
        clear_events()

    def test_emit_and_read_event(self):
        """Emits an event and verifies canonical envelope structure."""
        rec = emit_event(
            event_type="TEST_EVENT",
            payload={"action": "verify", "value": 42},
            source="test_runner"
        )
        self.assertTrue(rec["event_id"].startswith("evt_"))
        self.assertEqual(rec["type"], "TEST_EVENT")
        self.assertEqual(rec["source"], "test_runner")
        self.assertEqual(rec["payload"]["value"], 42)
        self.assertIn("timestamp_utc", rec)
        self.assertIn("provenance", rec)

        events = get_recent_events(limit=10)
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0]["event_id"], rec["event_id"])

    def test_concurrent_emits_no_data_corruption(self):
        """Spawns 20 concurrent threads writing events under file lock."""
        num_threads = 20

        def emit_worker(i):
            emit_event(
                event_type=f"CONCURRENT_{i}",
                payload={"index": i},
                source=f"worker_{i}"
            )

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(emit_worker, range(num_threads)))

        events = get_recent_events(limit=50)
        self.assertEqual(len(events), num_threads)

        # Ensure all records are valid, uncorrupted JSON objects
        indices = set()
        for e in events:
            self.assertTrue(e["type"].startswith("CONCURRENT_"))
            indices.add(e["payload"]["index"])
        self.assertEqual(len(indices), num_threads)


if __name__ == "__main__":
    unittest.main()
