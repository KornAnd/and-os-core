#!/usr/bin/env python3
"""
web_perf_baseline.py — Deterministic HTTP performance baseline & regression.

Part of the ui-inspector skill (Contour B: Evidence-Based QA, v1.1).
Measures a local web endpoint (Pulsar services :8080-:8099, dashboards)
with reproducible, token-cheap metrics:

  - TTFB (time to first byte, ms)
  - total time (ms)
  - body size (bytes)
  - DOM node estimate (HTML tag count) for HTML responses
  - resource reference count (src/href/link) for HTML responses

Baselines are stored in and_os/var/web_perf_baseline.json (Rule #50:
runtime state lives in var/, never in the skill folder).

Regression thresholds (fail, exit 1):
  TTFB or total time worse by more than +50%
  body size larger by more than +10%
  (smaller size / faster time is an improvement, never a regression)

Usage:
  python3 web_perf_baseline.py measure <url>
  python3 web_perf_baseline.py baseline <url> [--name NAME]
  python3 web_perf_baseline.py compare <url> [--name NAME]
  python3 web_perf_baseline.py list

Exit codes: 0 ok (no regression) · 1 regression detected · 2 usage error.
Stdlib only. Network scope: the target URL only (local services).
"""

import argparse
import json
import os
import re
import sys
sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.
import time
import urllib.error
import urllib.request

EXIT_OK = 0
EXIT_REGRESSION = 1
EXIT_USAGE = 2

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__))))
BASELINE_FILE = os.path.join(VAULT_ROOT, "and_os", "var",
                             "web_perf_baseline.json")

TTFB_BUDGET_GROWTH = 1.50
SIZE_BUDGET_GROWTH = 1.10
CONNECT_TIMEOUT_SECONDS = 5.0

TAG_RE = re.compile(r"<[a-zA-Z][a-zA-Z0-9-]*")
RESOURCE_RE = re.compile(r"(?:src|href)\s*=\s*[\"'][^\"']+")


def fail_usage(message: str) -> None:
    sys.stderr.write(f"[web_perf_baseline] ERROR: {message}\n")
    sys.exit(EXIT_USAGE)


def measure(url: str) -> dict:
    """Measures one GET request: TTFB, total time, size, DOM stats."""
    request = urllib.request.Request(url, method="GET")
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request,
                                    timeout=CONNECT_TIMEOUT_SECONDS) as resp:
            first_byte = time.perf_counter()
            body = resp.read()
            total = time.perf_counter()
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
    except (urllib.error.URLError, urllib.error.HTTPError,
            OSError) as err:
        sys.stderr.write(f"[web_perf_baseline] ERROR: GET {url} failed: "
                         f"{err}\n")
        sys.exit(EXIT_USAGE)
    text = None
    if "html" in content_type.lower():
        text = body.decode("utf-8", errors="replace")
    return {
        "url": url,
        "status": status,
        "ttfb_ms": round((first_byte - start) * 1000, 2),
        "total_ms": round((total - start) * 1000, 2),
        "body_bytes": len(body),
        "dom_nodes": len(TAG_RE.findall(text)) if text is not None else None,
        "resources": len(RESOURCE_RE.findall(text)) if text is not None
        else None,
        "measured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def load_baseline() -> dict:
    if not os.path.exists(BASELINE_FILE):
        return {}
    try:
        with open(BASELINE_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as err:
        fail_usage(f"baseline file unreadable: {err}")


def save_baseline(store: dict, key: str, entry: dict) -> None:
    store[key] = entry
    os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
    with open(BASELINE_FILE, "w", encoding="utf-8") as handle:
        json.dump(store, handle, indent=2, sort_keys=True)
        handle.write("\n")


def print_entry(title: str, entry: dict) -> None:
    sys.stdout.write(f"{title}: {entry['url']}  "
                     f"[{entry['status']}]\n")
    sys.stdout.write(f"  TTFB: {entry['ttfb_ms']} ms | "
                     f"total: {entry['total_ms']} ms | "
                     f"body: {entry['body_bytes']} bytes")
    if entry.get("dom_nodes") is not None:
        sys.stdout.write(f" | dom~{entry['dom_nodes']} | "
                         f"resources~{entry.get('resources')}")
    sys.stdout.write(f"\n  at: {entry['measured_at']}\n")


def compare_entries(baseline: dict, current: dict) -> list:
    """Returns the list of regression messages (empty = clean)."""
    regressions = []
    if baseline["status"] != current["status"]:
        regressions.append(
            f"status changed: {baseline['status']} -> {current['status']}")
    if (current["ttfb_ms"] > baseline["ttfb_ms"] * TTFB_BUDGET_GROWTH
            and current["ttfb_ms"] > baseline["ttfb_ms"] + 5):
        regressions.append(
            f"TTFB {baseline['ttfb_ms']} -> {current['ttfb_ms']} ms "
            f"(> +{int((TTFB_BUDGET_GROWTH - 1) * 100)}%)")
    if (current["total_ms"] > baseline["total_ms"] * TTFB_BUDGET_GROWTH
            and current["total_ms"] > baseline["total_ms"] + 5):
        regressions.append(
            f"total {baseline['total_ms']} -> {current['total_ms']} ms "
            f"(> +{int((TTFB_BUDGET_GROWTH - 1) * 100)}%)")
    if (current["body_bytes"]
            > baseline["body_bytes"] * SIZE_BUDGET_GROWTH
            and (baseline["body_bytes"] < 4096
                 or current["body_bytes"]
                 - baseline["body_bytes"] > 1024)):
        regressions.append(
            f"size {baseline['body_bytes']} -> {current['body_bytes']} "
            f"bytes (> +{int((SIZE_BUDGET_GROWTH - 1) * 100)}%)")
    return regressions


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="HTTP perf baseline & regression")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("measure", "baseline", "compare"):
        entry = sub.add_parser(name)
        entry.add_argument("url")
        entry.add_argument("--name", default=None,
                           help="baseline slot name (default: the URL)")
    sub.add_parser("list")
    args = parser.parse_args(argv)

    if args.cmd == "list":
        store = load_baseline()
        if not store:
            sys.stdout.write("no baselines stored\n")
            return EXIT_OK
        for key in sorted(store):
            print_entry(f"[{key}]", store[key])
        return EXIT_OK

    key = args.name or args.url
    if args.cmd == "measure":
        print_entry("MEASURE", measure(args.url))
        return EXIT_OK

    current = measure(args.url)
    if args.cmd == "baseline":
        store = load_baseline()
        save_baseline(store, key, current)
        print_entry(f"BASELINE SAVED [{key}]", current)
        sys.stdout.write(f"  -> {os.path.relpath(BASELINE_FILE, VAULT_ROOT)}\n")
        return EXIT_OK

    store = load_baseline()
    if key not in store:
        fail_usage(f"no baseline slot [{key}] — run 'baseline' first")
    baseline = store[key]
    print_entry("BASELINE", baseline)
    print_entry("CURRENT", current)
    regressions = compare_entries(baseline, current)
    if regressions:
        for item in regressions:
            sys.stdout.write(f"🔴 REGRESSION: {item}\n")
        return EXIT_REGRESSION
    sys.stdout.write("🟢 no regression vs baseline\n")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
