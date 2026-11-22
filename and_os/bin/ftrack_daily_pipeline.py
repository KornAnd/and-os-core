#!/usr/bin/env python3
"""ftrack_daily_pipeline.py — the daily Ftrack read-only loop (22.11).

22.11 (Phase 3 closeout, Andrei decision, option A): the 07:30
ftrack_cache cron no longer only rebuilds the gantt cache from the
latest slice — it runs the full daily loop so the production gantt
contours and the creative metrics never serve week-old data:

  1. kot export    and_os/bin/ftrack_sync.py --project kot  --export
  2. mars export   and_os/bin/ftrack_sync.py --project mars --export
  3. gantt cache   and_os/opt/apps/tracker_hub/modules/ftrack_gantt.py
                   --project all --module full

Invariants:
  - Ftrack access stays strictly READ-ONLY (Query only, existing
    Keychain key; no create/update/delete) — the Phase 3 lab invariant.
  - Each step runs in its own subprocess: one failure never corrupts
    the next step; the supervisor captures the combined output in the
    per-service logs (~/.and_os/logs/ftrack_cache.{out,err}.log).
  - The gantt rebuild runs even when an export fails: the cache then
    stays consistent with the last good slice (graceful staleness, no
    half-updated contours).
  - Exit code: 0 when every step succeeded, 1 otherwise — the
    supervisor retries once (max_retries) on failure; a retry re-runs
    the exports, which are incremental (read-only, idempotent).

Usage:
  python3 ftrack_daily_pipeline.py            # run all steps (cron path)
  python3 ftrack_daily_pipeline.py --dry-run  # print the plan, run nothing
"""
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.

BIN_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.dirname(os.path.dirname(BIN_DIR))
VENV_PY = os.path.join(VAULT_ROOT, "and_os", ".venv", "bin", "python3")

# (label, command) — order matters; labels are the log markers.
STEPS = [
    ("kot_export", [
        VENV_PY, os.path.join(BIN_DIR, "ftrack_sync.py"),
        "--project", "kot", "--export"]),
    ("mars_export", [
        VENV_PY, os.path.join(BIN_DIR, "ftrack_sync.py"),
        "--project", "mars", "--export"]),
    ("gantt_cache", [
        VENV_PY, os.path.join(VAULT_ROOT, "and_os", "opt", "apps",
                              "tracker_hub", "modules", "ftrack_gantt.py"),
        "--project", "all", "--module", "full"]),
]


USAGE = (
    "usage: ftrack_daily_pipeline.py [option]\n"
    "\n"
    "The daily Ftrack read-only loop (the 07:30 ftrack_cache cron):\n"
    "kot export, mars export, gantt cache rebuild.\n"
    "\n"
    "options:\n"
    "  (no option)  run all three steps (the cron path)\n"
    "  --dry-run    print the plan, run nothing\n"
    "  --help, -h   show this help and exit\n"
)


def main(argv):
    if "--help" in argv or "-h" in argv:
        # 22.11 C-01 class: an unhandled token must never fall through to
        # a real run — explicit usage path, exit 0.
        print(USAGE)
        return 0
    known = {"--dry-run", "--help", "-h"}
    unknown = [a for a in argv if a not in known]
    if unknown:
        print("unknown argument(s): %s\n%s" % (" ".join(unknown), USAGE))
        return 2
    if "--dry-run" in argv:
        for i, (label, cmd) in enumerate(STEPS, 1):
            print("[pipeline] DRY-RUN step %d/%d %s: %s"
                  % (i, len(STEPS), label, " ".join(cmd)))
        return 0

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")  # Rule #71, children.
    results = {}
    for i, (label, cmd) in enumerate(STEPS, 1):
        print("[pipeline] STEP %d/%d %s: START (%s)"
              % (i, len(STEPS), label, " ".join(cmd)), flush=True)
        t0 = time.monotonic()
        try:
            proc = subprocess.run(cmd, cwd=VAULT_ROOT, env=env)
            rc = proc.returncode
        except OSError as err:
            # Surfaced, not silent: the step is marked failed below and the
            # pipeline exit code carries it to the supervisor.
            print("[pipeline] STEP %s: FAILED to spawn: %s" % (label, err),
                  flush=True)
            results[label] = "spawn_error"
            continue
        dur = time.monotonic() - t0
        results[label] = "ok" if rc == 0 else "rc=%d" % rc
        print("[pipeline] STEP %s: %s (%.1fs, %s)"
              % (label, "OK" if rc == 0 else "FAILED", dur, results[label]),
              flush=True)
    summary = ", ".join("%s=%s" % (k, v) for k, v in results.items())
    ok = all(v == "ok" for v in results.values())
    print("[pipeline] RESULT: %s (%s)" % ("OK" if ok else "FAILED", summary),
          flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
