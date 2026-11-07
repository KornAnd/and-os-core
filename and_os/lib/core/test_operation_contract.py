"""
test_operation_contract.py — Comprehensive Unit Test Suite for Operation Contracts
AnD os v8.1 — Core Architecture Verification (C3 Gate)
"""

import unittest
from and_os.lib.core.operation_contract import (
    Capability,
    SideEffect,
    OperationError,
    OperationRequest,
    OperationResult,
    OperationSpec,
    SchemaValidationError,
    validate_schema,
)


class TestOperationContract(unittest.TestCase):
    """Test suite verifying immutable operation contracts, capabilities, and schema checks."""

    # -----------------------------------------------------------------------
    # 1. JSON Schema Subset Validator Tests
    # -----------------------------------------------------------------------

    def test_schema_validator_primitives(self):
        """Validates primitive type checking (string, integer, number, boolean)."""
        validate_schema("valid_string", {"type": "string"})
        validate_schema(42, {"type": "integer"})
        validate_schema(3.14, {"type": "number"})
        validate_schema(True, {"type": "boolean"})

        # Strict bool vs int isolation
        with self.assertRaises(SchemaValidationError):
            validate_schema(True, {"type": "integer"})
        with self.assertRaises(SchemaValidationError):
            validate_schema(100, {"type": "string"})

    def test_schema_validator_enum(self):
        """Verifies enum value enforcement."""
        schema = {"type": "string", "enum": ["PENDING", "ACTIVE", "ARCHIVED"]}
        validate_schema("ACTIVE", schema)

        with self.assertRaises(SchemaValidationError):
            validate_schema("DELETED", schema)

    def test_schema_validator_object_strictness(self):
        """Verifies object validation with required fields and additionalProperties=False."""
        schema = {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "additionalProperties": False,
        }

        # Valid payload
        valid_payload = {"id": 1, "name": "Test Asset", "tags": ["prod", "v1"]}
        validate_schema(valid_payload, schema)

        # Missing required field
        with self.assertRaises(SchemaValidationError):
            validate_schema({"id": 1}, schema)

        # Forbidden additional property
        with self.assertRaises(SchemaValidationError):
            validate_schema({"id": 1, "name": "A", "unexpected_field": True}, schema)

        # Inner array item type violation
        with self.assertRaises(SchemaValidationError):
            validate_schema({"id": 1, "name": "A", "tags": [123]}, schema)

    # -----------------------------------------------------------------------
    # 2. OperationRequest Immutability & Validation Tests
    # -----------------------------------------------------------------------

    def test_operation_request_creation_and_immutability(self):
        """Requests must be frozen dataclasses with positive timeouts."""
        req = OperationRequest(
            operation_id="system.audit",
            version="1.0.0",
            params={"deep": True},
            idempotency_key="audit-20261022-01",
            timeout_seconds=15.0,
        )
        self.assertEqual(req.operation_id, "system.audit")
        self.assertEqual(req.timeout_seconds, 15.0)

        # Frozen invariant
        with self.assertRaises(Exception):
            req.operation_id = "other.operation"

        # Invalid creation checks
        with self.assertRaises(ValueError):
            OperationRequest(operation_id="", version="1.0.0")
        with self.assertRaises(ValueError):
            OperationRequest(operation_id="test", version="", timeout_seconds=-5)

    # -----------------------------------------------------------------------
    # 3. Anti-Beta-Tester Gate on OperationResult
    # -----------------------------------------------------------------------

    def test_operation_result_requires_postcondition_evidence(self):
        """Success == True STRICTLY requires non-empty postcondition evidence."""
        # Success with genuine evidence: PASS
        res = OperationResult(
            operation_id="tasks.sync",
            success=True,
            data={"synced_count": 12},
            postcondition_evidence={"verified_file_exists": "/tmp/test.json", "rows_written": 12},
            elapsed_seconds=0.45,
        )
        self.assertTrue(res.success)
        self.assertEqual(res.data["synced_count"], 12)

        # Blind success without evidence: MUST FAIL CLOSED
        with self.assertRaises(ValueError) as ctx:
            OperationResult(
                operation_id="tasks.sync",
                success=True,
                data={"synced_count": 12},
                postcondition_evidence={},  # EMPTY -> REJECTED
            )
        self.assertIn("Anti-Beta-Tester Gate", str(ctx.exception))

    def test_operation_result_failure_requires_error_record(self):
        """Success == False requires a structured OperationError."""
        err = OperationError(
            code="NOT_FOUND",
            message="Target entity was not found.",
            details={"id": "non_existent"},
            recoverable=False,
        )
        res = OperationResult(
            operation_id="tasks.get",
            success=False,
            error=err,
            elapsed_seconds=0.01,
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error.code, "NOT_FOUND")

        # Failure without error: MUST FAIL CLOSED
        with self.assertRaises(ValueError):
            OperationResult(
                operation_id="tasks.get",
                success=False,
                error=None,
            )

    # -----------------------------------------------------------------------
    # 4. OperationSpec Contract Validation Tests
    # -----------------------------------------------------------------------

    def test_operation_spec_validates_request_and_result(self):
        """OperationSpec enforces parameters and outcome against declared schemas."""
        spec = OperationSpec(
            operation_id="vault.note.create",
            version="1.0.0",
            description="Creates a new markdown note in the designated realm",
            capabilities_required=(Capability.FS_WRITE, Capability.IPC_EMIT),
            side_effects=(SideEffect.FS_MUTATION, SideEffect.EVENT_APPEND),
            params_schema={
                "type": "object",
                "required": ["path", "content"],
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "additionalProperties": False,
            },
            result_schema={
                "type": "object",
                "required": ["bytes_written"],
                "properties": {
                    "bytes_written": {"type": "integer"}
                }
            }
        )

        valid_req = OperationRequest(
            operation_id="vault.note.create",
            version="1.0.0",
            params={"path": "Nero/test.md", "content": "# Test"}
        )
        # Must pass validation without error
        spec.validate_request(valid_req)
        spec.validate_result_data({"bytes_written": 6})

        # Mismatched operation ID
        invalid_id_req = OperationRequest(
            operation_id="vault.note.delete",
            version="1.0.0",
            params={"path": "Nero/test.md", "content": "# Test"}
        )
        with self.assertRaises(SchemaValidationError):
            spec.validate_request(invalid_id_req)

        # Mismatched version
        invalid_ver_req = OperationRequest(
            operation_id="vault.note.create",
            version="2.0.0",
            params={"path": "Nero/test.md", "content": "# Test"}
        )
        with self.assertRaises(SchemaValidationError):
            spec.validate_request(invalid_ver_req)

        # Invalid params schema
        bad_params_req = OperationRequest(
            operation_id="vault.note.create",
            version="1.0.0",
            params={"path": "Nero/test.md"}  # missing 'content'
        )
        with self.assertRaises(SchemaValidationError):
            spec.validate_request(bad_params_req)


if __name__ == "__main__":
    unittest.main()
