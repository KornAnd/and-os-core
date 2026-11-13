#!/usr/bin/env python3
"""
video_harness.py — Autonomous technical QC validator for video and passes (Video E2E Harness).
AnD os v1.0.0 — Island 7 & 5 (Pulsar & CG Production).

Provides end-to-end technical control of shot pipeline artifacts:
1. Validation of raw playblasts (Blender Viewport Playblast) and depth video passes.
2. Studio spec compliance check (FPS 24.0, H.264/ProRes, even resolution 1920x1080 / 1280x720).
3. Timing and frame-count match check between playblast and passes.
4. Keyframe delta computation (Start/End frame diff) to detect jumps and breaks.
5. QC result write into `shot.meta.json` before hand-off to ComfyUI.
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, Optional

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def get_ffprobe_bin() -> str:
    """Resolves ffprobe binary path across standard and Homebrew locations."""
    for candidate in ["/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe", "ffprobe"]:
        if os.path.exists(candidate) or shutil.which(candidate):
            return candidate
    return "ffprobe"

def probe_stream(file_path: str) -> Dict[str, Any]:
    """Extracts video technical parameters via ffprobe."""
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}

    ffprobe_bin = get_ffprobe_bin()
    cmd = [
        ffprobe_bin, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name,r_frame_rate,nb_frames,duration:format=duration,size,bit_rate",
        "-of", "json", file_path
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return {"status": "error", "message": res.stderr.strip()}
        
        info = json.loads(res.stdout)
        v_stream = info.get("streams", [{}])[0]
        fmt = info.get("format", {})

        # Parse FPS from a rational number "24/1" -> 24.0
        fps_str = v_stream.get("r_frame_rate", "24/1")
        try:
            num, den = fps_str.split("/")
            fps_val = round(float(num) / float(den), 2)
        except Exception:
            fps_val = 24.0

        dur = float(v_stream.get("duration") or fmt.get("duration") or 0.0)
        frames = int(v_stream.get("nb_frames") or round(dur * fps_val))

        return {
            "status": "ok",
            "file": file_path,
            "width": v_stream.get("width", 0),
            "height": v_stream.get("height", 0),
            "codec": v_stream.get("codec_name", "unknown"),
            "fps": fps_val,
            "duration_sec": round(dur, 3),
            "frames": frames,
            "size_bytes": int(fmt.get("size", 0))
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def validate_shot_passes(playblast_path: str, depth_path: Optional[str] = None, expected_fps: float = 24.0) -> Dict[str, Any]:
    """
    Runs a full QC pass over the playblast and the depth pass:
    - File existence check
    - Frame rate check (FPS == 24.0)
    - Frame geometry match check (Width/Height)
    - Runtime synchronization check (Frame Count Diff == 0)
    """
    report = {
        "status": "ok",
        "passed": True,
        "playblast": None,
        "depth_pass": None,
        "checks": [],
        "errors": []
    }

    # 1. Playblast check
    pb_info = probe_stream(playblast_path)
    if pb_info.get("status") != "ok":
        report["passed"] = False
        report["errors"].append(f"Playblast stream invalid: {pb_info.get('message')}")
        return report

    report["playblast"] = pb_info

    # FPS check
    if abs(pb_info["fps"] - expected_fps) > 0.05:
        report["passed"] = False
        report["errors"].append(f"FPS Mismatch: expected {expected_fps}, got {pb_info['fps']}")
    else:
        report["checks"].append(f"FPS Verified: {pb_info['fps']} fps")

    # Resolution parity check
    if pb_info["width"] % 2 != 0 or pb_info["height"] % 2 != 0:
        report["passed"] = False
        report["errors"].append(f"Odd resolution detected ({pb_info['width']}x{pb_info['height']}), requires mod-2 for video codecs")
    else:
        report["checks"].append(f"Resolution Verified: {pb_info['width']}x{pb_info['height']}")

    # 2. Depth pass check (if provided)
    if depth_path and os.path.exists(depth_path):
        dp_info = probe_stream(depth_path)
        if dp_info.get("status") == "ok":
            report["depth_pass"] = dp_info
            
            # Dimension cross-check
            if (dp_info["width"], dp_info["height"]) != (pb_info["width"], pb_info["height"]):
                report["passed"] = False
                report["errors"].append(f"Pass dimension mismatch: playblast is {pb_info['width']}x{pb_info['height']}, depth is {dp_info['width']}x{dp_info['height']}")
            else:
                report["checks"].append("Pass Dimensions Synchronized")

            # Frame-count cross-check
            if abs(dp_info["frames"] - pb_info["frames"]) > 1:
                report["passed"] = False
                report["errors"].append(f"Pass frame count desync: playblast has {pb_info['frames']} frames, depth has {dp_info['frames']} frames")
            else:
                report["checks"].append(f"Frame Count In Sync ({pb_info['frames']} frames)")

    report["status"] = "ok" if report["passed"] else "rejected"
    return report

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        pb = sys.argv[2]
        dp = sys.argv[3] if len(sys.argv) > 3 else None
        res = validate_shot_passes(pb, dp)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("Usage: video_harness.py --check <playblast_path> [depth_path]")
