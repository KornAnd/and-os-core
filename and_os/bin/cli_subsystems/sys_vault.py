"""Knowledge and Vault Guard subsystem (vault command: read, patch, set-frontmatter, move).
Modular extraction from sys_cli.py following Clean Architecture (Uncle Bob).
Rule #19 Invariant: Enforces AST-protected mutations and non-destructive reads.
"""

import sys
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry


class VaultSubsystem(BaseSubsystem):
    name = "vault"
    description = "Obsidian Vault Guard MCP Gateway (read, patch, set-frontmatter, move)"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        p_vg = subparsers.add_parser("vault", help="MCP Vault Guard gateway for safe reading and editing of notes")
        p_vg_sub = p_vg.add_subparsers(dest="subaction", required=True)

        p_vg_read = p_vg_sub.add_parser("read", help="Safe pinpoint reading of a note")
        p_vg_read.add_argument("path", help="Path to the note from the vault root")
        p_vg_read.add_argument("--section", help="Markdown section (e.g. '## 23.10')")
        p_vg_read.add_argument("--max-lines", type=int, default=200, help="Line limit")

        p_vg_patch = p_vg_sub.add_parser("patch", help="Atomic note patch with AST check")
        p_vg_patch.add_argument("path", help="Path to the note from the vault root")
        p_vg_patch.add_argument("--target", required=True, help="Exact line to replace")
        p_vg_patch.add_argument("--replacement", required=True, help="New line")

        p_vg_fm = p_vg_sub.add_parser("set-frontmatter", help="Safe metadata update")
        p_vg_fm.add_argument("path", help="Path to the note from the vault root")
        p_vg_fm.add_argument("--json", required=True, help="JSON string of the updates")

        p_vg_mv = p_vg_sub.add_parser("move", help="Atomic rename/move with cascading link refactoring")
        p_vg_mv.add_argument("src", help="Original relative path to the note")
        p_vg_mv.add_argument("dst", help="New relative path to the note")

    @classmethod
    def execute(cls, args: Any) -> int:
        if args.subaction == "move":
            flags = ["move", args.src, args.dst]
        else:
            flags = [args.subaction, args.path]
            if args.subaction == "read":
                if args.section:
                    flags.extend(["--section", args.section])
                if args.max_lines:
                    flags.extend(["--max-lines", str(args.max_lines)])
            elif args.subaction == "patch":
                flags.extend(["--target", args.target, "--replacement", args.replacement])
            elif args.subaction == "set-frontmatter":
                flags.extend(["--json", args.json])

        res = run_script("mcp_vault_guard.py", flags)
        print(res.get("stdout", ""))
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)

        target_info = f"{args.src} -> {args.dst}" if args.subaction == "move" else args.path
        auto_log_telemetry(f"Vault Guard: {args.subaction} on {target_info}", skill="mcp.vault_guard")
        return res.get("returncode", 0)
