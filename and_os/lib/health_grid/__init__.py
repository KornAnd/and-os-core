"""
health_grid — Modular distributed health diagnostic and audit grid (AnD os v1.0.0).
Concentric security rings architecture (Ring 0 - Ring 4).
"""

from typing import Dict, Any

class BaseProbeResult:
    def __init__(self, name: str, ring: int = 0):
        self.name = name
        self.ring = ring
        self.passed = True
        self.issues_count = 0
        self.errors = []
        self.warnings = []
        self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ring": self.ring,
            "passed": self.passed,
            "issues_count": self.issues_count,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details
        }

from .clean_code_probe import CleanCodeProbe
