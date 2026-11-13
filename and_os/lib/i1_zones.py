#!/usr/bin/env python3
"""
i1_zones.py - Single-source-of-truth loader for the I-1 kernel immutability
zones (audit R4, P11).

The I-1 declaration (rules.md "Kernel Immutability", AGENTS.md) used to be
duplicated in every consumer (banner contract test, manifest_probe, ad-hoc
fix scripts). The R4-P7 and R4-P7-2 incidents both came from an
unsynchronized extra copy letting a bulk edit touch the kernel. The zone
list now lives in one machine-readable file, and_os/etc/i1_kernel_zones.json;
every consumer loads it through this module.

When the file is absent (e.g. a miniature test vault) the built-in defaults
apply; they must stay identical to the shipped SSoT (pinned by
test_i1_kernel_zones_r4.py), so the fallback path is provably equivalent.
"""

import json
import os
import sys

SSoT_REL = os.path.join("and_os", "etc", "i1_kernel_zones.json")

# Built-in defaults: identical to the shipped SSoT file (drift is pinned by
# the contract test, never by manual synchronization).
# Since the B1 relocation (audit R4 backlog) the cg Production Skeleton
# physically lives in and_os/lib/core/cg/, so the kernel is one zone and
# the only exempt file is the usd animatic pipeline test.
DEFAULT_I1_ZONES = (
    "and_os/lib/core/",
)
DEFAULT_I1_EXEMPT_FILES = (
    "and_os/opt/apps/cg_workspace/tests/test_usd_animatic_pipeline.py",
)


def load_i1_zones(vault_root, strict=False):
    """Load the I-1 zone declaration.

    Returns a triple (zones, exempt_files, source):
      zones        - tuple of vault-relative path prefixes (end with "/")
      exempt_files - tuple of exact vault-relative file paths
      source       - "ssoT" when the file was read, "default:missing" or
                     "default:invalid:<error>" when the built-in defaults
                     were used instead.

    strict=True raises RuntimeError when the SSoT is missing or invalid
    (live-vault contract tests). Probes use strict=False so a broken file
    degrades to defaults plus a warning instead of flipping a ring.
    """
    path = os.path.join(vault_root, SSoT_REL)
    if not os.path.exists(path):
        if strict:
            raise RuntimeError("I-1 zones SSoT missing: " + path)
        return DEFAULT_I1_ZONES, DEFAULT_I1_EXEMPT_FILES, "default:missing"
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        zones = tuple(str(z) for z in data["zones"])
        files = tuple(str(f) for f in data["exempt_files"])
        if not zones or not files:
            raise ValueError("zones and exempt_files must be non-empty lists")
        return zones, files, "ssoT"
    except (OSError, ValueError, KeyError, TypeError) as err:
        if strict:
            raise RuntimeError("I-1 zones SSoT invalid: %s" % err)
        sys.stderr.write(
            "[i1_zones] SSoT unreadable (%s); using built-in defaults\n" % err)
        return DEFAULT_I1_ZONES, DEFAULT_I1_EXEMPT_FILES, "default:invalid:%s" % err
