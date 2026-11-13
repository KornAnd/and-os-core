"""
Non-Destructive Asset & Shot Reference Resolver
AnD os v1.0.0 — Island 7: 3D Pipeline Core (Production Skeleton)
"""

import os
from typing import Dict, Optional, Tuple

from and_os.lib.core.cg.schema import AssetSpec, ShotSpec, EntityStatus
from .base import PipelineIntegrityError
from .gatekeeper import GateKeeper


class ReferenceResolver:
    """
    Manages non-destructive reference paths between Asset Foundry and Shot Assembly.
    Prevents geometry duplication and enforces linking contracts.
    """

    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self.assets_dir = os.path.join(self.project_root, "assets")
        self.shots_dir = os.path.join(self.project_root, "shots")

    def resolve_asset_master_path(self, asset: AssetSpec) -> str:
        """
        Determines the canonical filesystem location of an approved master asset.
        Format: <project_root>/assets/<category_lower>/<asset_id>.blend
        """
        category_dir = asset.category.value.lower()
        return os.path.join(self.assets_dir, category_dir, f"{asset.id}.blend")

    def resolve_shot_scene_path(self, shot: ShotSpec) -> str:
        """
        Determines the canonical filesystem location of a compiled shot.
        Format: <project_root>/shots/<sequence_id>/<shot_id>.blend
        """
        return os.path.join(self.shots_dir, shot.sequence_id, f"{shot.id}.blend")

    def resolve_shot_dependencies(
        self,
        shot: ShotSpec,
        asset_registry: Dict[str, AssetSpec]
    ) -> Dict[str, str]:
        """
        Audits shot prerequisites against Gate 2 and returns a mapping of {asset_id: filepath}.
        Raises PipelineIntegrityError if any asset is missing or not FROZEN.
        """
        gate_res = GateKeeper.evaluate_shot_gate_2(shot, asset_registry)
        if not gate_res.passed:
            error_details = "\n  - ".join(gate_res.errors)
            raise PipelineIntegrityError(
                f"Cannot resolve shot '{shot.id}'. Gate 2 validation failed:\n  - {error_details}"
            )

        resolved_paths: Dict[str, str] = {}
        for ref in shot.required_assets:
            asset = asset_registry[ref.asset_id]
            resolved_paths[ref.asset_id] = self.resolve_asset_master_path(asset)

        if shot.environment_asset_id:
            env_asset = asset_registry[shot.environment_asset_id]
            resolved_paths[shot.environment_asset_id] = self.resolve_asset_master_path(env_asset)

        return resolved_paths
