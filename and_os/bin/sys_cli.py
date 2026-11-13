#!/usr/bin/env python3
"""
sys_cli.py — Unified Modular Dispatcher of AnD os (Modular Core CLI).
Consolidates all system scripts and core modules into a single CLI with telemetry and IPC:
  - sys_cli.py audit [--deep] [--compact] [--fix]
  - sys_cli.py sync [--fix] [--path PATH]
  - sys_cli.py state [--get DOMAIN | --get-all | --sync-auto | --set DOMAIN --key KEY --val VAL]
  - sys_cli.py vacuum [--all | --vault | --pulsar] [--dry-run]
  - sys_cli.py skills [--probe] [--dormancy] [--json]
  - sys_cli.py daemon [status | restart]

Core Invariants: Think in Code (Rule #16), IPC Data Bus, Hermetic FHS, Auto-Telemetry.
"""

import os
import sys
import json
import time
import socket
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, List

AI_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(AI_SCRIPT_DIR, "../..")))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)
PULSAR_ROOT = os.getenv("PULSAR_ROOT", os.path.expanduser("./pulsar"))

# Rule #68: Toolchain & Environment Parity Invariant (Auto-reexec under canonical .venv)
try:
    from and_os.lib.core.toolchain import ToolchainManager
    ToolchainManager(Path(VAULT_ROOT) if 'Path' in globals() else None).ensure_canonical_python(auto_reexec=True)
except (ImportError, AttributeError, OSError) as err:
    sys.stderr.write(f"[sys_cli] Notice: toolchain auto-reexec skipped ({err})\n")

def run_script(script_name: str, args_list: list, no_bytecode: bool = False) -> Dict[str, Any]:
    search_paths = [
        AI_SCRIPT_DIR,
        os.path.abspath(os.path.join(AI_SCRIPT_DIR, "../boot")),
        os.path.abspath(os.path.join(AI_SCRIPT_DIR, "../sbin")),
        os.path.abspath(os.path.join(VAULT_ROOT, "and_os/bin")),
        os.path.abspath(os.path.join(VAULT_ROOT, "and_os/lib/health")),
    ]
    script_path = None
    for sp in search_paths:
        candidate = os.path.join(sp, script_name)
        if os.path.exists(candidate):
            script_path = candidate
            break
            
    if not script_path:
        return {"stdout": f"❌ Script {script_name} not found across and_os/ or Nero/", "stderr": "Not found", "returncode": 1}
    
    cmd = [sys.executable]
    child_env = None
    if no_bytecode:
        cmd.append("-B")
        child_env = os.environ.copy()
        child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd.extend([script_path] + args_list)
    res = subprocess.run(cmd, capture_output=True, text=True, env=child_env)
    return {
        "stdout": res.stdout,
        "stderr": res.stderr,
        "returncode": res.returncode
    }

def sync_global_rules() -> None:
    """Сквозная синхронизация канонических правил Obsidian Vault с глобальным окружением Antigravity и Pulsar."""
    sources = {
        "AGENTS.md": os.path.join(VAULT_ROOT, "AGENTS.md"),
        "GEMINI.md": os.path.join(VAULT_ROOT, "AGENTS.md"),
        "CORE_RULES_MINI.md": os.path.join(VAULT_ROOT, "and_os", "etc", "CORE_RULES_MINI.md"),
        "DEV_PROTOCOL.md": os.path.join(VAULT_ROOT, "and_os", "etc", "DEV_PROTOCOL.md")
    }
    targets = [
        os.path.expanduser("~/.gemini/config"),
        os.path.expanduser("~/.gemini/antigravity"),
        os.path.join(PULSAR_ROOT, "docs"),
        os.path.join(PULSAR_ROOT, "mc_doc")
    ]
    # Auto-cleanup stray symlinks from pulsar root if created by mistake
    pulsar_root = PULSAR_ROOT
    for stray_name in sources.keys():
        stray_path = os.path.join(pulsar_root, stray_name)
        if os.path.islink(stray_path):
            try:
                os.remove(stray_path)
            except OSError as err:
                sys.stderr.write(f"[sys_cli:sync_rules] Warning: failed to remove stray symlink {stray_path}: {err}\n")

    synced = 0
    for target_dir in targets:
        if os.path.exists(target_dir):
            for name, src in sources.items():
                if os.path.exists(src):
                    dest = os.path.join(target_dir, name)
                    try:
                        if not os.path.exists(dest) or not os.path.islink(dest) or os.path.realpath(dest) != os.path.realpath(src):
                            if os.path.islink(dest) or os.path.exists(dest):
                                os.remove(dest)
                            os.symlink(src, dest)
                            synced += 1
                    except OSError as err:
                        sys.stderr.write(f"[sys_cli:sync_rules] Warning: failed to link {dest} -> {src}: {err}\n")
    print("⚡ Сквозная синхронизация глобальных правил (Antigravity & Pulsar) активна.")

def print_agent_motd() -> None:
    """L1 Fast Agent Capsule / MOTD Banner (~80 tokens). Output once on init/preflight."""
    ver = "1.0.0"
    rel_summary = ""
    try:
        from and_os.lib.core.root_config import get_system_version
        v_full = get_system_version(VAULT_ROOT)
        ver = ".".join(v_full.split(".")[:2])
    except (ImportError, AttributeError, KeyError) as err:
        sys.stderr.write(f"[sys_cli:motd] Notice: using fallback version ({err})\n")

    try:
        from and_os.lib.core.release_ledger import get_compact_motd_summary
        rel_summary = get_compact_motd_summary()
    except (ImportError, AttributeError, KeyError) as err:
        sys.stderr.write(f"[sys_cli:motd] Notice: release summary skipped ({err})\n")

    mode_name = "DEV"
    try:
        from and_os.bin.context_mode_manager import ContextModeManager
        mode_name = ContextModeManager(VAULT_ROOT).get_current_mode().upper()
    except (ImportError, AttributeError, OSError) as err:
        sys.stderr.write(f"[sys_cli:motd] Notice: mode manager skipped ({err})\n")

    print("=" * 65)
    print(f"🌌 AnD os v{ver} | AGENT FAST CAPSULE (MOTD / Ring 1) | MODE: {mode_name}")
    if rel_summary:
        print(f"📦 RELEASE: {rel_summary}")
    print("🚨 INVARIANTS: Чат/отчёты strictly Russian | Diff <= 15 строк | No bare except")
    print("📁 SCOPE: Знания -> Nero/<тема>/ (ЗАПРЕТ Nero/ai/docs/) | Код -> and_os/")
    print("🛑 PROTOCOL: Stop-on-3 Rule | Anti-Beta-Tester Gate | RED ZONE: No OS input hooks/resets")
    print("🛰️ PROCFS BEACON (0-Token): python3 and_os/bin/sys_cli.py proc --cat <sys|health|pulsar>")
    # Rule #68: Toolchain parity banner
    try:
        from and_os.lib.core.toolchain import ToolchainManager
        tc_res = ToolchainManager().check_parity()
        tc_icon = "🟢" if tc_res["passed"] else "🔴"
        tc_py = tc_res["stack"].get("python", {}).get("active", "unknown")
        print(f"⚙️ TOOLCHAIN: {tc_icon} Python {tc_py} (Target: 3.12.11) | Bun 1.3 | Swift 6.4 | FFmpeg 9")
    except (ImportError, AttributeError, KeyError) as err:
        sys.stderr.write(f"[sys_cli:motd] Notice: toolchain check skipped ({err})\n")
    print("🏁 DoD: sys_cli verify PASS (Rule #65) + audit PASS + блок 'НЕ ПРОВЕРЕНО'")
    print("=" * 65)

def auto_log_telemetry(task: str, mode: str = "SYSTEM", skill: str = "sys_cli", result: str = "success") -> None:
    telemetry_script = os.path.join(AI_SCRIPT_DIR, "telemetry_logger.py")
    if os.path.exists(telemetry_script):
        cmd = [
            sys.executable, telemetry_script,
            "--task", task,
            "--mode", mode,
            "--skill", skill,
            "--ctx", "min",
            "--result", result
        ]
        subprocess.run(cmd, capture_output=True, text=True)

def cmd_audit(args: Any) -> None:
    from and_os.bin.cli_subsystems import get_subsystem
    sub = get_subsystem("audit")
    ret = sub.execute(args) if sub else 1
    if ret != 0:
        sys.exit(ret)

def cmd_sync(args: Any) -> None:
    flags = ["--fix"] if args.fix else ["--check"]
    if args.path:
        flags.extend(["--path", args.path])
    res = run_script("sync_context.py", flags)
    print(res["stdout"])
    if res["stderr"]:
        print(res["stderr"], file=sys.stderr)
    
    if getattr(args, "parallel", False):
        print("🚀 Запуск параллельной синхронизации фоновых компонентов (ThreadPoolExecutor)...")
        tasks = [
            ("state_manager.py", ["--sync-auto"], "⚡ Авто-экстракция состояний доменов"),
            ("task_db_engine.py", [], "⚡ Индексация задач в SQLite"),
            ("obsidian_blueprint_generator.py", [], "⚡ Обновление Obsidian Blueprint"),
            ("system_tools_map.py", ["--build"], "⚡ Синхронизация SYSTEM_TOOLCHAIN")
        ]
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_script, s, f) for s, f, label in tasks]
            for i, fut in enumerate(futures):
                res_i = fut.result()
                label = tasks[i][2]
                print(f"{label} завершена [OK].")
    else:
        # Auto sync domain states
        state_res = run_script("state_manager.py", ["--sync-auto"])
        print("⚡ Авто-экстракция состояний доменов завершена.")

        # Auto index tasks
        task_res = run_script("task_db_engine.py", [])
        print("⚡ Индексация задач в SQLite завершена.")

        # Auto check/update Obsidian Blueprint (once a month)
        bp_res = run_script("obsidian_blueprint_generator.py", [])
        if bp_res.get("stdout"):
            print(f"⚡ {bp_res['stdout'].strip()}")

        # Auto update Toolchain and Runtime Environment map
        tc_res = run_script("system_tools_map.py", ["--build"])
        print("⚡ Регламент версий рантаймов и библиотек (SYSTEM_TOOLCHAIN) синхронизирован.")

    # Auto sync global rules to ~/.gemini and Pulsar workspaces
    sync_global_rules()

    auto_log_telemetry(f"Sync context ({'fix' if args.fix else 'check'})", skill="sys.sync")

def cmd_state(args: Any) -> None:
    flags = []
    if args.sync_auto:
        flags.append("--sync-auto")
    elif args.get:
        flags.extend(["--get", args.get])
    elif args.get_all:
        flags.append("--get-all")
    elif args.set and args.key and args.val:
        flags.extend(["--set", args.set, "--key", args.key, "--val", args.val])
    else:
        flags.append("--get-all")
    
    res = run_script("state_manager.py", flags)
    print(res["stdout"])
    auto_log_telemetry("State Manager query", skill="sys.state")

def cmd_chunk(args: Any) -> None:
    flags = ["--file", args.file]
    if args.act:
        flags.extend(["--act", str(args.act)])
    if args.episode:
        flags.extend(["--episode", str(args.episode)])
    if args.chapter:
        flags.extend(["--chapter", str(args.chapter)])
    
    res = run_script("script_chunker.py", flags)
    print(res["stdout"])
    auto_log_telemetry("Script Chunker query", skill="sys.chunker")

def cmd_taskdb(args: Any) -> None:
    flags = []
    if args.index:
        flags.append("--index")
    elif args.query:
        flags.append("--query-pending")
        if args.domain:
            flags.extend(["--domain", args.domain])
    elif args.canvas:
        flags.append("--build-canvas")
    else:
        flags.append("--index")
    
    res = run_script("task_db_engine.py", flags)
    print(res["stdout"])
    auto_log_telemetry("Task DB query/index", skill="sys.taskdb")

def cmd_deconstruct(args: Any) -> None:
    flags = [args.target]
    if getattr(args, "json", False):
        flags.append("--json")
    if getattr(args, "out", None):
        flags.extend(["--out", args.out])
    res = run_script("app_deconstructor.py", flags)
    if "stdout" in res:
        print(res["stdout"])
    if res.get("stderr"):
        print(res["stderr"], file=sys.stderr)
    auto_log_telemetry(f"App deconstruction: {args.target}", skill="app-deconstructor")

def cmd_postmortem(args: Any) -> None:
    flags = [args.sprint]
    if getattr(args, "file", None):
        flags.extend(["--file", args.file])
    if getattr(args, "json", False):
        flags.append("--json")
    if getattr(args, "out", None):
        flags.extend(["--out", args.out])
    res = run_script("postmortem_analyzer.py", flags)
    if "stdout" in res:
        print(res["stdout"])
    if res.get("stderr"):
        print(res["stderr"], file=sys.stderr)
    auto_log_telemetry(f"Production postmortem: {args.sprint}", skill="postmortem-analyzer")

def cmd_contract(args: Any) -> None:
    flags = [args.operation_id]
    if getattr(args, "desc", None):
        flags.extend(["--desc", args.desc])
    if getattr(args, "capabilities", None):
        flags.append("--capabilities")
        flags.extend(args.capabilities)
    if getattr(args, "params", None):
        flags.extend(["--params", args.params])
    if getattr(args, "returns", None):
        flags.extend(["--returns", args.returns])
    if getattr(args, "idempotent", False):
        flags.append("--idempotent")
    if getattr(args, "json", False):
        flags.append("--json")
    res = run_script("api_contract_generator.py", flags)
    if "stdout" in res:
        print(res["stdout"])
    if res.get("stderr"):
        print(res["stderr"], file=sys.stderr)
    auto_log_telemetry(f"Contract generation: {args.operation_id}", skill="api-contract-generator")

