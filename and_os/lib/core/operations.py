"""
operations.py — Canonical Microkernel Built-in Operations
AnD os v1.0.0 — Core Architecture Layer (Unix-Grade Microkernel Operations)

Defines and registers core operations conforming strictly to OperationSpec:
  - system.ping (v1.0.0): Diagnostics & round-trip check
  - system.audit (v1.0.0): System integrity check via Health Grid
  - state.get (v1.0.0): Provenance-aware state lookup (core or domain)
  - state.set (v1.0.0): Atomic operational metadata update
  - event.emit (v1.0.0): Append-only event emission
"""

from __future__ import annotations

import os
import sys
import subprocess
from typing import Any, Dict

from and_os.lib.core.operation_contract import (
    Capability,
    SideEffect,
    OperationError,
    OperationRequest,
    OperationResult,
    OperationSpec,
)
from and_os.lib.core.dispatcher import CoreRegistry, CORE_REGISTRY
from and_os.lib.core.root_config import resolve_vault_root
from and_os.lib.core.bus import emit_event as bus_emit_event
from and_os.lib.core.state import CoreMetadataStore, get_domain_state


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def handle_system_ping(request: OperationRequest) -> OperationResult:
    """Handler for system.ping operation."""
    msg = request.params.get("message", "pong")
    return OperationResult(
        operation_id=request.operation_id,
        success=True,
        data={"reply": msg, "caller": request.caller},
        postcondition_evidence={"echo_verified": True, "reply": msg},
    )


def handle_system_audit(request: OperationRequest) -> OperationResult:
    """Handler for system.audit operation (delegating to validate_system.py)."""
    deep = request.params.get("deep", False)
    compact = request.params.get("compact", False)
    json_mode = request.params.get("json", True)

    vault_root = resolve_vault_root()
    validator_path = os.path.join(vault_root, "and_os/bin/validate_system.py")
    if not os.path.exists(validator_path):
        err = OperationError(
            code="VALIDATOR_NOT_FOUND",
            message=f"Validator script not found at {validator_path}",
            recoverable=False
        )
        return OperationResult(
            operation_id=request.operation_id,
            success=False,
            error=err
        )

    cmd = [sys.executable, validator_path]
    if compact:
        cmd.append("--compact")
    elif json_mode:
        cmd.append("--json")
    elif deep:
        cmd.append("--deep")
    else:
        cmd.append("--check")

    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=vault_root)
    success = (proc.returncode == 0)

    if success:
        return OperationResult(
            operation_id=request.operation_id,
            success=True,
            data={"stdout": proc.stdout, "returncode": proc.returncode},
            postcondition_evidence={"returncode": 0, "probes_executed": True},
        )
    else:
        err = OperationError(
            code="AUDIT_FAILED",
            message="Health Grid probe(s) reported issues or failure.",
            details={"stderr": proc.stderr, "stdout": proc.stdout, "returncode": proc.returncode},
            recoverable=True
        )
        return OperationResult(
            operation_id=request.operation_id,
            success=False,
            error=err,
            data={"stdout": proc.stdout, "returncode": proc.returncode}
        )


def handle_state_get(request: OperationRequest) -> OperationResult:
    """Handler for state.get operation."""
    key = request.params.get("key")
    domain = request.params.get("domain")

    if key:
        store = CoreMetadataStore()
        try:
            val = store.get(key)
        except Exception as e:
            return OperationResult(
                operation_id=request.operation_id,
                success=False,
                error=OperationError(code="STORE_ERROR", message=str(e), recoverable=False)
            )
        return OperationResult(
            operation_id=request.operation_id,
            success=True,
            data={"key": key, "result": val},
            postcondition_evidence={"queried_key": key, "found": val is not None}
        )
    elif domain:
        dom_state = get_domain_state(domain)
        return OperationResult(
            operation_id=request.operation_id,
            success=True,
            data={"domain": domain, "result": dom_state},
            postcondition_evidence={"queried_domain": domain, "freshness": dom_state.get("_provenance", {}).get("freshness", "UNKNOWN")}
        )
    else:
        return OperationResult(
            operation_id=request.operation_id,
            success=False,
            error=OperationError(code="MISSING_TARGET", message="Either 'key' or 'domain' must be provided", recoverable=False)
        )


