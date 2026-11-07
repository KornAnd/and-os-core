"""
test_workflow_engine.py — Unit Tests for Declarative Skill Workflow Binding
AnD os v8.1 — Core Architecture Layer (Unix-Grade Workflow Engine)
"""

import unittest
from and_os.lib.core.operation_contract import Capability
from and_os.lib.core.dispatcher import CoreRegistry, CoreDispatcher
from and_os.lib.core.operations import register_builtin_operations
from and_os.lib.core.workflow_descriptor import (
    StepDescriptor,
    WorkflowDescriptor,
    WorkflowEngine,
    StepStatus,
)


class TestWorkflowEngine(unittest.TestCase):

    def setUp(self):
        self.registry = CoreRegistry()
        register_builtin_operations(self.registry)
        self.dispatcher = CoreDispatcher(self.registry)
        self.engine = WorkflowEngine(self.dispatcher)

    def test_deterministic_pilot_workflow_success(self):
        """Exercises a multi-step deterministic workflow without an LLM."""
        wf = WorkflowDescriptor(
            workflow_id="pilot_system_health_check",
            name="Autonomous System Health Check Pilot",
            primary_skill="system-audit",
            steps=(
                StepDescriptor(
                    step_id="step_ping",
                    description="Ping core microkernel",
                    operation_id="system.ping",
                    params={"message": "pilot_init"},
                    capabilities_required=(Capability.FS_READ,),
                    required_dod_keys=("echo_verified",),
                ),
                StepDescriptor(
                    step_id="step_state_checkpoint",
                    description="Record pre-audit operational checkpoint",
                    operation_id="state.set",
                    params={"key": "workflow.pilot.checkpoint", "value": {"status": "in_progress"}},
                    capabilities_required=(Capability.STATE_WRITE,),
                    required_dod_keys=("key", "observed_at"),
                ),
                StepDescriptor(
                    step_id="step_emit_audit_event",
                    description="Emit journal event confirming pilot start",
                    operation_id="event.emit",
                    params={"event_type": "PILOT_STEP_COMPLETED", "payload": {"step": "state_checkpoint"}},
                    capabilities_required=(Capability.IPC_EMIT,),
                    required_dod_keys=("event_id", "appended"),
                )
            )
        )

        res = self.engine.execute_workflow(wf, caller="test_pilot")
        self.assertTrue(res["success"])
        self.assertIsNone(res["failure_reason"])
        self.assertEqual(res["steps"]["step_ping"]["status"], StepStatus.COMPLETED.value)
        self.assertEqual(res["steps"]["step_state_checkpoint"]["status"], StepStatus.COMPLETED.value)
        self.assertEqual(res["steps"]["step_emit_audit_event"]["status"], StepStatus.COMPLETED.value)

    def test_workflow_failure_and_rollback(self):
        """Verifies fail-closed behavior and compensation triggers on step failure."""
        wf = WorkflowDescriptor(
            workflow_id="failing_workflow_test",
            name="Failing Workflow Test",
            primary_skill="system-audit",
            steps=(
                StepDescriptor(
                    step_id="step_1_set_temp_state",
                    description="Set temporary state",
                    operation_id="state.set",
                    params={"key": "workflow.temp_flag", "value": "active"},
                    capabilities_required=(Capability.STATE_WRITE,),
                    required_dod_keys=("key",),
                    compensation_op_id="state.set",
                    compensation_params={"key": "workflow.temp_flag", "value": "rolled_back"},
                ),
                StepDescriptor(
                    step_id="step_2_failing_missing_op",
                    description="Attempt call to unknown operation",
                    operation_id="unknown.operation.id",
                    capabilities_required=(),
                )
            )
        )

        res = self.engine.execute_workflow(wf, caller="test_failure")
        self.assertFalse(res["success"])
        self.assertIn("Step 'step_2_failing_missing_op' failed", res["failure_reason"])
        self.assertEqual(res["steps"]["step_1_set_temp_state"]["status"], StepStatus.ROLLED_BACK.value)
        self.assertEqual(res["steps"]["step_2_failing_missing_op"]["status"], StepStatus.FAILED.value)


if __name__ == "__main__":
    unittest.main()
