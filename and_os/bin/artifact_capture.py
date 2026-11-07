#!/usr/bin/env python3
"""
artifact_capture.py - Visual Artifact & Diagnostic State Capture Engine on Failure.
Captures:
  1. macOS desktop/window screenshot via /usr/sbin/screencapture (-x silent mode).
  2. Local services & port inspection (8087 ComfyUI, 8092, 8099 AND_Terminal, etc.).
  3. Last 50 lines of and_os event stream (events.jsonl).
  4. Automatically purges old failure artifacts keeping strictly the last 10.
"""

import sys
import os
import time
import json
import socket
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, List

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACT_DIR = VAULT_ROOT / "and_os" / "var" / "artifacts"
EVENT_LOG = VAULT_ROOT / "and_os" / "var" / "events.jsonl"
MAX_ARTIFACTS = 10

PORTS_TO_CHECK = [
    (8087, "ComfyUI Bridge"),
    (8092, "AnD Local Service"),
    (8099, "AND_Terminal UI"),
    (9090, "Telemetry/Metrics")
]

def check_port(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def get_recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    if not EVENT_LOG.exists():
        return []
    try:
        with open(EVENT_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
        recent = lines[-limit:]
        events = []
        for l in recent:
            try:
                events.append(json.loads(l.strip()))
            except Exception:
                events.append({"raw": l.strip()})
        return events
    except Exception as e:
        return [{"error": f"Failed to read events: {e}"}]

def rotate_artifacts(directory: Path, keep_limit: int = MAX_ARTIFACTS):
    """Keep only the latest N artifact sets (png + json)."""
    try:
        meta_files = sorted(directory.glob("fail_*.json"), key=lambda p: p.stat().st_mtime)
        if len(meta_files) > keep_limit:
            to_delete = meta_files[:-keep_limit]
            for mf in to_delete:
                base_stem = mf.stem
                png_file = directory / f"{base_stem}.png"
                if mf.exists():
                    mf.unlink()
                if png_file.exists():
                    png_file.unlink()
    except Exception:
        pass

def capture(reason: str = "Test failure or runtime crash", command: str = "") -> Dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    iso_time = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    
    png_path = ARTIFACT_DIR / f"fail_{ts}.png"
    json_path = ARTIFACT_DIR / f"fail_{ts}.json"

    # 1. Take silent screenshot using macOS screencapture
    screenshot_captured = False
    screencapture_bin = "/usr/sbin/screencapture"
    if os.path.exists(screencapture_bin):
        try:
            # -x: mute sound, -C: capture cursor
            p = subprocess.run([screencapture_bin, "-x", str(png_path)], capture_output=True, timeout=5)
            screenshot_captured = (p.returncode == 0 and png_path.exists())
        except Exception:
            screenshot_captured = False

    # 2. Inspect active network ports
    active_ports = {}
    for port, label in PORTS_TO_CHECK:
        active_ports[f"{port} ({label})"] = "LISTENING" if check_port(port) else "CLOSED"

    # 3. Read event stream
    events = get_recent_events(50)

    # 4. Construct diagnostic manifest
    manifest = {
        "timestamp": iso_time,
        "unix_epoch": ts,
        "reason": reason,
        "command": command,
        "screenshot": str(png_path.name) if screenshot_captured else None,
        "ports": active_ports,
        "recent_events_count": len(events),
        "recent_events": events[-10:] # Store last 10 in json summary
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # 5. Rotate old artifacts
    rotate_artifacts(ARTIFACT_DIR, MAX_ARTIFACTS)

    return {
        "status": "success",
        "timestamp": iso_time,
        "png": str(png_path) if screenshot_captured else "None",
        "manifest": str(json_path),
        "ports": active_ports
    }

def main():
    parser = argparse.ArgumentParser(description="Capture visual and state failure artifacts on macOS")
    parser.add_argument("--reason", "-r", default="Manual capture or unhandled test failure", help="Reason for failure")
    parser.add_argument("--cmd", "-c", default="", help="Command that failed")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()
    res = capture(reason=args.reason, command=args.cmd)

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print("📸 Failure Artifact Captured:")
        print(f"   Timestamp  : {res['timestamp']}")
        print(f"   Screenshot : {res['png']}")
        print(f"   Diagnostic : {res['manifest']}")
        print("   Port Status:")
        for p, s in res["ports"].items():
            print(f"     - {p}: {s}")

if __name__ == "__main__":
    main()
