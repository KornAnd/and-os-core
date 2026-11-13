"""SSoT Projection subsystem (manifest, registry, fulltext).
Wires the audit-R2 P1 single-source-of-truth tools into the unified
dispatcher: manifest_projector.py, projects_registry_sync.py,
rules_fulltext_expander.py. Kernel sys_cli.py stays immutable — commands
are discovered dynamically via SUBSYSTEM_MAP fast-path.
"""

import sys
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry

# command -> companion script in and_os/bin/
SOT_SCRIPTS = {
    "manifest": "manifest_projector.py",
    "registry": "projects_registry_sync.py",
    "fulltext": "rules_fulltext_expander.py",
}


class SotSubsystem(BaseSubsystem):
    name = "sot"
    description = "SSoT projections: root manifest, projects registry, rules fulltext"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        p_man = subparsers.add_parser(
            "manifest",
            help="Root manifest projection from the and_os/etc/system.json canon (project-root / verify)"
        )
        p_man.add_argument(
            "action",
            choices=["project-root", "verify"],
            help="project-root — regenerate the projection, verify — hash-chain and field check"
        )

        p_reg = subparsers.add_parser(
            "registry",
            help="Projects registry and_os/srv/projects_registry.json (sync / verify)"
        )
        p_reg.add_argument(
            "action",
            choices=["sync", "verify"],
            help="sync — regeneration from live inspectors, verify — freshness and generator stamp"
        )

        p_ft = subparsers.add_parser(
            "fulltext",
            help="Full rule texts in .opencode/rules.md (expand / rebuild / align-titles / verify)"
        )
        p_ft.add_argument(
            "action",
            choices=["expand", "rebuild", "align-titles", "verify"],
            help="expand — restore missing sections, rebuild — reassemble machine sections, "
                 "align-titles — align titles against the manifest, verify — drift control"
        )

    @classmethod
    def execute(cls, args: Any) -> int:
        cmd = args.command
        script = SOT_SCRIPTS.get(cmd)
        if not script:
            print(f"Error: unknown SSoT command '{cmd}'", file=sys.stderr)
            return 2
        res = run_script(script, [args.action])
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"SSoT {cmd} action: {args.action}", skill="sys.sot")
        return res.get("returncode", 0)
