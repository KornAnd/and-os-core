"""
xcode — Dedicated Island 9 Subsystem Package (AnD os Core).
Handles iOS / macOS Swift project discovery, Package.swift and xcodeproj inspection,
and passport synchronization with Nero/xcode/.
"""

from and_os.lib.xcode.inspector import XcodeInspector
from and_os.lib.xcode.passport_sync import XcodePassportSync

__all__ = ["XcodeInspector", "XcodePassportSync"]
