"""
Production Entity Contracts & Data Schemas
AnD os v1.0.0 — Island 7: 3D Pipeline Core (Schema-First Contract Standard)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple


class EntityStatus(str, Enum):
    """Lifecycle statuses for pipeline entities."""
    DRAFT = "DRAFT"                 # Work-in-progress, unverified, prohibited in shots
    PENDING_GATE = "PENDING_GATE"   # Submitted to Definition of Done quality gate
    FROZEN = "FROZEN"               # Verified, immutable, approved for reference linking
    DEPRECATED = "DEPRECATED"       # Retired asset, maintained only for historical cuts


class AssetCategory(str, Enum):
    """Canonical 3D asset taxonomy."""
    VEHICLE = "VEHICLE"
    CHARACTER = "CHARACTER"
    PROP = "PROP"
    ENVIRONMENT = "ENVIRONMENT"


@dataclass(frozen=True)
class AssetSpec:
    """
    Contract specification for an individual 3D Master Asset.
    Strictly decouples the component requirements from DCC software implementation.
    """
    id: str                                         # Unique canonical slug (e.g. 'bus_miracle')
    category: AssetCategory
    bounding_box_target: Tuple[float, float, float] # Expected dimensions [X, Y, Z] in meters
    version: int = 1
    status: EntityStatus = EntityStatus.DRAFT
    tags: List[str] = field(default_factory=list)
    description: str = ""

    def with_status(self, new_status: EntityStatus) -> "AssetSpec":
        """Returns a new immutable AssetSpec with updated lifecycle status."""
        return AssetSpec(
            id=self.id,
            category=self.category,
            bounding_box_target=self.bounding_box_target,
            version=self.version,
            status=new_status,
            tags=list(self.tags),
            description=self.description
        )


@dataclass(frozen=True)
class AssetReference:
    """
    Non-destructive linking contract.
    A shot only references master assets; copying raw geometry into shots is strictly prohibited.
    """
    asset_id: str
    target_version: int
    override_rig_only: bool = True                  # Only armature receives animation overrides


@dataclass
class ShotSpec:
    """
    Contract specification for a 3D Shot Scene.
    Acts as a container for referenced master assets, timeline bounds, and optics.
    """
    id: str                                         # E.g. 'sq01_sh010'
    sequence_id: str                                # E.g. 'sq01'
    frame_start: int
    frame_end: int
    fps: int = 24
    environment_asset_id: Optional[str] = None     # Master environment reference
    required_assets: List[AssetReference] = field(default_factory=list)
    status: EntityStatus = EntityStatus.DRAFT
    focal_length_mm: float = 35.0

    @property
    def frame_count(self) -> int:
        """Total frame duration including both boundary frames."""
        return (self.frame_end - self.frame_start) + 1

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds at canonical FPS."""
        return round(self.frame_count / self.fps, 2)
