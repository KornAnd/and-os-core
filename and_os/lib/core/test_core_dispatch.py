"""
test_core_dispatch.py — Comprehensive Unit Tests for C5 Core Dispatcher & Registry
AnD os v8.1 — Core Architecture Verification
"""

import unittest
from and_os.lib.core.operation_contract import (
    Capability,
    SideEffect,
    OperationError,
    OperationRequest,
    OperationResult,
    OperationSpec,
)
from and_os.lib.core.dispatcher import (
    CoreRegistry,
    CoreDispatcher,
    RegistryError,
)


class TestCoreDispatch(unittest.TestCase):

    def setUp(self):
        self.registry = CoreRegistry()
        self.dispatcher = CoreDispatcher(registry=self.registry)

        # Register a valid mock operation: "system.ping"
        self.ping_spec = OperationSpec(
            operation_id="system.ping",
            version="1.0.0",
            description="Diagnostic ping operation",
            capabilities_required=(Capability.IPC_EMIT,),
            side_effects=(SideEffect.NONE,),
            params_schema={
                "type": "object",
                "required": ["echo"],
                "properties": {"echo": {"type": "string"}},
                "additionalProperties": False,
            },
            result_schema={
                "type": "object",
                "required": ["reply"],
                "properties": {"reply": {"type": "string"}},
            }
        )

        def ping_handler(req: OperationRequest) -> OperationResult:
            echo_val = req.params["echo"]
            return OperationResult(
                operation_id=req.operation_id,
                success=True,
                data={"reply": f"pong: {echo_val}"},
                postcondition_evidence={"timestamp_checked": True, "echo_length": len(echo_val)}
            )

        self.registry.register(self.ping_spec, ping_handler)

    def test_successful_dispatch(self):
        """Happy path: dispatch with valid params and capabilities returns success."""
        req = OperationRequest(
            operation_id="system.ping",
            version="1.0.0",
            params={"echo": "hello core"},
            caller="test_runner"
        )
        res = self.dispatcher.dispatch(req, caller_capabilities=(Capability.IPC_EMIT,))
        self.assertTrue(res.success)
        self.assertEqual(res.data["reply"], "pong: hello core")
        self.assertIn("timestamp_checked", res.postcondition_evidence)
        self.assertGreaterEqual(res.elapsed_seconds, 0.0)

    def test_unregistered_operation_fails_closed(self):
        """Unknown operation ID fails closed with OPERATION_NOT_FOUND error."""
        req = OperationRequest(
            operation_id="unregistered.op",
            version="1.0.0",
            params={},
        )
        res = self.dispatcher.dispatch(req)
        self.assertFalse(res.success)
        self.assertEqual(res.error.code, "OPERATION_NOT_FOUND")

    def test_missing_capabilities_denied(self):
        """Caller missing required capability is rejected with PERMISSION_DENIED."""
        req = OperationRequest(
            operation_id="system.ping",
            version="1.0.0",
            params={"echo": "secret"},
            caller="unprivileged_agent"
        )
        # Calling without Capability.IPC_EMIT
        res = self.dispatcher.dispatch(req, caller_capabilities=(Capability.FS_READ,))
        self.assertFalse(res.success)
        self.assertEqual(res.error.code, "PERMISSION_DENIED")
        self.assertIn("missing_capabilities", res.error.details)

    def test_invalid_parameters_rejected(self):
        """Parameters violating spec schema are rejected before handler invocation."""
        req = OperationRequest(
            operation_id="system.ping",
            version="1.0.0",
            params={"echo": 12345},  # Invalid: integer instead of string
        )
        res = self.dispatcher.dispatch(req, caller_capabilities=(Capability.IPC_EMIT,))
        self.assertFalse(res.success)
        self.assertEqual(res.error.code, "INVALID_PARAMS")

    def test_duplicate_registration_prevented(self):
        """Re-registering the same operation ID and version raises RegistryError."""
        with self.assertRaises(RegistryError):
            self.registry.register(self.ping_spec, lambda req: None)


if __name__ == "__main__":
    unittest.main()
