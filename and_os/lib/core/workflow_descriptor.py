"""
workflow_descriptor.py — Deterministic Skill Workflow Binding & Execution Engine
AnD os v1.0.0 — Core Architecture Layer (Unix-Grade Microkernel Workflows)

Defines:
  - StepDescriptor: Atomic step bound to an OperationRequest or deterministic handler
  - WorkflowDescriptor: Declarative DAG/sequence of steps with DoD verification gates
  - WorkflowEngine: Executes workflows deterministically without LLM intervention,
    recording state in CoreMetadataStore and events in the canonical Event Journal.
  - Supports automatic rollback / compensations on step failure.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from and_os.lib.core.operation_contract import (
    Capability,
    OperationError,
    OperationRequest,
    OperationResult,
)
from and_os.lib.core.dispatcher import CoreDispatcher, CORE_REGISTRY
from and_os.lib.core.bus import emit_event
from and_os.lib.core.state import CoreMetadataStore


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(frozen=True)
class StepDescriptor:
    """Immutable specification of an executable workflow step."""
    step_id: str
    description: str
    operation_id: str
    version: str = "1.0.0"
    params: Dict[str, Any] = field(default_factory=dict)
    capabilities_required: Tuple[Capability, ...] = ()
    required_dod_keys: Tuple[str, ...] = ()
    compensation_op_id: Optional[str] = None
    compensation_params: Optional[Dict[str, Any]] = None


@dataclass
class StepExecutionRecord:
    """Runtime tracking of a step's execution."""
    step_id: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[OperationResult] = None
    error: Optional[str] = None
    elapsed_seconds: float = 0.0


@dataclass(frozen=True)
class WorkflowDescriptor:
    """Declarative specification of an AnD os skill/task workflow."""
    workflow_id: str
    name: str
    primary_skill: str
    steps: Tuple[StepDescriptor, ...]
    description: str = ""


class WorkflowEngine:
    """
    Executes declarative workflows deterministically without LLM involvement.
    Ensures fail-closed execution, step-by-step DoD verification, and state persistence.
    """

    def __init__(self, dispatcher: CoreDispatcher = None):
        self.dispatcher = dispatcher or CoreDispatcher(CORE_REGISTRY)
        self.metadata_store = CoreMetadataStore()

    def execute_workflow(
        self,
        workflow: WorkflowDescriptor,
        caller: str = "workflow_engine",
        idempotency_prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes all steps in the workflow in order:
          - Validates each step's postconditions and declared DoD.
          - On failure: triggers compensation steps for completed steps in reverse order.
          - Persists execution state to CoreMetadataStore under 'workflow.<workflow_id>'.
        """
        run_id = f"wf_run_{uuid.uuid4().hex[:10]}"
        prefix = idempotency_prefix or run_id
        start_time = time.monotonic()
        completed_steps: List[Tuple[StepDescriptor, OperationResult]] = []
        step_records: Dict[str, StepExecutionRecord] = {}

        emit_event(
            event_type="WORKFLOW_STARTED",
            payload={"workflow_id": workflow.workflow_id, "run_id": run_id, "step_count": len(workflow.steps)},
            source=caller
        )

        overall_success = True
        failure_reason = None

        for step in workflow.steps:
            rec = StepExecutionRecord(step_id=step.step_id, status=StepStatus.RUNNING)
            step_records[step.step_id] = rec

            req = OperationRequest(
                operation_id=step.operation_id,
                version=step.version,
                params=step.params,
                caller=f"{caller}:{workflow.workflow_id}:{step.step_id}",
                idempotency_key=f"{prefix}:{step.step_id}",
            )

            res = self.dispatcher.dispatch(
                request=req,
                caller_capabilities=step.capabilities_required,
                emit_audit_event=True
            )

            rec.result = res
            rec.elapsed_seconds = res.elapsed_seconds

            if not res.success:
                rec.status = StepStatus.FAILED
                rec.error = res.error.message if res.error else "Operation failed without error message"
                overall_success = False
                failure_reason = f"Step '{step.step_id}' failed: {rec.error}"
                break

            # Verify Definition of Done (DoD) keys exist in postcondition evidence
            missing_dod = [k for k in step.required_dod_keys if k not in res.postcondition_evidence]
            if missing_dod:
                rec.status = StepStatus.FAILED
                rec.error = f"DoD verification failed. Missing evidence keys: {missing_dod}"
                overall_success = False
                failure_reason = rec.error
                break

            rec.status = StepStatus.COMPLETED
            completed_steps.append((step, res))

        # Rollback / Compensation on failure
        if not overall_success and completed_steps:
            for c_step, _ in reversed(completed_steps):
                if c_step.compensation_op_id:
                    comp_req = OperationRequest(
                        operation_id=c_step.compensation_op_id,
                        version="1.0.0",
                        params=c_step.compensation_params or {},
                        caller=f"{caller}:compensation",
                        idempotency_key=f"{prefix}:comp:{c_step.step_id}",
                    )
                    self.dispatcher.dispatch(comp_req, caller_capabilities=c_step.capabilities_required)
                    step_records[c_step.step_id].status = StepStatus.ROLLED_BACK

        total_elapsed = round(time.monotonic() - start_time, 4)

        # Persist execution status in core operational state
        workflow_state = {
            "workflow_id": workflow.workflow_id,
            "run_id": run_id,
            "success": overall_success,
            "failure_reason": failure_reason,
            "elapsed_seconds": total_elapsed,
            "steps": {
                s_id: {
                    "status": r.status.value,
                    "elapsed_seconds": r.elapsed_seconds,
                    "error": r.error,
                }
                for s_id, r in step_records.items()
            }
        }

        try:
            self.metadata_store.set(f"workflow.{workflow.workflow_id}.latest", workflow_state, source="workflow_engine")
        except (KeyError, OSError, RuntimeError) as err:
            sys.stderr.write(f"[workflow_descriptor] Notice storing metadata: {err}\n")

        emit_event(
            event_type="WORKFLOW_FINISHED",
            payload={"workflow_id": workflow.workflow_id, "run_id": run_id, "success": overall_success, "elapsed_seconds": total_elapsed},
            source=caller
        )

        return workflow_state
