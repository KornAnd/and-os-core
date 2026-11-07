#!/usr/bin/env python3
"""
schema_validator.py — Движок валидации IPC-схем ответов системных модулей (Pydantic / Schema Engine).
Принцип: Data Contract Validation.

Проверяет структуру JSON-ответов от state_manager, task_db_engine, pdf_twin_converter.
"""

import sys
import json
import argparse

STATE_SCHEMA_KEYS = {"health", "work_mars", "work_kot", "ta_bu", "finance"}
REQUIRED_DOMAIN_FIELDS = {"domain", "last_updated", "status"}

def validate_domain_states(json_data):
    if not isinstance(json_data, dict):
        return False, "Data must be a dictionary"
    
    missing_keys = STATE_SCHEMA_KEYS - set(json_data.keys())
    if missing_keys:
        return False, f"Missing domain state keys: {missing_keys}"

    for dom, state in json_data.items():
        if not isinstance(state, dict):
            return False, f"State for domain {dom} must be a dict"
        missing_fields = REQUIRED_DOMAIN_FIELDS - set(state.keys())
        if missing_fields:
            return False, f"Domain {dom} missing required fields: {missing_fields}"

    return True, "All domain states match schema"

def main():
    parser = argparse.ArgumentParser(description="IPC Schema Validator")
    parser.add_argument("--json-file", type=str, help="Путь к JSON файлу")
    parser.add_argument("--type", type=str, choices=["states"], default="states", help="Тип схемы")

    args = parser.parse_args()

    if args.json_file:
        try:
            with open(args.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid, msg = validate_domain_states(data)
            print(json.dumps({"valid": valid, "message": msg}, ensure_ascii=False, indent=2))
        except Exception as e:
            print(json.dumps({"valid": False, "error": str(e)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
