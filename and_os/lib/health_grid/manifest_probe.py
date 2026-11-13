"""
manifest_probe.py — Ring 3: Manifest Synchronization, Security, Air-Gap & DEV_PROTOCOL.
Covers:
  - Core manifests synchronization (SYSTEM.md vs system.json vs REGISTRY vs README) [Vector 7]
  - Information security, Air-Gap and Zero-Leak secrets guard [Vector 23]
  - Engineering development protocol and code hygiene (DEV_PROTOCOL.md, bare except) [Vector 24]
  - Hermetic paths and code hygiene (Rule #42) [Vector 15]
"""

import os
import sys
import re
import json
import glob
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple
from and_os.lib.health_grid import BaseProbeResult
from and_os.lib.i1_zones import load_i1_zones

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".archive", ".venv", "venv", "var"}
IGNORE_FILES = {".DS_Store", "Icon\r", "Icon"}


def check_version_consistency(vault_root: str, canonical_version: str) -> List[str]:
    """VersionConsistency check (audit R3, F4): the canonical version from
    and_os/etc/system.json must agree with every current-version projection
    point. Returns a list of error strings (empty = consistent).

    Points covered here (RELEASE_LEDGER activeVersion and the SYSTEM.md
    identity line are verified by the existing SemVer block in run()):
      P1 canonical version is a SemVer triple
      P2 rules_fast_index.json `version`
      P3 toolchain.lock.json `system` ("AnD os v<major.minor.patch>")
      P4 export_template/SECURITY.md supported-matrix top line
    Missing optional files are skipped (they are checked by other gates).
    """
    errors: List[str] = []
    if not re.fullmatch(r"\d+\.\d+\.\d+", canonical_version or ""):
        errors.append(f"canonical version '{canonical_version}' is not a SemVer triple")
        return errors
    major_minor = ".".join(canonical_version.split(".")[:2])

    fast_index = os.path.join(vault_root, "and_os", "etc", "rules_fast_index.json")
    if os.path.exists(fast_index):
        try:
            with open(fast_index, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if data.get("version") != canonical_version:
                errors.append(
                    f"VersionConsistency: rules_fast_index.json version ({data.get('version')}) "
                    f"!= canonical ({canonical_version}) — recompile the index (sys_cli rules compile)")
        except (OSError, ValueError) as err:
            errors.append(f"VersionConsistency: rules_fast_index.json unreadable: {err}")

    toolchain_lock = os.path.join(vault_root, "and_os", "etc", "toolchain.lock.json")
    if os.path.exists(toolchain_lock):
        try:
            with open(toolchain_lock, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if data.get("system") != f"AnD os v{canonical_version}":
                errors.append(
                    f"VersionConsistency: toolchain.lock.json system ({data.get('system')}) "
                    f"!= 'AnD os v{canonical_version}'")
        except (OSError, ValueError) as err:
            errors.append(f"VersionConsistency: toolchain.lock.json unreadable: {err}")

    security_md = os.path.join(vault_root, "and_os", "etc", "export_template", "SECURITY.md")
    if os.path.exists(security_md):
        try:
            with open(security_md, "r", encoding="utf-8", errors="ignore") as handle:
                content = handle.read()
            if f"| {major_minor}.x" not in content:
                errors.append(
                    f"VersionConsistency: SECURITY.md export template has no supported "
                    f"'{major_minor}.x' matrix line (public promise drift)")
        except OSError as err:
            errors.append(f"VersionConsistency: SECURITY.md unreadable: {err}")
    return errors


BANNER_RE = re.compile(r"AnD os v(\d+\.\d+(?:\.\d+)?)")
BANNER_HEADER_CHARS = 2000
# I-1 kernel zones (audit R4, P7/P7-2/P11): the historical banners are
# accounted for only and never touched by the fix or the gate. The zone
# declaration is the SSoT file and_os/etc/i1_kernel_zones.json, loaded via
# and_os.lib.i1_zones (single copy; P11 removed the per-consumer
# duplication that caused the P7/P7-2 incidents).
BANNER_SKIP_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd",
                    ".smart-env", ".git", "node_modules", ".archive", "var", ".venv",
                    "venv", "checkpoints", "__pycache__", "vault_shadow", "backups"}


def scan_stale_banners(vault_root: str, canonical_version: str) -> List[str]:
    """Stale system banner scan (audit R4, P7, R4-VER-1; advisory).

    Every .py header (the first 2000 chars) that names the system version
    ("AnD os v...") must carry the canonical version or its major.minor.
    Returns "rel:path:L<line> v<stale>" strings (empty = clean). Advisory
    by contract: the caller reports findings as warnings WITHOUT an
    issues_count increment (R3-F6-1). I-1 kernel zones are exempt (SSoT
    file and_os/etc/i1_kernel_zones.json via and_os.lib.i1_zones; a
    missing/invalid SSoT degrades to the built-in defaults with a
    stderr warning instead of flipping the ring).
    """
    if not re.fullmatch(r"\d+\.\d+\.\d+", canonical_version or ""):
        return []
    i1_zones, i1_files, i1_source = load_i1_zones(vault_root)
    if i1_source != "ssoT":
        sys.stderr.write("[manifest_probe] I-1 zones SSoT unavailable "
                         "(%s); using built-in defaults\n" % i1_source)
    major_minor = ".".join(canonical_version.split(".")[:2])
    stale: List[str] = []
    base = os.path.join(vault_root, "and_os")
    if not os.path.isdir(base):
        return stale
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in BANNER_SKIP_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, vault_root).replace(os.sep, "/")
            if rel in i1_files or any(rel.startswith(z) for z in i1_zones):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                    head = handle.read(BANNER_HEADER_CHARS)
            except OSError as err:
                sys.stderr.write(f"[manifest_probe] Banner scan warning {path}: {err}\n")
                continue
            for m in BANNER_RE.finditer(head):
                ver = m.group(1)
                if ver not in (canonical_version, major_minor):
                    line = head[:m.start()].count("\n") + 1
                    stale.append(f"{rel}:L{line} v{ver}")
    return stale


