"""Typed Data Transfer Objects (DTO) and Contracts for Ftrack Production Contours.

Part of AnD os Clean Architecture standard (Uncle Bob / clean-code-guardian).
Enforces pure domain models with strict serialization and validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
import json


@dataclass(frozen=True)
class ShotStageMetricDTO:
    """Metric for a specific shot production stage."""
    stage: str
    total: int
    done: int
    pct: float
    emoji: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetCategoryMetricDTO:
    """Metric for asset category breakdown."""
    category: str
    total: int
    done: int
    pct: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EmployeeWorkloadDTO:
    """Aggregated workload metrics for an employee."""
    name: str
    primary_dept: str
    active: int
    overdue: int
    done: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OverdueTaskDTO:
    """Information regarding an overdue task bottleneck."""
    id: str
    name: str
    type: str
    parent: str
    end_date: str
    assignees: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FtrackProjectSummaryDTO:
    """Canonical domain DTO for project summary across all 3 contours."""
    project_key: str
    project_name: str
    updated_at: str
    slice_date: str
    shots_total: int
    shots_done: int
    shots_pct: float
    shots_by_status: Dict[str, int]
    shot_stages: List[ShotStageMetricDTO]
    assets_total: int
    assets_done: int
    assets_pct: float
    assets_stuck: int
    assets_by_category: List[AssetCategoryMetricDTO]
    overdue_count: int
    top_overdue: List[OverdueTaskDTO]
    tracked_employees_count: int
    top_workload: List[EmployeeWorkloadDTO]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_key": self.project_key,
            "project_name": self.project_name,
            "updated_at": self.updated_at,
            "slice_date": self.slice_date,
            "shots": {
                "total": self.shots_total,
                "done": self.shots_done,
                "pct": self.shots_pct,
                "by_status": self.shots_by_status,
                "stages": [s.to_dict() for s in self.shot_stages],
            },
            "assets": {
                "total": self.assets_total,
                "done": self.assets_done,
                "pct": self.assets_pct,
                "stuck_count": self.assets_stuck,
                "by_category": [c.to_dict() for c in self.assets_by_category],
            },
            "bottlenecks": {
                "overdue_count": self.overdue_count,
                "top_overdue": [o.to_dict() for o in self.top_overdue],
            },
            "employees": {
                "tracked_count": self.tracked_employees_count,
                "top_workload": [w.to_dict() for w in self.top_workload],
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_compact_cli(self) -> str:
        """Produce a sub-30 line deterministic CLI summary for Rule #16 (Think in Code)."""
        lines = [
            f"📊 [FTRACK DTO] Project: {self.project_name.upper()} ({self.project_key})",
            f"   • Data Slice:   {self.slice_date} | Updated: {self.updated_at}",
            f"   • Shots:        {self.shots_done}/{self.shots_total} ({self.shots_pct:.1f}%)",
            f"   • Assets:       {self.assets_done}/{self.assets_total} ({self.assets_pct:.1f}%) | Stuck: {self.assets_stuck}",
            f"   • Overdue:      🔴 {self.overdue_count} tasks | Active Pool: {self.tracked_employees_count}",
        ]
        if self.shot_stages:
            lines.append("   • Key Stages:")
            for st in self.shot_stages[:5]:
                lines.append(f"     - {st.stage}: {st.done}/{st.total} ({st.pct:.1f}%) {st.emoji}")
        if self.top_overdue:
            lines.append(f"   • Top Bottlenecks ({len(self.top_overdue[:3])} of {self.overdue_count}):")
            for ov in self.top_overdue[:3]:
                lines.append(f"     - [{ov.type}] {ov.parent}/{ov.name} (due {ov.end_date}) -> {ov.assignees or 'unassigned'}")
        return "\n".join(lines)

    @classmethod
    def from_summary_dict(cls, project_key: str, s: Dict[str, Any], slice_date: str = "") -> "FtrackProjectSummaryDTO":
        """Factory constructor mapping raw summary dictionary into typed domain DTO."""
        sh = s.get("shots", {})
        ast = s.get("assets", {})
        bot = s.get("bottlenecks", {})
        emp = s.get("employees", {})

        stages = [
            ShotStageMetricDTO(
                stage=str(stg.get("stage", "")),
                total=int(stg.get("total", 0)),
                done=int(stg.get("done", 0)),
                pct=float(stg.get("pct", 0.0)),
                emoji=str(stg.get("emoji", "")),
            )
            for stg in sh.get("stages", [])
        ]

        categories = [
            AssetCategoryMetricDTO(
                category=str(c.get("category", "")),
                total=int(c.get("total", 0)),
                done=int(c.get("done", 0)),
                pct=float(c.get("pct", 0.0)),
            )
            for c in ast.get("by_category", [])
        ]

        overdues = [
            OverdueTaskDTO(
                id=str(o.get("id", "")),
                name=str(o.get("name", "")),
                type=str(o.get("type", "")),
                parent=str(o.get("parent", "")),
                end_date=str(o.get("end_date", "")),
                assignees=str(o.get("assignees", "")),
            )
            for o in bot.get("top_overdue", [])
        ]

        workload = [
            EmployeeWorkloadDTO(
                name=str(w.get("name", "")),
                primary_dept=str(w.get("primary_dept", "")),
                active=int(w.get("active", 0)),
                overdue=int(w.get("overdue", 0)),
                done=int(w.get("done", 0)),
            )
            for w in emp.get("top_workload", [])
        ]

        # Calculate shots_done from stages or status
        shots_total = int(sh.get("total", 0))
        shots_by_status = {str(k): int(v) for k, v in sh.get("by_status", {}).items()}
        done_keywords = ["done", "approved", "\u0433\u043e\u0442\u043e\u0432\u043e", "\u043f\u0440\u0438\u043d\u044f\u0442\u043e"]
        shots_done = sum(v for k, v in shots_by_status.items() if any(done_kw in k.lower() for done_kw in done_keywords))
        shots_pct = (shots_done / shots_total * 100) if shots_total > 0 else 0.0

        return cls(
            project_key=project_key,
            project_name=str(s.get("project_name", project_key)),
            updated_at=str(s.get("updated_at", "")),
            slice_date=slice_date or str(s.get("slice_date", "")),
            shots_total=shots_total,
            shots_done=shots_done,
            shots_pct=shots_pct,
            shots_by_status=shots_by_status,
            shot_stages=stages,
            assets_total=int(ast.get("total", 0)),
            assets_done=int(ast.get("done", 0)),
            assets_pct=float(ast.get("pct", 0.0)),
            assets_stuck=int(ast.get("stuck_count", 0)),
            assets_by_category=categories,
            overdue_count=int(bot.get("overdue_count", 0)),
            top_overdue=overdues,
            tracked_employees_count=int(emp.get("tracked_count", 0)),
            top_workload=workload,
        )
