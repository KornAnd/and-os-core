#!/usr/bin/env python3
"""Houdini bridge facade (external composition; kernel sys_cli.py untouched, Rule #15).

Commands (Rule #73 execution protocol):
  status [--json]      hwebserver HTTP state up/zombie/down + instance count (exit 0/2/3)
  check                offline canary: config + allowlist 4/4 + sanitizer (<500 ms)
  call TOOL --arg k=v  one MCP tool call via the official fxhoudinimcp stdio server
  sanitize FILE --out  redact a payload per the negative allowlist (Rule #73)
  check-payload FILE   pre-send gate; exit 1 = blocked
  capture [--out DIR]  render_viewport -> PNG on the Rule #72 retention channel
  launch [--wait S]    start the SINGLE Houdini Apprentice instance (guarded)

Stateless (Rule #50): every call spawns one MCP stdio session and exits.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.
import time
from pathlib import Path

AND_OS_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = AND_OS_ROOT / "lib" / "skills" / "houdini-bridge" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import canary  # noqa: E402
import client  # noqa: E402
import sanitizer  # noqa: E402


def cmd_status(args: argparse.Namespace) -> int:
    """hweb_state() at the HTTP level: up (0) / zombie (2) / down (3)."""
    payload = client.status()
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"mcp: {payload['mcp']} | sesinetd: {'up' if payload['sesinetd'] else 'down'}"
              f" | houdini instances: {payload['houdini_instances']}")
    return {"up": 0, "zombie": 2, "down": 3}[payload["mcp"]]


def cmd_check(args: argparse.Namespace) -> int:
    """Offline canary (probe_cmd): config + allowlist + sanitizer, budget 500 ms."""
    try:
        checks, elapsed_ms = canary.run_checks()
    except sanitizer.PolicyError as err:
        print(f"FAIL: {err}", file=sys.stderr)
        return 1
    ok = all(c["ok"] for c in checks)
    if args.json:
        print(json.dumps({"ok": ok, "ms": elapsed_ms, "checks": checks}, indent=2))
    else:
        for check in checks:
            mark = "ok" if check["ok"] else "FAIL"
            print(f"  [{mark:>4}] {check['name']}: {check['detail']}")
        print(f"offline canary: {'PASS' if ok else 'FAIL'} ({elapsed_ms} ms)")
    return 0 if ok else 1


def _parse_args(pairs: list) -> dict:
    """--arg KEY=VALUE: JSON value when parseable, else string."""
    out = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise client.BridgeError(f"--arg expects KEY=VALUE, got {pair!r}")
        key, value = pair.split("=", 1)
        try:
            out[key] = json.loads(value)
        except json.JSONDecodeError:
            out[key] = value
    return out


def _require_up(config: dict) -> bool:
    bridge = config["bridge"]
    state = client.hweb_state(bridge["host"], bridge["port"])
    if state == "up":
        return True
    print(f"bridge is not up (state={state}) — restart the SINGLE DCC instance first "
          f"(Rule #73)", file=sys.stderr)
    return False


def cmd_call(args: argparse.Namespace) -> int:
    """One MCP tool call; evidence = reply JSON + ms (Rule #61)."""
    config = client.load_config()
    if not _require_up(config):
        return 2
    try:
        result = client.call_tool(args.tool, _parse_args(args.arg), config, timeout=args.timeout)
    except client.BridgeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


def cmd_sanitize(args: argparse.Namespace) -> int:
    """Redact a payload; refuses (exit 1) when the payload is blocked."""
    try:
        report = sanitizer.sanitize_file(Path(args.file), Path(args.out))
    except (sanitizer.PolicyError, sanitizer.PayloadBlocked, OSError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print(f"sanitized -> {args.out} | redact={len(report.redact)} verdict={report.verdict}")
    if args.report:
        Path(args.report).write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return 0


def cmd_check_payload(args: argparse.Namespace) -> int:
    """Pre-send gate (Rule #73): exit 1 = blocked, payload must not leave."""
    try:
        report = sanitizer.check_file(Path(args.file))
    except (sanitizer.PolicyError, OSError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2
    if report.verdict == "BLOCKED":
        print(f"BLOCKED: {len(report.reject)} reject-class hit(s) — payload must not leave the station")
        for hit in report.reject[:5]:
            print(f"  [{hit.section}] {hit.match!r}")
        return 1
    print(f"PASS: redactable hits={len(report.redact)} — run 'sanitize' before sending to an external LLM")
    return 0


def trim_captures(directory: Path, keep: int) -> int:
    """Rule #72: bound the capture channel BEFORE the write (keep newest N)."""
    pngs = sorted(directory.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for old in pngs[keep:]:
        old.unlink()
        removed += 1
    return removed


def cmd_capture(args: argparse.Namespace) -> int:
    """render_viewport -> PNG (the only reliable macOS capture; evidence checked)."""
    config = client.load_config()
    if not _require_up(config):
        return 2
    capture = config["canaries"]
    out_dir = Path(args.out or capture["capture_dir"])
    if not out_dir.is_absolute():
        out_dir = AND_OS_ROOT.parent / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    removed = trim_captures(out_dir, int(capture.get("capture_keep", 200)))
    width, height = capture["capture_resolution"]
    png = out_dir / f"capture_{time.strftime('%Y%m%d_%H%M%S')}.png"
    tool_args = {"output_path": str(png), "resolution": [width, height]}
    if args.camera:
        tool_args["camera"] = args.camera
    try:
        result = client.call_tool(capture["live_capture_tool"], tool_args, config,
                                  timeout=args.timeout)
    except client.BridgeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2
    if not result["ok"]:
        print(f"render_viewport failed: {str(result.get('result'))[:500]}", file=sys.stderr)
        return 1
    if not png.exists() or png.stat().st_size < 512:
        print(f"capture evidence missing: {png} (file not written or too small)", file=sys.stderr)
        return 1
    note = f" | trimmed {removed} old" if removed else ""
    print(f"capture: {png} ({png.stat().st_size} bytes, {result['ms']} ms){note}")
    return 0


def cmd_launch(args: argparse.Namespace) -> int:
    """Start the single Houdini instance; refuses on a served port or live instance."""
    config = client.load_config()
    bridge = config["bridge"]
    state = client.hweb_state(bridge["host"], bridge["port"])
    if state != "down":
        print(f"port {bridge['port']} already served (state={state}) — refusing a second "
              f"instance (Rule #73)", file=sys.stderr)
        return 1
    if client.houdini_instances(bridge) > 0:
        print("a Houdini instance is already running — one instance only (Rule #73)",
              file=sys.stderr)
        return 1
    binary = os.path.expanduser(bridge["dcc_binary"])
    if not Path(binary).exists():
        print(f"DCC binary not found: {binary}", file=sys.stderr)
        return 1
    env = dict(os.environ)
    for key, value in bridge.get("launch_env", {}).items():
        env[key] = os.path.expanduser(str(value))
    subprocess.Popen([binary], env=env, start_new_session=True)
    print(f"launched: {binary}")
    started = time.monotonic()
    deadline = started + args.wait
    state = "down"
    while time.monotonic() < deadline:
        state = client.hweb_state(bridge["host"], bridge["port"], timeout=2.0)
        if state == "up":
            break
        time.sleep(2)
    if state != "up":
        print(f"bridge not up after {args.wait:.0f}s (state={state}) — check the Houdini log; "
              f"after a SIGKILL: sudo launchctl kickstart -k system/com.sidefx.sesinetd",
              file=sys.stderr)
        return 1
    elapsed = int((time.monotonic() - started) * 1000)
    print(f"bridge UP in {elapsed} ms — single instance on {bridge['host']}:{bridge['port']}")
    return 0


def main(argv: list = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    parser = argparse.ArgumentParser(
        prog="houdini_bridge.py",
        description="Houdini MCP bridge facade (Rule #73; kernel untouched, Rule #15).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", parents=[common],
                   help="hweb state (exit 0 up / 2 zombie / 3 down)")
    sub.add_parser("check", parents=[common], help="offline canary (<500 ms)")
    pc = sub.add_parser("call", help="one MCP tool call")
    pc.add_argument("tool")
    pc.add_argument("--arg", action="append", default=[], metavar="KEY=VALUE")
    pc.add_argument("--timeout", type=float, default=120.0)
    ps = sub.add_parser("sanitize", help="redact a payload (Rule #73)")
    ps.add_argument("file")
    ps.add_argument("--out", required=True)
    ps.add_argument("--report", default=None)
    pp = sub.add_parser("check-payload", help="pre-send gate (exit 1 = blocked)")
    pp.add_argument("file")
    pcap = sub.add_parser("capture", help="render_viewport -> PNG (Rule #72 channel)")
    pcap.add_argument("--out", default=None)
    pcap.add_argument("--camera", default=None)
    pcap.add_argument("--timeout", type=float, default=180.0)
    pl = sub.add_parser("launch", help="start the single Houdini instance (guarded)")
    pl.add_argument("--wait", type=float, default=180.0)
    args = parser.parse_args(argv)

    handlers = {
        "status": cmd_status,
        "check": cmd_check,
        "call": cmd_call,
        "sanitize": cmd_sanitize,
        "check-payload": cmd_check_payload,
        "capture": cmd_capture,
        "launch": cmd_launch,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
