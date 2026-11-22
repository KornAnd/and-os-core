"""
bin_smoke_probe.py — Ring 2.75: Bin Entrypoint Smoke Probe (T2, 2026-11-17).

The M4 incident (deep audit 16.11, still dead on 17.11) proved the gap:
an entrypoint in and_os/bin/ can die with a runtime NameError for a week
while every static gate stays green — the failure only surfaces when a
skill chain actually invokes the script (mirror_collector / datetime).

This probe executes the bin layer hermetically:
  Tier B (entrypoints): every top-level and_os/bin/*.py carrying an
      `if __name__ == "__main__"` guard is run as
      `venv python -B <script> --help` in a subprocess (15s timeout,
      8 workers). Catches import-time crashes, broken argparse setup and
      top-level side-effect blowups.
  Tier C (functional registry): a policy-declared list of module calls
      (probe_policy.json -> probes.bin_smoke.functional_smokes) executed
      against a throwaway temp vault root — the deep canary class of the
      mirror_collector incident (a dead function, not a dead import).

Zero side effects, now ENFORCED (22.11, external audit C-01): the
--help contract is static (and_os/tests/test_smoke_contract.py: every
entrypoint is argparse / explicit --help handling / registered in
help_incompatible) and behavioral (mutation_canary: the smoke must not
mutate the vault outside the sanctioned volatile zones — an rc=0 writer
is exactly what exit-code tiers cannot see). Tier C runs against a temp
dir OUTSIDE the Vault; -B plus the venv .pth guard (C13 F4) keep
bytecode out of the tree. A dead entrypoint is a DEFECT (issues_count),
not an advisory — that is the point of the probe.
"""

import ast
import json
import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

from and_os.lib.health_grid import BaseProbeResult
from and_os.lib.health_grid import mutation_canary

SUBPROCESS_TIMEOUT_SEC = 15
WORKERS = 8


