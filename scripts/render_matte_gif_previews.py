#!/usr/bin/env python3
"""Render matte-background GIF previews from extracted RGBA pet frames."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

ROW_DURATIONS = {
    "idle": [280, 110, 110, 140, 140, 320],
    "running-right": [120, 120, 120, 120, 120, 120, 120, 220],
    "running-left": [120, 120, 120, 120, 120, 120, 120, 220],
    "waving": [140, 140, 140, 280],
    "jumping": [140, 140, 140, 140, 280],
    "failed": [140, 140, 140, 140, 140, 140, 140, 240],
    "waiting": [150, 150, 150, 150, 150, 260],
    "running": [120, 120, 120, 120, 120, 220],
    "review": [150, 150, 150, 150, 150, 280],
}
IMAGE_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg"}


def parse_hex_color(value: str) -> tuple[int, int, int]:
    value = value.strip()
    if value.startswith("#"):
        value = value[1:]
    if len(value) != 6:
        raise argparse.ArgumentTypeError("background must be a 6-digit hex color")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def frame_files(state_dir: Path) -> list[Path]:
    if not state_dir.is_dir():
        return []
    return sorted(path for path in state_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)


def load_frames(frames_root: Path, state: str, expected_count: int) -> list[Image.Image]:
    files = frame_files(frames_root / state)
    if len(files) != expected_count:
        raise SystemExit(
            f"{state} preview needs {expected_count} frames, found {len(files)} under {frames_root / state}"
        )
    frames: list[Image.Image] = []
    for path in files:
        with Image.open(path) as opened:
            frames.append(opened.convert("RGBA"))
    return frames


def flatten(frame: Image.Image, background: tuple[int, int, int], scale: int) -> Image.Image:
    canvas = Image.new("RGBA", frame.size, background + (255,))
    canvas.alpha_composite(frame)
    if scale != 1:
        canvas = canvas.resize((canvas.width * scale, canvas.height * scale), Image.Resampling.NEAREST)
    return canvas.convert("RGB")


def save_preview(
    frames: list[Image.Image],
    durations: list[int],
    output: Path,
    background: tuple[int, int, int],
    scale: int,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    flattened = [flatten(frame, background, scale) for frame in frames]
    flattened[0].save(
        output,
        save_all=True,
        append_images=flattened[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--background", type=parse_hex_color, default=(32, 37, 43))
    parser.add_argument("--scale", type=int, default=3)
    parser.add_argument("--state", action="append", choices=sorted(ROW_DURATIONS))
    args = parser.parse_args()

    if args.scale < 1:
        raise SystemExit("--scale must be >= 1")

    frames_root = Path(args.frames_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    selected = args.state or list(ROW_DURATIONS)
    previews = []
    for state in selected:
        durations = ROW_DURATIONS[state]
        frames = load_frames(frames_root, state, len(durations))
        output = output_dir / f"{state}.gif"
        save_preview(frames, durations, output, args.background, args.scale)
        previews.append({"state": state, "path": str(output), "frames": len(frames)})

    print(json.dumps({"ok": True, "output_dir": str(output_dir), "previews": previews}, indent=2))


if __name__ == "__main__":
    main()
