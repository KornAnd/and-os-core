#!/usr/bin/env python3
"""
agent_handoff.py - Validator and Generator for AnD os Subagent Handoff Protocol.
Ensures zero-context loss during inter-agent transitions conforming to AGENT_HANDOFF_SPEC.md.
"""

import os
import sys
import re
import argparse
from typing import Dict, Any, List

REQUIRED_SECTIONS = [
    "Context horizon",
    "Key decisions and invariants",
    "Touched files and deltas",
    "Quality verification status",
    "Open questions",
    "Recommended actions"
]


def validate_handoff_content(content: str) -> Dict[str, Any]:
    missing_sections = []
    for s in REQUIRED_SECTIONS:
        if not re.search(re.escape(s), content, re.IGNORECASE):
            missing_sections.append(s)

    # Check for secret leaks
    secret_leak = bool(re.search(r"sk-[a-zA-Z0-9]{20,}", content) or re.search(r"ghp_[a-zA-Z0-9]{20,}", content))

    passed = (len(missing_sections) == 0) and not secret_leak

    return {
        "valid": passed,
        "missing_sections": missing_sections,
        "secret_leak_detected": secret_leak
    }


def main():
    parser = argparse.ArgumentParser(description="AnD os Subagent Handoff Validator")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_val = subparsers.add_parser("validate", help="Check the handoff document against the spec")
    p_val.add_argument("file", help="Path to the handoff markdown file")

    args = parser.parse_args()

    if args.subcommand == "validate":
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}", file=sys.stderr)
            sys.exit(1)

        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()

        res = validate_handoff_content(content)
        if res["valid"]:
            print(f"🟢 HANDOFF VALID: document '{args.file}' is 100% compliant with the canonical spec.")
            sys.exit(0)
        else:
            print(f"🔴 HANDOFF INVALID: defects found in the document:")
            if res["missing_sections"]:
                print(f"  • Missing mandatory sections: {', '.join(res['missing_sections'])}")
            if res["secret_leak_detected"]:
                print(f"  • Potential secret/token leaks detected!")
            sys.exit(1)


if __name__ == "__main__":
    main()
