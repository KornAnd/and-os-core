#!/usr/bin/env python3
"""image_ocr.py - Thin facade delegating to the canonical hub module.

Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack lived in two
live copies (and_os/bin/ and the opt hubs) that drifted apart, so the
two consumers saw different behavior. The business logic now lives in
exactly one place:

  and_os/opt/apps/doc_hub/modules/image_ocr.py

This shim keeps the public entry point stable for the sys_cli
dispatcher (run_script), the skill probe commands and the shell
consumers. CLI arguments are forwarded unchanged.
"""

import os
import runpy

HUB_MODULE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "opt",
    "apps",
    "doc_hub",
    "modules",
    "image_ocr.py",
)

if __name__ == "__main__":
    runpy.run_path(HUB_MODULE, run_name="__main__")
