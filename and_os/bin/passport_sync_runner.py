#!/usr/bin/env python3
"""
passport_sync_runner.py — Daily cron wrapper for the Island 7 passport sync.

Runs the library-level PulsarPassportSync (and_os/lib/pulsar/passport_sync.py)
as a supervised cron job (and_os/etc/services.json, id=passport_sync) so the
Nero/pulsar/ passports stay in parity with the physical /WORK/pulsar/ tree
under the single control plane (audit R2, WI-4.7).
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
sys.path.insert(0, VAULT_ROOT)

from and_os.lib.pulsar.passport_sync import PulsarPassportSync  # noqa: E402


def main() -> int:
    try:
        result: Dict[str, Any] = PulsarPassportSync(vault_root=Path(VAULT_ROOT)).sync()
        print(
            f"passport_sync OK: total={result['total_apps']} "
            f"created={len(result['created'])} updated={len(result['updated'])}"
        )
        return 0
    except Exception as err:
        print(f"passport_sync FAILED: {type(err).__name__}: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
