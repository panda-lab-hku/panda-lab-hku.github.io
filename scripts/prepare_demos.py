"""Create browser-friendly homepage videos and posters without changing originals.

Run: python scripts/prepare_demos.py --ffmpeg /path/to/ffmpeg
If --ffmpeg is omitted, ffmpeg must be installed on PATH.
"""

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "demos"
DEMOS = ("aloha", "gausmi", "lasp", "rapid", "softmimic")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(ffmpeg, arguments):
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", *arguments],
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error("Provide --ffmpeg or install ffmpeg on PATH.")
    sources = [ASSETS / (name + ".mp4") for name in DEMOS]
    for source in sources:
        if not source.is_file():
            raise FileNotFoundError(source)
    original_hashes = {source: digest(source) for source in sources}
    OUTPUT.mkdir(exist_ok=True)
    for source in sources:
        target = OUTPUT / source.name
        run(args.ffmpeg, [
            "-i", str(source),
            "-map", "0:v:0", "-map", "0:a?",
            "-vf", "scale=w='min(1280,iw)':h='min(720,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-pix_fmt", "yuv420p", "-threads", "4",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", "-map_metadata", "-1",
            str(target),
        ])
        run(args.ffmpeg, [
            "-ss", "2", "-i", str(target),
            "-vf", "scale=w='min(640,iw)':h='min(360,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2",
            "-frames:v", "1", "-q:v", "3", "-update", "1",
            str(OUTPUT / (source.stem + ".jpg")),
        ])
        print(source.name, "->", round(target.stat().st_size / 1024), "KB", flush=True)
    for source, expected in original_hashes.items():
        if digest(source) != expected:
            raise ValueError("Original demo changed: " + str(source))
    print("Prepared five videos and posters. Original files are unchanged.", flush=True)


if __name__ == "__main__":
    main()
