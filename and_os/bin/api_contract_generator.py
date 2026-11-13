#!/usr/bin/env python3
"""
api_contract_generator.py — Typed API & Microkernel Contract Generator
AnD os v1.0.0 — System Engineering Layer (Type-Safe Contracts & Schemas)

Generates strict OperationSpec contracts, JSON Schema, and Python dataclass interfaces
from natural language descriptions, route definitions, or function signatures.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)


class ApiContractGenerator:
    """Generates canonical AnD os OperationSpec contracts and schemas."""

    def __init__(self, operation_id: str, description: str):
        self.operation_id = operation_id.strip()
        self.description = description.strip()

    def generate_spec_code(
        self,
        capabilities: List[str] = None,
        params: Dict[str, str] = None,
        returns: Dict[str, str] = None,
        idempotent: bool = False
    ) -> str:
        caps = capabilities or ["FS_READ"]
        param_props = {}
        for k, v in (params or {}).items():
            param_props[k] = {"type": v}

        return_props = {}
        for k, v in (returns or {}).items():
            return_props[k] = {"type": v}

        caps_str = ", ".join(f"Capability.{c}" for c in caps)
        params_json = json.dumps({"type": "object", "properties": param_props}, indent=8)
        result_json = json.dumps({"type": "object", "properties": return_props}, indent=8)

        code = f'''# Canonical OperationSpec for {self.operation_id}
from and_os.lib.core.operation_contract import OperationSpec, Capability, SideEffect

SPEC_{self.operation_id.upper().replace(".", "_")} = OperationSpec(
    operation_id="{self.operation_id}",
    version="1.0.0",
    description="{self.description}",
    capabilities_required=({caps_str},),
    side_effects=(SideEffect.NONE,),
    idempotent={str(idempotent)},
    params_schema={params_json},
    result_schema={result_json}
)
'''
        return code


def main():
    parser = argparse.ArgumentParser(description="AnD os Typed Contract Generator")
    parser.add_argument("operation_id", help="Operation ID (e.g. 'tasks.export')")
    parser.add_argument("--desc", default="Generated operation contract", help="Operation description")
    parser.add_argument("--capabilities", nargs="*", default=["FS_READ"], help="Required capabilities")
    parser.add_argument("--params", help="JSON string of parameter types (e.g. '{\"task_id\": \"string\"}')")
    parser.add_argument("--returns", help="JSON string of return types (e.g. '{\"status\": \"string\"}')")
    parser.add_argument("--idempotent", action="store_true", help="Mark operation as idempotent")
    parser.add_argument("--json", action="store_true", help="Output specification in JSON format")

    args = parser.parse_args()

    gen = ApiContractGenerator(args.operation_id, args.desc)
    params_dict = json.loads(args.params) if args.params else {"target": "string"}
    returns_dict = json.loads(args.returns) if args.returns else {"success": "boolean"}

    if args.json:
        data = {
            "operation_id": args.operation_id,
            "version": "1.0.0",
            "description": args.desc,
            "capabilities": args.capabilities,
            "idempotent": args.idempotent,
            "params_schema": {"type": "object", "properties": {k: {"type": v} for k, v in params_dict.items()}},
            "result_schema": {"type": "object", "properties": {k: {"type": v} for k, v in returns_dict.items()}}
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(gen.generate_spec_code(args.capabilities, params_dict, returns_dict, args.idempotent))


if __name__ == "__main__":
    main()
