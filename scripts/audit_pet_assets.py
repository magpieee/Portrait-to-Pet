#!/usr/bin/env python3
"""Audit Codex pet image assets for transparency residue and chroma halos."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageSequence

IMAGE_SUFFIXES = {".png", ".webp", ".gif"}


def parse_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip()
    if value.startswith("#"):
        value = value[1:]
        if len(value) != 6:
            raise argparse.ArgumentTypeError("hex colors must be RRGGBB")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("RGB colors must be '#RRGGBB' or 'r,g,b'")
    rgb = tuple(int(part) for part in parts)
    if any(channel < 0 or channel > 255 for channel in rgb):
        raise argparse.ArgumentTypeError("RGB channels must be between 0 and 255")
    return rgb  # type: ignore[return-value]


def near_color(rgb: tuple[int, int, int], key: tuple[int, int, int], distance: float) -> bool:
    return math.dist(rgb, key) <= distance


def image_paths(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in IMAGE_SUFFIXES else []
    return sorted(path for path in root.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)


def iter_frames(path: Path) -> Iterable[Image.Image]:
    with Image.open(path) as opened:
        for frame in ImageSequence.Iterator(opened):
            yield frame.convert("RGBA")


def has_transparent_neighbor(alpha, width: int, height: int, x: int, y: int) -> bool:
    for ny in range(max(0, y - 1), min(height, y + 2)):
        for nx in range(max(0, x - 1), min(width, x + 2)):
            if nx == x and ny == y:
                continue
            if alpha[nx, ny] == 0:
                return True
    return False


def audit_frame(
    image: Image.Image,
    key: tuple[int, int, int],
    distance: float,
    transparent_threshold: int,
    opaque_threshold: int,
) -> dict[str, int]:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    alpha = rgba.getchannel("A").load()
    transparent_rgb_residue = 0
    semitransparent_chroma = 0
    visible_chroma_edge = 0
    transparent_pixels = 0
    visible_pixels = 0

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            rgb = (r, g, b)
            if a <= transparent_threshold:
                transparent_pixels += 1
                if rgb != (0, 0, 0):
                    transparent_rgb_residue += 1
                continue
            visible_pixels += 1
            if a < opaque_threshold and near_color(rgb, key, distance):
                semitransparent_chroma += 1
            if near_color(rgb, key, distance) and has_transparent_neighbor(alpha, width, height, x, y):
                visible_chroma_edge += 1

    return {
        "transparent_pixels": transparent_pixels,
        "visible_pixels": visible_pixels,
        "transparent_rgb_residue": transparent_rgb_residue,
        "semitransparent_chroma": semitransparent_chroma,
        "visible_chroma_edge": visible_chroma_edge,
    }


def merge_counts(items: list[dict[str, int]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            result[key] = result.get(key, 0) + value
    return result


def audit_path(
    path: Path,
    key: tuple[int, int, int],
    distance: float,
    transparent_threshold: int,
    opaque_threshold: int,
) -> dict[str, object]:
    frames = [
        audit_frame(frame, key, distance, transparent_threshold, opaque_threshold)
        for frame in iter_frames(path)
    ]
    return {
        "path": str(path),
        "frames": len(frames),
        "counts": merge_counts(frames),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Image file or folder to audit")
    parser.add_argument("--chroma", type=parse_rgb, default=(0, 255, 0), help="Chroma key as #RRGGBB or r,g,b")
    parser.add_argument("--chroma-distance", type=float, default=90.0)
    parser.add_argument("--transparent-threshold", type=int, default=0)
    parser.add_argument("--opaque-threshold", type=int, default=255)
    parser.add_argument("--allow-transparent-residue", type=int, default=0)
    parser.add_argument("--allow-chroma-edge", type=int, default=256)
    parser.add_argument("--allow-semitransparent-chroma", type=int, default=256)
    parser.add_argument("--strict", action="store_true", help="Use zero tolerance for all residue counters")
    parser.add_argument("--json-out")
    parser.add_argument("--no-fail", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    paths = image_paths(root)
    if not paths:
        raise SystemExit(f"No PNG/WebP/GIF files found at {root}")

    files = [
        audit_path(path, args.chroma, args.chroma_distance, args.transparent_threshold, args.opaque_threshold)
        for path in paths
    ]
    totals = merge_counts([item["counts"] for item in files])  # type: ignore[list-item]
    limits = {
        "transparent_rgb_residue": 0 if args.strict else args.allow_transparent_residue,
        "visible_chroma_edge": 0 if args.strict else args.allow_chroma_edge,
        "semitransparent_chroma": 0 if args.strict else args.allow_semitransparent_chroma,
    }
    ok = (
        totals.get("transparent_rgb_residue", 0) <= limits["transparent_rgb_residue"]
        and totals.get("visible_chroma_edge", 0) <= limits["visible_chroma_edge"]
        and totals.get("semitransparent_chroma", 0) <= limits["semitransparent_chroma"]
    )
    result = {
        "ok": ok,
        "path": str(root),
        "chroma": args.chroma,
        "chroma_distance": args.chroma_distance,
        "limits": limits,
        "totals": totals,
        "files": files,
    }

    output = json.dumps(result, indent=2)
    print(output)
    if args.json_out:
        Path(args.json_out).expanduser().resolve().write_text(output + "\n", encoding="utf-8")
    if not ok and not args.no_fail:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
