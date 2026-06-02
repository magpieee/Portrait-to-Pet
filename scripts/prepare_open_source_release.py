#!/usr/bin/env python3
"""Prepare a GitHub-ready release folder for a finished Codex pet."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def copy_file(src: Path, dst: Path) -> bool:
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def copy_optional_from_sources(relative: str, sources: list[Path], output_dir: Path) -> bool:
    for source in sources:
        candidate = source / relative
        if copy_file(candidate, output_dir / relative):
            return True
    return False


def copy_optional_dir(relative: str, sources: list[Path], output_dir: Path) -> bool:
    for source in sources:
        candidate = source / relative
        if candidate.is_dir():
            shutil.copytree(candidate, output_dir / relative, dirs_exist_ok=True)
            return True
    return False


def license_text(owner: str) -> str:
    return f"""MIT License

Copyright (c) {owner}

Permission is hereby granted, free of charge, to any person obtaining a copy
of the software and documentation files in this repository to deal in them
without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies, subject to
the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the software and documentation.

THE SOFTWARE AND DOCUMENTATION ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

Artwork notice: this license applies to repository code and documentation only.
It does not grant rights to any underlying third-party character, game, brand,
or original artwork that inspired the pet assets.
"""


def readme_text(
    title: str,
    description: str,
    pet_id: str,
    github_url: str | None,
    fan_notice: str,
) -> str:
    repo_line = f"\nRepository: {github_url}\n" if github_url else ""
    return f"""# {title}

{description}
{repo_line}
![Contact sheet](contact-sheet.png)

## Preview

The pet atlas is `spritesheet.webp`. Motion previews are under `previews/`.

## Install

Copy these two files into your Codex custom pet folder:

```text
pet.json
spritesheet.webp
```

Suggested folder name:

```text
%USERPROFILE%\\.codex\\pets\\{pet_id}
```

Restart Codex or refresh pets after copying.

## Files

- `pet.json`: Codex pet manifest
- `spritesheet.webp`: final transparent atlas
- `contact-sheet.png`: row-by-row visual QA sheet
- `validation.json`: atlas validation summary
- `previews/*.gif`: motion previews on a matte QA background

## Notice

{fan_notice}
"""


def notice_text(title: str, fan_notice: str) -> str:
    return f"""# Notice

{title} is an unofficial custom Codex desktop pet.

{fan_notice}

No affiliation, sponsorship, or endorsement is implied unless explicitly stated
by the relevant rights holder.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pet-dir", required=True, help="Final pet/output folder containing pet.json")
    parser.add_argument("--output-dir", required=True, help="Repository-ready folder to create or update")
    parser.add_argument("--source-run", action="append", default=[], help="Optional run folder with qa/final outputs")
    parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument("--owner", default="contributors")
    parser.add_argument("--github-url")
    parser.add_argument(
        "--fan-notice",
        default=(
            "This is an unofficial fan-made desktop pet. Code and documentation may be reused "
            "under the repository license, but the generated character artwork is intended for "
            "personal, non-commercial fan use and does not grant rights to underlying IP."
        ),
    )
    parser.add_argument("--zip", action="store_true", help="Also create a .zip next to the output folder")
    args = parser.parse_args()

    pet_dir = Path(args.pet_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    source_runs = [Path(path).expanduser().resolve() for path in args.source_run]
    sources = [pet_dir]
    for run in source_runs:
        sources.extend([run, run / "qa", run / "final"])

    pet_json_path = pet_dir / "pet.json"
    if not pet_json_path.is_file():
        raise SystemExit(f"Missing pet.json under {pet_dir}")
    pet_json = read_json(pet_json_path)
    pet_id = pet_json.get("id") or output_dir.name
    title = args.title or pet_json.get("displayName") or pet_id
    description = args.description or pet_json.get("description") or f"Custom Codex pet for {title}."

    output_dir.mkdir(parents=True, exist_ok=True)

    required = [
        ("pet.json", "pet.json"),
        ("spritesheet.webp", "spritesheet.webp"),
    ]
    copied: list[str] = []
    missing: list[str] = []
    for src_rel, dst_rel in required:
        if copy_optional_from_sources(src_rel, sources, output_dir):
            copied.append(dst_rel)
        else:
            missing.append(src_rel)

    optional_files = [
        ("contact-sheet.png", "contact-sheet.png"),
        ("validation.json", "validation.json"),
        ("review.json", "review.json"),
        ("run-summary.json", "run-summary.json"),
        ("qa/contact-sheet.png", "contact-sheet.png"),
        ("qa/review.json", "review.json"),
        ("qa/run-summary.json", "run-summary.json"),
        ("final/validation.json", "validation.json"),
    ]
    for src_rel, dst_rel in optional_files:
        if (output_dir / dst_rel).exists():
            continue
        if copy_optional_from_sources(src_rel, sources, output_dir):
            copied.append(dst_rel)

    if copy_optional_dir("previews", sources, output_dir) or copy_optional_dir("qa/previews", sources, output_dir):
        copied.append("previews/")

    write_text(output_dir / "README.md", readme_text(title, description, pet_id, args.github_url, args.fan_notice))
    write_text(output_dir / "NOTICE.md", notice_text(title, args.fan_notice))
    write_text(output_dir / "LICENSE.md", license_text(args.owner))
    write_text(
        output_dir / ".gitignore",
        """
.DS_Store
Thumbs.db
*.tmp
work/
decoded/
frames/
prompts/
generated_images/
imagegen-jobs.json
""",
    )
    write_text(
        output_dir / ".gitattributes",
        """
*.png binary
*.webp binary
*.gif binary
*.jpg binary
*.jpeg binary
""",
    )

    zip_path = None
    if args.zip:
        archive = shutil.make_archive(str(output_dir), "zip", root_dir=output_dir)
        zip_path = str(Path(archive).resolve())

    result = {
        "ok": not missing,
        "output_dir": str(output_dir),
        "zip": zip_path,
        "copied": sorted(set(copied)),
        "missing_required": missing,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if missing:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
