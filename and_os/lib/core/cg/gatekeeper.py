"""
Quality Gatekeeper & Enforcement Engine
AnD os v1.0.0 — Island 7: 3D Pipeline Core (Production Skeleton)
"""

from typing import Dict, Any, List
import math

from and_os.lib.core.cg.schema import AssetSpec, ShotSpec, EntityStatus, GateCheckResult
from .base import PipelineIntegrityError


class GateKeeper:
    """
    Enforces quality boundaries between production phases.
    Operates on pure metrics and metadata, keeping DCC implementations isolated.
    """

    EPSILON = 1e-4

    @classmethod
    def evaluate_asset_gate_1(cls, metrics: Dict[str, Any], spec: AssetSpec) -> GateCheckResult:
        """
        GATE 1: Asset Definition of Done (DoD) Verification.
        Invariants:
          1. Unitary Scale: scale == (1.0, 1.0, 1.0)
          2. Grounded Origin: pivot_z == 0.0 (object sits exactly on ground plane)
          3. Root Anchor: must possess root_master world anchor
          4. Valid Collection: named col_asset_<asset_id>
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Scale Invariant
        scale = metrics.get("scale", (0.0, 0.0, 0.0))
        scale_ok = all(abs(s - 1.0) < cls.EPSILON for s in scale)
        if not scale_ok:
            errors.append(f"Scale non-unitary: {scale}. Must be (1.0, 1.0, 1.0)")

        # 2. Pivot Invariant (base plane Z=0)
        pivot_z = metrics.get("pivot_z", 1.0)
        pivot_ok = abs(pivot_z) < cls.EPSILON
        if not pivot_ok:
            errors.append(f"Origin pivot Z={pivot_z:.4f} is not on base plane Z=0.0")

        # 3. Root Kinematic Anchor
        has_root = bool(metrics.get("has_root_anchor", False))
        if not has_root:
            errors.append("Missing mandatory 'root_master' bone/locator anchor")

        # 4. Collection Naming
        expected_col = f"col_asset_{spec.id}"
        actual_col = metrics.get("root_collection_name", "")
        if actual_col and actual_col != expected_col:
            warnings.append(f"Root collection '{actual_col}' deviates from standard '{expected_col}'")

        # 5. Bounding box deviation check (warn if > 25% difference)
        actual_bbox = metrics.get("bounding_box")
        if actual_bbox and spec.bounding_box_target:
            for axis_name, act_dim, exp_dim in zip(["X", "Y", "Z"], actual_bbox, spec.bounding_box_target):
                if exp_dim > 0:
                    deviation = abs(act_dim - exp_dim) / exp_dim
                    if deviation > 0.25:
                        warnings.append(
                            f"Dimension along {axis_name} deviates by {deviation*100:.1f}% "
                            f"(expected {exp_dim}m, actual {act_dim:.2f}m)"
                        )

        passed = len(errors) == 0

        return GateCheckResult(
            gate_id="GATE_1_ASSET_INTEGRITY",
            entity_id=spec.id,
            passed=passed,
            scale_is_unitary=scale_ok,
            pivot_is_grounded=pivot_ok,
            root_anchor_present=has_root,
            dimensions_actual=actual_bbox,
            errors=errors,
            warnings=warnings
        )

    @classmethod
    def evaluate_shot_gate_2(
        cls,
        shot_spec: ShotSpec,
        asset_registry: Dict[str, AssetSpec]
    ) -> GateCheckResult:
        """
        GATE 2: Shot Assembly Pre-Flight Check.
        Invariants:
          1. Dependency Integrity: All referenced assets must exist and be in FROZEN state.
          2. Timeline Bounds: frame_end >= frame_start.
        """
        errors: List[str] = []
        missing: List[str] = []
        unfrozen: List[str] = []

        # 1. Timeline check
        if shot_spec.frame_end < shot_spec.frame_start:
            errors.append(f"Invalid frame range: [{shot_spec.frame_start} .. {shot_spec.frame_end}]")

        # 2. Dependency audit
        all_required_ids = [ref.asset_id for ref in shot_spec.required_assets]
        if shot_spec.environment_asset_id:
            all_required_ids.append(shot_spec.environment_asset_id)

        for a_id in all_required_ids:
            if a_id not in asset_registry:
                missing.append(a_id)
                errors.append(f"Referenced asset '{a_id}' does not exist in asset registry")
            else:
                asset = asset_registry[a_id]
                if asset.status != EntityStatus.FROZEN:
                    unfrozen.append(a_id)
                    errors.append(f"Asset '{a_id}' is in '{asset.status.value}' state, must be 'FROZEN'")

        passed = len(errors) == 0

        return GateCheckResult(
            gate_id="GATE_2_SHOT_INTEGRITY",
            entity_id=shot_spec.id,
            passed=passed,
            scale_is_unitary=True,
            pivot_is_grounded=True,
            root_anchor_present=True,
            missing_dependencies=missing + unfrozen,
            errors=errors
        )
