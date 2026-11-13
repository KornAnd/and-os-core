"""Knowledge Graph & Routing Subsystem (links, context, route, relate, asset, plan, find, doc, dep, pack).
Modular extraction from sys_cli.py following Clean Architecture (Uncle Bob).
Enforces Rule #13 (Think in Code Retrieval), Rule #19 (Vault Guard), and Rule #34 (Knowledge Graph Linkage).
"""

import os
import sys
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry, VAULT_ROOT


class KnowledgeGraphSubsystem(BaseSubsystem):
    name = "knowledge_graph"
    description = "Knowledge graph routing, linking, semantic relate, document conversion, and fast retrieval"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        # links
        p_links = subparsers.add_parser("links", help="The service of the audit and the auto repair of the links, the references and the symlinks in the and_os/")
        p_links.add_argument("--fix", action="store_true", help="Automatically repair the stale links")
        p_links.add_argument("--verbose", "-v", action="store_true", help="The detailed report over the broken links")
        p_links.add_argument("--json", action="store_true", help="The output of the report in the JSON format")

        # context
        p_ctx = subparsers.add_parser("context", help="The synchronization and the DB of all the CONTEXT.md files")
        p_ctx.add_argument("--sync", action="store_true", default=True, help="The launch of the full indexation of the contexts")

        # route
        p_route = subparsers.add_parser("route", help="The fast routing of the task to the needed CONTEXT.md")
        p_route.add_argument("query", type=str, help="The text of the task for the search of the suitable contexts")

        # relate
        p_relate = subparsers.add_parser("relate", help="The semantic search of the linked notes and the extracts (Smart Connections)")
        p_relate.add_argument("target", type=str, help="The path to the note or the file for the search of the linked documents")

        # asset
        p_asset = subparsers.add_parser("asset", help="The indexation of the non-MD assets (the media, the archives, the gigabytes of the files)")
        p_asset.add_argument("--sync", action="store_true", default=True, help="The launch of the full indexation of the assets")

        # plan
        p_plan = subparsers.add_parser("plan", help="The generation of the structured plan of the execution of the task (Post-Prompt Planner)")
        p_plan.add_argument("--task", required=True, help="The text or the description of the target task")
        p_plan.add_argument("--json", action="store_true", help="The output in the JSON format")

        # find
        p_find = subparsers.add_parser("find", help="The fast pinpoint search over the knowledge base (Think in Code Retrieval, the tokens economy)")
        p_find.add_argument("query", nargs="*", help="The search terms")
        p_find.add_argument("--category", "-c", help="The filter by the category")
        p_find.add_argument("--limit", "-l", type=int, default=4, help="The maximum of the results")
        p_find.add_argument("--json", action="store_true", help="The output in the JSON format")

        # doc
        p_doc = subparsers.add_parser("doc", help="The analysis and the conversion of the documents (MarkItDown, PDF Twin, OCR, Excel)")
        p_doc.add_argument("file", help="The path to the target file of the document")
        p_doc.add_argument("--ocr", action="store_true", help="The recognition of the text on the images (OCR)")
        p_doc.add_argument("--twin", action="store_true", help="The generation of the Markdown twin for the PDF")
        p_doc.add_argument("--json", action="store_true", help="The output in the JSON format")

        # dep
        p_dep = subparsers.add_parser("dep", help="The analysis of the informational links and the cascading auto update of the dependent files")
        p_dep.add_argument("--propagate", action="store_true", help="Perform the cascading update of the dependencies")
        p_dep.add_argument("--mermaid", action="store_true", help="Print the Mermaid code of the graph of the dependencies")
        p_dep.add_argument("--json", action="store_true", help="The output in the JSON format")

        # pack
        p_pack = subparsers.add_parser("pack", help="The build and the compression of the context by the domain")
        p_pack.add_argument("domain", help="The name of the domain or the path")
        p_pack.add_argument("--json", action="store_true", help="The output in the JSON")
        p_pack.add_argument("--code", action="store_true", help="The AST compression of the code file")

    @classmethod
    def execute(cls, args: Any) -> int:
        cmd = args.command

        if cmd == "links":
            flags = []
            if getattr(args, "fix", False):
                flags.append("--fix")
            if getattr(args, "verbose", False):
                flags.append("--verbose")
            if getattr(args, "json", False):
                flags.append("--json")
            res = run_script("link_guard.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Link guard audit", skill="sys.links")
            return res.get("returncode", 0)

        elif cmd == "context":
            res = run_script("context_router.py", [])
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Context DB sync", skill="sys.context")
            return res.get("returncode", 0)

        elif cmd == "route":
            res = run_script("context_router.py", ["route", args.query])
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Context routing", skill="sys.route")
            return res.get("returncode", 0)

        elif cmd == "relate":
            res = run_script("context_router.py", ["relate", args.target])
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Semantic relate: {args.target}", skill="sys.relate")
            return res.get("returncode", 0)

        elif cmd == "asset":
            flags = ["sync"] if getattr(args, "sync", False) else []
            res = run_script("asset_indexer.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Asset indexer sync", skill="sys.asset")
            return res.get("returncode", 0)

        elif cmd == "plan":
            flags = ["--task", args.task]
            if getattr(args, "json", False):
                flags.append("--json")
            res = run_script("post_prompt_planner.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Planner: {args.task}", skill="sys.plan")
            return res.get("returncode", 0)

        elif cmd == "find":
            flags = []
            if getattr(args, "category", None):
                flags.extend(["-c", args.category])
            if getattr(args, "limit", None):
                flags.extend(["-l", str(args.limit)])
            if getattr(args, "json", False):
                flags.append("--json")
            if getattr(args, "query", None):
                flags.extend(args.query)
            res = run_script("quick_find.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Quick knowledge search", skill="sys.find")
            return res.get("returncode", 0)

        elif cmd == "doc":
            flags = [args.file]
            if getattr(args, "json", False):
                flags.append("--json")
            target_script = "doc_analyze.py"
            if getattr(args, "ocr", False):
                target_script = "image_ocr.py"
            elif getattr(args, "twin", False):
                target_script = "pdf_twin_converter.py"
            elif args.file.endswith(".xlsx") or args.file.endswith(".xls"):
                target_script = "xl_analyze.py"
            res = run_script(target_script, flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Doc processing", skill="sys.doc")
            return res.get("returncode", 0)

        elif cmd == "dep":
            flags = []
            if getattr(args, "propagate", False):
                flags.append("--propagate")
            if getattr(args, "mermaid", False):
                flags.append("--mermaid")
            if getattr(args, "json", False):
                flags.append("--json")
            res = run_script("dependency_engine.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Dependency cascade update", skill="sys.dep")
            return res.get("returncode", 0)

        elif cmd == "pack":
            if getattr(args, "code", False):
                try:
                    from and_os.lib.core.code_ast_shrinker import shrink_file
                    print(shrink_file(args.domain))
                    auto_log_telemetry(f"AST Code shrink: {args.domain}", skill="sys.pack.code")
                    return 0
                except Exception as e:
                    print(f"Error shrinking code: {e}", file=sys.stderr)
                    return 1

            flags = [args.domain]
            if getattr(args, "json", False):
                flags.append("--json")
            res = run_script("context_bundler.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Context pack: {args.domain}", skill="sys.pack")
            return res.get("returncode", 0)

        return 1
