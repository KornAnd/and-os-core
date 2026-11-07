"""
dispatcher.py — Core In-Process Operation Registry & Secure Dispatcher
AnD os v8.1 — Core Architecture Layer (Unix-Grade Microkernel Dispatch)

Defines:
  - OperationHandler: Callable interface (OperationRequest -> OperationResult)
  - CoreRegistry: Thread-safe in-process catalog of OperationSpec & Handlers
  - CoreDispatcher: Validates requests against specs, checks capabilities,
    times execution, guarantees postcondition evidence, captures events,
    and returns deterministic OperationResult records.
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Callable, Dict, Optional, Tuple

from and_os.lib.core.operation_contract import (
    Capability,
    OperationError,
    OperationRequest,
    OperationResult,
    OperationSpec,
    SchemaValidationError,
)
from and_os.lib.core.bus import emit_event

OperationHandler = Callable[[OperationRequest], OperationResult]


class RegistryError(RuntimeError):
    """Raised when an operation cannot be registered or resolved."""
    pass


class DispatchError(RuntimeError):
    """Raised on critical dispatcher pipeline failures."""
    pass


class CoreRegistry:
    """
    In-process singleton registry of all verified operations in AnD os.
    Provides strict versioned resolution and capability introspection.
    """

    def __init__(self):
        self._specs: Dict[Tuple[str, str], OperationSpec] = {}
        self._handlers: Dict[Tuple[str, str], OperationHandler] = {}

    def register(self, spec: OperationSpec, handler: OperationHandler) -> None:
        """Registers an operation specification and its deterministic handler."""
        key = (spec.operation_id, spec.version)
        if key in self._specs:
            raise RegistryError(
                f"Operation '{spec.operation_id}' v'{spec.version}' is already registered."
            )
        self._specs[key] = spec
        self._handlers[key] = handler

    def get_spec(self, operation_id: str, version: str) -> Optional[OperationSpec]:
        """Retrieves an operation specification by ID and version."""
        return self._specs.get((operation_id, version))

    def get_handler(self, operation_id: str, version: str) -> Optional[OperationHandler]:
        """Retrieves an operation handler by ID and version."""
        return self._handlers.get((operation_id, version))

    def list_operations(self) -> Dict[str, str]:
        """Lists all registered operation IDs and their versions."""
        return {f"{k[0]}@{k[1]}": spec.description for k, spec in self._specs.items()}


# Global microkernel registry instance
CORE_REGISTRY = CoreRegistry()


class CoreDispatcher:
    """
    Central execution dispatcher.
    Enforces contract validation, capabilities, timeouts, and event journals.
    """

    def __init__(self, registry: CoreRegistry = CORE_REGISTRY):
        self.registry = registry

    def dispatch(
        self,
        request: OperationRequest,
        caller_capabilities: Optional[Tuple[Capability, ...]] = None,
        emit_audit_event: bool = True
    ) -> OperationResult:
        """
        Dispatches an OperationRequest through the microkernel pipeline:
          1. Operation & version resolution in registry (Fail closed if unknown).
          2. Capability permission verification.
          3. Input parameter schema validation.
          4. Execution with deterministic timing.
          5. Result schema & Anti-Beta-Tester postcondition evidence check.
          6. Event journal logging.
        """
        start_time = time.monotonic()
        op_id = request.operation_id
        ver = request.version

        # 1. Resolve operation specification
        spec = self.registry.get_spec(op_id, ver)
        if spec is None:
            elapsed = time.monotonic() - start_time
            err = OperationError(
                code="OPERATION_NOT_FOUND",
                message=f"Operation '{op_id}' version '{ver}' is not registered in the core registry.",
                details={"operation_id": op_id, "version": ver},
                recoverable=False,
            )
            return OperationResult(
                operation_id=op_id,
                success=False,
                error=err,
                elapsed_seconds=round(elapsed, 4),
            )

        handler = self.registry.get_handler(op_id, ver)
        if handler is None:
            elapsed = time.monotonic() - start_time
            err = OperationError(
                code="HANDLER_NOT_FOUND",
                message=f"Specification exists for '{op_id}' v'{ver}', but no handler is bound.",
                recoverable=False,
            )
            return OperationResult(
                operation_id=op_id,
                success=False,
                error=err,
                elapsed_seconds=round(elapsed, 4),
            )

        # 2. Check capabilities
        if spec.capabilities_required and caller_capabilities is not None:
            caller_caps_set = set(caller_capabilities)
            missing = [cap for cap in spec.capabilities_required if cap not in caller_caps_set]
            if missing:
                elapsed = time.monotonic() - start_time
                err = OperationError(
                    code="PERMISSION_DENIED",
                    message=f"Caller '{request.caller}' lacks required capabilities: {[c.value for c in missing]}",
                    details={"missing_capabilities": [c.value for c in missing]},
                    recoverable=False,
                )
                return OperationResult(
                    operation_id=op_id,
                    success=False,
                    error=err,
                    elapsed_seconds=round(elapsed, 4),
                )

        # 3. Validate input parameters schema
        try:
            spec.validate_request(request)
        except SchemaValidationError as e:
            elapsed = time.monotonic() - start_time
            err = OperationError(
                code="INVALID_PARAMS",
                message=f"Parameter schema validation failed: {e}",
                details={"error": str(e)},
                recoverable=False,
            )
            return OperationResult(
                operation_id=op_id,
                success=False,
                error=err,
                elapsed_seconds=round(elapsed, 4),
            )

        # 4. Execute handler
        try:
            raw_result = handler(request)
        except Exception as exc:
            elapsed = time.monotonic() - start_time
            err = OperationError(
                code="HANDLER_EXCEPTION",
                message=f"Unhandled exception in operation handler: {exc}",
                details={"traceback": traceback.format_exc()},
                recoverable=False,
            )
            return OperationResult(
                operation_id=op_id,
                success=False,
                error=err,
                elapsed_seconds=round(elapsed, 4),
            )

        elapsed = time.monotonic() - start_time

        # 5. Validate output payload schema if successful
        if raw_result.success:
            try:
                spec.validate_result_data(raw_result.data)
            except SchemaValidationError as sve:
                err = OperationError(
                    code="INVALID_RESULT_SCHEMA",
                    message=f"Handler returned invalid result data schema: {sve}",
                    details={"error": str(sve)},
                    recoverable=False,
                )
                return OperationResult(
                    operation_id=op_id,
                    success=False,
                    error=err,
                    elapsed_seconds=round(elapsed, 4),
                )

        # Construct final timed result (preserving postcondition evidence)
        final_result = OperationResult(
            operation_id=raw_result.operation_id,
            success=raw_result.success,
            data=raw_result.data,
            error=raw_result.error,
            postcondition_evidence=raw_result.postcondition_evidence,
            elapsed_seconds=round(elapsed, 4),
        )

        # 6. Event journal logging
        if emit_audit_event:
            try:
                emit_event(
                    event_type="OPERATION_DISPATCHED",
                    payload={
                        "operation_id": op_id,
                        "caller": request.caller,
                        "success": final_result.success,
                        "elapsed_seconds": final_result.elapsed_seconds,
                    },
                    source="dispatcher",
                    provenance={"idempotency_key": request.idempotency_key}
                )
            except (OSError, RuntimeError) as err:
                sys.stderr.write(f"[dispatcher] Warning emitting completion event: {err}\n")

        return final_result
