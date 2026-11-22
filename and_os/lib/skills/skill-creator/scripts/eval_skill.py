#!/usr/bin/env python3
"""
eval_skill.py -- Routing-eval harness for skill descriptions (skill-creator v1.2).

Measures whether a SKILL.md description actually routes: a per-skill
benchmark (trigger prompts + expected skill + decoys) is scored against a
decisions log produced by a fresh subagent that saw ONLY the candidate
descriptions and the prompts (never the expected answers).

Subcommands:
  score  --benchmark <b.json>... --decisions <d.json> [--json]
         pooled precision/recall/F1 per skill, decoy-capture breakdown.
  ab     --benchmark <b.json> --decisions-a <a.json> --decisions-b <b2.json>
         description gate: delta = accuracy_A - accuracy_B; PASS only when
         delta <= 0 (a candidate description must not regress routing).
  split  --benchmark <b.json> --out-dir <dir> [--ratio 0.6] [--seed 42]
         deterministic 60/40 split into optimize/holdout benchmark files.

Benchmark schema:
  {"skill": "kebab-name", "version": "x.y.z", "created": "YYYY-MM-DD",
   "prompts": [{"id": "uniq", "prompt": "user prompt text",
                "expected": "kebab-name", "decoys": ["rival", ...]}]}

Decisions log schema:
  {"benchmark": "<path-or-sha>", "model": "<who routed>", "date": "...",
   "decisions": [{"id": "uniq", "chosen": "skill-name"}, ...]}

Validation codes:
  B001 skill name missing / not kebab     B002 prompts empty
  B003 bad/duplicate ids, bad decoys      B004 expected != benchmark skill
  D001 bad log shape / bad chosen         D002 duplicate decision ids
  D003 unknown decision id                D004 benchmark id missing

Exit codes: 0 scored / gate PASS, 1 gate FAIL, 2 validation/usage error.
Stdlib only.
"""

import argparse
import json
import os
import random
import re
import sys
from typing import Dict, List, Tuple

EXIT_OK = 0
EXIT_GATE_FAIL = 1
EXIT_INVALID = 2
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_json(path: str) -> object:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_benchmark(bench: object) -> List[str]:
    errors: List[str] = []
    if not isinstance(bench, dict):
        return ["B001: benchmark must be a JSON object"]
    skill = bench.get("skill")
    if not isinstance(skill, str) or not SLUG_RE.match(skill):
        errors.append("B001: 'skill' must be a kebab-case name")
    prompts = bench.get("prompts")
    if not isinstance(prompts, list) or not prompts:
        errors.append("B002: 'prompts' must be a non-empty list")
        return errors
    seen = set()
    for index, prompt in enumerate(prompts):
        if not isinstance(prompt, dict):
            errors.append("B003: prompt %d must be an object" % index)
            continue
        pid = prompt.get("id")
        if not isinstance(pid, str) or not pid:
            errors.append("B003: prompt %d: 'id' must be a non-empty string" % index)
            pid = ""
        elif pid in seen:
            errors.append("B003: duplicate prompt id %r" % pid)
        seen.add(pid)
        if not isinstance(prompt.get("prompt"), str) or not prompt["prompt"].strip():
            errors.append("B003: prompt %r: 'prompt' must be non-empty" % pid)
        expected = prompt.get("expected")
        if not isinstance(expected, str) or not expected:
            errors.append("B003: prompt %r: 'expected' must be non-empty" % pid)
        elif isinstance(skill, str) and expected != skill:
            errors.append(
                "B004: prompt %r: 'expected' must equal the benchmark skill %r" % (pid, skill))
        decoys = prompt.get("decoys", [])
        if not isinstance(decoys, list):
            errors.append("B003: prompt %r: 'decoys' must be a list" % pid)
        elif isinstance(expected, str) and expected in decoys:
            errors.append("B003: prompt %r: a decoy must not be the expected skill" % pid)
    return errors


