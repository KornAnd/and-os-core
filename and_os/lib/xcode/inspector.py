"""
inspector.py — Island 9 (Xcode & iOS Gamedev) Muscle Realm Scanner & Validator.
Scans /WORK/xcode/ projects, verifies Swift package manifests, xcodeproj schemes,
and parses canonical PROJECT.md contracts.
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class XcodeInspector:
    DEFAULT_ROOT = Path("./xcode")

    def __init__(self, xcode_root: Optional[Path] = None):
        self.root = xcode_root or self.DEFAULT_ROOT

    def scan_projects(self) -> List[Dict[str, Any]]:
        """Discovers all valid Xcode / Swift projects in Island 9 Muscle Realm."""
        if not self.root.exists() or not self.root.is_dir():
            return []

        projects = []
        for entry in sorted(os.listdir(self.root)):
            if entry.startswith(".") or entry.endswith(".png"):
                continue

            proj_dir = self.root / entry
            if proj_dir.is_dir():
                proj_info = self.inspect_project(entry, proj_dir)
                projects.append(proj_info)

        return projects

    def inspect_project(self, project_id: str, proj_dir: Path) -> Dict[str, Any]:
        """Inspects a single Xcode project directory and reads PROJECT.md."""
        project_md = proj_dir / "PROJECT.md"
        meta = self._parse_frontmatter(project_md) if project_md.exists() else {}

        has_xcodeproj = any(f.endswith(".xcodeproj") for f in os.listdir(proj_dir))
        has_package_swift = (proj_dir / "Package.swift").exists()

        return {
            "id": meta.get("id", project_id.lower()),
            "name": meta.get("name", project_id),
            "dir_name": project_id,
            "path": str(proj_dir),
            "has_contract": project_md.exists(),
            "island_id": 9,
            "category": meta.get("category", "iOS Game / SpriteKit"),
            "stack": meta.get("stack", "Swift 6 / SpriteKit / SwiftUI"),
            "swift_version": meta.get("swift_version", "6.4"),
            "swift_valid": ("6." in str(meta.get("swift_version", "6.4"))),
            "platform": meta.get("platform", "iOS 18+ / macOS"),
            "has_xcodeproj": has_xcodeproj,
            "has_package_swift": has_package_swift,
            "build_command": meta.get("build_command", "swift build" if has_package_swift else "xcodebuild build"),
            "test_command": meta.get("test_command", "swift test" if has_package_swift else ""),
            "smoke_test": meta.get("smoke_test", ""),
            "status": meta.get("status", "in_development"),
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