def handle_state_set(request: OperationRequest) -> OperationResult:
    """Handler for state.set operational metadata."""
    key = request.params["key"]
    val = request.params["value"]
    source = request.params.get("source", request.caller)

    store = CoreMetadataStore()
    try:
        store.set(key, val, source=source)
        # Verify read-back postcondition
        readback = store.get(key)
        if readback is None or readback["value"] != val:
            raise RuntimeError(f"Read-back postcondition check failed for key '{key}'")
    except Exception as e:
        return OperationResult(
            operation_id=request.operation_id,
            success=False,
            error=OperationError(code="STORE_WRITE_ERROR", message=str(e), recoverable=False)
        )

    return OperationResult(
        operation_id=request.operation_id,
        success=True,
        data={"key": key, "status": "stored"},
        postcondition_evidence={"key": key, "observed_at": readback["provenance"]["observed_at"]}
    )


def handle_event_emit(request: OperationRequest) -> OperationResult:
    """Handler for event.emit operation."""
    event_type = request.params["event_type"]
    payload = request.params.get("payload", {})
    source = request.params.get("source", request.caller)
    provenance = request.params.get("provenance", {})

    try:
        record = bus_emit_event(
            event_type=event_type,
            payload=payload,
            source=source,
            provenance=provenance
        )
    except Exception as e:
        return OperationResult(
            operation_id=request.operation_id,
            success=False,
            error=OperationError(code="BUS_EMIT_ERROR", message=str(e), recoverable=False)
        )

    return OperationResult(
        operation_id=request.operation_id,
        success=True,
        data=record,
        postcondition_evidence={"event_id": record["event_id"], "appended": True}
    )


# ---------------------------------------------------------------------------
# Specifications
# ---------------------------------------------------------------------------

SPEC_SYSTEM_PING = OperationSpec(
    operation_id="system.ping",
    version="1.0.0",
    description="Test system reachability and round-trip responsiveness",
    capabilities_required=(Capability.FS_READ,),
    side_effects=(SideEffect.NONE,),
    params_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string"}
        }
    },
    result_schema={
        "type": "object",
        "properties": {
            "reply": {"type": "string"},
            "caller": {"type": "string"}
        },
        "required": ["reply"]
    }
)

SPEC_SYSTEM_AUDIT = OperationSpec(
    operation_id="system.audit",
    version="1.0.0",
    description="Execute full Health Grid system audit verification",
    capabilities_required=(Capability.FS_READ, Capability.PROC_EXEC),
    side_effects=(SideEffect.NONE,),
    params_schema={
        "type": "object",
        "properties": {
            "deep": {"type": "boolean"},
            "compact": {"type": "boolean"},
            "json": {"type": "boolean"}
        }
    },
    result_schema={
        "type": "object",
        "properties": {
            "stdout": {"type": "string"},
            "returncode": {"type": "integer"}
        },
        "required": ["returncode"]
    }
)

SPEC_STATE_GET = OperationSpec(
    operation_id="state.get",
    version="1.0.0",
    description="Retrieve operational metadata or domain state with provenance",
    capabilities_required=(Capability.STATE_READ,),
    side_effects=(SideEffect.NONE,),
    params_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "domain": {"type": "string"}
        }
    },
    result_schema={
        "type": "object"
    }
)

SPEC_STATE_SET = OperationSpec(
    operation_id="state.set",
    version="1.0.0",
    description="Update operational state in SQLite metadata store with atomic commit",
    capabilities_required=(Capability.STATE_WRITE,),
    side_effects=(SideEffect.STATE_MUTATION,),
    idempotent=True,
    params_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "value": {},
            "source": {"type": "string"}
        },
        "required": ["key", "value"]
    },
    result_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "status": {"type": "string"}
        },
        "required": ["key", "status"]
    }
)

SPEC_EVENT_EMIT = OperationSpec(
    operation_id="event.emit",
    version="1.0.0",
    description="Atomically emit an event to the append-only journal",
    capabilities_required=(Capability.IPC_EMIT,),
    side_effects=(SideEffect.EVENT_APPEND,),
    params_schema={
        "type": "object",
        "properties": {
            "event_type": {"type": "string"},
            "payload": {"type": "object"},
            "source": {"type": "string"},
            "provenance": {"type": "object"}
        },
        "required": ["event_type"]
    },
    result_schema={
        "type": "object",
        "properties": {
            "event_id": {"type": "string"},
            "timestamp_utc": {"type": "string"},
            "type": {"type": "string"}
        },
        "required": ["event_id", "timestamp_utc", "type"]
    }
)


def register_builtin_operations(registry: CoreRegistry = CORE_REGISTRY) -> None:
    """Registers all canonical operations into the designated registry."""
    registry.register(SPEC_SYSTEM_PING, handle_system_ping)
    registry.register(SPEC_SYSTEM_AUDIT, handle_system_audit)
    registry.register(SPEC_STATE_GET, handle_state_get)
    registry.register(SPEC_STATE_SET, handle_state_set)
    registry.register(SPEC_EVENT_EMIT, handle_event_emit)