def parse_skill_registry_table(content: str, disk_skills: set) -> Tuple[Set[str], List[str]]:
    """Parses the SYSTEM.md §3 skill registry table and checks it against disk
    (audit R3, F4; closes S-02 — the registry table was outside every probe).

    Row format: | Category (N) | skill-a, skill-b, ... |
    Checks: per-row declared count N == actual name count; table names exist
    on disk; every disk skill appears in the table. Returns (names, errors).
    A missing table yields (empty set, no errors) — section presence is a
    separate manifest concern.
    """
    row_re = re.compile(r"^\|\s*(.+?)\s*\((\d+)\)\s*\|\s*(.+?)\s*\|\s*$", re.MULTILINE)
    rows = row_re.findall(content)
    if not rows:
        return set(), []
    names: Set[str] = set()
    errors: List[str] = []
    for category, declared, raw_names in rows:
        row_names = [n.strip() for n in raw_names.split(",") if n.strip()]
        if len(row_names) != int(declared):
            errors.append(
                f"Registry table: category '{category}' declares {declared} skills "
                f"but lists {len(row_names)}")
        names.update(row_names)
    missing_on_disk = sorted(names - disk_skills)
    if missing_on_disk:
        errors.append(f"Registry table: skills absent on disk: {missing_on_disk}")
    missing_in_table = sorted(disk_skills - names)
    if missing_in_table:
        errors.append(f"Registry table: disk skills missing from the table: {missing_in_table}")
    return names, errors


