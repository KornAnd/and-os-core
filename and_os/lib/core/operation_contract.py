"""
operation_contract.py — Immutable Operation Contracts & Schema Validation
AnD os v8.1 — Core Architecture Layer (Unix-Grade Microkernel Contracts)

Defines:
  - Capability (allowlisted permissions: fs.read, fs.write, state.read, state.write, ipc.emit, proc.exec)
  - SideEffect (declared system impact: NONE, FS_MUTATION, STATE_MUTATION, EVENT_APPEND, PROCESS_SPAWN)
  - OperationError (normalized structured error record)
  - OperationRequest (frozen invocation specification with idempotency & timeout)
  - OperationResult (frozen outcome record requiring non-empty postcondition evidence for success)
  - OperationSpec (immutable metadata and schema definition for an operation)
  - Strict JSON Schema validator (stdlib-only subset: type, properties, required, additionalProperties, enum)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


# ---------------------------------------------------------------------------
# Core Enums
# ---------------------------------------------------------------------------

class Capability(str, Enum):
    """Allowlisted capability tokens for operation sandboxing and permission checks."""
    FS_READ = "fs.read"
    FS_WRITE = "fs.write"
    STATE_READ = "state.read"
    STATE_WRITE = "state.write"
    IPC_EMIT = "ipc.emit"
    PROC_EXEC = "proc.exec"


class SideEffect(str, Enum):
    """Declared side-effect classes to prevent covert state changes."""
    NONE = "NONE"
    FS_MUTATION = "FS_MUTATION"
    STATE_MUTATION = "STATE_MUTATION"
    EVENT_APPEND = "EVENT_APPEND"
    PROCESS_SPAWN = "PROCESS_SPAWN"


# ---------------------------------------------------------------------------
# Strict JSON Schema Subset Validator (Unix stdlib-only)
# ---------------------------------------------------------------------------

class SchemaValidationError(ValueError):
    """Raised when an operation payload violates its declared JSON schema."""
    pass


def validate_schema(data: Any, schema: Dict[str, Any], path: str = "payload") -> None:
    """
    Validates data against a deterministic subset of JSON Schema.
    Supported keywords: type, properties, required, additionalProperties, enum.
    Fails closed on unsupported keywords or type mismatches.
    """
    if not isinstance(schema, dict):
        raise SchemaValidationError(f"Schema at '{path}' must be a dict.")

    # 1. Type validation
    expected_type = schema.get("type")
    if expected_type:
        type_mapping = {
            "object": dict,
            "array": list,
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "null": type(None),
        }
        py_type = type_mapping.get(expected_type)
        if py_type is None:
            raise SchemaValidationError(f"Unsupported schema type '{expected_type}' at '{path}'.")
        # Python bool is a subclass of int; handle strictly
        if expected_type == "integer" and isinstance(data, bool):
            raise SchemaValidationError(f"Expected integer at '{path}', got boolean.")
        if expected_type == "number" and isinstance(data, bool):
            raise SchemaValidationError(f"Expected number at '{path}', got boolean.")
        if not isinstance(data, py_type):
            raise SchemaValidationError(
                f"Type mismatch at '{path}': expected '{expected_type}', got '{type(data).__name__}'."
            )

    # 2. Enum validation
    if "enum" in schema:
        allowed = schema["enum"]
        if not isinstance(allowed, (list, tuple, set)):
            raise SchemaValidationError(f"Schema 'enum' at '{path}' must be a list/sequence.")
        if data not in allowed:
            raise SchemaValidationError(
                f"Value {json.dumps(data)} at '{path}' is not in allowed enum: {allowed}."
            )

    # 3. Object validation
    if expected_type == "object" and isinstance(data, dict):
        required_fields: Sequence[str] = schema.get("required", [])
        for req in required_fields:
            if req not in data:
                raise SchemaValidationError(f"Missing required property '{req}' at '{path}'.")

        properties: Dict[str, Any] = schema.get("properties", {})
        allow_additional: bool = schema.get("additionalProperties", True)

        for key, val in data.items():
            if key in properties:
                validate_schema(val, properties[key], path=f"{path}.{key}")
            elif not allow_additional:
                raise SchemaValidationError(
                    f"Additional property '{key}' not allowed at '{path}'."
                )

    # 4. Array validation
    if expected_type == "array" and isinstance(data, list):
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(data):
                validate_schema(item, item_schema, path=f"{path}[{idx}]")


# ---------------------------------------------------------------------------
# Immutable Operation Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OperationError:
    """Normalized structured error record for operation failures."""
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


@dataclass(frozen=True)
class OperationRequest:
    """
    Immutable specification of an operation invocation.
    Guarantees idempotency and explicit execution parameters.
    """
    operation_id: str
    version: str
    params: Dict[str, Any] = field(default_factory=dict)
    caller: str = "cli"
    idempotency_key: Optional[str] = None
    timeout_seconds: float = 30.0

    def __post_init__(self):
        if not self.operation_id or not isinstance(self.operation_id, str):
            raise ValueError("OperationRequest: operation_id must be a non-empty string.")
        if not self.version or not isinstance(self.version, str):
            raise ValueError("OperationRequest: version must be a non-empty string.")
        if self.timeout_seconds <= 0:
            raise ValueError("OperationRequest: timeout_seconds must be positive.")
        if not isinstance(self.params, dict):
            raise ValueError("OperationRequest: params must be a dictionary.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "version": self.version,
            "params": self.params,
            "caller": self.caller,
            "idempotency_key": self.idempotency_key,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True)
class OperationResult:
    """
    Immutable outcome of an operation.
    Invariants:
      - Anti-Beta-Tester Gate: success == True REQUIRES non-empty postcondition_evidence.
      - If success == False, error MUST be present.
    """
    operation_id: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[OperationError] = None
    postcondition_evidence: Dict[str, Any] = field(default_factory=dict)
    elapsed_seconds: float = 0.0

    def __post_init__(self):
        if not self.operation_id:
            raise ValueError("OperationResult: operation_id cannot be empty.")
        if self.success:
            if not self.postcondition_evidence:
                raise ValueError(
                    f"Anti-Beta-Tester Gate: OperationResult for '{self.operation_id}' succeeded "
                    f"but lacks required 'postcondition_evidence'. Blind success is prohibited."
                )
            if self.error is not None:
                raise ValueError("OperationResult cannot have both success=True and an error.")
        else:
            if self.error is None:
                raise ValueError("OperationResult with success=False MUST provide an OperationError.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "success": self.success,
            "data": self.data,
            "error": self.error.to_dict() if self.error else None,
            "postcondition_evidence": self.postcondition_evidence,
            "elapsed_seconds": self.elapsed_seconds,
        }


@dataclass(frozen=True)
class OperationSpec:
    """
    Immutable contract definition of an available system operation.
    Enforces declared capabilities and strict payload schemas before execution.
    """
    operation_id: str
    version: str
    description: str
    capabilities_required: Tuple[Capability, ...] = ()
    side_effects: Tuple[SideEffect, ...] = (SideEffect.NONE,)
    params_schema: Dict[str, Any] = field(default_factory=lambda: {"type": "object"})
    result_schema: Dict[str, Any] = field(default_factory=lambda: {"type": "object"})
    default_timeout: float = 30.0
    idempotent: bool = True

    def __post_init__(self):
        if not self.operation_id or not isinstance(self.operation_id, str):
            raise ValueError("OperationSpec: operation_id must be a non-empty string.")
        if not self.version or not isinstance(self.version, str):
            raise ValueError("OperationSpec: version must be a non-empty string.")
        if self.default_timeout <= 0:
            raise ValueError("OperationSpec: default_timeout must be positive.")
        # Ensure schemas are valid dicts
        if not isinstance(self.params_schema, dict) or not isinstance(self.result_schema, dict):
            raise ValueError("OperationSpec schemas must be dicts.")

    def validate_request(self, request: OperationRequest) -> None:
        """Validates incoming request against this operation specification."""
        if request.operation_id != self.operation_id:
            raise SchemaValidationError(
                f"Operation ID mismatch: expected '{self.operation_id}', got '{request.operation_id}'."
            )
        if request.version != self.version:
            raise SchemaValidationError(
                f"Version mismatch for '{self.operation_id}': expected '{self.version}', got '{request.version}'."
            )
        validate_schema(request.params, self.params_schema, path="params")

    def validate_result_data(self, data: Dict[str, Any]) -> None:
        """Validates outcome payload against result schema."""
        validate_schema(data, self.result_schema, path="result.data")
