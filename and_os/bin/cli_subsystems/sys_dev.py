"""Development, Release and Architecture Subsystem (tools, release, checkpoint, clean, mode, handoff, sync-docs, bootstrap).
Modular extraction from sys_cli.py following Clean Architecture (Uncle Bob).
Enforces Rule #55 (Release Ledger SQLite), Rule #69 (Spec-Before-Code), APFS CoW checkpoints, and Subagent Handoff.
"""

import os
import sys
import json
import subprocess
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry, VAULT_ROOT


class DevSubsystem(BaseSubsystem):
    name = "dev"
    description = "Release ledger, APFS checkpoints, refactor-cleaner, dev modes, handoff, and system tools"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        # tools
        p_tools = subparsers.add_parser("tools", help="The universal facade of the system utilities (smoke, ui-inspect, native-build, check, graph)")
        p_tools.add_argument("utility", help="The name of the utility")
        p_tools.add_argument("extra_args", nargs="*", help="The arguments of the utility")

        # release
        p_rel = subparsers.add_parser("release", help="The control of the system versions and the releases log on the SQLite base (Rule #55)")
        p_rel_sub = p_rel.add_subparsers(dest="subaction", required=True)
        p_rel_bump = p_rel_sub.add_parser("bump", help="Fix the new version in the SQLite and update the projections")
        p_rel_bump.add_argument("version", help="The version number")
        p_rel_bump.add_argument("--summary", required=True, help="The brief essence of the release")
        p_rel_bump.add_argument("--changes", nargs="+", required=True, help="The list of the key changes")
        p_rel_bump.add_argument("--type", choices=["MAJOR", "MINOR", "PATCH"], default="MINOR", help="The type of the release")
        p_rel_bump.add_argument("--components", default="core", help="The affected components of the system")
        p_rel_bump.add_argument("--gate", action="store_true", help="Run the quality gate (quick_verify + audit) — enabled by default for MAJOR/MINOR, use for PATCH on demand")
        p_rel_bump.add_argument("--no-checkpoint", action="store_true", help="Skip the pre-release CoW checkpoint (NOT recommended)")
        p_rel_list = p_rel_sub.add_parser("list", help="Show the history of the releases from the SQLite")
        p_rel_list.add_argument("-n", "--limit", type=int, default=10, help="The count of the printed releases")
        p_rel_list.add_argument("--json", action="store_true", help="The output in the JSON format")
        p_rel_show = p_rel_sub.add_parser("show", help="Show the details of the specific version")
        p_rel_show.add_argument("version", nargs="?", default="", help="The version for the viewing")
        p_rel_sub.add_parser("sync", help="Synchronize the RELEASE_LEDGER.json and the CHANGELOG.md from the SQLite")

        # checkpoint
        p_cp = subparsers.add_parser("checkpoint", help="The control of the checkpoints and the instant CoW snapshots of the working area")
        p_cp.add_argument("action", choices=["create", "verify", "rollback", "list", "clear"], help="The action")
        p_cp.add_argument("name", nargs="?", help="The name of the checkpoint")
        p_cp.add_argument("--targets", nargs="*", help="The target catalogs")
        p_cp.add_argument("--keep", type=int, default=5, help="How many of the last snapshots to keep on the cleaning")

        # clean
        p_clean = subparsers.add_parser("clean", help="The safe audit and the cleaning of the dead code with the registration in the DELETION_LOG")
        p_clean.add_argument("action", nargs="?", default="audit", choices=["audit", "dry-run", "log"], help="The action")
        p_clean.add_argument("--dir", help="The target subcatalog for the scanning")

        # mode
        p_mode = subparsers.add_parser("mode", help="The control of the behavior presets of the agent (dev, research, review)")
        p_mode.add_argument("action", nargs="?", default="get", choices=["get", "set", "show", "list"], help="The action")
        p_mode.add_argument("target_mode", nargs="?", help="The target mode")

        # handoff
        p_hnd = subparsers.add_parser("handoff", help="The control and the validation of the canonical protocol of the tasks transfer between the subagents")
        p_hnd.add_argument("action", choices=["validate"], help="The action")
        p_hnd.add_argument("file", help="The path to the handoff markdown file")

        # sync-docs
        p_sdocs = subparsers.add_parser("sync-docs", help="The auto-generation and the synchronization of the production runbook RUNBOOK.md from the kernel code")
        p_sdocs.add_argument("--check", action="store_true", help="Check the actuality without the overwriting")

        # bootstrap
        p_boot = subparsers.add_parser("bootstrap", help="The check of the readiness to the transfer and the auto-deployment of the system on a new computer")
        p_boot.add_argument("--install", action="store_true", help="Automatically install the missing pip dependencies")
        p_boot.add_argument("--json", action="store_true", help="The output in the JSON format")

    @classmethod
    def execute(cls, args: Any) -> int:
        cmd = args.command

        if cmd == "tools":
            tool_map = {
                "smoke": "dash_smoke_test.py",
                "ui-inspect": "ui_inspector.py",
                "app-check": "app_quick_check.py",
                "build-native": "build_native.py",
                "graph": "graph_builder.py",
                "gen-ctx": "gen_context.py",
                "health-bridge": "health_bridge.py",
                "ftrack-cache": "ftrack_cache.py",
                "board-parser": "board_parser.py",
                "trim-output": "trim_output.py",
                "graph-orphans": "audit_graph_orphans.py",
                "schema-validator": "schema_validator.py",
                "link-orphans": "link_graph_orphans.py",
                "clean-links": "clean_links.py",
                "tags-links": "audit_tags_links.py",
                "webdav-fix": "fix_webdav_sync_issues.py",
                "budget-calc": "budget_calc.py",
                "convert-doc": "convert_doc.py",
                "telemetry_sync": "telemetry_sync_sync.py",
                "yt-analyze": "yt_analyze.py",
                "career-radar": "career_radar.py",
                "mirror": "mirror_collector.py",
                "architect": "architect_engine.py"
            }
            if args.utility == "kot-sync":
                pulsar_kot = "./pulsar/kot_gantt"
                print("🔄 [KOT GANTT] The actualization of the data and the build of the index.html...")
                res1 = subprocess.run([sys.executable, f"{pulsar_kot}/build_data.py"], capture_output=True, text=True)
                print(res1.stdout, end="")
                if res1.stderr:
                    print(res1.stderr, file=sys.stderr)
                res2 = subprocess.run([sys.executable, f"{pulsar_kot}/generate_html.py"], capture_output=True, text=True)
                print(res2.stdout, end="")
                auto_log_telemetry("Kot Gantt data sync", skill="sys.tools")
                return 0
            elif args.utility == "mars-sync":
                pulsar_mars = "./pulsar/mars_gantt"
                print("🚀 [MARS GANTT] The actualization of the data and the build of the index.html...")
                res1 = subprocess.run([sys.executable, f"{pulsar_mars}/build_data.py"], capture_output=True, text=True)
                print(res1.stdout, end="")
                if res1.stderr:
                    print(res1.stderr, file=sys.stderr)
                res2 = subprocess.run([sys.executable, f"{pulsar_mars}/generate_html.py"], capture_output=True, text=True)
                print(res2.stdout, end="")
                auto_log_telemetry("Mars Gantt data sync", skill="sys.tools")
                return 0

            target_script = tool_map.get(args.utility)
            if target_script:
                res = run_script(target_script, args.extra_args or [])
                print(res.get("stdout", ""), end="")
                if res.get("stderr"):
                    print(res["stderr"], file=sys.stderr)
                auto_log_telemetry(f"Utility tool run: {args.utility}", skill="sys.tools")
                return res.get("returncode", 0)
            else:
                print(f"[!] Unknown utility: {args.utility}", file=sys.stderr)
                return 1

        elif cmd == "release":
            from and_os.lib.core.release_ledger import record_release, list_releases, get_latest_release, sync_projections
            if args.subaction == "bump":
                # Canonical release pipeline (audit R3, F3; R3-VER-1..3):
                # gate(opt) -> CoW checkpoint -> canonical write -> root
                # projection -> ledger -> post-release integrity verify.
                from and_os.lib.release_pipeline import ReleaseAbortError, run_release_pipeline
                try:
                    result = run_release_pipeline(
                        vault_root=VAULT_ROOT,
                        version=args.version,
                        summary=args.summary,
                        changes=args.changes,
                        release_type=args.type,
                        components=args.components,
                        gate=args.gate or args.type in ("MAJOR", "MINOR"),
                        checkpoint=not args.no_checkpoint,
                    )
                except ReleaseAbortError as err:
                    print(f"🛑 The release v{args.version} was ABORTED before any write:")
                    print(f"   • {err}")
                    return 1
                for line in result["log"]:
                    print(f"   • {line}")
                if not result["ok"]:
                    for err in result["errors"]:
                        sys.stderr.write(f"   [ERROR] {err}\n")
                    print(f"⚠️ The release v{args.version} was recorded, but the post-release integrity verify FAILED.")
                    auto_log_telemetry(f"Release bump: v{args.version} (verify FAIL)", skill="sys.release")
                    return 1
                print(f"🎉 The release v{args.version} was fixed: canonical + projection + ledger, integrity verified.")
                print(f"   • Essence: {args.summary}")
                print(f"   • Changes: {len(args.changes)}")
                auto_log_telemetry(f"Release bump: v{args.version}", skill="sys.release")
                return 0
            elif args.subaction == "list":
                rels = list_releases(limit=args.limit)
                if getattr(args, "json", False):
                    print(json.dumps(rels, ensure_ascii=False, indent=2))
                else:
                    print(f"=== 📜 AnD os System Release History (Top {len(rels)}) ===")
                    for r in rels:
                        print(f"  • v{r['version']} [{r['release_date']}] ({r['release_type']}): {r['summary']}")
                return 0
            elif args.subaction == "show":
                target_v = args.version
                if not target_v:
                    rel = get_latest_release()
                else:
                    rels = [r for r in list_releases(limit=100) if r["version"] == target_v]
                    rel = rels[0] if rels else None
                if not rel:
                    print(f"❌ The release '{target_v}' was not found in the SQLite ledger.", file=sys.stderr)
                    return 1
                print(f"=== 📦 AnD os Release v{rel['version']} ({rel['release_date']}) ===")
                print(f"Type: {rel['release_type']} | Components: {rel.get('affected_components', 'all')}")
                print(f"Essence: {rel['summary']}")
                print("Changes:")
                for ch in rel.get("changes", []):
                    print(f"  - {ch}")
                return 0
            elif args.subaction == "sync":
                sync_projections()
                print("✅ The projections of the RELEASE_LEDGER.json and the CHANGELOG.md were synchronized from the SQLite.")
                return 0

        elif cmd == "checkpoint":
            flags = [args.action]
            if getattr(args, "name", None):
                flags.append(args.name)
            if getattr(args, "targets", None):
                flags.append("--targets")
                flags.extend(args.targets)
            if args.action == "clear":
                flags.extend(["--keep", str(args.keep)])
            res = run_script("checkpoint_manager.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Checkpoint action: {args.action}", skill="sys.checkpoint")
            return res.get("returncode", 0)

        elif cmd == "clean":
            flags = [args.action]
            if getattr(args, "dir", None):
                flags.extend(["--dir", args.dir])
            res = run_script("refactor_cleaner.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Clean action: {args.action}", skill="sys.clean")
            return res.get("returncode", 0)

        elif cmd == "mode":
            flags = [args.action]
            if getattr(args, "target_mode", None):
                flags.append(args.target_mode)
            res = run_script("context_mode_manager.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Mode action: {args.action}", skill="sys.mode")
            return res.get("returncode", 0)

        elif cmd == "handoff":
            flags = [args.action, args.file]
            res = run_script("agent_handoff.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Handoff action: {args.action}", skill="sys.handoff")
            return res.get("returncode", 0)

        elif cmd == "sync-docs":
            flags = ["--check"] if getattr(args, "check", False) else []
            res = run_script("docs_sync.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Sync docs and runbook", skill="sys.docs")
            return res.get("returncode", 0)

        elif cmd == "bootstrap":
            flags = []
            if getattr(args, "install", False):
                flags.append("--install")
            if getattr(args, "json", False):
                flags.append("--json")
            res = run_script("bootstrap_system.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("System bootstrap & portability check", skill="sys.bootstrap")
            return res.get("returncode", 0)

        return 1
