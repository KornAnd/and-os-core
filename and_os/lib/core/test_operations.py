"""
test_operations.py — Unit Tests for Canonical Microkernel Operations
AnD os v1.0.0 — Core Architecture Layer (Unix-Grade Microkernel Operations)
"""

import unittest
from and_os.lib.core.operation_contract import Capability, OperationRequest
from and_os.lib.core.dispatcher import CoreRegistry, CoreDispatcher
from and_os.lib.core.operations import register_builtin_operations


class TestBuiltinOperations(unittest.TestCase):

    def setUp(self):
        self.registry = CoreRegistry()
        register_builtin_operations(self.registry)
        self.dispatcher = CoreDispatcher(self.registry)

    def test_system_ping(self):
        req = OperationRequest(
            operation_id="system.ping",
            version="1.0.0",
            params={"message": "hello microkernel"},
            caller="test_runner"
        )
        res = self.dispatcher.dispatch(req, caller_capabilities=(Capability.FS_READ,), emit_audit_event=False)
        self.assertTrue(res.success)
        self.assertEqual(res.data["reply"], "hello microkernel")
        self.assertIn("echo_verified", res.postcondition_evidence)

    def test_state_set_and_get(self):
        # Set operational state key
        set_req = OperationRequest(
            operation_id="state.set",
            version="1.0.0",
            params={"key": "system.test_flag", "value": {"status": "active"}},
            caller="test_runner"
        )
        set_res = self.dispatcher.dispatch(set_req, caller_capabilities=(Capability.STATE_WRITE,), emit_audit_event=False)
        self.assertTrue(set_res.success)
        self.assertEqual(set_res.data["key"], "system.test_flag")

        # Get operational state key
        get_req = OperationRequest(
            operation_id="state.get",
            version="1.0.0",
            params={"key": "system.test_flag"},
            caller="test_runner"
        )
        get_res = self.dispatcher.dispatch(get_req, caller_capabilities=(Capability.STATE_READ,), emit_audit_event=False)
        self.assertTrue(get_res.success)
        self.assertEqual(get_res.data["result"]["value"]["status"], "active")

    def test_event_emit(self):
        req = OperationRequest(
            operation_id="event.emit",
            version="1.0.0",
            params={"event_type": "TEST_EVENT", "payload": {"msg": "ok"}},
            caller="test_runner"
        )
        res = self.dispatcher.dispatch(req, caller_capabilities=(Capability.IPC_EMIT,), emit_audit_event=False)
        self.assertTrue(res.success)
        self.assertEqual(res.data["type"], "TEST_EVENT")
        self.assertTrue(res.postcondition_evidence.get("appended"))


if __name__ == "__main__":
    unittest.main()
