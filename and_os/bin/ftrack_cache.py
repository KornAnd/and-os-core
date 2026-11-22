#!/usr/bin/env python3
"""ftrack_cache.py - Thin facade delegating to the canonical hub module.

Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack lived in two
live copies (and_os/bin/ and the opt hubs) that drifted apart, so the
two consumers saw different behavior. The business logic now lives in
exactly one place:

  and_os/opt/apps/tracker_hub/modules/ftrack_cache.py

This shim keeps the public entry point stable for the sys_cli
dispatcher (run_script), the skill probe commands and the shell
consumers. CLI arguments are forwarded unchanged.
"""

import os
import sys
sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.
import runpy

HUB_MODULE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "opt",
    "apps",
    "tracker_hub",
    "modules",
    "ftrack_cache.py",
)

# 17.11 audit (R4-DUP-1 regression): when run as and_os/bin/<x>.py,
# sys.path[0] is and_os/bin/, where the SIBLING SHIMS shadow the canonical
# hub modules by name — a hub-to-hub import (ftrack_sync -> ftrack_report)
# resolved to a shim and crashed with AttributeError. Anchor the hub
# directory before delegation so every inter-hub import resolves to the
# real module.
sys.path.insert(0, os.path.dirname(os.path.abspath(HUB_MODULE)))

if __name__ == "__main__":
    runpy.run_path(HUB_MODULE, run_name="__main__")
