"""
AnD os Kernel Core Package.
Provides unified low-latency primitives for VFS, Event Bus, State Manager, and ProcFS.
"""

from and_os.lib.core.vfs import (
    VAULT_ROOT, AND_OS_ROOT, DIR_BIN, DIR_BOOT, DIR_ETC, DIR_LIB, DIR_OPT,
    DIR_PROC, DIR_SBIN, DIR_SRV, DIR_VAR, DIR_DB, DIR_LOG, DIR_RUN,
    resolve_path, ensure_system_dirs
)
from and_os.lib.core.root_config import (
    resolve_vault_root, resolve_pulsar_root, RootConfig, RootResolutionError,
    get_system_version, get_system_release
)
from and_os.lib.core.bus import emit_event, get_recent_events, clear_events
from and_os.lib.core.state import (
    load_states, save_states, get_domain_state, set_domain_state,
    CoreMetadataStore, StateFreshness, ProvenanceRecord
)
from and_os.lib.core.procfs import update_procfs, read_sys_stat
from and_os.lib.core.platform_compat import (
    get_os_type, normalize_path, notify, open_browser, get_secret,
    OS_MAC, OS_LINUX, OS_WINDOWS, CURRENT_OS
)
from and_os.lib.core.security_guard import scan_system_secrets, scan_file_for_leaks
from and_os.lib.core.code_ast_shrinker import shrink_python_code, shrink_file
from and_os.lib.core.operation_contract import (
    Capability, SideEffect, OperationError, OperationRequest,
    OperationResult, OperationSpec, SchemaValidationError, validate_schema
)

__all__ = [
    "VAULT_ROOT", "AND_OS_ROOT", "DIR_BIN", "DIR_BOOT", "DIR_ETC", "DIR_LIB",
    "DIR_OPT", "DIR_PROC", "DIR_SBIN", "DIR_SRV", "DIR_VAR", "DIR_DB",
    "DIR_LOG", "DIR_RUN", "resolve_path", "ensure_system_dirs",
    "resolve_vault_root", "resolve_pulsar_root", "RootConfig", "RootResolutionError",
    "get_system_version", "get_system_release",
    "emit_event", "get_recent_events", "clear_events",
    "load_states", "save_states", "get_domain_state", "set_domain_state",
    "CoreMetadataStore", "StateFreshness", "ProvenanceRecord",
    "update_procfs", "read_sys_stat",
    "get_os_type", "normalize_path", "notify", "open_browser", "get_secret",
    "OS_MAC", "OS_LINUX", "OS_WINDOWS", "CURRENT_OS",
    "scan_system_secrets", "scan_file_for_leaks",
    "shrink_python_code", "shrink_file",
    "Capability", "SideEffect", "OperationError", "OperationRequest",
    "OperationResult", "OperationSpec", "SchemaValidationError", "validate_schema"
]
