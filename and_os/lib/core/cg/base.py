"""
Pipeline Core Abstract Base Classes
AnD os v1.0.0 — Island 7: 3D Pipeline Core (Production Skeleton)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import os

from and_os.lib.core.cg.schema import AssetSpec, ShotSpec, GateCheckResult


class PipelineIntegrityError(Exception):
    """Raised when an operation violates production graph constraints or quality gates."""
    pass


class BaseDCCDriver(ABC):
    """
    Abstract execution driver for Digital Content Creation software (Blender, UE, Houdini).
    DCC drivers implement the actual mesh/rig/scene manipulations, while the pipeline skeleton
    governs data contracts, validation rules, and lifecycle state.
    """

    @abstractmethod
    def inspect_asset_geometry(self, asset_filepath: str) -> Dict[str, Any]:
        """
        Extracts physical mesh and armature telemetry without side effects:
        Returns: {
            'scale': (float, float, float),
            'pivot_z': float,
            'has_root_anchor': bool,
            'bounding_box': (float, float, float),
            'root_collection_name': str
        }
        """
        pass

    @abstractmethod
    def assemble_shot_scene(
        self,
        shot_spec: ShotSpec,
        resolved_asset_paths: Dict[str, str],
        output_filepath: str
    ) -> bool:
        """
        Constructs the shot scene via strict Library Linking and overrides.
        Copying raw mesh data into the shot file is strictly prohibited.
        """
        pass
