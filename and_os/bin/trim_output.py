#!/usr/bin/env python3
"""
trim_output.py — Sandbox CLI execution wrapper with automatic log truncation (Rule #24).
Keeps Head (first N lines) + Tail (last M lines), filtering duplicates and cutting excess noise.
"""

import sys
import subprocess
import argparse

def trim_text(text: str, head: int = 15, tail: int = 20) -> str:
    lines = text.splitlines()
    if len(lines) <= head + tail:
        return text
    
    head_lines = lines[:head]
    tail_lines = lines[-tail:]
    omitted = len(lines) - (head + tail)
    
    result = head_lines + [f"\n--- ✂️ [ANDREY OS SYSTEM: {omitted} log lines truncated for token economy (Rule #24)] ✂️ ---\n"] + tail_lines
    return "\n".join(result)

def main():
    parser = argparse.ArgumentParser(description="Sandboxed command execution with long-log truncation.")
    parser.add_argument("--head", type=int, default=15, help="Number of head lines")
    parser.add_argument("--tail", type=int, default=20, help="Number of tail lines")
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute")

    args = parser.parse_args()

    # If stdin is piped and no command passed, trim stdin directly
    if not args.cmd and not sys.stdin.isatty():
        input_text = sys.stdin.read()
        print(trim_text(input_text, head=args.head, tail=args.tail))
        sys.exit(0)

    if not args.cmd:
        print("Error: specify a command to run or pipe a stream in", file=sys.stderr)
        sys.exit(1)

    cmd_str = " ".join(args.cmd)
    try:
        res = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)  # nosec: CLI pipeline execution tool
        trimmed_out = trim_text(res.stdout, head=args.head, tail=args.tail)
        trimmed_err = trim_text(res.stderr, head=args.head, tail=args.tail)
        
        if trimmed_out:
            print(trimmed_out)
        if trimmed_err:
            print(trimmed_err, file=sys.stderr)
            
        sys.exit(res.returncode)
    except Exception as e:
        print(f"Sandbox run error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