def validate_decisions(bench: dict, log: object) -> List[str]:
    errors: List[str] = []
    if not isinstance(log, dict) or not isinstance(log.get("decisions"), list):
        return ["D001: decisions log must be an object with a 'decisions' list"]
    bench_ids = {p["id"] for p in bench["prompts"]}
    seen = set()
    for entry in log["decisions"]:
        did = entry.get("id") if isinstance(entry, dict) else None
        if not isinstance(did, str) or not did:
            errors.append("D002: decision id must be a non-empty string")
            continue
        if did in seen:
            errors.append("D002: duplicate decision id %r" % did)
        seen.add(did)
        if did not in bench_ids:
            errors.append("D003: unknown decision id %r (not in benchmark)" % did)
        if not isinstance(entry.get("chosen"), str) or not entry["chosen"]:
            errors.append("D001: decision %r: 'chosen' must be a non-empty string" % did)
    for missing in sorted(bench_ids - seen):
        errors.append("D004: benchmark id %r missing from decisions" % missing)
    return errors


def score(benchmarks: List[dict], logs: List[dict]) -> Dict[str, object]:
    chosen_by_id: Dict[str, str] = {}
    for log in logs:
        for entry in log["decisions"]:
            chosen_by_id[entry["id"]] = entry["chosen"]
    tp: Dict[str, int] = {}
    fp: Dict[str, int] = {}
    fn: Dict[str, int] = {}
    total = 0
    correct = 0
    misses: List[Dict[str, str]] = []
    decoy_captures: Dict[str, int] = {}
    for bench in benchmarks:
        for prompt in bench["prompts"]:
            total += 1
            expected = prompt["expected"]
            chosen = chosen_by_id[prompt["id"]]
            for table in (tp, fp, fn):
                table.setdefault(expected, 0)
                table.setdefault(chosen, 0)
            if chosen == expected:
                tp[expected] += 1
                correct += 1
            else:
                fp[chosen] += 1
                fn[expected] += 1
                decoy_captures[chosen] = decoy_captures.get(chosen, 0) + 1
                misses.append({"id": prompt["id"], "chosen": chosen, "expected": expected})
    per_skill: Dict[str, Dict[str, float]] = {}
    for skill in sorted(set(tp) | set(fp) | set(fn)):
        t, f, m = tp.get(skill, 0), fp.get(skill, 0), fn.get(skill, 0)
        precision = t / (t + f) if (t + f) else 1.0
        recall = t / (t + m) if (t + m) else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        per_skill[skill] = {"tp": t, "fp": f, "fn": m,
                            "precision": precision, "recall": recall, "f1": f1}
    return {"n": total, "correct": correct,
            "accuracy": correct / total if total else 0.0,
            "per_skill": per_skill, "decoy_captures": decoy_captures, "misses": misses}


def ab_gate(bench: dict, log_a: dict, log_b: dict) -> Dict[str, object]:
    metrics_a = score([bench], [log_a])
    metrics_b = score([bench], [log_b])
    delta = metrics_a["accuracy"] - metrics_b["accuracy"]
    passed = delta <= 1e-12
    return {"n": metrics_a["n"],
            "accuracy_a": metrics_a["accuracy"],
            "accuracy_b": metrics_b["accuracy"],
            "delta": delta, "pass": passed,
            "exit_code": EXIT_OK if passed else EXIT_GATE_FAIL}


def split_benchmark(bench: dict, ratio: float = 0.6, seed: int = 42) -> Tuple[dict, dict]:
    ids = sorted(p["id"] for p in bench["prompts"])
    shuffled = list(ids)
    random.Random(seed).shuffle(shuffled)
    cut = int(len(shuffled) * ratio)
    ids_a = set(shuffled[:cut])
    ids_b = set(shuffled[cut:])

    def subset(id_set: set) -> dict:
        out = {key: value for key, value in bench.items() if key != "prompts"}
        out["prompts"] = [p for p in bench["prompts"] if p["id"] in id_set]
        return out

    return subset(ids_a), subset(ids_b)


