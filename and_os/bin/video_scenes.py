#!/usr/bin/env python3
"""
video_scenes.py — The selective media analysis of the video via the FFmpeg (Scene Detection).
A part of the standard Think in Code (Rule #16).

The FFmpeg filter `select='gt(scene,0.02)'` extracts only the frames/screens changes,
compressing the 20-minute video into the 20-30 pictures instead of the thousands of the useless duplicates.

Usage:
  python3 video_scenes.py --detect input.mp4
  python3 video_scenes.py --extract input.mp4 --out ./frames/ --threshold 0.05
  python3 video_scenes.py --detect input.mp4 --json > scenes.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def check_ffmpeg() -> bool:
    """Checks the availability of the ffmpeg and the ffprobe."""
    for tool in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([tool, "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"[ERROR] the {tool} was not found. Install: brew install ffmpeg", file=sys.stderr)
            return False
    return True


def get_video_duration(video_path: str) -> Optional[float]:
    """Returns the duration of the video in the seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    return float(data.get("format", {}).get("duration", 0))


def detect_scenes(video_path: str, threshold: float = 0.02) -> List[dict]:
    """
    Detects the scenes in the video via the FFmpeg scene filter.
    Returns the list of the dict with the fields: frame, pts_time, score.
    
    threshold: the sensitivity (0.02 = the standard, the less = the more scenes).
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_frames",
        "-select_streams", "v:0",
        "-read_intervals", "%+#9999",
        "-vf", f"select=\'gt(scene,{threshold})\'",
        video_path
    ]
    
    # The alternative approach via the ffmpeg with the lavfi
    cmd2 = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"select=gt(scene\\,{threshold}),showinfo",
        "-vsync", "vfr",
        "-f", "null",
        "-"
    ]
    
    result = subprocess.run(cmd2, capture_output=True, text=True)
    
    scenes = []
    # Parsing the lines of the showinfo from the stderr
    pattern = re.compile(r"n:\s*(\d+).*pts_time:(\d+\.?\d*).*")
    for line in result.stderr.splitlines():
        if "pts_time" in line and "Parsed_showinfo" in line:
            m = re.search(r"n:\s*(\d+).*pts_time:(\d+(?:\.\d+)?)", line)
            if m:
                scenes.append({
                    "frame": int(m.group(1)),
                    "pts_time": float(m.group(2)),
                    "score": threshold  # For the showinfo the score is not available directly
                })
    
    return scenes


def extract_scene_frames(video_path: str, output_dir: str, 
                         threshold: float = 0.02, quality: int = 2) -> int:
    """
    Extracts the frames of the scenes changes into the output_dir.
    
    threshold: the sensitivity (0.02 is recommended for the screen recordings).
    quality: 1-31, where 2 — the high quality of the JPEG.
    
    Returns the count of the extracted frames.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_pattern = os.path.join(output_dir, "scene_%04d.jpg")
    
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"select=gt(scene\\,{threshold})",
        "-vsync", "vfr",
        "-q:v", str(quality),
        output_pattern,
        "-y"
    ]
    
    print(f"⚙️ The extraction of the scenes frames (the threshold={threshold})...")
    print(f"   The command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[ERROR] the FFmpeg was completed with the error:", file=sys.stderr)
        print(result.stderr[-1000:], file=sys.stderr)
        return 0
    
    # Counting the extracted files
    extracted = len(list(Path(output_dir).glob("scene_*.jpg")))
    return extracted


def main():
    parser = argparse.ArgumentParser(
        description="The selective media analysis: the detection of the scenes via the FFmpeg (Rule #16)"
    )
    parser.add_argument("video", help="The path to the input video file")
    
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--detect", action="store_true",
                            help="Only detect the scenes changes (without the extraction of the frames)")
    mode_group.add_argument("--extract", action="store_true",
                            help="Extract the frames of the scenes changes into the folder")
    
    parser.add_argument("--out", "-o", default="./scene_frames",
                        help="The folder for the saving of the frames (by default: ./scene_frames)")
    parser.add_argument("--threshold", "-t", type=float, default=0.02,
                        help="The threshold of the sensitivity of the detector (0.02 by default). "
                             "The less = the more scenes. For the screen recordings: 0.02-0.05")
    parser.add_argument("--quality", "-q", type=int, default=2,
                        help="The quality of the JPEG (1=better, 31=worse, by default: 2)")
    parser.add_argument("--json", action="store_true",
                        help="Print the results in the JSON format")
    
    args = parser.parse_args()
    
    if not check_ffmpeg():
        sys.exit(1)
    
    if not os.path.exists(args.video):
        print(f"[ERROR] the video file was not found: {args.video}", file=sys.stderr)
        sys.exit(1)
    
    duration = get_video_duration(args.video)
    video_name = os.path.basename(args.video)
    
    if not args.json:
        print(f"🎬 The file: {video_name}")
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            print(f"   The duration: {minutes}m {seconds}s ({duration:.1f}s)")
        print(f"   The threshold of the detector: {args.threshold}")
    
    if args.detect:
        scenes = detect_scenes(args.video, threshold=args.threshold)
        
        if args.json:
            result = {
                "video": args.video,
                "duration": duration,
                "threshold": args.threshold,
                "scene_count": len(scenes),
                "scenes": scenes
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n✅ The scenes were detected: {len(scenes)}")
            for i, scene in enumerate(scenes, 1):
                t = scene["pts_time"]
                minutes = int(t // 60)
                seconds = t % 60
                print(f"   [{i:3d}] t={minutes}:{seconds:05.2f}s  (the frame #{scene['frame']})")
    
    elif args.extract:
        count = extract_scene_frames(
            args.video, args.out,
            threshold=args.threshold,
            quality=args.quality
        )
        
        if args.json:
            result = {
                "video": args.video,
                "output_dir": args.out,
                "threshold": args.threshold,
                "frames_extracted": count
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if count > 0:
                print(f"\n✅ The frames were extracted: {count}")
                print(f"   The saving was completed in: {os.path.abspath(args.out)}")
                if duration:
                    ratio = duration / count if count > 0 else 0
                    print(f"   The compression: 1 frame / {ratio:.1f}s of the video")
            else:
                print("\n[WARNING] the frames were not extracted. Check the input file and the threshold.", file=sys.stderr)


if __name__ == "__main__":
    main()
