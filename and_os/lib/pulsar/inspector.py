"""
inspector.py — Island 7 (Pulsar Space) Muscle Realm Scanner & Validator.
Scans /WORK/pulsar/ applications, verifies port assignments (:8080-:8099),
and parses canonical PROJECT.md contracts without external database overhead.
"""

import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class PulsarInspector:
    DEFAULT_ROOT = Path("./pulsar")
    VALID_PORT_RANGE = range(8080, 8100)

    def __init__(self, pulsar_root: Optional[Path] = None):
        self.root = pulsar_root or self.DEFAULT_ROOT

    def scan_applications(self) -> List[Dict[str, Any]]:
        """Discovers all valid application folders in Pulsar Space."""
        if not self.root.exists() or not self.root.is_dir():
            return []

        apps = []
        for entry in sorted(os.listdir(self.root)):
            if entry.startswith(".") or entry in ("docs", "shared", "Nero"):
                continue

            app_dir = self.root / entry
            if not app_dir.is_dir():
                continue

            project_md = app_dir / "PROJECT.md"
            if project_md.exists():
                app_info = self.inspect_app(entry, app_dir)
                apps.append(app_info)
            else:
                # Check for nested projects in category directories (e.g. reverse/)
                for subentry in sorted(os.listdir(app_dir)):
                    if subentry.startswith("."):
                        continue
                    sub_app_dir = app_dir / subentry
                    if sub_app_dir.is_dir() and (sub_app_dir / "PROJECT.md").exists():
                        sub_app_info = self.inspect_app(subentry, sub_app_dir)
                        apps.append(sub_app_info)

        return apps

    def inspect_app(self, app_id: str, app_dir: Path) -> Dict[str, Any]:
        """Inspects a single Pulsar application folder and reads PROJECT.md."""
        project_md = app_dir / "PROJECT.md"
        meta = self._parse_frontmatter(project_md) if project_md.exists() else {}

        port = meta.get("port")
        if port is not None:
            try:
                port = int(port)
            except (ValueError, TypeError):
                port = None

        runtime_target = meta.get("runtime_target", "python3.12")
        runtime_valid = ("3.12" in str(runtime_target)) or ("native" in str(runtime_target).lower())

        return {
            "id": meta.get("id", app_id),
            "name": meta.get("name", app_id.replace("_", " ").title()),
            "dir_name": app_id,
            "path": str(app_dir),
            "has_contract": project_md.exists(),
            "island_id": 7,
            "category": meta.get("category", "Standalone Utility"),
            "stack": meta.get("stack", "Python 3 / Native"),
            "runtime_target": runtime_target,
            "runtime_valid": runtime_valid,
            "port": port,
            "port_valid": (port in self.VALID_PORT_RANGE) if port else True,
            "entrypoint": meta.get("entrypoint", self._guess_entrypoint(app_dir)),
            "run_command": meta.get("run_command", ""),
            "smoke_test": meta.get("smoke_test", ""),
            "status": meta.get("status", "active"),
            "description": meta.get("description", "")
        }

    def _parse_frontmatter(self, file_path: Path) -> Dict[str, Any]:
        """Parses basic YAML frontmatter from markdown without heavy dependencies."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content.startswith("---"):
                return {}

            parts = content.split("---", 2)
            if len(parts) < 3:
                return {}

            frontmatter_raw = parts[1]
            data: Dict[str, Any] = {}
            for line in frontmatter_raw.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"\'')
                    if v.lower() == "null" or not v:
                        data[k] = None
                    elif v.lower() == "true":
                        data[k] = True
                    elif v.lower() == "false":
                        data[k] = False
                    elif v.isdigit():
                        data[k] = int(v)
                    else:
                        data[k] = v
            return data
        except Exception:
            return {}

    def _guess_entrypoint(self, app_dir: Path) -> str:
        """Guesses main entry file if not specified in manifest."""
        candidates = ["server.py", "main.py", "app.py", "run.sh", "Start_mc_doc.command"]
        for c in candidates:
            if (app_dir / c).exists():
                return c
        return "main.py"
