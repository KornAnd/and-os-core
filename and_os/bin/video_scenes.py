#!/usr/bin/env python3
"""
video_scenes.py — Селективный медиа-анализ видео через FFmpeg (Scene Detection).
Часть стандарта Think in Code (Правило №16).

Фильтр FFmpeg `select='gt(scene,0.02)'` извлекает только смены кадров/экранов,
сжимая 20-минутное видео в 20-30 картинок вместо тысяч бесполезных дубликатов.

Использование:
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
    """Проверяет доступность ffmpeg и ffprobe."""
    for tool in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([tool, "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"[ОШИБКА] {tool} не найден. Установи: brew install ffmpeg", file=sys.stderr)
            return False
    return True


def get_video_duration(video_path: str) -> Optional[float]:
    """Возвращает длительность видео в секундах."""
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
    Детектирует сцены в видео через FFmpeg scene filter.
    Возвращает список dict с полями: frame, pts_time, score.
    
    threshold: чувствительность (0.02 = стандарт, меньше = больше сцен).
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
    
    # Альтернативный подход через ffmpeg с lavfi
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
    # Парсим строки showinfo из stderr
    pattern = re.compile(r"n:\s*(\d+).*pts_time:(\d+\.?\d*).*")
    for line in result.stderr.splitlines():
        if "pts_time" in line and "Parsed_showinfo" in line:
            m = re.search(r"n:\s*(\d+).*pts_time:(\d+(?:\.\d+)?)", line)
            if m:
                scenes.append({
                    "frame": int(m.group(1)),
                    "pts_time": float(m.group(2)),
                    "score": threshold  # Для showinfo score не доступен напрямую
                })
    
    return scenes


def extract_scene_frames(video_path: str, output_dir: str, 
                         threshold: float = 0.02, quality: int = 2) -> int:
    """
    Извлекает кадры смены сцен в output_dir.
    
    threshold: чувствительность (0.02 рекомендуется для экранных записей).
    quality: 1-31, где 2 — высокое качество JPEG.
    
    Возвращает количество извлечённых кадров.
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
    
    print(f"⚙️ Извлечение кадров сцен (порог={threshold})...")
    print(f"   Команда: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[ОШИБКА] FFmpeg завершился с ошибкой:", file=sys.stderr)
        print(result.stderr[-1000:], file=sys.stderr)
        return 0
    
    # Считаем извлечённые файлы
    extracted = len(list(Path(output_dir).glob("scene_*.jpg")))
    return extracted


def main():
    parser = argparse.ArgumentParser(
        description="Селективный медиа-анализ: детекция сцен через FFmpeg (Правило №16)"
    )
    parser.add_argument("video", help="Путь к входному видеофайлу")
    
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--detect", action="store_true",
                            help="Только обнаружить смены сцен (без извлечения кадров)")
    mode_group.add_argument("--extract", action="store_true",
                            help="Извлечь кадры смен сцен в папку")
    
    parser.add_argument("--out", "-o", default="./scene_frames",
                        help="Папка для сохранения кадров (по умолчанию: ./scene_frames)")
    parser.add_argument("--threshold", "-t", type=float, default=0.02,
                        help="Порог чувствительности детектора (0.02 по умолчанию). "
                             "Меньше = больше сцен. Для экранных записей: 0.02-0.05")
    parser.add_argument("--quality", "-q", type=int, default=2,
                        help="Качество JPEG (1=лучше, 31=хуже, по умолчанию: 2)")
    parser.add_argument("--json", action="store_true",
                        help="Вывести результаты в формате JSON")
    
    args = parser.parse_args()
    
    if not check_ffmpeg():
        sys.exit(1)
    
    if not os.path.exists(args.video):
        print(f"[ОШИБКА] Видеофайл не найден: {args.video}", file=sys.stderr)
        sys.exit(1)
    
    duration = get_video_duration(args.video)
    video_name = os.path.basename(args.video)
    
    if not args.json:
        print(f"🎬 Файл: {video_name}")
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            print(f"   Длительность: {minutes}м {seconds}с ({duration:.1f}с)")
        print(f"   Порог детектора: {args.threshold}")
    
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
            print(f"\n✅ Обнаружено сцен: {len(scenes)}")
            for i, scene in enumerate(scenes, 1):
                t = scene["pts_time"]
                minutes = int(t // 60)
                seconds = t % 60
                print(f"   [{i:3d}] t={minutes}:{seconds:05.2f}с  (кадр #{scene['frame']})")
    
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
                print(f"\n✅ Извлечено кадров: {count}")
                print(f"   Сохранено в: {os.path.abspath(args.out)}")
                if duration:
                    ratio = duration / count if count > 0 else 0
                    print(f"   Сжатие: 1 кадр / {ratio:.1f}с видео")
            else:
                print("\n[ПРЕДУПРЕЖДЕНИЕ] Кадры не извлечены. Проверь входной файл и порог.", file=sys.stderr)


if __name__ == "__main__":
    main()
