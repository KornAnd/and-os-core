"""
Unit & Integration Test Suite for Production 3D Skeleton
AnD os v1.0.0 — Island 7: 3D Pipeline Core Verification
"""

import sys
import os
import unittest

# The skeleton lives in the kernel zone (and_os/lib/core/cg); the vault
# root must be importable (the canonical runner starts pytest from it).
VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)

from and_os.lib.core.cg.schema import (
    AssetSpec,
    ShotSpec,
    AssetCategory,
    EntityStatus,
    AssetReference,
    GateCheckResult
)
from and_os.lib.core.cg import (
    GateKeeper,
    ReferenceResolver,
    PipelineIntegrityError
)


class TestProductionSkeleton(unittest.TestCase):

    def setUp(self):
        self.project_root = "/tmp/pulsar_test_chbs"
        self.resolver = ReferenceResolver(self.project_root)

    def test_asset_gate_1_rejection_on_bad_scale(self):
        """DoD Gate 1 must strictly reject an asset if scale is not (1.0, 1.0, 1.0)."""
        spec = AssetSpec(
            id="bus_miracle",
            category=AssetCategory.VEHICLE,
            bounding_box_target=(4.5, 2.0, 2.2)
        )
        bad_metrics = {
            "scale": (1.0, 0.5, 1.0),       # BAD: Y is 0.5
            "pivot_z": 0.0,
            "has_root_anchor": True,
            "root_collection_name": "col_asset_bus_miracle"
        }
        res = GateKeeper.evaluate_asset_gate_1(bad_metrics, spec)
        self.assertFalse(res.passed)
        self.assertFalse(res.scale_is_unitary)
        self.assertTrue(any("Scale non-unitary" in e for e in res.errors))

    def test_asset_gate_1_rejection_on_unanchored_pivot(self):
        """DoD Gate 1 must reject asset if pivot is not grounded at Z=0.0."""
        spec = AssetSpec(
            id="bus_miracle",
            category=AssetCategory.VEHICLE,
            bounding_box_target=(4.5, 2.0, 2.2)
        )
        bad_metrics = {
            "scale": (1.0, 1.0, 1.0),
            "pivot_z": 1.25,                 # BAD: floating in air
            "has_root_anchor": True,
            "root_collection_name": "col_asset_bus_miracle"
        }
        res = GateKeeper.evaluate_asset_gate_1(bad_metrics, spec)
        self.assertFalse(res.passed)
        self.assertFalse(res.pivot_is_grounded)
        self.assertTrue(any("Z=1.2500" in e for e in res.errors))

    def test_asset_gate_1_approval(self):
        """DoD Gate 1 passes when all physical and kinematic invariants are met."""
        spec = AssetSpec(
            id="bus_miracle",
            category=AssetCategory.VEHICLE,
            bounding_box_target=(4.5, 2.0, 2.2)
        )
        good_metrics = {
            "scale": (1.0, 1.0, 1.0),
            "pivot_z": 0.0,
            "has_root_anchor": True,
            "bounding_box": (4.48, 2.02, 2.19),
            "root_collection_name": "col_asset_bus_miracle"
        }
        res = GateKeeper.evaluate_asset_gate_1(good_metrics, spec)
        self.assertTrue(res.passed)
        self.assertEqual(res.summary_code, "PASS")
        self.assertEqual(len(res.errors), 0)

    def test_shot_gate_2_blocks_draft_assets(self):
        """Gate 2 must physically prohibit assembling a shot from DRAFT assets."""
        asset_draft = AssetSpec(
            id="bus_miracle",
            category=AssetCategory.VEHICLE,
            bounding_box_target=(4.5, 2.0, 2.2),
            status=EntityStatus.DRAFT       # Unapproved DRAFT
        )
        registry = {asset_draft.id: asset_draft}

        shot = ShotSpec(
            id="sq01_sh010",
            sequence_id="sq01",
            frame_start=101,
            frame_end=172,
            required_assets=[AssetReference(asset_id="bus_miracle", target_version=1)]
        )

        # Resolver must raise PipelineIntegrityError
        with self.assertRaises(PipelineIntegrityError) as ctx:
            self.resolver.resolve_shot_dependencies(shot, registry)

        self.assertIn("must be 'FROZEN'", str(ctx.exception))

    def test_shot_gate_2_passes_and_resolves_frozen_assets(self):
        """Gate 2 approves assembly and generates reference links when assets are FROZEN."""
        asset_frozen = AssetSpec(
            id="bus_miracle",
            category=AssetCategory.VEHICLE,
            bounding_box_target=(4.5, 2.0, 2.2),
            status=EntityStatus.FROZEN      # Approved master
        )
        env_frozen = AssetSpec(
            id="env_slums",
            category=AssetCategory.ENVIRONMENT,
            bounding_box_target=(200.0, 200.0, 40.0),
            status=EntityStatus.FROZEN
        )
        registry = {
            asset_frozen.id: asset_frozen,
            env_frozen.id: env_frozen
        }

        shot = ShotSpec(
            id="sq01_sh010",
            sequence_id="sq01",
            frame_start=101,
            frame_end=172,
            environment_asset_id="env_slums",
            required_assets=[AssetReference(asset_id="bus_miracle", target_version=1)]
        )

        resolved = self.resolver.resolve_shot_dependencies(shot, registry)
        self.assertEqual(len(resolved), 2)
        self.assertEqual(
            resolved["bus_miracle"],
            os.path.join(self.project_root, "assets", "vehicle", "bus_miracle.blend")
        )
        self.assertEqual(
            resolved["env_slums"],
            os.path.join(self.project_root, "assets", "environment", "env_slums.blend")
        )
        self.assertEqual(
            self.resolver.resolve_shot_scene_path(shot),
            os.path.join(self.project_root, "shots", "sq01", "sq01_sh010.blend")
        )


if __name__ == "__main__":
    unittest.main()
