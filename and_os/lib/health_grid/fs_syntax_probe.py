"""
fs_syntax_probe.py — Ring 0: Filesystem, Syntax, Bytecode & Path Semantics.
Covers:
  - Artifact detection and corruption stripping ([[|]], CJK) [Vector 1]
  - YAML frontmatter validation and indentation [Vector 2]
  - Python script syntax compilation (and_os/bin, boot, sbin, opt) [Vector 9]
  - WebDAV/FS semantic naming standards and path cleanliness [Vector 14]
  - Duplicate and conflict copy protection (Rule #55) [Vector 8]
"""

import os
import re
import sys
import json
import glob
import tokenize
from typing import Dict, Any, List, Tuple
from and_os.lib.health_grid import BaseProbeResult

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".archive", ".vault_shadow", "vault_shadow", "backups", "scratch", "tmp", "var"}
IGNORE_FILES = {".DS_Store", "Icon\r", "Icon"}


class FSSyntaxProbe:
    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 0: FS & Syntax Probe", ring=0)
        
        # 1. Corruption markers [[|]] and CJK artifacts check
        bad_marker = chr(91) + chr(91) + chr(124) + chr(93) + chr(93)
        corrupted_files = []
        cjk_files = []
        cjk_pat = re.compile(r"[\u4e00-\u9fff]")

        # 2. YAML frontmatter (real parse; 1-space style demoted to warning)
        yaml_errors = 0
        yaml_style_warnings = 0
        fixed_yaml = 0

        # 3. WebDAV/FS semantic naming
        bad_chars = re.compile(r'[?*:|"<>\n\r]')
        naming_issues = []

        # 4. Duplicate and conflict copies (including localized copy suffix as unicode escape)
        conflict_pattern = re.compile(r"(\s\(\d+\)|\scopy|\s\u043a\u043e\u043f\u0438\u044f)\.[a-zA-Z0-9]+$", re.IGNORECASE)
        conflict_files = []

        for root, dirs, files in os.walk(vault_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".tmp.drive")]
            
            # Directory naming verification
            for d in dirs:
                if d.strip() != d or bad_chars.search(d):
                    naming_issues.append(('dir', os.path.join(root, d), d))

            for f in files:
                if f in IGNORE_FILES or f.startswith("Icon") or f.startswith(".tmp.drive"):
                    continue

                fpath = os.path.join(root, f)

                # File naming verification
                if f.strip() != f or bad_chars.search(f):
                    naming_issues.append(('file', fpath, f))

                # Conflict copies check (.md files only)
                if f.endswith(".md") and conflict_pattern.search(f):
                    conflict_files.append(fpath)

                if not f.endswith(".md"):
                    continue

                # Markdown content analysis
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as file:
                        c = file.read()

                    if bad_marker in c:
                        corrupted_files.append(os.path.relpath(fpath, vault_root))
                    if "Nero/work" in fpath and cjk_pat.search(c):
                        cjk_files.append(os.path.relpath(fpath, vault_root))

                    # YAML frontmatter: real parse via pyyaml (audit R2, WI-2.3).
                    # A parse failure is a hard error with the file path; the
                    # legacy 1-space indentation heuristic is demoted to a
                    # style warning (it is legal YAML, just non-idiomatic).
                    if c.startswith("---"):
                        parts = c.split("---", 2)
                        if len(parts) >= 3:
                            frontmatter = parts[1]
                            try:
                                import yaml
                                yaml.safe_load(frontmatter)
                            except yaml.YAMLError as yerr:
                                yaml_errors += 1
                                result.errors.append(
                                    f"Invalid YAML frontmatter in {os.path.relpath(fpath, vault_root)}: {str(yerr).splitlines()[0]}")
                            single_space_items = re.findall(r"\n - [^\s\-]", frontmatter)
                            if single_space_items:
                                yaml_style_warnings += len(single_space_items)
                                if fix:
                                    new_fm = re.sub(r"\n - ([^\s\-])", r"\n  - \1", frontmatter)
                                    new_content = "---" + new_fm + "---" + parts[2]
                                    try:
                                        with open(fpath, "w", encoding="utf-8") as fw:
                                             fw.write(new_content)
                                        fixed_yaml += 1
                                    except OSError as err:
                                        sys.stderr.write(f"[fs_syntax_probe] Notice writing {fpath}: {err}\n")
                except OSError as err:
                    sys.stderr.write(f"[fs_syntax_probe] Notice reading {fpath}: {err}\n")

        # 5. Python syntax compilation (and_os core + opt/apps + Pulsar space)
        py_files = []
        for sub in ["bin", "boot", "sbin", "lib"]:
            sub_p = os.path.join(vault_root, "and_os", sub)
            if os.path.exists(sub_p):
                for r, _, fs in os.walk(sub_p):
                    for f in fs:
                        if f.endswith(".py"):
                            py_files.append(os.path.join(r, f))

        opt_apps_dir = os.path.join(vault_root, "and_os", "opt", "apps")
        if os.path.exists(opt_apps_dir):
            for r, _, fs in os.walk(opt_apps_dir):
                for f in fs:
                    if f.endswith(".py"):
                        py_files.append(os.path.join(r, f))

        # Scan external Pulsar Space projects (Island 7)
        try:
            from and_os.lib.core.root_config import resolve_pulsar_root
            pulsar_root = resolve_pulsar_root() or os.path.expanduser("./pulsar")
        except Exception:
            pulsar_root = os.path.expanduser("./pulsar")
        pulsar_scripts_count = 0
        if os.path.exists(pulsar_root):
            for proj in os.listdir(pulsar_root):
                p = os.path.join(pulsar_root, proj)
                if os.path.isdir(p) and not proj.startswith("."):
                    for r, dirs, fs in os.walk(p):
                        dirs[:] = [d for d in dirs if d not in [".git", "venv", "__pycache__", "node_modules", ".space"]]
                        for f in fs:
                            if f.endswith(".py"):
                                py_files.append(os.path.join(r, f))
                                pulsar_scripts_count += 1

        syntax_errors = []
        for pf in py_files:
            try:
                with tokenize.open(pf) as source_file:
                    compile(source_file.read(), pf, "exec")
            except (SyntaxError, UnicodeError, OSError) as e:
                syntax_errors.append((os.path.relpath(pf, vault_root), str(e)))

        # 5.1 Toolchain Parity & Hermetic .venv Gate (Rule #68)
        toolchain_errors = []
        try:
            from and_os.lib.core.toolchain import ToolchainManager
            tm = ToolchainManager(vault_root)
            tc_res = tm.check_parity()
            if not tc_res["passed"]:
                for err in tc_res["errors"]:
                    toolchain_errors.append(err)
        except (OSError, ValueError, ImportError) as e:
            toolchain_errors.append(f"Toolchain probe error: {e}")

        # 5.2 Hermetic FHS Boundary (Rule #50): the source tree must be free
        # of binary contamination. Golden-interpreter bytecode caches
        # (cpython-<golden major.minor> from toolchain.lock.json) are
        # documented transient runtime state and tolerated; any other
        # interpreter's bytecode or a shared object outside and_os/var is an
        # ERROR (drift vector, cf. cpython-315 pyc found in audit R2 P1).
        golden_tag = None
        toolchain_lock_path = os.path.join(vault_root, "and_os", "etc", "toolchain.lock.json")
        if os.path.exists(toolchain_lock_path):
            try:
                with open(toolchain_lock_path, "r", encoding="utf-8") as tlf:
                    tver = json.load(tlf).get("golden_stack", {}).get("python", {}).get("target_version", "")
                vparts = tver.split(".")
                if len(vparts) >= 2:
                    golden_tag = f"cpython-{vparts[0]}{vparts[1]}"
            except (OSError, json.JSONDecodeError, ValueError) as terr:
                sys.stderr.write(f"[fs_syntax_probe] Notice reading toolchain lock: {terr}\n")

        binary_contamination = []
        transient_caches = 0
        pyc_tag_re = re.compile(r"\.(cpython-\d+)\.pyc$")
        and_os_root = os.path.join(vault_root, "and_os")
        if os.path.exists(and_os_root):
            for broot, bdirs, bfiles in os.walk(and_os_root):
                bdirs[:] = [d for d in bdirs if d not in ("var", ".venv", "venv")]
                in_pycache = os.path.basename(broot) == "__pycache__"
                violating_here = []
                for bf in bfiles:
                    bfp = os.path.join(broot, bf)
                    rel_bf = os.path.relpath(bfp, vault_root)
                    if bf.endswith((".so", ".pyd")):
                        violating_here.append(rel_bf)
                    elif bf.endswith(".pyc"):
                        tag_match = pyc_tag_re.search(bf)
                        if golden_tag is None or (tag_match and tag_match.group(1) != golden_tag):
                            violating_here.append(rel_bf)
                if in_pycache and not violating_here:
                    transient_caches += 1
                for rel_bf in violating_here:
                    binary_contamination.append(rel_bf)
                    if fix:
                        try:
                            os.remove(rel_bf if os.path.isabs(rel_bf) else os.path.join(vault_root, rel_bf))
                            if in_pycache and not os.listdir(os.path.dirname(os.path.join(vault_root, rel_bf))):
                                import shutil
                                shutil.rmtree(os.path.dirname(os.path.join(vault_root, rel_bf)))
                        except OSError as err:
                            sys.stderr.write(f"[fs_syntax_probe] Notice removing {rel_bf}: {err}\n")

        # Ring 0 summary
        total_issues = len(corrupted_files) + len(cjk_files) + (yaml_errors if not fix else 0) + len(naming_issues) + len(conflict_files) + len(syntax_errors) + len(toolchain_errors) + (0 if fix else len(binary_contamination))
        result.issues_count = total_issues
        result.passed = (total_issues == 0)

        result.details = {
            "corrupted_files": len(corrupted_files),
            "cjk_files": len(cjk_files),
            "yaml_errors": yaml_errors,
            "yaml_style_warnings": yaml_style_warnings,
            "naming_issues": len(naming_issues),
            "conflict_files": len(conflict_files),
            "python_scripts_total": len(py_files),
            "pulsar_scripts_scanned": pulsar_scripts_count,
            "syntax_errors": len(syntax_errors),
            "binary_contamination": len(binary_contamination) if not fix else 0,
            "transient_bytecode_caches": transient_caches
        }

        # 6. Hermetic Workspace Boundary Check (Rule #7 & Rule #54)
        # Block rogue pipeline scripts leaking into ~/Downloads or ~/Desktop
        stray_executables = []
        user_home = os.path.expanduser("~")
        for check_dir in [os.path.join(user_home, "Downloads"), os.path.join(user_home, "Desktop")]:
            if os.path.exists(check_dir):
                for p_sub in ["pipeline_3d", "scripts"]:
                    target_p = os.path.join(check_dir, p_sub)
                    if os.path.exists(target_p):
                        stray_executables.append(target_p)

        # 6. Immutable Archives & Git Containment Audit (Zero-Trust UNIX Gate)
        archive_dir = os.path.join(vault_root, 'Book/.archive_versions')
        if os.path.exists(archive_dir):
            import stat
            st = os.stat(archive_dir)
            # Check UF_IMMUTABLE flag (0x2) on macOS
            has_uchg = bool(st.st_flags & 0x2) if hasattr(st, 'st_flags') else True
            if not has_uchg:
                result.errors.append("Security Gate Breach: 'Book/.archive_versions' is missing hardware uchg immutable flag!")

        # 7. Sovereign Vault Boundary Audit (Rule #67: Zero Git tracking in Vault)
        git_dir = os.path.join(vault_root, '.git')
        if os.path.exists(git_dir):
            import subprocess
            try:
                tracked_files = subprocess.check_output(
                    ['git', 'ls-files'],
                    cwd=vault_root,
                    stderr=subprocess.DEVNULL
                ).decode('utf-8').strip()
                if tracked_files:
                    result.errors.append(f"Security Gate Breach (Rule #67): Obsidian Vault has active Git tracking ({len(tracked_files.splitlines())} files). Core & vault must remain untracked.")
            except (subprocess.SubprocessError, OSError) as err:
                sys.stderr.write(f"[fs_syntax_probe] Git tracking check notice: {err}\n")

        # 8. Git Binary Interceptor Integrity (Rule #67)
        git_shim = os.path.join(vault_root, 'and_os/bin/git')
        if not (os.path.exists(git_shim) and os.access(git_shim, os.X_OK)):
            result.errors.append("Security Gate Breach: Hard binary interceptor 'and_os/bin/git' is missing or not executable!")

        if stray_executables:
            result.errors.append(f"Hermetic Boundary Breach: stray pipeline scripts found in user directories: {stray_executables}")
        if binary_contamination and not fix:
            shown = ", ".join(sorted(binary_contamination)[:10])
            result.errors.append(
                f"Hermetic FHS Breach (Rule #50): binary contamination outside and_os/var "
                f"({len(binary_contamination)} items): {shown} — run with --fix to clean")
        if yaml_style_warnings and not fix:
            result.warnings.append(f"YAML frontmatter style: {yaml_style_warnings} single-space list indent(s) (legal YAML, non-idiomatic; --fix normalizes)")

        if corrupted_files:
            result.errors.append(f"Corrupted files with [[|]] artifacts: {len(corrupted_files)}")
        if syntax_errors:
            for pf, err in syntax_errors:
                result.errors.append(f"Syntax error in {pf}: {err}")
        if conflict_files:
            result.warnings.append(f"Conflict file copies: {len(conflict_files)}")
        if naming_issues:
            result.warnings.append(f"Path semantic violations: {len(naming_issues)}")

        return result
