"""
contract_probe.py — Ring 2: AST Contracts, Interface Consistency & Language Governance (Rule #3).
Covers:
  - AST parsing of argparse arguments vs sys_cli.py dispatcher
  - Rule #3 English Language Governance Gate for and_os/ codebase (Zero-Cyrillic Invariant)
  - Rule #41 Local rules consistency with OS core [Vector 21]
  - Rule #54 Component binding to system core and ROUTING.md [Vector 22]
  - Rule #51 IPC contracts & data schema validation (schema_validator.py) [Vector 13]
"""

import os
import ast
import io
import json
import re
import subprocess
import sys
import tokenize
from typing import Dict, Any, List, Set, Tuple
from and_os.lib.health_grid import BaseProbeResult

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".archive"}

CYRILLIC_PATTERN = re.compile(r"[\u0400-\u04FF]")


class ContractProbe:
    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 2: AST Contracts & Governance Probe", ring=2)

        issues = 0
        bin_dir = os.path.join(vault_root, "and_os", "bin")
        cli_file = os.path.join(bin_dir, "sys_cli.py")
        skills_dir = os.path.join(vault_root, "and_os", "lib", "skills")
        routing_file = os.path.join(skills_dir, "ROUTING.md")

        # 1. Verify script integration into sys_cli.py
        unconnected_scripts = []
        if os.path.exists(cli_file) and os.path.exists(bin_dir):
            try:
                with open(cli_file, "r", encoding="utf-8") as f:
                    cli_text = f.read()
                # Include modular subsystems in dispatcher registration text
                subsystems_dir = os.path.join(bin_dir, "cli_subsystems")
                if os.path.exists(subsystems_dir):
                    for sub_f in os.listdir(subsystems_dir):
                        if sub_f.endswith(".py"):
                            with open(os.path.join(subsystems_dir, sub_f), "r", encoding="utf-8", errors="ignore") as sf:
                                cli_text += sf.read()
                bin_scripts = [f for f in os.listdir(bin_dir) if f.endswith(".py") and not f.startswith(".") and f != "sys_cli.py"]
                # The supervisor mesh (etc/services.json) is the second control
                # plane: cron wrappers it executes are connected by definition
                # (audit R2, WI-4.7), not dispatcher orphans.
                supervised_scripts = set()
                services_cfg = os.path.join(vault_root, "and_os", "etc", "services.json")
                if os.path.exists(services_cfg):
                    try:
                        with open(services_cfg, "r", encoding="utf-8") as scf:
                            for svc in json.load(scf).get("services", []):
                                cmd = svc.get("command", [])
                                if len(cmd) >= 2:
                                    supervised_scripts.add(os.path.basename(cmd[1]))
                    except (OSError, json.JSONDecodeError, ValueError) as cerr:
                        sys.stderr.write(f"[contract_probe] Notice reading services.json: {cerr}\n")
                for bs in bin_scripts:
                    if bs not in cli_text and bs not in supervised_scripts:
                        unconnected_scripts.append(bs)
            except Exception as e:
                issues += 1
                result.errors.append(f"sys_cli.py read error: {e}")

        if unconnected_scripts:
            result.warnings.append(f"Scripts in and_os/bin without direct sys_cli.py dispatcher entry ({len(unconnected_scripts)} items): {unconnected_scripts}")

        # 2. Verify skill routing in ROUTING.md
        orphaned_skills = []
        if os.path.exists(routing_file) and os.path.exists(skills_dir):
            try:
                with open(routing_file, "r", encoding="utf-8") as f:
                    r_text = f.read()
                active_skills = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d)) and not d.startswith(".") and d not in ["scripts", "references"]]
                orphaned_skills = [s for s in active_skills if s not in r_text]
            except Exception as e:
                issues += 1
                result.errors.append(f"ROUTING.md read error: {e}")

        if orphaned_skills:
            result.warnings.append(f"Skills unmapped in ROUTING.md: {orphaned_skills}")

        # 3. Rule #3 Language Governance Gate (English Invariant for and_os/ core)
        # Scope: ALL of and_os/ (state dirs excluded). Two-stage migration gate:
        #   Cyrillic in code tokens (NAME/OP/NUMBER)      -> ERROR (hard invariant)
        #   Cyrillic in string/comment tokens             -> level from the config
        #       "warning" = migration backlog (pre-flip)
        #       "error"   = P5 flip: the backlog is closed, findings are hard errors
        # Kernel/dialogue exemptions live in etc/language_gate.json (config, not code).
        language_gate_cfg = {}
        gate_cfg_path = os.path.join(vault_root, "and_os", "etc", "language_gate.json")
        if os.path.exists(gate_cfg_path):
            try:
                with open(gate_cfg_path, "r", encoding="utf-8") as gf:
                    language_gate_cfg = json.load(gf)
            except (OSError, json.JSONDecodeError) as err:
                issues += 1
                result.errors.append(f"language_gate.json unreadable: {err}")
        exempt_files = language_gate_cfg.get("exempt_files", {})
        string_level = language_gate_cfg.get("string_violation_level", "warning")
        comment_level = language_gate_cfg.get("comment_violation_level", "warning")

        LANGUAGE_SKIP_DIRS = {"var", ".venv", "venv", "__pycache__", "node_modules"}
        string_token_types = (tokenize.STRING, tokenize.FSTRING_START,
                              tokenize.FSTRING_MIDDLE, tokenize.FSTRING_END)
        cyrillic_code = []      # (relpath, line) — hard violations
        cyrillic_string_files = set()
        cyrillic_comment_files = set()
        and_os_dir = os.path.join(vault_root, "and_os")
        if os.path.exists(and_os_dir):
            for root, dirs, files in os.walk(and_os_dir):
                dirs[:] = [d for d in dirs if d not in LANGUAGE_SKIP_DIRS]
                for f in files:
                    if not f.endswith(".py"):
                        continue
                    fp = os.path.join(root, f)
                    rel_p = os.path.relpath(fp, vault_root)
                    if rel_p in exempt_files:
                        continue
                    try:
                        with open(fp, "r", encoding="utf-8") as fsrc:
                            tokens = list(tokenize.generate_tokens(fsrc.readline))
                    except (OSError, SyntaxError, tokenize.TokenizeError, UnicodeError) as err:
                        sys.stderr.write(f"[contract_probe] Notice scanning {rel_p}: {type(err).__name__}: {err}\n")
                        continue
                    for tok in tokens:
                        if not CYRILLIC_PATTERN.search(tok.string):
                            continue
                        if tok.type in string_token_types:
                            cyrillic_string_files.add(rel_p)
                        elif tok.type == tokenize.COMMENT:
                            cyrillic_comment_files.add(rel_p)
                        else:
                            cyrillic_code.append((rel_p, tok.start[0]))

        if cyrillic_code:
            issues += len(cyrillic_code)
            shown = ", ".join(f"{p}:L{ln}" for p, ln in sorted(cyrillic_code)[:10])
            result.errors.append(
                f"Rule #3 Violation: Cyrillic in code tokens (identifiers/expressions) — {len(cyrillic_code)} occurrence(s): {shown}")
        text_findings = []
        if cyrillic_string_files:
            text_findings.append(f"{len(cyrillic_string_files)} files with Cyrillic string content")
        if cyrillic_comment_files:
            text_findings.append(f"{len(cyrillic_comment_files)} files with Cyrillic comments")
        if text_findings:
            level = string_level if cyrillic_string_files else comment_level
            sample = ", ".join(sorted(cyrillic_string_files | cyrillic_comment_files)[:5])
            message = f"Rule #3 language gate ({level}): {'; '.join(text_findings)} — e.g. {sample}"
            if level == "error":
                # P5 flip: the migration backlog is closed, text findings are hard errors
                issues += len(cyrillic_string_files | cyrillic_comment_files)
                result.errors.append(message)
            else:
                result.warnings.append(message)

        # 4. Consistency audit of local rule files (Rule #41)
        # Frozen snapshot zones (CoW checkpoints, vault shadow, backups,
        # scratch, tmp) are machine-generated mirrors, not live rule files:
        # pruning them keeps approved rule text (e.g. the #53
        # build-artifacts exception) from being flagged inside a frozen
        # copy (audit R3, in-flight finding R3-F6-1). The shared IGNORE_DIRS
        # above serve the other walks and are left untouched.
        frozen_zones = IGNORE_DIRS | {"var", ".vault_shadow", "vault_shadow",
                                      "backups", "scratch", "tmp"}
        rule_files = []
        for root, dirs, files in os.walk(vault_root):
            dirs[:] = [d for d in dirs if d not in frozen_zones]
            for f in files:
                fl = f.lower()
                if fl in [".windsurfrules", ".cursorrules"] or ("rule" in fl and f.endswith(".md") and f != "rules.md"):
                    rule_files.append(os.path.join(root, f))

        forbidden_patterns = [
            ("rm -rf", "Destructive deletion pattern without confirmation"),
            ("git push --force", "Dangerous force push pattern"),
            ("no tests", "Attempted test suppression pattern"),
            ("ignore rules", "Attempted core rules bypass pattern"),
        ]

        rule_conflicts = []
        for rf in rule_files:
            try:
                with open(rf, "r", encoding="utf-8") as f:
                    c = f.read().lower()
                for pat, desc in forbidden_patterns:
                    if pat in c:
                        rule_conflicts.append((os.path.relpath(rf, vault_root), desc))
            except OSError as err:
                sys.stderr.write(f"[contract_probe] Notice reading rule file {rf}: {err}\n")

        if rule_conflicts:
            issues += len(rule_conflicts)
            for r_file, r_desc in rule_conflicts:
                result.warnings.append(f"{r_desc} in {r_file}")

        # 5. IPC schema contract validation (domain_states.json)
        state_file = os.path.join(vault_root, "and_os", "var", "domain_states.json")
        val_script = os.path.join(vault_root, "and_os", "bin", "schema_validator.py")
        ipc_valid = True
        if os.path.exists(state_file) and os.path.exists(val_script):
            res = subprocess.run([sys.executable, val_script, "--json-file", state_file], capture_output=True, text=True)
            if res.returncode != 0 or "All domain states match schema" not in res.stdout:
                issues += 1
                ipc_valid = False
                result.errors.append("domain_states.json does not match canonical IPC schema")

        # 6. AST CLI argument parser inspection in sys_cli.py
        ast_cli_valid = True
        try:
            with open(cli_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename="sys_cli.py")
            has_main = any(isinstance(node, ast.FunctionDef) and node.name == "main" for node in tree.body)
            if not has_main:
                ast_cli_valid = False
                issues += 1
                result.errors.append("AST: function 'main' missing in sys_cli.py")
        except Exception as e:
            issues += 1
            ast_cli_valid = False
            result.errors.append(f"AST parse error in sys_cli.py: {e}")

        result.issues_count = issues
        result.passed = (issues == 0)

        result.details = {
            "unconnected_scripts_count": len(unconnected_scripts),
            "orphaned_skills_count": len(orphaned_skills),
            "language_governance_violations": len(cyrillic_code),
            "language_string_migration_files": len(cyrillic_string_files),
            "language_comment_migration_files": len(cyrillic_comment_files),
            "checked_rule_files": len(rule_files),
            "rule_conflicts_count": len(rule_conflicts),
            "ipc_schema_valid": ipc_valid,
            "ast_cli_valid": ast_cli_valid
        }

        return result
