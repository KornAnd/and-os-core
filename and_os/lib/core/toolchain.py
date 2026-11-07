"""
toolchain.py — Centralized Toolchain & Runtime Parity Manager for AnD os (Rule #68).
Validates runtime conformity against and_os/etc/toolchain.lock.json.
Provides auto-redirection, status auditing, and parity gates for Health Grid and quick_verify.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class ToolchainManager:
    VAULT_ROOT = Path(os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))))
    CONFIG_PATH = VAULT_ROOT / "and_os/etc/toolchain.lock.json"
    CANONICAL_VENV = VAULT_ROOT / "and_os/.venv"
    CANONICAL_PY = CANONICAL_VENV / "bin/python"

    def __init__(self, vault_root: Optional[Any] = None):
        if vault_root is not None:
            self.root = Path(vault_root)
        else:
            self.root = self.VAULT_ROOT
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        cfg_path = self.root / "and_os/etc/toolchain.lock.json"
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def ensure_canonical_python(self, auto_reexec: bool = True) -> bool:
        """
        Rule #68 Fail-Safe Gate:
        Checks if current process runs under canonical Python 3.12.x.
        If not and auto_reexec=True, transparently re-executes current script under .venv.
        """
        v = sys.version_info
        is_canonical = (v.major == 3 and v.minor == 12)
        if is_canonical:
            return True

        if not auto_reexec:
            return False

        # Check if canonical venv exists
        if self.CANONICAL_PY.exists():
            # Transparently replace current process with .venv python
            args = [str(self.CANONICAL_PY)] + sys.argv
            env = os.environ.copy()
            env["VIRTUAL_ENV"] = str(self.CANONICAL_VENV)
            env["PATH"] = f"{self.CANONICAL_VENV / 'bin'}:{env.get('PATH', '')}"
            try:
                os.execve(str(self.CANONICAL_PY), args, env)
            except Exception as e:
                sys.stderr.write(f"⚠️ [Toolchain] Failed to re-exec under canonical venv: {e}\n")
                return False

        return False

    def check_parity(self) -> Dict[str, Any]:
        """Audits all system runtimes against golden_stack specification."""
        results: Dict[str, Any] = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "stack": {}
        }

        # 1. Python check
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        py_target = self.config.get("golden_stack", {}).get("python", {}).get("target_version", "3.12.11")
        py_ok = (sys.version_info.major == 3 and sys.version_info.minor == 12)
        
        results["stack"]["python"] = {
            "active": py_ver,
            "target": py_target,
            "executable": sys.executable,
            "is_venv": hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix),
            "passed": py_ok
        }
        if not py_ok:
            results["passed"] = False
            results["errors"].append(
                f"Python version mismatch: running {py_ver} ({sys.executable}), target is {py_target}. Run via and_os/.venv"
            )

        # 2. Bun / Node check
        bun_bin = shutil.which("bun") or str(Path(os.path.expanduser("~/.bun/bin/bun")))
        bun_ver = None
        if os.path.exists(bun_bin):
            try:
                p = subprocess.run([bun_bin, "--version"], capture_output=True, text=True, timeout=2)
                bun_ver = p.stdout.strip()
            except Exception:
                pass

        results["stack"]["bun"] = {
            "path": bun_bin if bun_ver else None,
            "version": bun_ver,
            "passed": bool(bun_ver)
        }
        if not bun_ver:
            results["warnings"].append("Bun runtime not found in PATH or ~/.bun/bin/bun")

        # 3. Swift check
        swift_ver = None
        try:
            p = subprocess.run(["swift", "--version"], capture_output=True, text=True, timeout=2)
            out = p.stdout or p.stderr
            if "Swift version" in out:
                swift_ver = out.splitlines()[0]
        except Exception:
            pass

        results["stack"]["swift"] = {
            "version": swift_ver,
            "passed": bool(swift_ver and "6." in swift_ver)
        }
        if not results["stack"]["swift"]["passed"]:
            results["warnings"].append(f"Swift toolchain not aligned with 6.x: {swift_ver}")

        # 4. FFmpeg check
        ffmpeg_bin = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        ffmpeg_ok = False
        ffmpeg_encoders = []
        if os.path.exists(ffmpeg_bin):
            try:
                p = subprocess.run([ffmpeg_bin, "-encoders"], capture_output=True, text=True, timeout=3)
                txt = p.stdout
                if "videotoolbox" in txt:
                    ffmpeg_ok = True
                    ffmpeg_encoders = [e for e in ["h264_videotoolbox", "hevc_videotoolbox"] if e in txt]
            except Exception:
                pass

        results["stack"]["ffmpeg"] = {
            "path": ffmpeg_bin if os.path.exists(ffmpeg_bin) else None,
            "videotoolbox": ffmpeg_ok,
            "encoders": ffmpeg_encoders,
            "passed": ffmpeg_ok
        }
        if not ffmpeg_ok:
            results["warnings"].append("FFmpeg with VideoToolbox hardware acceleration not detected")

        # 5. ComfyUI check
        comfy_root = Path(os.path.expanduser("~/Documents/ComfyUI"))
        comfy_py = comfy_root / ".venv/bin/python"
        comfy_ok = False
        comfy_details = {}
        if comfy_py.exists():
            try:
                p = subprocess.run([str(comfy_py), "--version"], capture_output=True, text=True, timeout=2)
                comfy_details["python"] = p.stdout.strip()
                p2 = subprocess.run([str(comfy_py), "-c", "import torch; print(torch.__version__, torch.backends.mps.is_available())"], capture_output=True, text=True, timeout=3)
                if p2.returncode == 0:
                    t_ver, mps = p2.stdout.strip().split()
                    comfy_details["torch"] = t_ver
                    comfy_details["mps"] = (mps == "True")
                    comfy_ok = (mps == "True")
            except Exception:
                pass

        results["stack"]["comfyui"] = {
            "path": str(comfy_root),
            "details": comfy_details,
            "passed": comfy_ok
        }

        return results

    def format_status_report(self) -> str:
        res = self.check_parity()
        lines = [
            "=================================================================",
            "  ⚙️ AnD os Toolchain & Runtime Parity Report (Rule #68)",
            "================================================================="
        ]
        
        st = res["stack"]
        # Python
        py = st.get("python", {})
        py_icon = "🟢" if py.get("passed") else "🔴"
        lines.append(f"{py_icon} Python Core      : {py.get('active')} (Target: {py.get('target')})")
        lines.append(f"   Executable       : {py.get('executable')}")

        # Bun
        bun = st.get("bun", {})
        bun_icon = "🟢" if bun.get("passed") else "🟡"
        lines.append(f"{bun_icon} JS/TS (Bun)     : {bun.get('version') or 'Not Found'}")

        # Swift
        swift = st.get("swift", {})
        sw_icon = "🟢" if swift.get("passed") else "🟡"
        lines.append(f"{sw_icon} Swift Compiler   : {swift.get('version') or 'Not Found'}")

        # FFmpeg
        ff = st.get("ffmpeg", {})
        ff_icon = "🟢" if ff.get("passed") else "🟡"
        lines.append(f"{ff_icon} Media (FFmpeg)  : VideoToolbox {'Active (' + ', '.join(ff.get('encoders', [])) + ')' if ff.get('videotoolbox') else 'Missing'}")

        # ComfyUI
        cf = st.get("comfyui", {})
        cf_icon = "🟢" if cf.get("passed") else "🟡"
        lines.append(f"{cf_icon} AI Runtime      : ComfyUI (Torch {cf.get('details', {}).get('torch', 'N/A')}, MPS: {cf.get('details', {}).get('mps', False)})")

        lines.append("-----------------------------------------------------------------")
        if res["passed"] and not res["warnings"]:
            lines.append("✅ Overall Status   : 🟢 100% PARITY MATCH (Golden Stack Active)")
        elif res["passed"]:
            lines.append("⚠️ Overall Status   : 🟡 COMPATIBLE WITH ADVISORIES")
            for w in res["warnings"]:
                lines.append(f"   - {w}")
        else:
            lines.append("❌ Overall Status   : 🔴 PARITY GATE BREACH (Defects Detected)")
            for e in res["errors"]:
                lines.append(f"   - {e}")

        lines.append("=================================================================")
        return "\n".join(lines)
