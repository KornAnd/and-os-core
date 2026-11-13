"""
Pipeline Quality Gate & Validation Contracts
AnD os v1.0.0 — Island 7: 3D Pipeline Core (Schema-First Contract Standard)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass(frozen=True)
class GateCheckResult:
    """
    Immutable result object produced by an automated Quality Barrier (DoD Gate).
    Acts as the physical cryptographic stamp for entity status promotion.
    """
    gate_id: str                                    # E.g. 'GATE_1_ASSET_INTEGRITY'
    entity_id: str
    passed: bool
    scale_is_unitary: bool                          # Scale == (1.0, 1.0, 1.0)
    pivot_is_grounded: bool                         # Z-pivot == 0.0 on base plane
    root_anchor_present: bool                       # Presence of root_master world anchor
    dimensions_actual: Optional[Tuple[float, float, float]] = None
    missing_dependencies: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def summary_code(self) -> str:
        """Compact status code for logging and dashboard telemetry."""
        return "PASS" if self.passed else f"FAIL({len(self.errors)}_ERRORS)"
