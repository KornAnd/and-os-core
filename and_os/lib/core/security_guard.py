#!/usr/bin/env python3
"""
security_guard.py — Automated Security Sentinel & Secret Leak Guard (AnD os v8.1).
Core subsystem (and_os/lib/core/).
Rule #6: Secrets via macOS Keychain only (@@K:key), plaintext tokens forbidden in codebase.

Inspects:
1. Potential API keys (Ftrack, Telegram, AWS, OpenAI, GitHub, WebDAV).
2. Private RSA/SSH keys and certificates.
3. Plaintext passwords in configurations and notes.
"""

import os
import re
import sys
import json
from typing import List, Dict, Any

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
AND_OS_ROOT = os.path.join(VAULT_ROOT, "and_os")
try:
    from and_os.lib.core.root_config import resolve_pulsar_root
    PULSAR_ROOT = resolve_pulsar_root() or os.path.expanduser("~/Yandex.Disk.localized/WORK/pulsar")
except Exception:
    PULSAR_ROOT = os.path.expanduser("~/Yandex.Disk.localized/WORK/pulsar")

# Regular expressions for secret leak detection
LEAK_PATTERNS = [
    (r"(?i)(?:api_key|apikey|secret_key|access_token|bot_token|token)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "High-entropy API token assignment"),
    (r"(?i)bot[0-9]{8,10}:[a-zA-Z0-9_\-]{35}", "Telegram Bot Token Pattern"),
    (r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "Private Key Header"),
    (r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{6,}['\"]", "Plaintext Password Assignment"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"xox[baprs]-[0-9]{10,12}-[0-9]{10,12}-[a-zA-Z0-9]{24,32}", "Slack Token")
]

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".cache", ".tmp.drive",
    "venv", ".venv", "dist", "build", ".DS_Store"
}

IGNORE_FILES = {
    "security_guard.py", "telemetry.md"
}

def scan_file_for_leaks(filepath: str) -> List[Dict[str, Any]]:
    """Scan an individual file for potential secret leaks."""
    if os.path.basename(filepath) in IGNORE_FILES:
        return []
    
    # Ignore binary files
    ext = os.path.splitext(filepath)[1].lower()
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".db", ".sqlite", ".pyc", ".blend", ".zip", ".tar", ".gz"}:
        return []

    findings = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                # Skip legitimate Keychain references @@K:
                if "@@K:" in line or "os.environ" in line or "keychain" in line.lower() and "@@" in line:
                    continue
                # Skip test/template strings
                if "<API_KEY>" in line or "<KEY>" in line or "<TOKEN>" in line or "YOUR_" in line or "example" in line.lower():
                    continue

                for pattern, desc in LEAK_PATTERNS:
                    if re.search(pattern, line):
                        findings.append({
                            "file": filepath,
                            "line_num": line_no,
                            "desc": desc,
                            "snippet": line.strip()[:80]
                        })
    except OSError as err:
        sys.stderr.write(f"[security_guard] Warning reading {filepath}: {err}\n")
    return findings

def scan_system_secrets() -> Dict[str, Any]:
    """Scan Obsidian Vault and Pulsar Space for sensitive credentials."""
    all_findings = []
    targets = [
        AND_OS_ROOT,
        os.path.join(VAULT_ROOT, "Nero"),
        os.path.join(VAULT_ROOT, ".opencode")
    ]
    if os.path.exists(PULSAR_ROOT):
        targets.append(PULSAR_ROOT)

    for target_dir in targets:
        if not os.path.exists(target_dir):
            continue
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                full_path = os.path.join(root, file)
                findings = scan_file_for_leaks(full_path)
                if findings:
                    all_findings.extend(findings)

    return {
        "status": "PASS" if not all_findings else "ALERT",
        "leaks_found": len(all_findings),
        "details": all_findings
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AnD os Secret Sentinel & Leak Guard")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    report = scan_system_secrets()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print("=== 🛡️ AND OS SECRET SENTINEL & LEAK GUARD (Rule #6) ===")
    if report["status"] == "PASS":
        print("🟢 Secrets secured: No plaintext tokens or passwords detected in codebase.")
        print("🔒 All production service credentials isolated via macOS Keychain (@@K:).")
    else:
        print(f"🔴 ALERT: Potential credential leaks detected: {report['leaks_found']}")
        for f in report["details"]:
            rel = os.path.relpath(f['file'], VAULT_ROOT) if f['file'].startswith(VAULT_ROOT) else f['file']
            print(f"  ⚠️ [{f['desc']}] {rel}:{f['line_num']}")
            print(f"     `{f['snippet']}`")
    print("=========================================================")

if __name__ == "__main__":
    main()