def _load(path: str, what: str) -> object:
    try:
        return load_json(path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
        sys.stderr.write("eval_skill: %s unreadable or invalid JSON: %s\n" % (what, err))
        sys.exit(EXIT_INVALID)


def _fail(errors: List[str]) -> None:
    for err in errors:
        sys.stderr.write("eval_skill: %s\n" % err)
    sys.exit(EXIT_INVALID)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="eval_skill.py",
        description=("Routing-eval harness for skill descriptions: "
                     "benchmark -> decisions -> precision/recall, A/B gate, 60/40 split."))
    sub = parser.add_subparsers(dest="command")

    p_score = sub.add_parser("score", help="score benchmarks against a decisions log")
    p_score.add_argument("--benchmark", action="append", required=True,
                         help="benchmark JSON (repeatable for a pooled run)")
    p_score.add_argument("--decisions", required=True, help="decisions log JSON")
    p_score.add_argument("--json", action="store_true", dest="as_json")

    p_ab = sub.add_parser("ab", help="A/B description gate (delta = acc_a - acc_b, PASS when <= 0)")
    p_ab.add_argument("--benchmark", required=True)
    p_ab.add_argument("--decisions-a", required=True, help="decisions under description A (current)")
    p_ab.add_argument("--decisions-b", required=True, help="decisions under description B (candidate)")
    p_ab.add_argument("--json", action="store_true", dest="as_json")

    p_split = sub.add_parser("split", help="deterministic optimize/holdout split of a benchmark")
    p_split.add_argument("--benchmark", required=True)
    p_split.add_argument("--out-dir", required=True)
    p_split.add_argument("--ratio", type=float, default=0.6)
    p_split.add_argument("--seed", type=int, default=42)

    args = parser.parse_args(argv)
    if not args.command:
        parser.error("choose score, ab, or split")

    if args.command == "score":
        benchmarks = []
        for path in args.benchmark:
            bench = _load(path, "benchmark")
            errors = validate_benchmark(bench)
            if errors:
                _fail(errors)
            benchmarks.append(bench)
        log = _load(args.decisions, "decisions log")
        union = {"prompts": [{"id": p["id"]}
                             for b in benchmarks for p in b["prompts"]]}
        errors = validate_decisions(union, log)
        if errors:
            _fail(errors)
        payload = score(benchmarks, [log])
        if args.as_json:
            sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write("n=%d correct=%d accuracy=%.3f\n" % (
                payload["n"], payload["correct"], payload["accuracy"]))
            for skill, s in payload["per_skill"].items():
                sys.stdout.write("  %s: P=%.3f R=%.3f F1=%.3f (tp=%d fp=%d fn=%d)\n" % (
                    skill, s["precision"], s["recall"], s["f1"], s["tp"], s["fp"], s["fn"]))
            for miss in payload["misses"]:
                sys.stdout.write("  MISS %s: expected %s, chose %s\n" % (
                    miss["id"], miss["expected"], miss["chosen"]))
        return EXIT_OK

    if args.command == "ab":
        bench = _load(args.benchmark, "benchmark")
        errors = validate_benchmark(bench)
        if errors:
            _fail(errors)
        log_a = _load(args.decisions_a, "decisions-a")
        log_b = _load(args.decisions_b, "decisions-b")
        for label, log in (("a", log_a), ("b", log_b)):
            errors = validate_decisions(bench, log)
            if errors:
                sys.stderr.write("eval_skill: decisions-%s invalid:\n" % label)
                _fail(errors)
        result = ab_gate(bench, log_a, log_b)
        if args.as_json:
            sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write("acc_a=%.3f acc_b=%.3f delta=%+.3f -> %s\n" % (
                result["accuracy_a"], result["accuracy_b"], result["delta"],
                "PASS" if result["pass"] else "FAIL (regression)"))
        return int(result["exit_code"])

    bench = _load(args.benchmark, "benchmark")
    errors = validate_benchmark(bench)
    if errors:
        _fail(errors)
    part_a, part_b = split_benchmark(bench, ratio=args.ratio, seed=args.seed)
    os.makedirs(args.out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.benchmark))[0]
    path_a = os.path.join(args.out_dir, stem + ".optimize.json")
    path_b = os.path.join(args.out_dir, stem + ".holdout.json")
    for path, part in ((path_a, part_a), (path_b, part_b)):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(part, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    sys.stdout.write("optimize: %s (%d prompts)\nholdout: %s (%d prompts)\n" % (
        path_a, len(part_a["prompts"]), path_b, len(part_b["prompts"])))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