class ManifestProbe:
    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 3: Manifests & Security Governance Probe", ring=3)
        issues = 0

        # 1. Manifest synchronization
        sys_md = os.path.join(vault_root, "SYSTEM.md")
        sys_json = os.path.join(vault_root, "system.json")
        skills_reg = os.path.join(vault_root, "and_os/lib/skills/REGISTRY.md")
        skills_dir = os.path.join(vault_root, "and_os/lib/skills")
        toolchain_lock = os.path.join(vault_root, "and_os/etc/toolchain.lock.json")
        req_lock = os.path.join(vault_root, "and_os/etc/requirements.lock")

        if not os.path.exists(sys_md) or not os.path.exists(sys_json) or not os.path.exists(skills_reg):
            issues += 1
            result.errors.append("Key manifest files missing (SYSTEM.md / system.json / REGISTRY.md)")

        if not os.path.exists(toolchain_lock) or not os.path.exists(req_lock):
            issues += 1
            result.errors.append("Toolchain lock manifests missing (toolchain.lock.json / requirements.lock)")

        actual_skills_count = len([
            d for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d)) and os.path.exists(os.path.join(skills_dir, d, "SKILL.md"))
        ])

        manifest_checks = [
            ("AGENTS.md", os.path.join(vault_root, "AGENTS.md"), rf"\u0440\u0435\u0435\u0441\u0442\u0440 {actual_skills_count} \u0441\u043a\u0438\u043b\u043b\u043e\u0432"),
            ("SYSTEM_MAP.md", os.path.join(vault_root, "and_os/etc/SYSTEM_MAP.md"), rf"{actual_skills_count} [Aa]ctive [Ss]kills"),
            ("SYSTEM_ARCHITECTURE_GRAPH.md", os.path.join(vault_root, "and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md"), rf"{actual_skills_count} Active Skills"),
            ("skills/README.md", os.path.join(vault_root, "and_os/lib/skills/README.md"), rf"{actual_skills_count} active skills")
        ]

        sync_mismatches = []
        for name, m_path, pat in manifest_checks:
            if os.path.exists(m_path):
                with open(m_path, "r", encoding="utf-8") as mf:
                    mc = mf.read()
                if not re.search(pat, mc):
                    sync_mismatches.append(f"{name} (expected: '{actual_skills_count}')")
                    issues += 1

        if sync_mismatches:
            result.warnings.append(f"Skill counts desynchronized across manifests: {', '.join(sync_mismatches)}")

        # 1.1 Single SemVer invariant (Rule #55 & #65)
        version_consistency_ok = None
        canonical_version = ""
        try:
            import json
            with open(sys_json, "r", encoding="utf-8") as jf:
                s_data = json.load(jf)
            canonical_version = s_data.get("version", "")
            
            # Verify RELEASE_LEDGER.json synchronization
            ledger_path = os.path.join(vault_root, "and_os/etc/RELEASE_LEDGER.json")
            if os.path.exists(ledger_path):
                with open(ledger_path, "r", encoding="utf-8") as lf:
                    ledger_data = json.load(lf)
                ledger_version = ledger_data.get("activeVersion", "")
                if ledger_version != canonical_version:
                    issues += 1
                    result.errors.append(f"system.json version ({canonical_version}) does not match RELEASE_LEDGER.json ({ledger_version})")
            else:
                issues += 1
                result.errors.append("Missing authoritative and_os/etc/RELEASE_LEDGER.json")

            # Verify boot_engine.py (Single Source of Truth)
            boot_path = os.path.join(vault_root, "and_os/boot/boot_engine.py")
            if os.path.exists(boot_path):
                with open(boot_path, "r", encoding="utf-8") as bf:
                    bc = bf.read()
                if "system.json" not in bc:
                    issues += 1
                    result.errors.append("boot_engine.py does not reference canonical system.json")

            # Verify SYSTEM.md
            with open(sys_md, "r", encoding="utf-8") as sf:
                sc = sf.read()
            major_minor = ".".join(canonical_version.split(".")[:2])
            if f"AnD os v{major_minor}" not in sc and f"AnD os v{canonical_version}" not in sc:
                issues += 1
                result.errors.append(f"SYSTEM.md out of sync with system.json (version {canonical_version})")

            # 1.1.d VersionConsistency across projection points (audit R3, F4):
            # fast index, toolchain lock, SECURITY export matrix.
            vc_errors = check_version_consistency(vault_root, canonical_version)
            version_consistency_ok = not vc_errors
            if vc_errors:
                issues += len(vc_errors)
                result.errors.extend(vc_errors)

            # 1.1.b Evolutionary Release Gate (Anti-Stagnation & Minor Version Bump Enforcement)
            # If the codebase has active unreleased architecture work or the ledger date is stale while activeVersion is bumped, verify audit freshness
            if os.path.exists(ledger_path):
                today_str = datetime.now().strftime("%Y-%m-%d")
                latest_release = ledger_data.get("releases", [{}])[0]
                latest_ver = latest_release.get("version", "")
                if latest_ver != canonical_version:
                    issues += 1
                    result.errors.append(
                        f"Evolution Gate: activeVersion ({canonical_version}) not documented as latest entry in releases list ({latest_ver})"
                    )

            # 1.1.c SQLite Release Ledger & Version Sentinel Check (Rule #55)
            try:
                from and_os.lib.core.release_ledger import verify_release_parity
                ok_parity, parity_msg = verify_release_parity()
                if not ok_parity:
                    issues += 1
                    result.errors.append(f"SQLite Release Ledger Parity Error: {parity_msg}")
            except Exception as le:
                issues += 1
                result.errors.append(f"SQLite Release Ledger Error: {le}")
        except Exception as e:
            issues += 1
            result.errors.append(f"SemVer manifest verification error: {e}")

        # 1.1.e Stale system banner advisory (audit R4, P7, R4-VER-1):
        # .py header banners naming a non-canonical system version.
        # Advisory only — warnings + details, no issues_count increment (R3-F6-1).
        stale_banners = scan_stale_banners(vault_root, canonical_version)
        if stale_banners:
            result.warnings.append(
                f"Stale system version banner advisory (no issues_count increment): "
                f"{len(stale_banners)} site(s), e.g. {stale_banners[:3]}")

        # 1.2 Zero-Hardcode & Modular API Gate (Rule #52)
        hardcode_violations = []
        boot_engine_file = os.path.join(vault_root, "and_os/boot/boot_engine.py")
        if os.path.exists(boot_engine_file):
            with open(boot_engine_file, "r", encoding="utf-8") as bef:
                be_content = bef.read()
            if '"version": "8.' in be_content:
                hardcode_violations.append("and_os/boot/boot_engine.py (hardcoded version literal)")

        if hardcode_violations:
            issues += len(hardcode_violations)
            result.errors.append(f"Rule #52 (Zero-Hardcode Gate): hardcoded constants detected: {', '.join(hardcode_violations)}")

        # 1.2 Root Manifest Projection Integrity (audit R2, WI-2.4; N-001 guard).
        # The vault-root system.json must be a thin generated projection of the
        # canonical and_os/etc/system.json: sha256 chain + mirrored scalar
        # parity + zero duplicated content blocks.
        projection_checked = False
        canonical_path = os.path.join(vault_root, "and_os", "etc", "system.json")
        if os.path.exists(sys_json) and os.path.exists(canonical_path):
            try:
                import hashlib
                with open(sys_json, "r", encoding="utf-8") as rf:
                    root_manifest = json.load(rf)
                with open(canonical_path, "r", encoding="utf-8") as cf:
                    canonical_manifest = json.load(cf)
                if root_manifest.get("root_marker") is True:
                    projection_checked = True
                    def _sha256(path: str) -> str:
                        digest = hashlib.sha256()
                        with open(path, "rb") as handle:
                            for chunk in iter(lambda: handle.read(65536), b""):
                                digest.update(chunk)
                        return digest.hexdigest()
                    if root_manifest.get("canonical_sha256") != _sha256(canonical_path):
                        issues += 1
                        result.errors.append(
                            "Root manifest projection stale: canonical_sha256 does not match "
                            "and_os/etc/system.json — re-run 'sys_cli manifest project-root'")
                    for key in ("manifestVersion", "name", "version", "status", "rulesCount"):
                        if key in canonical_manifest and root_manifest.get(key) != canonical_manifest[key]:
                            issues += 1
                            result.errors.append(
                                f"Root manifest projection drifted on '{key}': "
                                f"root={root_manifest.get(key)!r} canonical={canonical_manifest[key]!r}")
                for content_key in ("rules", "skills", "modules"):
                    if content_key in root_manifest:
                        issues += 1
                        result.errors.append(
                            f"Manifest uniqueness breach: root system.json duplicates canonical "
                            f"content block '{content_key}' (drift vector; use projection only)")
            except (OSError, json.JSONDecodeError) as perr:
                issues += 1
                result.errors.append(f"Root manifest projection check failed: {perr}")

        # 1.3 Projects Registry Freshness (audit R2, WI-2.4): generated
        # projection of live project state; staleness beyond 30 days means
        # the registry no longer reflects the islands.
        registry_path = os.path.join(vault_root, "and_os", "srv", "projects_registry.json")
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as regf:
                    registry = json.load(regf)
                updated = datetime.fromisoformat(registry.get("updated", "1970-01-01"))
                age_days = (datetime.now() - updated).days
                if age_days > 30:
                    issues += 1
                    result.errors.append(
                        f"Projects registry stale: updated {registry.get('updated')} "
                        f"({age_days} days ago) — re-run 'sys_cli registry sync'")
            except (OSError, json.JSONDecodeError, ValueError) as rerr:
                issues += 1
                result.errors.append(f"Projects registry check failed: {rerr}")

        # 1.4 Skill registry table vs disk (audit R3, F4; closes S-02 — the
        # registry table was outside every probe).
        registry_table_skills = 0
        registry_table_errors: List[str] = []
        if os.path.exists(sys_md) and os.path.isdir(skills_dir):
            with open(sys_md, "r", encoding="utf-8") as sf:
                registry_content = sf.read()
            disk_skills = {
                d for d in os.listdir(skills_dir)
                if os.path.isdir(os.path.join(skills_dir, d))
                and os.path.exists(os.path.join(skills_dir, d, "SKILL.md"))
            }
            registry_table_skills, registry_table_errors = parse_skill_registry_table(
                registry_content, disk_skills)
            if registry_table_errors:
                issues += len(registry_table_errors)
                result.errors.extend(registry_table_errors)

        # 2. Security: DAC permissions (no world-writable files)
        world_writable = []
        for check_root in [vault_root, os.path.join(vault_root, "and_os")]:
            for root, dirs, files in os.walk(check_root):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".tmp")]
                for f in files:
                    if f in IGNORE_FILES: continue
                    fp = os.path.join(root, f)
                    try:
                        mode = os.lstat(fp).st_mode
                        if not os.path.islink(fp) and (mode & 0o002):
                            world_writable.append(os.path.relpath(fp, vault_root))
                    except OSError as err:
                        sys.stderr.write(f"[manifest_probe] DAC check warning {fp}: {err}\n")

        if world_writable:
            issues += len(world_writable)
            result.errors.append(f"Found {len(world_writable)} world-writable files (DAC risk)")

        # 3. Security: Zero-Leak secrets in scripts
        secret_pat = re.compile(r'MDc4NzhkNjgt' + r'ZjhlZC00MWM0LWJhMjItZTljOTEzMWNhZGZl')
        secret_leaks = []
        scripts_dir = os.path.join(vault_root, "and_os", "bin")
        if os.path.exists(scripts_dir):
            for pf in glob.glob(os.path.join(scripts_dir, "*.py")):
                if os.path.basename(pf) == "validate_system.py": continue
                try:
                    with open(pf, "r", encoding="utf-8", errors="ignore") as f:
                        if secret_pat.search(f.read()):
                            secret_leaks.append(os.path.basename(pf))
                except OSError as err:
                    sys.stderr.write(f"[manifest_probe] Secret scan warning {pf}: {err}\n")

        if secret_leaks:
            issues += len(secret_leaks)
            result.errors.append(f"Secret token leaks detected in: {secret_leaks}")

        # 4. Check DEV_PROTOCOL.md and absence of bare except
        proto_path = os.path.join(vault_root, "and_os", "etc", "DEV_PROTOCOL.md")
        if not os.path.exists(proto_path):
            issues += 1
            result.errors.append(f"Missing DEV_PROTOCOL.md: {proto_path}")
        else:
            with open(proto_path, "r", encoding="utf-8") as f:
                content = f.read().lower()
            # Support bilingual verification (Russian or English)
            sec_checks = [
                ("permission matrix", ("\u043c\u0430\u0442\u0440\u0438\u0446\u0430 \u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u0438\u0439", "permission matrix")),
                ("debugging protocol", ("\u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b \u0447\u0435\u0441\u0442\u043d\u043e\u0439 \u043e\u0442\u043b\u0430\u0434\u043a\u0438", "debugging protocol")),
                ("report format", ("\u0444\u043e\u0440\u043c\u0430\u0442 \u043e\u0442\u0447", "report format", "mandatory report standard")),
                ("stop-on-3", ("hard stop-on-3 circuit breaker", "stop-on-3")),
                ("anti-beta-tester", ("anti-beta-tester", "\u0437\u0430\u043f\u0440\u0435\u0442 \u0441\u0438\u043c\u0443\u043b\u044f\u0446\u0438\u0438 \u043f\u0440\u0438\u0451\u043c\u043a\u0438"))
            ]
            missing_sec = []
            for sec_name, variants in sec_checks:
                if not any(v in content for v in variants):
                    missing_sec.append(sec_name)
            if missing_sec:
                issues += len(missing_sec)
                result.errors.append(f"DEV_PROTOCOL.md missing required sections: {missing_sec}")

        # Check bare except
        bare_except_pattern = re.compile(r"^\s*except\s*:")
        bare_excepts = []
        if os.path.exists(scripts_dir):
            for pf in glob.glob(os.path.join(scripts_dir, "*.py")):
                try:
                    with open(pf, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, 1):
                            if bare_except_pattern.search(line):
                                bare_excepts.append(f"{os.path.basename(pf)}:L{idx}")
                except OSError as err:
                    sys.stderr.write(f"[manifest_probe] Bare except scan warning {pf}: {err}\n")

        if bare_excepts:
            issues += len(bare_excepts)
            result.errors.append(f"Bare untyped 'except:' detected: {bare_excepts}")

        # 5. Check Telemetry Sentinel (Rule #11 DoD Enforcement)
        telemetry_file = os.path.join(vault_root, 'and_os/lib/skills/telemetry.md')
        if not os.path.exists(telemetry_file):
            issues += 1
            result.errors.append("Telemetry Sentinel: 'telemetry.md' is missing!")

        # 6. Check Dual-Realm Anti-Dumping Invariant (Rule #7)
        # Ensure no accidental note dumping directly into Nero/ai/docs/ without routing
        docs_dir = os.path.join(vault_root, 'Nero/ai/docs')
        if os.path.exists(docs_dir):
            stray_dumps = [f for f in os.listdir(docs_dir) if f.endswith('.md') and not f.startswith('CONTEXT') and not f.startswith("doc_")]
            if len(stray_dumps) > 5:
                result.warnings.append(f"Dual-Realm Warning: Detected potential file dumping in Nero/ai/docs/: {stray_dumps[:3]} (Rule #7)")

        # 7. Check CORE_RULES_MINI.md
        mini_path = os.path.join(vault_root, "and_os", "etc", "CORE_RULES_MINI.md")
        if not os.path.exists(mini_path):
            issues += 1
            result.errors.append("Missing CORE_RULES_MINI.md")

        result.issues_count = issues
        result.passed = (issues == 0)

        result.details = {
            "skills_count_verified": actual_skills_count,
            "manifest_sync_errors": len(sync_mismatches),
            "root_projection_checked": projection_checked,
            "version_consistency_ok": version_consistency_ok,
            "stale_banner_files": len(stale_banners),
            "registry_table_skills": registry_table_skills,
            "registry_table_errors": len(registry_table_errors),
            "world_writable_files": len(world_writable),
            "secret_leaks_count": len(secret_leaks),
            "bare_excepts_count": len(bare_excepts),
            "dev_protocol_active": os.path.exists(proto_path),
            "core_rules_mini_active": os.path.exists(mini_path)
        }

        return result
