"""Base class and common execution context for modular CLI subsystems.
Follows UNIX / Git-style subcommand architecture.
"""

import os
import sys
import subprocess
from typing import List, Dict, Any, Optional

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
AI_SCRIPT_DIR = os.path.join(VAULT_ROOT, "and_os", "bin")


def run_script(script_name: str, args: List[str] = None, no_bytecode: bool = False) -> Dict[str, Any]:
    """Execute a companion subsystem script in a deterministic sub-process."""
    if args is None:
        args = []
    search_paths = [
        AI_SCRIPT_DIR,
        os.path.abspath(os.path.join(AI_SCRIPT_DIR, "../boot")),
        os.path.abspath(os.path.join(AI_SCRIPT_DIR, "../sbin")),
        os.path.abspath(os.path.join(VAULT_ROOT, "and_os/lib/health")),
    ]
    script_path = None
    for sp in search_paths:
        candidate = os.path.join(sp, script_name)
        if os.path.exists(candidate):
            script_path = candidate
            break

    if not script_path:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"Error: Script {script_name} not found across and_os/ (bin, sbin, boot)\n"
        }

    env = os.environ.copy()
    if no_bytecode:
        env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = f"{VAULT_ROOT}:{env.get('PYTHONPATH', '')}"

    cmd = [sys.executable, script_path] + args
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return {
        "returncode": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr
    }


def auto_log_telemetry(task: str, mode: str = "SYSTEM", skill: str = "sys_cli", result: str = "success") -> None:
    """Log task execution telemetry complying with Rule #11."""
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


class BaseSubsystem:
    """Abstract base class for domain CLI subsystems."""
    name: str = "base"
    description: str = "Base subsystem"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        """Register domain-specific argument subparser."""
        raise NotImplementedError

    @classmethod
    def execute(cls, args: Any) -> int:
        """Execute the command and return exit code."""
        raise NotImplementedError
