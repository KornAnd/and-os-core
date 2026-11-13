"""Media and 3D CG Pipeline subsystem (cg, comfy, animatic, hybrid-render, montage, conform, consistency).
Modular extraction from sys_cli.py following Clean Architecture (Uncle Bob).
Enforces Rule #27 (Muscle Realm Isolation), LiteGraph v0.4 schema validation, and OpenTimelineIO standards.
"""

import os
import sys
import subprocess
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry, VAULT_ROOT


class MediaSubsystem(BaseSubsystem):
    name = "media"
    description = "3D CG tooling, ComfyUI registry, generative montage, OTIO conform, and hybrid render"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        # cg
        p_cg = subparsers.add_parser("cg", help="The control of the 3D pipeline, the scenes and the ComfyUI nodes")
        p_cg.add_argument("action", choices=["nodes", "graph", "scenes", "bridge"], help="The action")
        p_cg.add_argument("--json", action="store_true", help="The output in the JSON format")

        # comfy
        p_comfy = subparsers.add_parser("comfy", help="The versions base of the ComfyUI nodes and the compatibility check on the updates")
        p_comfy.add_argument("--verify", action="store_true", help="The verification of the nodes compatibility with the global registry")
        p_comfy.add_argument("--target", type=str, help="The path to the specific workflow JSON for the check")
        p_comfy.add_argument("--json", action="store_true", help="The output in the JSON format")

        # animatic
        p_anim = subparsers.add_parser("animatic", help="The generation of the animatic and the shot timeline by the scenario beats")
        p_anim.add_argument("title", help="The shot/episode name (e.g. E010_SH010)")
        p_anim.add_argument("--framework", choices=["save_the_cat", "hero_journey", "story_circle", "dan_harmon", "three_act", "hybrid"], default="hybrid", help="The dramaturgical framework")
        p_anim.add_argument("--beats", help="The path to the scene beats JSON file or the raw text")
        p_anim.add_argument("--comfy-export", action="store_true", help="Export the nodes structure for the ComfyUI")
        p_anim.add_argument("--json", action="store_true", help="The output in the JSON format")
        p_anim.add_argument("--out", "-o", help="The path of the saving of the animatic manifest")

        # hybrid-render
        p_hr = subparsers.add_parser("hybrid-render", help="The 3D-to-AI stylization via the Multi-ControlNet ComfyUI")
        p_hr.add_argument("shot_id", help="The shot identifier (e.g. 'E010_SH030')")
        p_hr.add_argument("--prompt", required=True, help="The main textual prompt for the stylization")
        p_hr.add_argument("--depth", help="The path to the Depth pass (the depth map from the Blender)")
        p_hr.add_argument("--normal", help="The path to the Normal pass (the normals map)")
        p_hr.add_argument("--lineart", help="The path to the LineArt pass (the Freestyle contours)")
        p_hr.add_argument("--denoise", type=float, default=0.45, help="The denoise strength (0.35-0.55)")
        p_hr.add_argument("--json", action="store_true", help="The output in the JSON format")
        p_hr.add_argument("--out", "-o", help="The path for the generated frame/video")

        # consistency
        p_tc = subparsers.add_parser("consistency", help="The check of the temporal stability of the animation sequence")
        p_tc.add_argument("sequence_dir", help="The catalog with the frames of the sequence (PNG/JPEG)")
        p_tc.add_argument("--threshold", type=float, default=0.85, help="The SSIM optical flow threshold (0.0-1.0)")
        p_tc.add_argument("--json", action="store_true", help="The output in the JSON format")
        p_tc.add_argument("--out", "-o", help="The path for the saving of the stability report")

        # conform
        p_conf = subparsers.add_parser("conform", help="The conform of the editorial timeline (OpenTimelineIO / EDL / XML)")
        p_conf.add_argument("sequence", help="The name or the path of the sequence (e.g. 'E010')")
        p_conf.add_argument("--edl", help="The path to the CMX 3600 EDL editing file")
        p_conf.add_argument("--shots", help="The path to the catalog of the rendered shots for the substitution")
        p_conf.add_argument("--fps", type=float, default=24.0, help="The base frame rate of the timeline")
        p_conf.add_argument("--handles", type=int, default=8, help="The handles size (the frames of the overlap)")
        p_conf.add_argument("--roundtrip", choices=["fcp_xml", "edl", "otio"], default="otio", help="The export format for the edit")
        p_conf.add_argument("--json", action="store_true", help="The output in the JSON format")
        p_conf.add_argument("--out", "-o", help="The path of the saving of the conformed file")

        # montage
        p_montage = subparsers.add_parser("montage", help="The generative video editing and the orchestration of the timelines (Montage Hub)")
        p_montage.add_argument("montage_sub", nargs="?", default="info", help="The montage subcommand: info, build, render, beat, conform, audit")
        p_montage.add_argument("extra_args", nargs="*", help="The additional arguments for the montage_cli.py")

    @classmethod
    def execute(cls, args: Any) -> int:
        cmd = args.command

        if cmd == "cg":
            if args.action == "nodes":
                script = "comfy_node_registry.py"
            elif args.action == "graph":
                script = "comfy_graph.py"
            elif args.action == "scenes":
                script = "video_scenes.py"
            else:
                script = "cg_bridge.py"
            flags = ["--json"] if getattr(args, "json", False) else []
            res = run_script(script, flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"CG 3D pipeline ({args.action})", skill="sys.cg")
            return res.get("returncode", 0)

        elif cmd == "comfy":
            flags = []
            if getattr(args, "verify", False):
                flags.append("--verify")
                if getattr(args, "target", None):
                    flags.append(args.target)
            else:
                flags.append("--scan")
                if getattr(args, "json", False):
                    flags.append("--json")
            res = run_script("comfy_node_registry.py", flags)
            print(res.get("stdout", ""))
            auto_log_telemetry(f"ComfyUI node registry: {'verify' if getattr(args, 'verify', False) else 'scan'}", skill="sys.comfy")
            return res.get("returncode", 0)

        elif cmd == "animatic":
            flags = [args.title]
            if getattr(args, "framework", None):
                flags.extend(["--framework", args.framework])
            if getattr(args, "beats", None):
                flags.extend(["--beats", args.beats])
            if getattr(args, "comfy_export", False):
                flags.append("--comfy-export")
            if getattr(args, "json", False):
                flags.append("--json")
            if getattr(args, "out", None):
                flags.extend(["--out", args.out])
            res = run_script("hybrid_animatic_director.py", flags)
            if "stdout" in res:
                print(res["stdout"])
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Hybrid animatic: {args.title} ({getattr(args, 'framework', 'hybrid')})", skill="hybrid-animatic-director")
            return res.get("returncode", 0)

        elif cmd == "hybrid-render":
            flags = [args.shot_id, "--prompt", args.prompt]
            if getattr(args, "depth", None):
                flags.extend(["--depth", args.depth])
            if getattr(args, "normal", None):
                flags.extend(["--normal", args.normal])
            if getattr(args, "lineart", None):
                flags.extend(["--lineart", args.lineart])
            if getattr(args, "denoise", None):
                flags.extend(["--denoise", str(args.denoise)])
            if getattr(args, "json", False):
                flags.append("--json")
            if getattr(args, "out", None):
                flags.extend(["--out", args.out])
            res = run_script("hybrid_comfyui_render.py", flags)
            if "stdout" in res:
                print(res["stdout"])
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Hybrid ComfyUI render: {args.shot_id}", skill="hybrid-comfyui-render")
            return res.get("returncode", 0)

        elif cmd == "consistency":
            flags = [args.sequence_dir]
            if getattr(args, "threshold", None):
                flags.extend(["--threshold", str(args.threshold)])
            if getattr(args, "json", False):
                flags.append("--json")
            if getattr(args, "out", None):
                flags.extend(["--out", args.out])
            res = run_script("temporal_consistency_guard.py", flags)
            if "stdout" in res:
                print(res["stdout"])
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Temporal consistency: {args.sequence_dir}", skill="temporal-consistency-guard")
            return res.get("returncode", 0)

        elif cmd == "conform":
            flags = [args.sequence]
            if getattr(args, "edl", None):
                flags.extend(["--edl", args.edl])
            if getattr(args, "shots", None):
                flags.extend(["--shots", args.shots])
            if getattr(args, "fps", None):
                flags.extend(["--fps", str(args.fps)])
            if getattr(args, "handles", None):
                flags.extend(["--handles", str(args.handles)])
            if getattr(args, "roundtrip", None):
                flags.extend(["--roundtrip", args.roundtrip])
            if getattr(args, "json", False):
                flags.append("--json")
            if getattr(args, "out", None):
                flags.extend(["--out", args.out])
            res = run_script("editorial_otio_conform.py", flags)
            if "stdout" in res:
                print(res["stdout"])
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Editorial conform: {args.sequence}", skill="editorial-otio-conform")
            return res.get("returncode", 0)

        elif cmd == "montage":
            target = os.path.join(VAULT_ROOT, "and_os/opt/apps/montage_hub/montage_cli.py")
            if not os.path.exists(target):
                sys.stderr.write("montage_hub engine not found in and_os/opt/apps/montage_hub\n")
                return 1
            sub = getattr(args, "montage_sub", None) or "info"
            extra = getattr(args, "extra_args", []) or []
            cmd_args = [sys.executable, str(target), sub] + extra
            try:
                res = subprocess.run(cmd_args)
                auto_log_telemetry(f"Montage Hub: {sub}", skill="openmontage-builder")
                return res.returncode
            except (subprocess.SubprocessError, OSError) as e:
                sys.stderr.write(f"Montage execution failed: {e}\n")
                return 1

        return 1
