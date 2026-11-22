"""
link_probe.py — Ring 1: Link Integrity (vault-wide wikilink dead-link gate).
AnD os v1.2.0 (R-2, 20.11).

Closes the coverage gap measured by the Agent Journey Efficiency Audit
(20.11): the Grid passed 10/10 while 20 wikilinks in active docs pointed
at moved/removed targets. Core scanner: and_os/lib/health_grid/link_scan.py
(shared with the and_os/bin/link_guard.py CLI).

Blocking: broken NOTE links (no extension) in live documents. Non-blocking:
  - ASSET links (images, pdf, docx, json, base, canvas, media) — lost
    attachments are content loss, not a link-gate failure (advisory).
  - historical records (Nero/reports/, and_os/var/audits/, telemetry
    journals) and snapshot/env targets (var/checkpoints/, .venv) — their
    links are a point-in-time record (forward-only, Rule #61).

Performance: fingerprint-cached (file count + md count + max mtime +
schema) — the first full pass is ~1-2 s on the current vault, subsequent
Grid runs reuse the cache while the vault is unchanged.
"""

import os
from typing import Any

from and_os.lib.health_grid import BaseProbeResult
from and_os.lib.health_grid.link_scan import scan_vault


class LinkProbe:
    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 1: Link Integrity (wikilink dead-link gate)", ring=1)
        issues = 0
        try:
            scan = scan_vault(vault_root, use_cache=True)
        except Exception as e:  # scanner crash is a probe failure, not a silent pass
            issues += 1
            result.errors.append(f"Link scan failed: {e}")
            return result

        broken = scan.get("broken", [])
        for entry in broken[:20]:
            result.errors.append(
                f"Dead wikilink in {entry['file']}: [[{entry['link']}]] "
                f"(target '{entry['target']}' not found in vault)")
        if len(broken) > 20:
            result.errors.append(f"... and {len(broken) - 20} more dead links")
        if broken:
            issues += len(broken)

        hist = scan.get("historical_broken", 0)
        artifacts = scan.get("artifact_broken", 0)
        assets = scan.get("asset_broken", 0)
        if hist:
            result.warnings.append(
                f"{hist} broken link(s) in historical records (Nero/reports/, "
                f"var/audits/, telemetry, checkpoint/venv snapshots) — "
                f"forward-only, not blocked ({artifacts} of them snapshot/env targets)")
        if assets:
            result.warnings.append(
                f"{assets} dead attachment(s) (images/pdf/docx/json/media) — "
                f"content loss, not a link-gate failure (advisory)")

        result.details = {
            "files_scanned": scan.get("files_scanned", 0),
            "links_scanned": scan.get("links_scanned", 0),
            "broken_live": len(broken),
            "broken_historical": hist,
            "broken_artifact": artifacts,
            "broken_asset": assets,
            "cached": scan.get("cached", False),
            "elapsed_sec": scan.get("elapsed_sec", 0),
        }
        result.issues_count = issues
        result.passed = issues == 0
        if verbose and result.details:
            print(f"  • Link Integrity: {result.details['links_scanned']} links in "
                  f"{result.details['files_scanned']} files, "
                  f"{len(broken)} dead (live) / {hist} (historical), "
                  f"{'cached' if result.details['cached'] else 'full scan'} "
                  f"({result.details['elapsed_sec']}s)")
        return result