def _has_main_guard(source: str) -> bool:
    """True when the module carries an `if __name__ == "__main__":` guard."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare):
            continue
        if not (isinstance(test.left, ast.Name) and test.left.id == "__name__"):
            continue
        if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
            continue
        if len(test.comparators) != 1:
            continue
        comp = test.comparators[0]
        if isinstance(comp, ast.Constant) and comp.value == "__main__":
            return True
    return False


def _first_error_line(err: str) -> str:
    for line in (err or "").splitlines():
        line = line.strip()
        if line:
            return line[:200]
    return ""


def _build_smoke_code() -> str:
    # argv: [bin_dir, module, dotted.call, *call_args]
    return (
        "import sys\n"
        "import importlib\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "mod = importlib.import_module(sys.argv[2])\n"
        "fn = mod\n"
        "for part in sys.argv[3].split('.'):\n"
        "    fn = getattr(fn, part)\n"
        "fn(*sys.argv[4:])\n"
        "print('ok')\n"
    )


class BinSmokeProbe:
    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 2.75: Bin Entrypoint Smoke Probe", ring=2)
        bin_dir = os.path.join(vault_root, "and_os", "bin")
        venv_python = os.path.join(vault_root, "and_os", ".venv", "bin", "python3")
        failures = []
        # Initialized before the entrypoint scan: the Tier B skip map is
        # policy-driven, and the policy block runs after the scan starts.
        help_incompatible = {}

        scripts = []
        if os.path.isdir(bin_dir):
            scripts = sorted(
                f for f in os.listdir(bin_dir)
                if f.endswith(".py") and os.path.isfile(os.path.join(bin_dir, f))
            )

        smoke_specs = []
        policy_path = os.path.join(vault_root, "and_os", "etc", "probe_policy.json")
        if os.path.isfile(policy_path):
            try:
                with open(policy_path, "r", encoding="utf-8") as fh:
                    policy = json.load(fh)
                raw = (policy.get("probes", {}).get("bin_smoke", {}) or {})
                smoke_specs = raw.get("functional_smokes", []) or []
                help_incompatible = raw.get("help_incompatible", {}) or {}
            except (OSError, ValueError) as e:
                result.warnings.append(f"probe policy unreadable — Tier C skipped: {e}")

        entrypoints = []
        for fname in scripts:
            path = os.path.join(bin_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    src = fh.read()
            except OSError as e:
                failures.append({"script": fname, "tier": "read", "rc": None, "stderr": str(e)})
                continue
            if _has_main_guard(src):
                if fname in help_incompatible:
                    continue
                entrypoints.append(fname)

        if not os.path.isfile(venv_python):
            # The toolchain probe owns venv liveness; degrade visibly here.
            result.warnings.append(
                "venv interpreter absent — smoke tiers skipped (toolchain owns venv liveness)")
            result.details = {
                "bin_scripts": len(scripts),
                "entrypoints": len(entrypoints),
                "functional_smokes": len(smoke_specs),
                "failed": failures,
                "skipped": "no venv interpreter",
            }
            return result

        def smoke_help(fname: str) -> tuple:
            try:
                r = subprocess.run(
                    [venv_python, "-B", os.path.join(bin_dir, fname), "--help"],
                    capture_output=True, text=True,
                    timeout=SUBPROCESS_TIMEOUT_SEC, cwd=vault_root)
                return fname, r.returncode, _first_error_line(r.stderr)
            except subprocess.TimeoutExpired:
                return fname, 124, f"timeout after {SUBPROCESS_TIMEOUT_SEC}s"
            except OSError as e:
                return fname, 125, str(e)

        # Mutation canary (22.11, C-01): snapshot before any smoke tier
        # executes; a successful side effect (rc=0 writer) must surface
        # as a failure even though every exit code was green.
        before_snapshot = mutation_canary.snapshot(vault_root)

        if entrypoints:
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                for fname, rc, err in ex.map(smoke_help, entrypoints):
                    if rc != 0:
                        failures.append({"script": fname, "tier": "help", "rc": rc, "stderr": err})

        tmp_root = tempfile.mkdtemp(prefix="bin_smoke_")
        try:
            for spec in smoke_specs:
                module = spec.get("module", "")
                call = spec.get("call", "")
                if not module or not call:
                    failures.append({"script": spec.get("script", "?"), "tier": "config",
                                     "rc": None, "stderr": "functional_smokes entry needs module+call"})
                    continue
                args = [str(a).replace("{tmp}", tmp_root) for a in spec.get("args", [])]
                cmd = [venv_python, "-B", "-c", _build_smoke_code(), bin_dir, module, call] + args
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True,
                                       timeout=SUBPROCESS_TIMEOUT_SEC, cwd=vault_root)
                    ok = r.returncode == 0
                    rc = r.returncode
                    err = _first_error_line(r.stderr)
                except subprocess.TimeoutExpired:
                    ok, rc, err = False, 124, f"timeout after {SUBPROCESS_TIMEOUT_SEC}s"
                except OSError as e:
                    ok, rc, err = False, 125, str(e)
                if not ok:
                    failures.append({"script": spec.get("script", module + ".py"),
                                     "tier": "functional", "rc": rc, "stderr": err})
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)

        # Canary verdict: any vault mutation outside the sanctioned
        # volatile zones is a defect (tier="canary"), whatever the rcs said.
        mutation_report = mutation_canary.compare(
            before_snapshot, mutation_canary.snapshot(vault_root))
        if not mutation_canary.is_clean(mutation_report):
            failures.append({
                "script": "<fs-mutation>", "tier": "canary", "rc": None,
                "stderr": "vault mutated by smoke run: " + json.dumps(mutation_report)[:400],
            })

        for f in failures:
            result.errors.append(
                f"dead bin entrypoint {f['script']} (tier={f['tier']}, rc={f['rc']}): {f['stderr']}")
        result.issues_count = len(failures)
        result.passed = not failures
        result.details = {
            "bin_scripts": len(scripts),
            "entrypoints": len(entrypoints),
            "help_skipped": {f: help_incompatible.get(f, "no reason recorded")
                             for f in sorted(set(scripts) & set(help_incompatible))},
            "functional_smokes": len(smoke_specs),
            "failed": failures,
        }
        return result