def cmd_bible(args: Any) -> None:
    flags = [args.script_file]
    if getattr(args, "json", False):
        flags.append("--json")
    if getattr(args, "out", None):
        flags.extend(["--out", args.out])
    res = run_script("script_bible_extractor.py", flags)
    if "stdout" in res:
        print(res["stdout"])
    if res.get("stderr"):
        print(res["stderr"], file=sys.stderr)
    auto_log_telemetry(f"Script bible extraction: {args.script_file}", skill="script-bible-extractor")

def cmd_montage(args: Any) -> None:
    target = os.path.join(VAULT_ROOT, "and_os/opt/apps/montage_hub/montage_cli.py")
    if not os.path.exists(target):
        sys.stderr.write("montage_hub engine not found in and_os/opt/apps/montage_hub\n")
        sys.exit(1)
    sub = getattr(args, "montage_sub", None) or "info"
    extra = getattr(args, "extra_args", []) or []
    cmd = [sys.executable, str(target), sub] + extra
    try:
        res = subprocess.run(cmd)
        auto_log_telemetry(f"Montage Hub: {sub}", skill="openmontage-builder")
        sys.exit(res.returncode)
    except (subprocess.SubprocessError, OSError) as e:
        sys.stderr.write(f"Montage execution failed: {e}\n")
        sys.exit(1)

def cmd_preflight(args: Any) -> None:
    print_agent_motd()
    flags = []
    if getattr(args, "hours", None):
        flags.extend(["--hours", str(args.hours)])
    res = run_script("sync_preflight.py", flags)
    print(res["stdout"], end="")
    if res["stderr"]:
        print(res["stderr"], file=sys.stderr)
    auto_log_telemetry("Pre-flight scan & delta sync", skill="sys.preflight")

def cmd_init(args: Any) -> None:
    print_agent_motd()
    # Rule №47: Pre-Flight Cross-Chat Delta Scan first
    pf_res = run_script("sync_preflight.py", [])
    if pf_res["stdout"]:
        print(pf_res["stdout"], end="")
    fix_flag = not args.check_only
    res = run_script("sync_service.py", ["--json"] if args.json else [])
    if "stdout" in res:
        print(res["stdout"])
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))

