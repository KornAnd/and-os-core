"""
test_operations.py — Unit Tests for Canonical Microkernel Operations
AnD os v1.2.0 — Core Architecture Layer (Unix-Grade Microkernel Operations)
"""

import unittest
import unittest.mock
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


class TestSystemAuditFlagContract(unittest.TestCase):
    """C14 K2: system.audit must only pass flags that validate_system.py
    actually declares (--compact/--json/--fix/--save-report). The old
    elif-chain passed the phantom flags '--check' (json=false branch) and
    '--deep', which the validator's argparse rejects with rc=2."""

    def setUp(self):
        import and_os.lib.core.operations as ops
        self.ops = ops
        self.registry = CoreRegistry()
        register_builtin_operations(self.registry)
        self.dispatcher = CoreDispatcher(self.registry)

    def _dispatch_audit(self, params):
        req = OperationRequest(
            operation_id="system.audit",
            version="1.0.0",
            params=params,
            caller="test_runner",
        )
        return self.dispatcher.dispatch(req, caller_capabilities=(Capability.FS_READ, Capability.PROC_EXEC), emit_audit_event=False)

    def test_json_false_uses_verbose_not_phantom_check(self):
        with unittest.mock.patch.object(self.ops.subprocess, "run") as run_mock:
            run_mock.return_value = unittest.mock.Mock(returncode=0, stdout="ok", stderr="")
            res = self._dispatch_audit({"json": False})
        self.assertTrue(res.success)
        cmd = run_mock.call_args.args[0]
        self.assertNotIn("--check", cmd, "phantom flag: validate_system.py has no --check")
        self.assertNotIn("--deep", cmd, "phantom flag: validate_system.py has no --deep")
        self.assertNotIn("--json", cmd)
        self.assertNotIn("--compact", cmd)  # verbose mode = no format flag

    def test_default_uses_json(self):
        with unittest.mock.patch.object(self.ops.subprocess, "run") as run_mock:
            run_mock.return_value = unittest.mock.Mock(returncode=0, stdout="{}", stderr="")
            res = self._dispatch_audit({})
        self.assertTrue(res.success)
        cmd = run_mock.call_args.args[0]
        self.assertIn("--json", cmd)

    def test_compact_wins_over_json(self):
        with unittest.mock.patch.object(self.ops.subprocess, "run") as run_mock:
            run_mock.return_value = unittest.mock.Mock(returncode=0, stdout="ok", stderr="")
            res = self._dispatch_audit({"compact": True, "json": True})
        self.assertTrue(res.success)
        cmd = run_mock.call_args.args[0]
        self.assertIn("--compact", cmd)
        self.assertNotIn("--json", cmd)

    def test_subprocess_env_disables_bytecode(self):
        # C14 K2 / class C13 F4: the audit subprocess must not compile
        # bytecode into the source tree, even under a non-golden interpreter.
        with unittest.mock.patch.object(self.ops.subprocess, "run") as run_mock:
            run_mock.return_value = unittest.mock.Mock(returncode=0, stdout="{}", stderr="")
            self._dispatch_audit({})
        env = run_mock.call_args.kwargs.get("env")
        self.assertIsNotNone(env, "audit subprocess must run with an explicit env")
        self.assertEqual(env.get("PYTHONDONTWRITEBYTECODE"), "1")

    def test_spec_schema_has_no_phantom_deep(self):
        from and_os.lib.core.operations import SPEC_SYSTEM_AUDIT
        props = SPEC_SYSTEM_AUDIT.params_schema.get("properties", {})
        self.assertNotIn("deep", props, "'deep' must be removed from the spec: it has no effect")


if __name__ == "__main__":
    unittest.main()