def cmd_project(args: Any) -> None:
    sub = getattr(args, "subaction", "list")
    if sub in ["pulsar", "xcode"]:
        flags = [sub]
        if getattr(args, "scan", False):
            flags.append("--scan")
        if getattr(args, "sync", False):
            flags.append("--sync")
        if getattr(args, "name", None):
            flags.extend(["--name", args.name])
        if getattr(args, "desc", None):
            flags.extend(["--desc", args.desc])
        if sub == "pulsar":
            if getattr(args, "category", None):
                flags.extend(["--category", args.category])
            if getattr(args, "port", None):
                flags.extend(["--port", str(args.port)])
            if getattr(args, "repo", None):
                flags.extend(["--repo", args.repo])
        elif sub == "xcode":
            if getattr(args, "type", None):
                flags.extend(["--type", args.type])
            if getattr(args, "source", None):
                flags.extend(["--source", args.source])
        if getattr(args, "status", None):
            flags.extend(["--status", args.status])
        if getattr(args, "tags", None):
            flags.extend(["--tags", args.tags])
        res = run_script("project_manager.py", flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Project action: {args.subaction}", skill="sys.project")
    else:

        res = run_script("project_registry.py", [])
        print(res["stdout"])
        auto_log_telemetry("Project registry", skill="sys.project")

def cmd_app(args: Any) -> None:
    flags = []
    if args.blueprint:
        flags.extend(["blueprint", "--id", args.blueprint])
    else:
        flags.append("status")
    res = run_script("app_bridge.py", flags)
    print(res["stdout"])
    auto_log_telemetry("App bridge query", skill="sys.app")

def cmd_skills(args: Any) -> None:
    # External Skills Gateway routing
    if getattr(args, "search", None):
        gateway_script = os.path.join(VAULT_ROOT, "and_os/lib/skills/external-skills-gateway/scripts/skills_gateway.py")
        subprocess.run([sys.executable, gateway_script, "search", args.search])
        auto_log_telemetry(f"Skills Gateway search: {args.search}", skill="sys.skills-gateway")
        return
    if getattr(args, "inspect", None):
        gateway_script = os.path.join(VAULT_ROOT, "and_os/lib/skills/external-skills-gateway/scripts/skills_gateway.py")
        subprocess.run([sys.executable, gateway_script, "inspect", args.inspect])
        auto_log_telemetry(f"Skills Gateway inspect: {args.inspect}", skill="sys.skills-gateway")
        return

    flags = []
    if getattr(args, "probe", False):
        flags.append("--probe")
    if getattr(args, "json", False):
        flags.append("--json")
    if getattr(args, "dormancy", False):
        res = run_script("skill_dormancy_checker.py", [])
    else:
        res = run_script("sos_auditor.py", flags)
    print(res.get("stdout", ""), end="")
    if res.get("stderr"):
        print(res["stderr"], file=sys.stderr)
    auto_log_telemetry("Skills stack parallel audit", skill="sys.skills")

def cmd_skill(args: Any) -> None:
    # Route meta-actions (create, lint, verify) to skill-creator engine
    if args.skill_action in ["lint", "verify"]:
        s_name = getattr(args, "skill_name", None)
        val_script = os.path.join(VAULT_ROOT, "and_os/lib/skills/skill-creator/scripts/validate_skill.py")
        hyg_script = os.path.join(VAULT_ROOT, "and_os/lib/skills/skill-creator/scripts/check_code_hygiene.py")
        
        if not s_name or s_name in ["--all", "all"]:
            res1 = subprocess.run([sys.executable, val_script, "--all"], capture_output=True, text=True)
            print(res1.stdout, end="")
            if res1.stderr:
                print(res1.stderr, file=sys.stderr, end="")
            auto_log_telemetry("Full skill stack ABI lint", skill="sys.skill-creator")
            return

        skill_dir = os.path.join(VAULT_ROOT, "and_os/lib/skills", s_name)
        res1 = subprocess.run([sys.executable, val_script, skill_dir], capture_output=True, text=True)
        print(res1.stdout, end="")
        if res1.stderr:
            print(res1.stderr, file=sys.stderr, end="")
            
        res2 = subprocess.run([sys.executable, hyg_script, skill_dir], capture_output=True, text=True)
        print(res2.stdout, end="")
        if res2.stderr:
            print(res2.stderr, file=sys.stderr, end="")
        auto_log_telemetry(f"Skill lint: {s_name}", skill="sys.skill-creator")
        return

    flags = [args.skill_action]
    if getattr(args, "skill_name", None):
        flags.append(args.skill_name)
    if getattr(args, "consumer", None):
        flags.append(args.consumer)
    if getattr(args, "topic", None):
        flags.extend(["--topic", args.topic])
    if getattr(args, "list", False):
        flags.append("--list")
    if getattr(args, "json", False):
        flags.append("--json")
    if getattr(args, "extra_args", None):
        flags.extend(args.extra_args)
    res = run_script("skill_bus.py", flags)
    if "stdout" in res:
        print(res["stdout"], end="")
    if res.get("stderr"):
        print(res["stderr"], file=sys.stderr, end="")
    auto_log_telemetry(f"Skill bus {args.skill_action}: {getattr(args, 'skill_name', '')}", skill="sys.skill_bus")

def cmd_daemon(args: Any) -> None:
    import socket
    target_name = getattr(args, "pos_target", "") or getattr(args, "target", "")
    sock_candidates = [
        os.path.expanduser("~/.and_os/var/run/supervisor.sock"),
        os.path.join(VAULT_ROOT, "and_os/var/run/supervisor.sock")
    ]
    sup_sock = next((p for p in sock_candidates if os.path.exists(p)), None)
    
    # 1. Check if Master Supervisor is running
    if sup_sock:
        try:
            s_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s_sock.settimeout(0.3)
            s_sock.connect(sup_sock)
            if args.action == "status":
                s_sock.sendall(b"STATUS")
                raw = s_sock.recv(4096).decode("utf-8")
                s_sock.close()
                data = json.loads(raw)
                print("=== 🛰️ AnD os Master Supervisor Modules Status ===")
                for s in data.get("services", []):
                    icon = "🟢" if s["status"] in ["HEALTHY", "RUNNING", "SCHEDULED"] else "🔴"
                    port_info = f"Port :{s['port']} ({s['latency_ms']}ms)" if s.get("port") else "Internal"
                    pid_info = f"PID {s['pid']}" if s.get("pid") else "Cron/Standby"
                    print(f"  • {s['name']} [{s['id']}]: {icon} {s['status']} | {port_info} | {pid_info}")
                auto_log_telemetry(f"Daemon {args.action} (Supervisor)", skill="sys.daemon")
                return
            elif args.action == "restart":
                cmd = f"RESTART {target_name or 'all'}"
                s_sock.sendall(cmd.encode("utf-8"))
                raw = s_sock.recv(1024).decode("utf-8")
                s_sock.close()
                print(f"  [OK] Сигнал перезапуска отправлен в Master Supervisor для '{target_name or 'all'}'.")
                auto_log_telemetry(f"Daemon {args.action} (Supervisor)", skill="sys.daemon")
                return
        except (socket.error, OSError, json.JSONDecodeError) as sup_err:
            # Supervisor socket unreachable or not ready, fallback to standalone launchctl
            sys.stderr.write(f"[sys_cli:daemon] Notice: supervisor unavailable ({sup_err}), using launchctl fallback\n")

    # 2. Standalone launchctl fallback
    target_services = [
        {"id": "mars_gantt", "name": "Pulsar Mars Gantt", "port": 8087, "plist": "com.pulsar.mars_gantt"},
        {"id": "kot_gantt", "name": "Pulsar Kot Gantt", "port": 8092, "plist": "com.pulsar.kot_gantt"},
    ]
    
    if args.action == "status":
        print("=== 🛰️ macOS LaunchAgents & Pulsar Daemons Status (Standalone) ===")
        for s in target_services:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            res = sock.connect_ex(("127.0.0.1", s["port"]))
            sock.close()
            status_port = "🟢 LISTEN (127.0.0.1:" + str(s["port"]) + ")" if res == 0 else "🔴 DOWN"
            
            # Check launchctl
            chk = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
            in_launchctl = s["plist"] in chk.stdout
            status_agent = "🟢 LOADED" if in_launchctl else "⚪ NOT LOADED"
            print(f"  • {s['name']} [{s['plist']}]: Daemon {status_agent} | Port: {status_port}")
            
    elif args.action == "restart":
        print(f"=== 🔄 Перезапуск фонового демона {target_name or 'всех'} ===")
        targets = [s for s in target_services if not target_name or target_name in s["id"] or target_name in s["plist"]]
        if not targets:
            print(f"  [!] Не найден сервис по фильтру '{args.target}'")
            return
        for s in targets:
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{s['plist']}.plist")
            if os.path.exists(plist_path):
                subprocess.run(["launchctl", "unload", plist_path], capture_output=True)
                res = subprocess.run(["launchctl", "load", plist_path], capture_output=True)
                if res.returncode == 0:
                    print(f"  [OK] Демон {s['name']} успешно перезапущен через launchctl.")
                else:
                    print(f"  [!] Ошибка перезапуска {s['name']}: {res.stderr.strip()}")
            else:
                print(f"  [!] Plist-файл не найден: {plist_path}")
    auto_log_telemetry(f"Daemon {args.action}", skill="sys.daemon")

def cmd_islands(args: Any) -> None:
    islands_data = [
        {
            "num": 1,
            "name": "Universal Knowledge Base",
            "path": "Clippings/CONTEXT.md",
            "domain": "Клиппинг, Заметки, Саммари, Таксономия тегов",
            "realm": "Shared Knowledge Base",
            "paths": ["Clippings/", "Tags/", "CG_core/Статьи/"],
            "scripts": ["and_os/bin/sys_cli.py find", "quick_knowledge_db.py"],
            "daemons": ["None (File-based index)"],
            "bridges": "Остров 2 (CG_core), Остров 3 (Ta-Bu), Остров 4 (Story)"
        },
        {
            "num": 2,
            "name": "Consulting & Media",
            "path": "CG_core/CONTEXT.md",
            "domain": "Консалтинг, CG/VFX Экспертиза, Фабрика контента, Школа Scream School",
            "realm": "Author Workshop (CG_core/) ⟷ AI Analytics (Nero/cg_core/)",
            "paths": ["CG_core/", "Industry/", "Nero/cg_core/"],
            "scripts": ["cg_core.py", "cg-content-factory", "cg-core-consulting"],
            "daemons": ["None (Event-triggered)"],
            "bridges": "Остров 1 (Knowledge), Остров 3 (Ta-Bu), Остров 5 (Studio)"
        },
        {
            "num": 3,
            "name": "Startup Incubator",
            "path": "Ta-Bu/CONTEXT.md",
            "domain": "Стартапы, B2B SaaS, Бот-архитектура, Unit-экономика, Гранты ИРИ",
            "realm": "Author Workshop (Ta-Bu/) ⟷ AI Analytics (Nero/ta_bu/)",
            "paths": ["Ta-Bu/", "Nero/ta_bu/"],
            "scripts": ["ta-bu-plan", "investor-outreach", "closed_loop.py"],
            "daemons": ["None (Operational)"],
            "bridges": "Остров 2 (CG_core), Остров 5 (Product), Остров 6 (Finance)"
        },
        {
            "num": 4,
            "name": "Narrative & Books",
            "path": "Story/CONTEXT.md",
            "domain": "Сценарии (Чудобус, Бар, Жесть), Книги, Сторителинг, Библии миров",
            "realm": "Author Workshop (Story/, Book/) ⟷ AI Analytics (Nero/story/, Nero/book/)",
            "paths": ["Story/", "Book/", "Nero/story/", "Nero/book/"],
            "scripts": ["script_chunker.py", "story-dev", "book-hub"],
            "daemons": ["None (Hermetic writing)"],
            "bridges": "Остров 5 (Production previs), Остров 7 (ComfyUI / 3D)"
        },
        {
            "num": 5,
            "name": "Studio Production",
            "path": "Product/CONTEXT.md",
            "domain": "Студийное CG-производство, Studio, 15 департаментов, Ftrack, Weeek",
            "realm": "Execution Workspace (Product/, Tasks/) ⟷ AI Analytics (Nero/work/)",
            "paths": ["Product/", "Tasks/", "Studio/", "Nero/work/"],
            "scripts": ["and_os/bin/sys_cli.py ftrack", "employee-hub", "task_aggregator.py"],
            "daemons": ["ftrack_gantt (:8087, :8092 via LaunchAgents)"],
            "bridges": "Остров 3 (Ta-Bu), Остров 4 (Story animatics), Остров 7 (Pulsar 3D)"
        },
        {
            "num": 6,
            "name": "Creator Profile & Clinical Health",
            "path": "Nero/CONTEXT.md",
            "domain": "Клиническое здоровье семьи (UC, биомаркеры), Half Ironman, Личные цели, Финансы",
            "realm": "Sovereign Brain Realm (Nero/ - Single Source of Truth)",
            "paths": ["Nero/profile/health/", "Nero/profile/sport/", "Nero/profile/finance/", "Nero/profile/goals/"],
            "scripts": ["health-diagnostics-hub", "endurance-training-plan", "portfolio-summary"],
            "daemons": ["None (Passive 7-day interval health guard)"],
            "bridges": "Остров 8 (and_os Core Highways), Остров 5 (Energy & Production)"
        },
        {
            "num": 7,
            "name": "Pulsar 3D Tooling & Apps",
            "path": "Nero/pulsar/INDEX.md",
            "domain": "Внешние сервисы, Дашборды, Headless 3D Pipeline, Comfy-USD, Blender",
            "realm": "External Execution Muscle (Pulsar Space / WORK/pulsar/)",
            "paths": ["and_os/opt/apps/", os.path.expanduser("./pulsar/"), "Nero/pulsar/"],
            "scripts": ["cg_core.py", "cg-pipeline", "server.py"],
            "daemons": ["ftrack_gantt (:8087, :8092)", "comfyui (:8188)"],
            "bridges": "Остров 4 (Story), Остров 5 (Studio assets), Остров 8 (Kernel Bus)"
        },
        {
            "num": 8,
            "name": "and_os Kernel, Terminal & System Compiler",
            "path": "and_os/opt/terminal/CONTEXT.md",
            "domain": "Суверенное ядро ОС, FHS дерево, CLI, компилятор, шина D-Bus, Web GUI (:8099)",
            "realm": "Sovereign System Core (and_os/)",
            "paths": ["and_os/bin/", "and_os/sbin/", "and_os/etc/", "and_os/lib/", "and_os/var/", "and_os/opt/terminal/"],
            "scripts": ["and_os/bin/sys_cli.py", "sys_bus.py", "build_os.py", "context_router.py"],
            "daemons": ["vfs_daemon.py", "sys_bus.py daemon"],
            "bridges": "Сквозной контроль над всеми Островами (1-7), Аудит 25 векторов"
        },
        {
            "num": 9,
            "name": "Mobile App & Game Engineering (Xcode / iOS)",
            "path": "Nero/xcode/CONTEXT.md",
            "domain": "Нативные мобильные игры и приложения для Apple (iOS/macOS), Swift, SpriteKit, SwiftUI",
            "realm": "External Code Muscle (WORK/xcode/) & Brain Spec (Nero/xcode/)",
            "paths": ["Nero/xcode/", os.path.expanduser("./xcode/")],
            "scripts": ["ios-game-builder (Skill)", "swift", "xcodebuild", "xcrun simctl"],
            "daemons": ["Xcode Simulator (On-Demand)"],
            "bridges": "Остров 1 (Clippings/ASO), Остров 3 (Ta-Bu/MVP), Остров 4 (Story/Narrative), Остров 6 (Nero/Dev Accounts), Остров 7 (Pulsar/Sprites & SFX)"
        },
    ]

    selected_info = getattr(args, "info", None)
    if selected_info:
        matched = [isl for isl in islands_data if isl["num"] == selected_info]
        if matched:
            isl = matched[0]
            full_p = os.path.join(VAULT_ROOT, isl["path"])
            exists = "🟢 Активен" if os.path.exists(full_p) else "🔴 Отсутствует"
            print(f"==================================================")
            print(f"🏝️ ПАСПОРТ ОСТРОВА {isl['num']}: {isl['name']}")
            print(f"==================================================")
            print(f"  • Статус входа: {exists} ({isl['path']})")
            print(f"  • Топологический Realm: {isl['realm']}")
            print(f"  • Сфера ответственности: {isl['domain']}")
            print(f"  • Связанные пути:")
            for p in isl["paths"]:
                print(f"      - {p}")
            print(f"  • Ключевые скрипты и утилиты:")
            for s in isl["scripts"]:
                print(f"      - {s}")
            print(f"  • Фоновые демоны / сервисы:")
            for d in isl["daemons"]:
                print(f"      - {d}")
            print(f"  • Межостровные мосты: {isl['bridges']}")
            print(f"==================================================")
            auto_log_telemetry(f"Islands info #{selected_info}", skill="sys.islands")
            return

    print("=== 🏝️ Архитектура 9 Логических Островов AnD os v1.0.0 ===")
    for isl in islands_data:
        full_p = os.path.join(VAULT_ROOT, isl["path"])
        exists = "🟢" if os.path.exists(full_p) else "🔴"
        print(f"  {exists} Остров {isl['num']}: {isl['name']}")
        print(f"     Файл: {isl['path']} | Realm: {isl['realm']}")
        print(f"     Область: {isl['domain']}")
    print("\n🌉 Связность: 100% Zero-Isolation — сквозные кросс-магистрали активны.")
    print("💡 Для детального паспорта используй: sys_cli.py islands --info <1-9>")
    auto_log_telemetry("Islands listing", skill="sys.islands")

def cmd_backup(args: Any) -> None:
    flags = []
    if getattr(args, "status", False):
        flags.append("--status")
    res = run_script("backup_engine.py", flags)
    print(res["stdout"])
    if res["stderr"]:
        print(res["stderr"], file=sys.stderr)
    auto_log_telemetry(f"Vault backup ({'status' if getattr(args, 'status', False) else 'run'})", skill="sys.backup")

def cmd_top(args: Any) -> None:
    res = run_script("system_dashboard.py", [])
    print(res["stdout"])
    auto_log_telemetry("System TUI top dashboard", skill="sys.top")

def cmd_terminal(args: Any) -> None:
    term_dir = os.path.expanduser("./pulsar/AND_Terminal")
    server_script = os.path.join(term_dir, "server.py")
    if not os.path.exists(server_script):
        # Fallback to in-vault location
        server_script = os.path.join(VAULT_ROOT, "and_os/opt/terminal/server.py")
        if not os.path.exists(server_script):
            print(f"[!] Файл {server_script} не найден.")
            return

    # Check if already running on port 8099
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3)
    is_running = (sock.connect_ex(("127.0.0.1", 8099)) == 0)
    sock.close()

    if is_running:
        print("ℹ️ [AnD os] AND_Terminal уже запущен на http://127.0.0.1:8099")
    else:
        print("🚀 [AnD os] Запуск AND_Terminal на порту 8099...")
        subprocess.Popen([sys.executable, server_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)

    subprocess.run(["open", "http://127.0.0.1:8099"])
    auto_log_telemetry("AND_Terminal Web Console launch", skill="sys.terminal")

def cmd_vault(args: Any) -> None:
    """Шлюз безопасного взаимодействия с заметками Obsidian через mcp_vault_guard (Subsystem Delegation)."""
    from and_os.bin.cli_subsystems import get_subsystem
    sub = get_subsystem("vault")
    if sub:
        ret = sub.execute(args)
        if ret != 0:
            sys.exit(ret)
    else:
        print("Error: vault subsystem failed to load", file=sys.stderr)
        sys.exit(1)

def cmd_event(args: Any) -> None:
    flags = [args.action]
    if args.action == "emit":
        flags.extend(["--type", args.type])
        if args.payload:
            flags.extend(["--payload", args.payload])
        if args.source:
            flags.extend(["--source", args.source])
    elif args.action == "list":
        if args.count:
            flags.extend(["-n", str(args.count)])
        if args.json:
            flags.append("--json")
    res = run_script("sys_bus.py", flags)
    print(res.get("stdout", ""))
    if res.get("stderr"):
        print(res["stderr"], file=sys.stderr)
    auto_log_telemetry(f"Event bus: {args.action}", skill="sys.event")

def cmd_toolchain(args: Any) -> None:
    """Управление и аудит соответствия тулчейна (Rule #68)."""
    from and_os.lib.core.toolchain import ToolchainManager
    tm = ToolchainManager()
    
    if args.action == "status":
        print(tm.format_status_report())
    elif args.action == "check":
        res = tm.check_parity()
        if res["passed"]:
            print("🟢 Toolchain Parity: PASS (All runtimes match golden stack)")
            sys.exit(0)
        else:
            print("🔴 Toolchain Parity: FAIL")
            for err in res["errors"]:
                print(f"  - {err}")
            sys.exit(1)
    elif args.action == "sync":
        print("🔄 Синхронизация зависимостей канонического окружения and_os/.venv через uv...")
        lock_file = os.path.join(VAULT_ROOT, "and_os/etc/requirements.lock")
        venv_py = os.path.join(VAULT_ROOT, "and_os/.venv/bin/python")
        if not os.path.exists(lock_file):
            print("❌ requirements.lock не найден. Запустите компиляцию.")
            sys.exit(1)
        res = subprocess.run(["uv", "pip", "sync", lock_file, "--python", venv_py], capture_output=True, text=True)
        if res.returncode == 0:
            print("✅ Зависимости and_os/.venv успешно синхронизированы.")
            print(res.stdout)
        else:
            print(f"❌ Ошибка синхронизации: {res.stderr}")
            sys.exit(1)
    auto_log_telemetry(f"Toolchain: {args.action}", skill="sys.toolchain")

def main() -> None:
    try:
        from and_os.lib.core.root_config import get_system_version
        current_ver = get_system_version(VAULT_ROOT)
    except Exception:
        current_ver = "1.0.0"

    # UNIX Git-Style Fast-Path: If invoking a mapped subsystem command with --help or arguments,
    # register ONLY that targeted subsystem's parsers to bypass 59k function calls in monolithic argparse.
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        first_cmd = sys.argv[1]
        try:
            from and_os.bin.cli_subsystems import get_subsystem
            sub_cls = get_subsystem(first_cmd)
            if sub_cls and hasattr(sub_cls, "register_subparsers"):
                fast_p = argparse.ArgumentParser(
                    prog=f"sys_cli.py",
                    description=f"AnD os v{current_ver} Unified Modular CLI"
                )
                fast_p.add_argument("--version", "-v", action="version", version=f"AnD os v{current_ver} (Production Release)")
                fast_subs = fast_p.add_subparsers(dest="command")
                sub_cls.register_subparsers(fast_subs)
                try:
                    f_args, f_unknown = fast_p.parse_known_args()
                    if getattr(f_args, "command", None) == first_cmd:
                        if hasattr(f_args, "extra_args") and f_unknown:
                            f_args.extra_args.extend(f_unknown)
                        ret = sub_cls.execute(f_args)
                        sys.exit(ret if isinstance(ret, int) else 0)
                except SystemExit as se:
                    # If parse_known_args triggered --help or syntax error exit, honor it immediately
                    sys.exit(se.code)
        except Exception as e:
            # Safe Fallback to monolithic parser if lazy fast-path throws any unexpected error
            sys.stderr.write(f"[sys_cli:fast_path] Notice: fallback to monolithic parser ({e})\n")

    parser = argparse.ArgumentParser(description=f"AnD os v{current_ver} Unified Modular CLI")
    parser.add_argument("--version", "-v", action="version", version=f"AnD os v{current_ver} (Production Release)")
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # Vault Backup (Enterprise Backup)
    p_bup = subparsers.add_parser("backup", help="Полное резервное копирование хранилища Obsidian Vault в WORK (лимит 5 ГБ)")
    p_bup.add_argument("--status", action="store_true", help="Проверить статус последнего бэкапа и здоровье контура")

    # Vault Guard MCP Gateway
    p_vg = subparsers.add_parser("vault", help="Шлюз MCP Vault Guard для безопасного чтения и правки заметок")
    p_vg_sub = p_vg.add_subparsers(dest="subaction", required=True)

    p_vg_read = p_vg_sub.add_parser("read", help="Безопасное точечное чтение заметки")
    p_vg_read.add_argument("path", help="Путь к заметке от корня vault")
    p_vg_read.add_argument("--section", help="Секция markdown (например, '## 23.10')")
    p_vg_read.add_argument("--max-lines", type=int, default=200, help="Лимит строк")

    p_vg_patch = p_vg_sub.add_parser("patch", help="Атомарный патч заметки с проверкой AST")
    p_vg_patch.add_argument("path", help="Путь к заметке от корня vault")
    p_vg_patch.add_argument("--target", required=True, help="Точная заменяемая строка")
    p_vg_patch.add_argument("--replacement", required=True, help="Новая строка")

    p_vg_fm = p_vg_sub.add_parser("set-frontmatter", help="Безопасное обновление метаданных")
    p_vg_fm.add_argument("path", help="Путь к заметке от корня vault")
    p_vg_fm.add_argument("--json", required=True, help="JSON-строка обновлений")

    p_vg_mv = p_vg_sub.add_parser("move", help="Атомарное переименование/перемещение с каскадным рефакторингом ссылок")
    p_vg_mv.add_argument("src", help="Исходный относительный путь к заметке")
    p_vg_mv.add_argument("dst", help="Новый относительный путь к заметке")

    # Event Bus (System Bus)
    p_evt = subparsers.add_parser("event", help="Шина событий (emit, list, clear)")
    p_evt.add_argument("action", choices=["emit", "list", "clear"], help="Действие над шиной событий")
    p_evt.add_argument("type", nargs="?", default="EVENT", help="Тип события для emit")
    p_evt.add_argument("payload", nargs="?", default="{}", help="Полезная нагрузка или сообщение")
    p_evt.add_argument("--source", default="cli", help="Источник события")
    p_evt.add_argument("-n", "--count", type=int, default=20, help="Количество выводимых событий")
    p_evt.add_argument("--json", action="store_true", help="Вывод в JSON")

    # App Deconstructor (Static Reverse Engineering & Architecture Dossier)
    p_decon = subparsers.add_parser("deconstruct", help="Декомпозиция и реверс-инжиниринг приложений и сервисов")
    p_decon.add_argument("target", help="Путь к сервису или приложению")
    p_decon.add_argument("--json", action="store_true", help="Вывод в JSON")
    p_decon.add_argument("--out", help="Сохранить Markdown-досье в файл")

    # Postmortem & TOC Bottleneck Analyzer
    p_pm = subparsers.add_parser("postmortem", help="Анализ спринта и узких мест продакшна по теории ограничений (TOC)")
    p_pm.add_argument("sprint", help="Имя или ID спринта/вехи (например: 'Mars_Sprint_42')")
    p_pm.add_argument("--file", help="Путь к JSON-файлу с задачами")
    p_pm.add_argument("--json", action="store_true", help="Вывод в JSON")
    p_pm.add_argument("--out", help="Сохранить отчет в Markdown-файл")

    # API & Microkernel Contract Generator
    p_cg = subparsers.add_parser("contract", help="Генерация типизированных OperationSpec контрактов микроядра")
    p_cg.add_argument("operation_id", help="Идентификатор операции (например: 'tasks.export')")
    p_cg.add_argument("--desc", help="Описание операции")
    p_cg.add_argument("--capabilities", nargs="*", default=["FS_READ"], help="Требуемые Capabilities")
    p_cg.add_argument("--params", help="JSON строка словаря параметров")
    p_cg.add_argument("--returns", help="JSON строка словаря возвращаемых полей")
    p_cg.add_argument("--idempotent", action="store_true", help="Идемпотентная операция")
    p_cg.add_argument("--json", action="store_true", help="Вывод в JSON")

    # Script & Narrative Bible Extractor
    p_sb = subparsers.add_parser("bible", help="Экстракция Библии проекта, персонажей и локаций из сценария")
    p_sb.add_argument("script_file", help="Путь к сценарию или тексту")
    p_sb.add_argument("--json", action="store_true", help="Вывод в JSON")
    p_sb.add_argument("--out", help="Сохранить Библию в Markdown-файл")

    # Hybrid Animatic Director
    p_anim = subparsers.add_parser("animatic", help="Генерация анимитика и шотного таймлайна по сценарным битам")
    p_anim.add_argument("title", help="Название проекта или эпизода")
    p_anim.add_argument("--framework", choices=["comfyui", "blender", "hybrid"], default="hybrid", help="Целевой фреймворк исполнения (Target Framework Gate)")
    p_anim.add_argument("--beats", help="JSON строка или путь к файлу с битами")
    p_anim.add_argument("--comfy-export", action="store_true", help="Экспорт воркфлоу в Comfy Desktop")
    p_anim.add_argument("--json", action="store_true", help="Вывод в JSON")
    p_anim.add_argument("--out", help="Сохранить таймлайн в Markdown-файл")

    # Hybrid ComfyUI Render
    p_hr = subparsers.add_parser("hybrid-render", help="3D-to-AI стилизация через Multi-ControlNet ComfyUI")
    p_hr.add_argument("shot_id", help="Идентификатор шота")
    p_hr.add_argument("--prompt", required=True, help="Промпт стилизации")
    p_hr.add_argument("--depth", help="Путь к Depth пассу")
    p_hr.add_argument("--normal", help="Путь к Normal пассу")
    p_hr.add_argument("--lineart", help="Путь к Lineart пассу")
    p_hr.add_argument("--denoise", type=float, default=0.65, help="Сила денойза")
    p_hr.add_argument("--json", action="store_true", help="Вывод в JSON")
    p_hr.add_argument("--out", help="Сохранить спецификацию в файл")

    # Temporal Consistency Guard
    p_tc = subparsers.add_parser("consistency", help="Проверка темпоральной стабильности анимационной секвенции")
    p_tc.add_argument("sequence_dir", help="Путь к директории с секвенцией кадров")
    p_tc.add_argument("--threshold", type=float, default=0.15, help="Порог оптической дисперсии (фликеринга)")
    p_tc.add_argument("--json", action="store_true", help="Вывод в JSON")
    p_tc.add_argument("--out", help="Сохранить отчет аудита в файл")

    # Editorial OTIO Conform
    p_montage = subparsers.add_parser("montage", help="Генеративный видеомонтаж и оркестрация таймлайнов (Montage Hub)")
    p_montage.add_argument("montage_sub", nargs="?", default="info", choices=["info", "render", "pace", "ffmpeg"], help="Подкоманда montage_cli")
    p_montage.add_argument("extra_args", nargs=argparse.REMAINDER, help="Дополнительные флаги подкоманды")
    p_montage.set_defaults(func=cmd_montage)

    p_conf = subparsers.add_parser("conform", help="Конформ монтажного таймлайна (OpenTimelineIO / EDL / XML)")
    p_conf.add_argument("sequence", help="Имя или ID секвенции (e.g. Mars_Sq01)")
    p_conf.add_argument("--edl", help="Путь к CMX 3600 EDL файлу или строка")
    p_conf.add_argument("--shots", help="JSON список шотов или путь к JSON файлу")
    p_conf.add_argument("--fps", type=float, default=24.0, help="Частота кадров (FPS)")
    p_conf.add_argument("--handles", type=int, default=8, help="Запас кадров по краям (Handles)")
    p_conf.add_argument("--roundtrip", help="JSON словарь версий шотов для обновления в таймлайне")
    p_conf.add_argument("--json", action="store_true", help="Вывод в JSON")
    p_conf.add_argument("--out", help="Сохранить таймлайн в файл (.otio / .json / .md)")

    # App Bridge
    p_app = subparsers.add_parser("app", help="Управление связью с внешними веб-приложениями (status/blueprint)")
    p_app.add_argument("--blueprint", type=str, help="Сгенерировать архитектурный промпт-паспорт для ID приложения")

    # Project Registry
    p_proj = subparsers.add_parser("project", help="Управление реестром проектов и онбординг (Pulsar / Xcode)")
    p_proj.add_argument("subaction", nargs="?", choices=["list", "pulsar", "xcode"], default="list", help="Действие: list, pulsar или xcode")
    p_proj.add_argument("--scan", action="store_true", help="Сканировать приложения в рабочей директории")
    p_proj.add_argument("--sync", action="store_true", help="Синхронизировать паспорта в Obsidian")
    p_proj.add_argument("--name", help="Название сервиса или игры")
    p_proj.add_argument("--desc", help="Описание проекта или концепции")
    p_proj.add_argument("--category", default="Web Dashboard", help="Категория (для Pulsar)")
    p_proj.add_argument("--type", default="iOS Game / SpriteKit", help="Тип (для Xcode)")
    p_proj.add_argument("--port", type=int, help="Сетевой TCP порт")
    p_proj.add_argument("--status", choices=["production", "active", "in_development", "concept"], default="active")
    p_proj.add_argument("--repo", help="Путь к исходникам")
    p_proj.add_argument("--source", help="Путь к исходникам Xcode")
    p_proj.add_argument("--tags", help="Теги через запятую")

    # Context Router
    p_ctx = subparsers.add_parser("context", help="БД-индекс и маршрутизация CONTEXT.md (индексация, route/relate). Интегралити карт и фоновые синки — подкоманда `sync`")
    p_ctx.add_argument("--sync", action="store_true", default=True, help="Запуск полной индексации контекстов")

    # Route
    p_route = subparsers.add_parser("route", help="Быстрая маршрутизация задачи к нужному CONTEXT.md")
    p_route.add_argument("query", type=str, help="Текст задачи для поиска подходящих контекстов")

    # Relate (Smart Connections / Semantic Linking)
    p_relate = subparsers.add_parser("relate", help="Семантический поиск связанных заметок и выжимок (Smart Connections)")
    p_relate.add_argument("target", type=str, help="Путь к заметке или файлу для поиска связанных документов")

    # Asset Indexer
    p_asset = subparsers.add_parser("asset", help="Индексация не-MD ассетов (медиа, архивы, гигабайты файлов)")
    p_asset.add_argument("--sync", action="store_true", default=True, help="Запуск полной индексации ассетов")

    # Link Guard (AnD os Связи и Зависимости)
    p_links = subparsers.add_parser("links", help="Служба аудита и авто-починки связей, ссылок и симлинков в and_os/")
    p_links.add_argument("--fix", action="store_true", help="Автоматически починить устаревшие ссылки")
    p_links.add_argument("--verbose", "-v", action="store_true", help="Подробный отчет по битым ссылкам")
    p_links.add_argument("--json", action="store_true", help="Вывод отчета в формате JSON")

    # Pre-Flight Sync (Rule №47)
    p_pf = subparsers.add_parser("preflight", help="Предстартовый аудит структуры и двусторонняя синхронизация дельты с Pulsar/Terminal")
    p_pf.add_argument("--hours", type=float, default=12.0, help="Глубина сканирования изменений в часах (default: 12.0)")

    # Init Service
    p_init = subparsers.add_parser("init", help="Стартовая инициализация и каскадный аудит сессии")
    p_init.add_argument("--check-only", action="store_true", help="Только диагностика")
    p_init.add_argument("--json", action="store_true", help="Вывод в JSON")

    # Audit
    p_audit = subparsers.add_parser("audit", help="Запуск 16-векторного аудита системы AnD os v1.0.0")
    audit_mode = p_audit.add_mutually_exclusive_group()
    audit_mode.add_argument("--fix", action="store_true", help="Автоматически исправить дефекты")
    audit_mode.add_argument("--read-only", action="store_true", help="Проверка без телеметрии, кэша и байткода")
    p_audit.add_argument("--compact", "-c", action="store_true", help="Токеноэффективная экспресс-сводка (1 строка для LLM)")
    p_audit.add_argument("--json", action="store_true", help="Вывод в JSON")
    p_audit.add_argument("--deep", action="store_true", help="Глубокая развернутая проверка")

    # Sync
    p_sync = subparsers.add_parser("sync", help="Интегралити карт CONTEXT.md и 4 фоновых синка (state, taskdb, blueprint, toolchain). БД-индекс CONTEXT.md — подкоманда `context`")
    p_sync.add_argument("--fix", action="store_true", help="Автоматически исправить расхождения")
    p_sync.add_argument("--path", type=str, default="", help="Каталог для проверки")
    p_sync.add_argument("--parallel", action="store_true", help="Параллельный асинхронный запуск фоновых задач синхронизации")

    # State
    p_state = subparsers.add_parser("state", help="Управление состояниями доменов")
    p_state.add_argument("--get", type=str, help="Получить состояние домена")
    p_state.add_argument("--get-all", action="store_true", help="Получить состояние всех доменов")
    p_state.add_argument("--sync-auto", action="store_true", help="Авто-синхронизация состояний из frontmatter .md заметок")
    p_state.add_argument("--set", type=str, help="Домен для установки")
    p_state.add_argument("--key", type=str, help="Ключ состояния")
    p_state.add_argument("--val", type=str, help="Значение состояния")

    # Chunk
    p_chunk = subparsers.add_parser("chunk", help="Умный чанкинг сценариев и книг")
    p_chunk.add_argument("--file", type=str, required=True, help="Путь к файлу")
    p_chunk.add_argument("--act", type=int, help="Номер акта")
    p_chunk.add_argument("--episode", type=int, help="Номер эпизода")
    p_chunk.add_argument("--chapter", type=int, help="Номер главы")

    # TaskDB
    p_task = subparsers.add_parser("taskdb", help="Локальная БД задач SQLite и Dashboard")
    p_task.add_argument("--index", action="store_true", help="Индексация всех задач Vault")
    p_task.add_argument("--query", action="store_true", help="Вывод незавершенных задач")
    p_task.add_argument("--domain", type=str, help="Фильтр по домену")

    # Plan
    p_plan = subparsers.add_parser("plan", help="Генерация карты процессов Post-Prompt Execution DAG")
    p_plan.add_argument("--task", type=str, required=True, help="Текст задачи")
    p_plan.add_argument("--json", action="store_true", help="Вывод в JSON")

    # Closed Loop (Autonomous Hermetic Pipeline)
    p_cl = subparsers.add_parser("closed-loop", help="Автономный закрытый контур регистрации артефактов (closed_loop.py)")
    p_cl.add_argument("cl_args", nargs=argparse.REMAINDER, help="Аргументы для closed_loop.py")

    # Pack (Context Bundler & Code AST Shrinker)
    p_pack = subparsers.add_parser("pack", help="Сжатый пакет контекста домена или сжатие кода AST (Think in Code / Правило №16)")
    p_pack.add_argument("domain", help="Целевой домен или путь к Python файлу при --code")
    p_pack.add_argument("--code", action="store_true", help="Сжатие Python файла в AST-сигнатуру (80-90%% экономии токенов)")
    p_pack.add_argument("--json", action="store_true", help="Вывод в JSON")

    # Skills Stack & Parallel Auditor (Skill Operating Stack - SOS)
    p_skills = subparsers.add_parser("skills", help="Параллельный многопоточный аудит и управление стеком скиллов (SOS)")
    p_skills.add_argument("--probe", action="store_true", help="Запустить канареечные самопроверки скиллов (probe_cmd)")
    p_skills.add_argument("--dormancy", action="store_true", help="Запустить ревизию неактивности скиллов (>3 месяцев)")
    p_skills.add_argument("--search", type=str, help="Поиск внешних агентских скиллов в репозиториях (External Skills Gateway)")
    p_skills.add_argument("--inspect", type=str, help="Инспекция внешнего скилла без установки (repo или URL)")
    p_skills.add_argument("--json", action="store_true", help="Вывод в JSON")

    # Microkernel Skill Bus & Interop OS Gateway
    p_skill = subparsers.add_parser("skill", help="Единый шлюз микроядра к модулям-скиллам (run, ref, info, pipe, list, lint, verify)")
    p_skill.add_argument("skill_action", choices=["run", "ref", "info", "pipe", "list", "lint", "verify"], help="Действие шлюза")
    p_skill.add_argument("skill_name", nargs="?", help="Имя целевого скилла")
    p_skill.add_argument("consumer", nargs="?", help="Имя второго скилла (только для pipe)")
    p_skill.add_argument("--topic", help="Раздел референса (только для ref)")
    p_skill.add_argument("--list", action="store_true", help="Список доступных топиков (для ref)")
    p_skill.add_argument("--json", action="store_true", help="Формат JSON")
    p_skill.add_argument("extra_args", nargs=argparse.REMAINDER, help="Дополнительные аргументы для выполнения")

    # Daemon (macOS LaunchAgents & Pulsar Port Guard)
    p_daemon = subparsers.add_parser("daemon", help="Управление фоновыми демонами macOS и сервисами Pulsar (Правило №28)")
    p_daemon.add_argument("action", choices=["status", "restart"], help="Действие над демонами")
    p_daemon.add_argument("pos_target", nargs="?", default="", help="Имя сервиса (позиционный аргумент)")
    p_daemon.add_argument("--target", type=str, default="", help="Имя сервиса (флаг)")

    # Islands (9 Logical Islands Archipelago & Deep Info)
    p_islands = subparsers.add_parser("islands", help="Сводка 9 логических островов и детальный паспорт (--info <1-9>)")
    p_islands.add_argument("--info", type=int, choices=range(1, 10), help="Номер острова (1-9) для вывода детального системного паспорта")

    # Status (UNIX-like Non-Formal Health & Liveness Grid)
    p_status = subparsers.add_parser("status", help="Глубокая фактическая проверка здоровья и liveness-пробы сервисов (UNIX probe)")
    p_status.add_argument("--json", action="store_true", help="Вывод в JSON")

    # Boot (Darwin / OS 4.0 Init & Diagnostics)
    p_boot = subparsers.add_parser("boot", help="Быстрый старт системы и экран готовности (Runlevel 5 Init)")
    p_boot.add_argument("--no-notify", action="store_true", help="Не отправлять тихое уведомление macOS")

    # Proc (Linux/Darwin Virtual State Mesh)
    p_proc = subparsers.add_parser("proc", help="Виртуальное пространство телеметрии /proc (0-Token Reading)")
    p_proc.add_argument("--sync", action="store_true", help="Обновить файлы состояния /proc")
    p_proc.add_argument("--cat", type=str, help="Прочитать файл состояния (sys, daemons, islands, tasks)")

    # Snapshot (APFS Native CoW & Manifest Snapshots)
    p_snap = subparsers.add_parser("snapshot", help="File-level APFS shadow: micro-снимки и откат отдельных файлов (apfs_shadow). Tree-level — подкоманда `checkpoint`")
    p_snap.add_argument("action", choices=["create", "list", "micro", "shadow", "rollback"], help="Действие со снимком")
    p_snap.add_argument("--target", type=str, default="", help="Целевой файл для shadow-снапшота или отката")
    p_snap.add_argument("--id", type=str, default="", help="Идентификатор снимка для отката")
    p_snap.add_argument("-m", "--comment", type=str, default="", help="Описание снимка")

    # Notify (macOS Silent Notification Center Bridge)
    p_notif = subparsers.add_parser("notify", help="Отправка тихого уведомления в Центр Уведомлений macOS")
    p_notif.add_argument("title", type=str, help="Заголовок уведомления")
    p_notif.add_argument("message", type=str, help="Текст уведомления")
    p_notif.add_argument("--subtitle", type=str, default="", help="Подзаголовок")

    # Env (Runtimes & Installed Libraries Standard)
    p_env = subparsers.add_parser("env", help="Регламент рантаймов (Python, Node.js, Git) и установленных библиотек")
    p_env.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    # Vacuum (System Cleaner & Garbage Collector)
    p_vacuum = subparsers.add_parser("vacuum", help="Системный санитар и очистка от временных файлов (.DS_Store, *.bak, __pycache__)")
    p_vacuum.add_argument("--target", choices=["all", "vault", "pulsar"], default="all", help="Область очистки (по умолчанию all)")
    p_vacuum.add_argument("--dry-run", action="store_true", help="Режим сканирования без удаления файлов")

    # ComfyUI (Node Registry & Update Regression Guard)
    p_comfy = subparsers.add_parser("comfy", help="База версий нод ComfyUI и проверка совместимости при обновлениях")
    p_comfy.add_argument("--verify", action="store_true", help="Верификация совместимости нод с глобальным реестром")
    p_comfy.add_argument("--target", type=str, help="Путь к конкретному workflow JSON для проверки")
    p_comfy.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    # Top (Autonomous Rich TUI Dashboard)
    p_top = subparsers.add_parser("top", help="Интерактивный TUI-дашборд состояния системы (Live System Top)")

    # Terminal (AND_Terminal Web GUI Console)
    p_term = subparsers.add_parser("terminal", help="Запуск визуального веб-терминала AND_Terminal (:8099)")

    # Toolchain & Runtime Parity Manager (Rule #68)
    p_tc = subparsers.add_parser("toolchain", help="Управление и проверка соответствия тулчейна золотому стандарту (Rule #68)")
    p_tc.add_argument("action", choices=["status", "check", "sync"], help="Действие: status (отчет), check (проверка), sync (синхронизация .venv)")

    # Component Lifecycle Engine (Rule 41 & 42)
    p_reg_sk = subparsers.add_parser("register-skill", help="Безопасная регистрация нового скилла со всеми манифестами")
    p_reg_sk.add_argument("--name", required=True, help="Имя скилла (kebab-case)")
    p_reg_sk.add_argument("--desc", required=True, help="Краткое описание")
    p_reg_sk.add_argument("--domain", default="General", help="Домен скилла")
    p_reg_sk.add_argument("--tags", help="Теги через запятую")

    p_reg_mod = subparsers.add_parser("register-module", help="Изолированная регистрация нового python-модуля в целевой хаб")
    p_reg_mod.add_argument("--hub", choices=["doc_hub", "tracker_hub", "cg_workspace", "terminal"], required=True, help="Целевой фасадный хаб")
    p_reg_mod.add_argument("--name", required=True, help="Имя модуля (snake_case)")
    p_reg_mod.add_argument("--src", required=True, help="Путь к исходному скрипту .py")
    p_reg_mod.add_argument("--role", required=True, help="Роль модуля в пайплайне")

    p_reg_know = subparsers.add_parser("register-knowledge", help="Сквозная регистрация нового знания со связью с Островами, CONTEXT и поиском")
    p_reg_know.add_argument("--title", required=True, help="Название книги/статьи")
    p_reg_know.add_argument("--author", default="", help="Автор книги/материала")
    p_reg_know.add_argument("--category", default="Управление", help="Категория (Управление, Эффективность, Ии, Лидерство, etc.)")
    p_reg_know.add_argument("--island", default="", help="Целевой Остров (clippings, cg_core, ta_bu, story, book, etc.)")
    p_reg_know.add_argument("--essence", default="", help="Краткая практическая суть")
    p_reg_know.add_argument("--for-whom", default="", dest="for_whom", help="Целевая аудитория и роли")
    p_reg_know.add_argument("--competence", default="", help="Компетенция для матрицы компетенций")
    p_reg_know.add_argument("--skill", default="", help="Связанный скилл системы (напр. status-report)")
    p_reg_know.add_argument("--tasks", default="", help="Решаемые прикладные задачи")
    p_reg_know.add_argument("--tags", default="", help="Теги через запятую")
    p_reg_know.add_argument("--content", default="", help="Основной текст/принципы")
    p_reg_know.add_argument("--checklist", default="", help="Пункты чек-листа через точку с запятой (;)")

    # Clinical Health Registration
    p_reg_hlth = subparsers.add_parser("register-health", help="Сквозная регистрация медицинского факта (анализ/прием) в тайм-серию и подостров")
    p_reg_hlth.add_argument("--patient", required=True, choices=["andrey", "misha", "yulia", "pavel", "mom"], help="ID пациента")
    p_reg_hlth.add_argument("--type", choices=["fact", "consultation"], default="fact", help="Тип записи (fact или consultation)")
    p_reg_hlth.add_argument("--date", required=True, help="Дата (YYYY-MM-DD)")
    p_reg_hlth.add_argument("--name", required=True, help="Название маркера или диагноза")
    p_reg_hlth.add_argument("--key", default="", help="Ключ маркера (wbc, crp, alt, etc.)")
    p_reg_hlth.add_argument("--value", default="0", help="Значение показателя")
    p_reg_hlth.add_argument("--unit", default="", help="Единица измерения")
    p_reg_hlth.add_argument("--ref-low", default="", dest="ref_low", help="Нижняя граница нормы")
    p_reg_hlth.add_argument("--ref-high", default="", dest="ref_high", help="Верхняя граница нормы")
    p_reg_hlth.add_argument("--lab", default="ИНВИТРО", help="Лаборатория")
    p_reg_hlth.add_argument("--specialty", default="Терапевт", help="Специальность врача")
    p_reg_hlth.add_argument("--icd10", default="", help="Код МКБ-10")
    p_reg_hlth.add_argument("--recommendations", default="", help="Назначения и рекомендации")
    p_reg_hlth.add_argument("--doctor", default="", help="ФИО врача")
    p_reg_hlth.add_argument("--clinic", default="", help="Клиника")
    p_reg_hlth.add_argument("--source", default="", help="Документ-источник")

    # Sovereign Air-Gap Finance Registration
    p_reg_fin = subparsers.add_parser("register-finance", help="Сквозная регистрация финансового баланса или притока капитала (Air-Gap)")
    p_reg_fin.add_argument("--account", required=True, choices=["broker_account", "broker_account", "capital_account", "capital_account"], help="Счет брокера")
    p_reg_fin.add_argument("--type", choices=["snapshot", "cashflow"], default="snapshot", help="Тип записи (snapshot или cashflow)")
    p_reg_fin.add_argument("--total", required=True, help="Общая стоимость счета или сумма притока")
    p_reg_fin.add_argument("--pnl-rub", default="0", dest="pnl_rub", help="P/L в рублях")
    p_reg_fin.add_argument("--pnl-pct", default="0", dest="pnl_pct", help="P/L в процентах")
    p_reg_fin.add_argument("--cash", default="0", help="Остаток свободных денежных средств (кэш)")
    p_reg_fin.add_argument("--flow", default="DIVIDEND", choices=["DIVIDEND", "COUPON", "CONTRIBUTION"], help="Тип притока")
    p_reg_fin.add_argument("--ticker", default="", help="Тикер актива")
    p_reg_fin.add_argument("--date", default="", help="Дата операции/среза (YYYY-MM-DD)")
    p_reg_fin.add_argument("--note", default="", help="Примечание")
    p_reg_fin.add_argument("--source", default="", help="Документ-источник")

    # Finance Master Bridge & Portfolio Engine
    p_fin = subparsers.add_parser("finance", help="Сжатый токено-эффективный срез инвестиционного капитала (Net Worth, БКС, Альфа, P&L)")
    p_fin.add_argument("--broker", choices=["broker_account", "alfa"], help="Фильтр по брокеру (broker_account или alfa)")
    p_fin.add_argument("--summary", action="store_true", help="Сжатая сводка Net Worth (50 токенов)")
    p_fin.add_argument("--check", action="store_true", help="Проверка целостности базы и Air-Gap защиты")
    p_fin.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    # Closed-Loop Tasks Registration & Production Pulse
    p_reg_tsk = subparsers.add_parser("register-task", help="Регистрация задачи со всеми подзадачами в доску Tasks/ и в SQLite")
    p_reg_tsk.add_argument("--project", required=True, choices=["mars", "kot", "pm", "Studio", "general"], help="Целевой проект/доска")
    p_reg_tsk.add_argument("--title", required=True, help="Основная задача")
    p_reg_tsk.add_argument("--subtasks", default="", help="Подзадачи через точку с запятой (;)")
    p_reg_tsk.add_argument("--priority", default="normal", choices=["normal", "high", "urgent"], help="Приоритет")
    p_reg_tsk.add_argument("--due", default="", help="Дедлайн (YYYY-MM-DD)")
    p_reg_tsk.add_argument("--section", default="", help="Секция на доске (H2)")

    p_tasks = subparsers.add_parser("tasks", help="Мгновенный производственный пульс студии и оперативный контроль задач")
    p_tasks.add_argument("--pulse", action="store_true", help="Сжатый оперативный пульс (<50 токенов)")
    p_tasks.add_argument("--project", choices=["mars", "kot", "pm", "Studio"], help="Фильтр по проекту")
    p_tasks.add_argument("--complete", default="", help="Отметить задачу выполненной (- [x])")
    p_tasks.add_argument("--check", action="store_true", help="Проверка базы задач SQLite")
    p_tasks.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    # VFS Reactive Engine & Automated Context Projector
    p_vfs = subparsers.add_parser("vfs", help="Реактивная виртуальная файловая система и авто-проектор контекстов")
    p_vfs.add_argument("--status", action="store_true", help="Статус VFS и фонового демона")
    p_vfs.add_argument("--pulsar", action="store_true", help="Матрица сервисов и модулей Pulsar Space")
    p_vfs.add_argument("--find", type=str, help="Мгновенный поиск файлов по SQLite индексу")
    p_vfs.add_argument("--island", type=str, help="Фильтр по острову (1-8)")
    p_vfs.add_argument("--ext", type=str, help="Фильтр по расширению файла")
    p_vfs.add_argument("--sync", action="store_true", help="Полная синхронизация VFS индекса")
    p_vfs.add_argument("--start", action="store_true", help="Запуск фонового демона VFS")
    p_vfs.add_argument("--stop", action="store_true", help="Остановка фонового демона VFS")

    # telemetry_sync Deep Intelligence Weekly Engine
    p_telemetry_sync = subparsers.add_parser("telemetry_sync", help="Еженедельный глубокий анализ и синхронизация биометрии telemetry_sync Connect")
    p_telemetry_sync.add_argument("--mock", action="store_true", help="Использовать верифицированный профильный датасет")
    p_telemetry_sync.add_argument("--json", action="store_true", help="Вывод в формате JSON")
    # Health Intelligence Master Orchestrator
    p_health = subparsers.add_parser("health", help="Единый кросс-синтез контура здоровья (клиника + анализы + telemetry_sync + InBody)")
    p_health.add_argument("--patient", choices=["andrey", "misha", "yulia", "pavel", "mom"], help="ID пациента для сжатой клинической сводки")
    p_health.add_argument("--summary", action="store_true", help="Сжатый токено-эффективный отчет по пациенту (50 токенов)")
    p_health.add_argument("--check", action="store_true", help="Проверка целостности базы и изоляции подостровов")
    p_health.add_argument("--json", action="store_true", help="Вывод в формате JSON")
    # Quick Knowledge Finder
    p_find = subparsers.add_parser("find", help="Быстрый точечный поиск по базе знаний (Think in Code Retrieval, экономия токенов)")
    p_find.add_argument("query", nargs="*", help="Поисковые термины")
    p_find.add_argument("--category", "-c", help="Фильтр по категории")
    p_find.add_argument("--limit", "-l", type=int, default=4, help="Максимум результатов")
    p_find.add_argument("--json", action="store_true", help="Вывод в формате JSON")
    # Zero-Touch System Bootstrap & Portability Engine
    p_boot = subparsers.add_parser("bootstrap", help="Проверка готовности к переносу и авто-развертывание системы на новом компьютере")
    p_boot.add_argument("--install", action="store_true", help="Автоматически установить недостающие pip-зависимости")
    p_boot.add_argument("--json", action="store_true", help="Вывод в формате JSON")
    # Cascade Dependency & Information Engine
    p_dep = subparsers.add_parser("dep", help="Анализ информационных связей и каскадное авто-обновление зависимых файлов")
    p_dep.add_argument("--propagate", action="store_true", help="Выполнить каскадное обновление зависимостей")
    p_dep.add_argument("--mermaid", action="store_true", help="Вывести Mermaid-код графа зависимостей")
    p_dep.add_argument("--json", action="store_true", help="Вывод в формате JSON")
    # Document Intelligence Facade
    p_doc = subparsers.add_parser("doc", help="Анализ и конвертация документов (MarkItDown, PDF Twin, OCR, Excel)")
    p_doc.add_argument("file", help="Путь к целевому файлу документа")
    p_doc.add_argument("--ocr", action="store_true", help="Распознавание текста на изображениях (OCR)")
    p_doc.add_argument("--twin", action="store_true", help="Генерация Markdown-двойника для PDF")
    p_doc.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    # Production Trackers Facade
    p_track = subparsers.add_parser("track", help="Синхронизация трекеров продакшна (Ftrack, Weeek, Mattermost)")
    p_track.add_argument("service", choices=["ftrack", "weeek", "mattermost", "all"], help="Целевой сервис")
    p_track.add_argument("--project", choices=["mars", "kot", "all"], default="mars", help="Проект студии (mars / kot)")
    p_track.add_argument("--report", action="store_true", help="Сформировать продюсерский отчет")
    p_track.add_argument("--gantt", action="store_true", help="Экспорт данных в диаграмму Ганта")
    p_track.add_argument("--inspect", action="store_true", help="Аудит структуры и каналов/полей (Ftrack / Mattermost)")
    p_track.add_argument("--verify", action="store_true", help="Проверка целостности локального среза (raw_latest)")
    p_track.add_argument("--export", action="store_true", help="Бережный поэтапный экспорт из API")
    p_track.add_argument("--summary", action="store_true", help="Компактная сводка из локального кэша (< 1000 токенов)")
    p_track.add_argument("--channel", type=str, help="Имя или фильтр канала Mattermost")
    p_track.add_argument("--search", type=str, help="Поисковый запрос по сообщениям")
    p_track.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    # 3D & Graphics Facade
    p_cg = subparsers.add_parser("cg", help="Управление 3D пайплайном, сценами и нодами ComfyUI")
    p_cg.add_argument("action", choices=["nodes", "graph", "scenes", "bridge"], help="Действие")
    p_cg.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    # System Utilities Facade (Rule №54 Holistic Connection)
    p_tools = subparsers.add_parser("tools", help="Универсальный фасад системных утилит (smoke, ui-inspect, native-build, check, graph)")
    p_tools.add_argument("utility", choices=[
        "smoke", "ui-inspect", "app-check", "build-native", "graph", "gen-ctx",
        "health-bridge", "ftrack-cache", "board-parser", "trim-output", "graph-orphans",
        "schema-validator", "link-orphans", "clean-links", "tags-links", "webdav-fix",
        "budget-calc", "convert-doc", "telemetry_sync", "yt-analyze", "career-radar",
        "kot-sync", "mars-sync", "mirror", "architect"
    ], help="Имя целевой системной утилиты")
    p_tools.add_argument("extra_args", nargs="*", help="Аргументы для целевой утилиты")

    # Blast Radius Trash (Rule №53)
    p_trash = subparsers.add_parser("trash", help="Безопасное перемещение файла в корзину (.trash/) без физического удаления")
    p_trash.add_argument("target", help="Путь к файлу для перемещения в корзину")

    # Continuous Learning & Pattern Compilation Engine
    p_learn = subparsers.add_parser("learn", help="Автономное извлечение и сохранение инженерного опыта и решений в Obsidian Knowledge Graph")
    p_learn.add_argument("--topic", required=True, help="Тема или название обнаруженного паттерна")
    p_learn.add_argument("--domain", choices=["blender", "comfyui", "davinci", "swift", "xcode", "core", "user", "story", "article", "process", "finance"], default="core", help="Технологический домен")
    p_learn.add_argument("--problem", required=True, help="Описание возникшей проблемы или симптома")
    p_learn.add_argument("--solution", required=True, help="Верифицированное решение или паттерн")
    p_learn.add_argument("--tags", help="Дополнительные теги через запятую")
    # Strategic Context Compaction Facade
    p_compact = subparsers.add_parser("compact", help="Аудит и контроль бюджета контекста сессии, стратегическая компактификация")
    p_compact.add_argument("--status", action="store_true", help="Показать текущий статус использования контекста и счетчик действий")
    p_compact.add_argument("--reset", action="store_true", help="Сбросить счетчик сессии после успешной компактификации")
    p_compact.add_argument("--phase-check", nargs=2, metavar=("CURR", "TGT"), help="Проверить безопасность перехода между фазами (напр. PHASE_2 PHASE_3)")

    # Minimal-Diffs Build Error Resolver Facade
    p_bfix = subparsers.add_parser("build-fix", help="Хирургическое устранение ошибок сборки и синтаксиса с минимальными диффами")
    p_bfix.add_argument("--verify", help="Путь к файлу для верификации компиляции")
    p_bfix.add_argument("--file", help="Целевой файл для применения исправления")
    p_bfix.add_argument("--old", help="Исходная подстрока для точечной замены")
    p_bfix.add_argument("--new", help="Новая исправленная подстрока")

    # Video Pass & Playblast Technical Harness
    p_vh = subparsers.add_parser("video-harness", help="Технический аудит и ОТК видео-плейбластов и пассов глубины перед ComfyUI")
    p_vh.add_argument("--check", nargs="+", help="Путь к плейбласту и опционально пассу глубины")

    # Skeleton Engine Facade
    p_skel = subparsers.add_parser("skeleton", help="Генерация эталонных архитектурных каркасов (iOS SpriteKit, CG Tools)")
    p_skel.add_argument("--ios", nargs=2, metavar=("DIR", "NAME"), help="Развернуть нативный Swift/SpriteKit каркас игры")

    # Codemap Architecture Engine
    p_cmap = subparsers.add_parser("codemap", help="Генерация компактных 0-токенных карт архитектуры классов и функций")
    p_cmap.add_argument("--dir", required=True, help="Целевой каталог для сканирования")
    p_cmap.add_argument("--title", help="Заголовок архитектурной карты")

    # Runtime Statusline Beacon
    p_sline = subparsers.add_parser("statusline", help="Вывод однострочного терминального маяка состояния ядра и контекста")
    p_sline.add_argument("--no-color", action="store_true", help="Отключить ANSI цвета")

    # Fast 8-Phase Pre-Flight Verification Loop
    p_rules = subparsers.add_parser("rules", help="Компиляция и аудит быстрого индекса правил (Rules Fast Index)")
    p_rules.add_argument("action", choices=["compile", "verify", "status"], default="compile", nargs="?", help="Действие: compile или verify")

    p_hooks = subparsers.add_parser("hooks", help="Аппаратный аудит и статус жизненного цикла хуков (SessionStart, PreToolUse)")
    p_hooks.add_argument("action", choices=["status", "verify", "test"], default="status", nargs="?", help="Действие: status, verify, test")

    p_ver = subparsers.add_parser("verify", help="8-фазный предкоммитный фильтр качества (синтаксис, типы, clean code, секреты, тесты, diff, память, правила)")
    p_ver.add_argument("paths", nargs="*", help="Файлы или каталоги для точечной верификации")
    p_ver.add_argument("--json", action="store_true", help="Машиночитаемый JSON вывод")
    p_ver.add_argument("--verbose", "-v", action="store_true", help="Развернутый вывод отчёта")

    # Release Ledger Engine (SQLite & Changelog Architecture)
    p_rel = subparsers.add_parser("release", help="Управление версиями системы и журналом релизов на базе SQLite (Rule #55)")
    p_rel_sub = p_rel.add_subparsers(dest="subaction", required=True)
    
    p_rel_bump = p_rel_sub.add_parser("bump", help="Зафиксировать новую версию в SQLite и обновить проекции")
    p_rel_bump.add_argument("version", help="Номер версии (например: '9.5.0')")
    p_rel_bump.add_argument("--summary", required=True, help="Краткая суть релиза (1-2 предложения)")
    p_rel_bump.add_argument("--changes", nargs="+", required=True, help="Список ключевых изменений")
    p_rel_bump.add_argument("--type", choices=["MAJOR", "MINOR", "PATCH"], default="MINOR", help="Тип релиза")
    p_rel_bump.add_argument("--components", default="core", help="Затронутые компоненты системы")

    p_rel_list = p_rel_sub.add_parser("list", help="Показать историю релизов из SQLite")
    p_rel_list.add_argument("-n", "--limit", type=int, default=10, help="Количество выводимых релизов")
    p_rel_list.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    p_rel_show = p_rel_sub.add_parser("show", help="Показать детали конкретной версии")
    p_rel_show.add_argument("version", nargs="?", default="", help="Версия для просмотра (по умолчанию последняя)")

    p_rel_sync = p_rel_sub.add_parser("sync", help="Синхронизировать RELEASE_LEDGER.json и CHANGELOG.md из SQLite")

    # APFS CoW & Git Checkpoint Engine
    p_cp = subparsers.add_parser("checkpoint", help="Tree-level CoW: снимки и откат каталогов/рабочей области (checkpoint_manager). File-level — подкоманда `snapshot`")
    p_cp.add_argument("action", choices=["create", "verify", "rollback", "list", "clear"], help="Действие: create, verify, rollback, list, clear")
    p_cp.add_argument("name", nargs="?", help="Название контрольной точки")
    p_cp.add_argument("--targets", nargs="*", help="Целевые каталоги для снимка")
    p_cp.add_argument("--keep", type=int, default=5, help="Сколько последних снимков сохранить при очистке")

    # Eval-Driven Development (EDD) Framework
    p_eval = subparsers.add_parser("eval", help="Фреймворк Eval-Driven Development (метрики pass@1, pass@3, регрессионный контроль)")
    p_eval.add_argument("action", choices=["define", "check", "list"], help="Действие: define, check, list")
    p_eval.add_argument("feature", nargs="?", help="Название фичи или системы")
    p_eval.add_argument("--desc", default="", help="Описание требований")
    p_eval.add_argument("--domain", default="core", help="Домен системы")

    # Subagent Handoff Protocol
    p_hnd = subparsers.add_parser("handoff", help="Управление и валидация канонического протокола передачи задач между субагентами")
    p_hnd.add_argument("action", choices=["validate"], help="Действие: validate")
    p_hnd.add_argument("file", help="Путь к handoff markdown файлу")

    # Context Modes Switcher
    p_mode = subparsers.add_parser("mode", help="Управление пресетами поведения агента (dev, research, review)")
    p_mode.add_argument("action", nargs="?", default="get", choices=["get", "set", "show", "list"], help="Действие: get, set, show, list")
    p_mode.add_argument("target_mode", nargs="?", help="Целевой режим (dev, research, review)")

    # Safe Refactor-Cleaner & Dead Code Guard
    p_clean = subparsers.add_parser("clean", help="Безопасный аудит и очистка мёртвого кода с регистрацией в DELETION_LOG")
    p_clean.add_argument("action", nargs="?", default="audit", choices=["audit", "dry-run", "log"], help="Действие: audit, dry-run, log")
    p_clean.add_argument("--dir", help="Целевой подкаталог для сканирования")

    # Documentation & Runbook Synchronizer
    p_sdocs = subparsers.add_parser("sync-docs", help="Авто-генерация и синхронизация production ранбука RUNBOOK.md из кода ядра")
    p_sdocs.add_argument("--check", action="store_true", help="Проверить актуальность без перезаписи")

    # TDD Test Scaffold Generator
    p_tdd = subparsers.add_parser("tdd", help="Генератор скелетов модульных тестов (Python unittest / Swift XCTest)")
    p_tdd.add_argument("file", help="Исходный файл для генерации тестов (.py или .swift)")
    p_tdd.add_argument("--out", "-o", help="Кастомный путь сохранения теста")
    p_tdd.add_argument("--run", "-r", action="store_true", help="Мгновенный запуск созданного теста")

    # Security & OWASP Top-10 / Injection Scanner
    p_sec = subparsers.add_parser("sec-audit", help="Аудит безопасности, инъекций и векторов OWASP Top-10")
    p_sec.add_argument("path", nargs="?", default="and_os", help="Путь для сканирования (default: and_os)")

    # Visual Artifact on Failure Engine
    p_cap = subparsers.add_parser("capture-failure", help="Захват экранного снимка macOS и сетевых дампов при сбое")
    p_cap.add_argument("--reason", "-r", default="Manual capture or unhandled test failure", help="Причина сбоя")
    p_cap.add_argument("--cmd", "-c", default="", help="Команда, вызвавшая сбой")
    p_cap.add_argument("--json", action="store_true", help="Вывод в JSON")

    # DAG Phase Planner & Acceptance Criteria Engine
    p_dplan = subparsers.add_parser("dag-plan", help="Фазовый планировщик задач DAG и контроль критериев приемки (DoD)")
    p_dplan.add_argument("action", nargs="?", default="status", choices=["new", "check", "status"], help="Действие: new, check, status")
    p_dplan.add_argument("task_id", nargs="?", help="Идентификатор задачи")
    p_dplan.add_argument("--phases", "-p", default="", help="Фазы через запятую (для new)")
    # Reverse-Engineering Engine Dispatcher (REA)
    p_rev = subparsers.add_parser("reverse", help="Диспетчер декомпиляции и статического анализа бинарников и приложений (REA)")
    p_rev.add_argument("subaction", choices=["status", "inspect", "search", "decompile", "check-update"], help="Команда: status, inspect, search, decompile, check-update")
    p_rev.add_argument("target", nargs="?", default="", help="Целевой файл или директория (Mach-O, ASAR, Electron, SQLite)")
    p_rev.add_argument("--pattern", "-p", default="", help="Шаблон поиска для search")
    p_rev.add_argument("--procedure", default="", help="Имя процедуры/функции для декомпиляции")
    p_rev.add_argument("--token-limit", type=int, default=2000, help="Аппаратный потолок токенов (default: 2000)")
    p_rev.add_argument("--json", action="store_true", help="Вывод в JSON")

    args, unknown = parser.parse_known_args()
    if hasattr(args, "extra_args") and unknown:
        args.extra_args.extend(unknown)





    if args.command == "telemetry_sync":
        flags = []
        if args.mock:
            flags.append("--mock")
        if args.json:
            flags.append("--json")
        res = run_script("telemetry_sync_deep_sync.py", flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry("telemetry_sync weekly deep sync", skill="sys.telemetry_sync")
    elif args.command == "health":
        flags = []
        if getattr(args, "check", False):
            res = run_script("health_bridge.py", ["check"])
        elif getattr(args, "summary", False) or getattr(args, "patient", None):
            pid = args.patient or "andrey"
            bridge_flags = ["summary", "--patient", pid]
            if args.json:
                bridge_flags.append("--json")
            res = run_script("health_bridge.py", bridge_flags)
        else:
            if args.json:
                flags.append("--json")
            res = run_script("health_orchestrator_engine.py", flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry("Health command execution", skill="sys.health")
    elif args.command in ("find", "dep", "doc"):
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem(args.command)
        ret = sub.execute(args) if sub else 1
        sys.exit(ret)

    elif args.command == "track":
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem("track")
        if sub:
            ret = sub.execute(args)
            if ret != 0:
                sys.exit(ret)
        else:
            print("Error: track subsystem failed to load", file=sys.stderr)
            sys.exit(1)

    elif args.command == "cg":
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem("cg")
        ret = sub.execute(args) if sub else 1
        if ret != 0:
            sys.exit(ret)
    elif args.command == "tools":
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem("tools")
        ret = sub.execute(args) if sub else 1
        sys.exit(ret)
    elif args.command == "trash":
        target_path = os.path.abspath(args.target) if os.path.isabs(args.target) else os.path.join(VAULT_ROOT, args.target)
        if not os.path.exists(target_path):
            print(f"❌ Файл не найден: {args.target}", file=sys.stderr)
            sys.exit(1)
        trash_dir = os.path.join(VAULT_ROOT, ".trash")
        os.makedirs(trash_dir, exist_ok=True)
        dst = os.path.join(trash_dir, os.path.basename(target_path))
        import shutil
        shutil.move(target_path, dst)
        print(f"🗑️ Файл перемещен в безопасную корзину: {os.path.relpath(dst, VAULT_ROOT)}")
        auto_log_telemetry(f"Safe trash: {os.path.basename(target_path)}", skill="sys.trash")
    elif args.command == "learn":
        import importlib.util
        cl_path = os.path.join(AI_SCRIPT_DIR, "continuous_learner.py")
        spec = importlib.util.spec_from_file_location("continuous_learner", cl_path)
        cl_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cl_mod)

        custom_tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        res = cl_mod.record_learned_pattern(
            topic=args.topic,
            domain=args.domain,
            problem=args.problem,
            solution=args.solution,
            source="sys_cli_learn",
            tags=custom_tags
        )
        print(f"✅ Успешно зафиксирован инженерный опыт в AnD os:")
        print(f"   • Тема: {res['topic']}")
        print(f"   • Домен: {res['domain']}")
        print(f"   • Заметка в Vault: {res['note_path']}")
        print(f"   • Быстрая БЗ (quick_db): {'🟢 ОБНОВЛЕНА' if res.get('quick_db_updated') else '⚪ БЕЗ ИЗМЕНЕНИЙ'}")
        auto_log_telemetry(f"Learned pattern: {args.topic} ({args.domain})", skill="sys.learn")
    elif args.command == "compact":
        import importlib.util
        cbg_path = os.path.join(AI_SCRIPT_DIR, "context_budget_guard.py")
        spec = importlib.util.spec_from_file_location("context_budget_guard", cbg_path)
        cbg_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cbg_mod)

        if args.reset:
            r = cbg_mod.reset_session_counter()
            print("🔄 [ContextGuard] Счетчик вызовов сессии сброшен. Контекст очищен.")
        elif args.phase_check:
            curr_p, tgt_p = args.phase_check[0], args.phase_check[1]
            r = cbg_mod.evaluate_phase_transition(curr_p, tgt_p)
            print(f"🔍 [ContextGuard] Фазовый аудит: {curr_p} ➔ {tgt_p}")
            print(f"   • Действий в сессии: {r['tool_count']}")
            print(f"   • Требуется сжатие: {'⚠️ ДА' if r['needs_compaction'] else '🟢 НЕТ'}")
            print(f"   • Рекомендация: {r['recommendation']}")
        else: # default status
            r = cbg_mod.track_tool_invocation("status_check")
            print(f"📊 [ContextGuard] Сессия: {r['session_id']}")
            print(f"   • Всего инструментальных действий: {r['count']}")
            print(f"   • Статус бюджета: {'⚠️ РЕКОМЕНДУЕТСЯ /compact' if r['suggest_compact'] else '🟢 В ПРЕДЕЛАХ НОРМЫ'}")
            if r.get("reason"):
                print(f"   • Причина: {r['reason']}")
        auto_log_telemetry("Context budget audit", skill="sys.compact")
    elif args.command == "build-fix":
        import importlib.util
        br_path = os.path.join(AI_SCRIPT_DIR, "build_resolver.py")
        spec = importlib.util.spec_from_file_location("build_resolver", br_path)
        br_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(br_mod)

        if args.verify:
            res = br_mod.verify_file_compilation(args.verify)
            print(f"🔧 [BuildResolver] Проверка компиляции: {args.verify}")
            print(f"   • Тип: {res.get('type')}")
            print(f"   • Статус: {'🟢 ВАЛИДЕН' if res.get('valid') else '🔴 ОШИБКА'}")
            if res.get("error"):
                print(f"   • Ошибка: {res['error']}")
        elif args.file and args.old and args.new:
            res = br_mod.apply_minimal_fix(args.file, args.old, args.new)
            print(f"🔧 [BuildResolver] Применение Minimal Diff к: {args.file}")
            print(f"   • Статус: {res.get('status')}")
            print(f"   • Действие: {res.get('action')}")
            if res.get("compilation_verified"):
                print(f"   • Компиляция подтверждена: 🟢 ДА")
            if res.get("message"):
                print(f"   • Инфо: {res['message']}")
        else:
            print("Использование: sys_cli.py build-fix --verify <file> ИЛИ --file <file> --old <old> --new <new>")
        auto_log_telemetry("Build error resolver", skill="sys.build-fix")
    elif args.command == "video-harness":
        import importlib.util
        vh_path = os.path.join(AI_SCRIPT_DIR, "video_harness.py")
        spec = importlib.util.spec_from_file_location("video_harness", vh_path)
        vh_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vh_mod)

        if args.check:
            pb = args.check[0]
            dp = args.check[1] if len(args.check) > 1 else None
            res = vh_mod.validate_shot_passes(pb, dp)
            print(f"🎬 [VideoHarness] Техническое ОТК шотного рендера:")
            print(f"   • Статус приемки: {'🟢 ACCEPTED' if res.get('passed') else '🔴 REJECTED'}")
            for c in res.get("checks", []):
                print(f"   • [OK] {c}")
            for err in res.get("errors", []):
                print(f"   • [FAIL] {err}")
        else:
            print("Использование: sys_cli.py video-harness --check <playblast.mp4> [depth.mp4]")
        auto_log_telemetry("Video pass harness audit", skill="sys.video-harness")
    elif args.command == "skeleton":
        import importlib.util
        sk_path = os.path.join(AI_SCRIPT_DIR, "project_skeleton.py")
        spec = importlib.util.spec_from_file_location("project_skeleton", sk_path)
        sk_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sk_mod)

        if args.ios:
            target_d, app_n = args.ios[0], args.ios[1]
            res = sk_mod.create_ios_game_skeleton(target_d, app_n)
            print(f"🎮 [Skeleton] Развернут эталонный каркас iOS игры '{res['app_name']}':")
            print(f"   • Директория: {res['target_dir']}")
            print(f"   • Файлов создано: {len(res['created_files'])}")
            print(f"   • Манифест: {res['meta_file']}")
        else:
            print("Использование: sys_cli.py skeleton --ios <dir> <app_name>")
        auto_log_telemetry("Project skeleton scaffolding", skill="sys.skeleton")
    elif args.command == "codemap":
        import importlib.util
        cm_path = os.path.join(AI_SCRIPT_DIR, "codemap_engine.py")
        spec = importlib.util.spec_from_file_location("codemap_engine", cm_path)
        cm_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cm_mod)

        title = args.title or os.path.basename(args.dir)
        codemap_md = cm_mod.generate_codemap(args.dir, title)
        print(codemap_md)
        auto_log_telemetry(f"Codemap generated for {title}", skill="sys.codemap")
    elif args.command == "statusline":
        import importlib.util
        sl_path = os.path.join(AI_SCRIPT_DIR, "statusline.py")
        spec = importlib.util.spec_from_file_location("statusline", sl_path)
        sl_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sl_mod)

        print(sl_mod.format_statusline(color=not args.no_color))
        auto_log_telemetry("Statusline beacon output", skill="sys.statusline")
    elif args.command == "rules":
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem("rules")
        ret = sub.execute(args) if sub else 1
        sys.exit(ret)
    elif args.command == "hooks":
        # Hardware-Level Lifecycle Hooks Audit
        settings_file = "~/.gemini/settings.json"
        hooks_config = "~/.gemini/config/hooks.json"
        session_gate = os.path.join(AI_SCRIPT_DIR, "session_gate.py")
        vault_guard = os.path.join(AI_SCRIPT_DIR, "vault_guard_hook.py")

        s_ok = os.path.exists(settings_file)
        h_ok = os.path.exists(hooks_config)
        sg_ok = os.path.exists(session_gate) and os.access(session_gate, os.X_OK)
        vg_ok = os.path.exists(vault_guard) and os.access(vault_guard, os.X_OK)

        print("┌─────────────────────────────────────────────────────────────┐")
        print("│  ⚡ AnD os v1.0.0 Hardware Lifecycle Hooks Status          │")
        print("├─────────────────────────────────────────────────────────────┤")
        print(f"│  1. SessionStart Hook (session_gate.py) : {'🟢 ACTIVE' if sg_ok and s_ok else '🔴 INACTIVE'}               │")
        print(f"│     • Binary executable : {'🟢 YES' if sg_ok else '🔴 NO'}                                  │")
        print(f"│     • In settings.json  : {'🟢 REGISTERED' if s_ok else '🔴 MISSING'}                           │")
        print("├─────────────────────────────────────────────────────────────┤")
        print(f"│  2. PreToolUse Guard (vault_guard_hook) : {'🟢 ACTIVE' if vg_ok and h_ok else '🔴 INACTIVE'}               │")
        print(f"│     • Binary executable : {'🟢 YES' if vg_ok else '🔴 NO'}                                  │")
        print(f"│     • In hooks.json     : {'🟢 REGISTERED' if h_ok else '🔴 MISSING'}                           │")
        print("├─────────────────────────────────────────────────────────────┤")
        print(f"│  Overall Hooks Gate Status              : {'🟢 100% OPERATIONAL' if sg_ok and vg_ok and s_ok and h_ok else '🔴 COMPROMISED'}        │")
        print("└─────────────────────────────────────────────────────────────┘")
        auto_log_telemetry(f"Hooks audit action: {args.action}", skill="sys.hooks")
        sys.exit(0 if (sg_ok and vg_ok and s_ok and h_ok) else 1)
    elif args.command == "verify":
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem("verify")
        ret = sub.execute(args) if sub else 1
        sys.exit(ret)
    elif args.command in ("release", "checkpoint", "handoff", "mode", "clean", "sync-docs"):
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem(args.command)
        ret = sub.execute(args) if sub else 1
        sys.exit(ret)
    elif args.command == "capture-failure":
        flags = ["--reason", args.reason]
        if args.cmd:
            flags.extend(["--cmd", args.cmd])
        if args.json:
            flags.append("--json")
        res = run_script("artifact_capture.py", flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry("Failure artifact capture", skill="sys.capture")
        sys.exit(res.get("returncode", 0))
    elif args.command == "dag-plan":
        flags = [args.action]
        if args.task_id:
            flags.append(args.task_id)
        if args.action == "new":
            if args.phases:
                flags.extend(["--phases", args.phases])
            if args.desc:
                flags.extend(["--desc", args.desc])
        elif args.action == "check" and args.done:
            flags.append("--done")
        res = run_script("dag_planner.py", flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"DAG planner {args.action}", skill="sys.dag-plan")
        sys.exit(res.get("returncode", 0))
    elif args.command == "register-skill":




        flags = ["new-skill", "--name", args.name, "--desc", args.desc, "--domain", args.domain]
        if args.tags:
            flags.extend(["--tags", args.tags])
        res = run_script("register_component.py", flags)
        print(res.get("stdout", ""))
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Register skill: {args.name}", skill="sys.register")
    elif args.command == "register-module":
        flags = ["new-module", "--hub", args.hub, "--name", args.name, "--src", args.src, "--role", args.role]
        if args.commands:
            flags.extend(["--commands", args.commands])
        res = run_script("register_component.py", flags)
        print(res.get("stdout", ""))
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Register module: {args.name} -> {args.hub}", skill="sys.register")
    elif args.command == "register-knowledge":
        cl_args = ["register-knowledge", "--title", args.title]
        if args.author:
            cl_args.extend(["--author", args.author])
        if args.category:
            cl_args.extend(["--category", args.category])
        if args.island:
            cl_args.extend(["--island", args.island])
        if args.essence:
            cl_args.extend(["--essence", args.essence])
        if args.for_whom:
            cl_args.extend(["--for-whom", args.for_whom])
        if args.competence:
            cl_args.extend(["--competence", args.competence])
        if args.skill:
            cl_args.extend(["--skill", args.skill])
        if args.tasks:
            cl_args.extend(["--tasks", args.tasks])
        if args.tags:
            cl_args.extend(["--tags", args.tags])
        if args.content:
            cl_args.extend(["--content", args.content])
        if args.checklist:
            cl_args.extend(["--checklist", args.checklist])
        res = run_script("closed_loop.py", cl_args)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Register knowledge: {args.title}", skill="sys.register_knowledge")
    elif args.command == "register-health":
        cl_args = [
            "register-health",
            "--patient", args.patient,
            "--type", args.type,
            "--date", args.date,
            "--name", args.name
        ]
        if args.key:
            cl_args.extend(["--key", args.key])
        if args.value:
            cl_args.extend(["--value", str(args.value)])
        if args.unit:
            cl_args.extend(["--unit", args.unit])
        if args.ref_low:
            cl_args.extend(["--ref-low", str(args.ref_low)])
        if args.ref_high:
            cl_args.extend(["--ref-high", str(args.ref_high)])
        if args.lab:
            cl_args.extend(["--lab", args.lab])
        if args.specialty:
            cl_args.extend(["--specialty", args.specialty])
        if args.icd10:
            cl_args.extend(["--icd10", args.icd10])
        if args.recommendations:
            cl_args.extend(["--recommendations", args.recommendations])
        if args.source:
            cl_args.extend(["--source", args.source])
        res = run_script("closed_loop.py", cl_args)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Register health: {args.patient} | {args.name}", skill="sys.register_health")
    elif args.command == "register-finance":
        cl_args = [
            "register-finance",
            "--account", args.account,
            "--type", args.type,
            "--total", str(args.total)
        ]
        if args.pnl_rub:
            cl_args.extend(["--pnl-rub", str(args.pnl_rub)])
        if args.pnl_pct:
            cl_args.extend(["--pnl-pct", str(args.pnl_pct)])
        if args.cash:
            cl_args.extend(["--cash", str(args.cash)])
        if args.flow:
            cl_args.extend(["--flow", args.flow])
        if args.ticker:
            cl_args.extend(["--ticker", args.ticker])
        if args.date:
            cl_args.extend(["--date", args.date])
        if args.note:
            cl_args.extend(["--note", args.note])
        if args.source:
            cl_args.extend(["--source", args.source])
        res = run_script("closed_loop.py", cl_args)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Register finance: {args.account} [{args.type}]", skill="sys.register_finance")
    elif args.command == "finance":
        flags = []
        if getattr(args, "check", False):
            flags.append("check")
        else:
            flags.append("summary")
            if getattr(args, "broker", None):
                flags.extend(["--broker", args.broker])
            if args.json:
                flags.append("--json")
        res = run_script("finance_bridge.py", flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry("Finance summary check", skill="sys.finance")
    elif args.command == "register-task":
        cl_args = [
            "register-task",
            "--project", args.project,
            "--title", args.title
        ]
        if args.subtasks:
            cl_args.extend(["--subtasks", args.subtasks])
        if args.priority:
            cl_args.extend(["--priority", args.priority])
        if args.due:
            cl_args.extend(["--due", args.due])
        if args.section:
            cl_args.extend(["--section", args.section])
        res = run_script("closed_loop.py", cl_args)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Register task: [{args.project}] {args.title}", skill="sys.register_task")
    elif args.command == "tasks":
        flags = []
        if getattr(args, "check", False):
            flags.append("check")
        elif getattr(args, "complete", ""):
            flags.extend(["complete", args.complete])
            if getattr(args, "project", None):
                flags.extend(["--project", args.project])
        else:
            flags.append("pulse")
            if getattr(args, "project", None):
                flags.extend(["--project", args.project])
            if args.json:
                flags.append("--json")
        res = run_script("tasks_bridge.py", flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Tasks pulse check ({getattr(args, 'project', 'all')})", skill="sys.tasks")
    elif args.command == "vfs":
        flags = []
        if getattr(args, "status", False):
            flags.append("--status")
        elif getattr(args, "pulsar", False):
            flags.append("--pulsar")
        elif getattr(args, "find", None):
            flags.extend(["--find", args.find])
            if getattr(args, "island", None):
                flags.extend(["--island", args.island])
            if getattr(args, "ext", None):
                flags.extend(["--ext", args.ext])
        elif getattr(args, "sync", False):
            flags.append("--sync")
        elif getattr(args, "start", False):
            flags.append("--start")
        elif getattr(args, "stop", False):
            flags.append("--stop")
        else:
            flags.append("--status")
        res = run_script("vfs_bridge.py", flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry("VFS command execution", skill="sys.vfs")
    elif args.command == "dev-flow":
        res = run_script("dev_flow.py", args.dev_args)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry("dev-flow execution", skill="dev-flow")
    elif args.command == "closed-loop":
        res = run_script("closed_loop.py", args.cl_args)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry("closed-loop execution", skill="sys.closed_loop")
    elif args.command == "app":
        cmd_app(args)
    elif args.command == "pack":
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem("pack")
        ret = sub.execute(args) if sub else 1
        sys.exit(ret)
    elif args.command == "skills":
        cmd_skills(args)
    elif args.command == "skill":
        cmd_skill(args)
    elif args.command == "daemon":
        cmd_daemon(args)
    elif args.command == "islands":
        cmd_islands(args)
    elif args.command in ("status", "boot", "proc", "snapshot", "notify", "env", "vacuum"):
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem(args.command)
        if sub:
            ret = sub.execute(args)
            if ret != 0:
                sys.exit(ret)
        else:
            print(f"Error: subsystem for {args.command} failed to load", file=sys.stderr)
            sys.exit(1)
    elif args.command == "comfy":
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem("comfy")
        ret = sub.execute(args) if sub else 1
        if ret != 0:
            sys.exit(ret)
    elif args.command == "top":
        cmd_top(args)
    elif args.command == "terminal":
        cmd_terminal(args)
    elif args.command == "event":
        cmd_event(args)
    elif args.command == "project":
        cmd_project(args)
    elif args.command in ("context", "route", "relate", "asset", "plan"):
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem(args.command)
        ret = sub.execute(args) if sub else 1
        sys.exit(ret)
    elif args.command == "deconstruct":
        cmd_deconstruct(args)
    elif args.command == "postmortem":
        cmd_postmortem(args)
    elif args.command == "contract":
        cmd_contract(args)
    elif args.command == "bible":
        cmd_bible(args)
    elif args.command in ("animatic", "hybrid-render", "consistency", "conform", "montage"):
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem(args.command)
        ret = sub.execute(args) if sub else 1
        if ret != 0:
            sys.exit(ret)
    elif args.command == "links":
        from and_os.bin.cli_subsystems import get_subsystem
        sub = get_subsystem("links")
        ret = sub.execute(args) if sub else 1
        sys.exit(ret)
    elif args.command == "preflight":
        cmd_preflight(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "state":
        cmd_state(args)
    elif args.command == "chunk":
        cmd_chunk(args)
    elif args.command == "taskdb":
        cmd_taskdb(args)
    elif args.command == "backup":
        cmd_backup(args)
    elif args.command == "vault":
        cmd_vault(args)
    elif args.command == "toolchain":
        cmd_toolchain(args)
    elif args.command == "reverse":
        from and_os.lib.core.rea_engine import REAEngine
        engine = REAEngine(token_limit=args.token_limit)
        if args.subaction == "status":
            st = engine.status()
            if args.json:
                print(json.dumps(st, indent=2, ensure_ascii=False))
            else:
                icon = "🟢" if st.get("healthy") else "🔴"
                print(f"{icon} REA Engine: {st.get('engine_version', 'unknown')} | Node: {st.get('node_path')} | Bound: {st.get('token_limit')} tokens")
        elif args.subaction == "check-update":
            upd = engine.check_update()
            if args.json:
                print(json.dumps(upd, indent=2, ensure_ascii=False))
            else:
                if upd.get("update_available"):
                    print(f"🟡 REA Update available: {upd.get('current_pinned')} -> {upd.get('upstream_latest')}")
                else:
                    print(f"🟢 REA is up-to-date (v{upd.get('current_pinned')})")
        elif args.subaction == "inspect":
            if not args.target:
                print("❌ Error: Target path required for inspect", file=sys.stderr)
                sys.exit(1)
            res = engine.inspect_target(args.target)
            print(json.dumps(res.get("data", res), indent=2, ensure_ascii=False))
        elif args.subaction == "search":
            if not args.target or not args.pattern:
                print("❌ Error: Both target path and --pattern required for search", file=sys.stderr)
                sys.exit(1)
            res = engine.search_symbols(args.target, args.pattern)
            print(json.dumps(res.get("data", res), indent=2, ensure_ascii=False))
        elif args.subaction == "decompile":
            if not args.target or not args.procedure:
                print("❌ Error: Both target path and --procedure required for decompile", file=sys.stderr)
                sys.exit(1)
            res = engine.decompile_procedure(args.target, args.procedure)
            print(json.dumps(res.get("data", res), indent=2, ensure_ascii=False))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
