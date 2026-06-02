---
name: portrait-to-pet
description: Turn a single character portrait, standing illustration, mascot reference, or provided character image into a Codex-compatible animated desktop pet, then clean chroma-key/green-screen artifacts, optimize action semantics such as directional running versus task-running, validate previews, package the pet, and prepare an open-source GitHub-ready release. Use when a user asks to make a personal pet from character art, repair green edges or GIF color flicker in a pet spritesheet, improve pet animation rows, install a custom Codex pet, or publish the pet files to a repository.
---

# Portrait To Pet

## Overview

Use this skill as the high-level production workflow for turning one character reference image into a finished Codex pet and a clean release package. It composes `$hatch-pet` for the atlas pipeline, `$imagegen` for visual generation, and the GitHub app or local Git only for publishing after the pet assets are complete.

Always load `$hatch-pet` before starting visual generation. Load `$imagegen` through `$hatch-pet` for base art and action rows. Use the GitHub plugin when the user asks to create issues, update repository files, inspect remote state, or publish through a connected account.

## Workflow

1. Intake the character reference.
   - Capture the source image path, pet id, display name, one-sentence description, style target, and required identity details.
   - For fan characters or existing IP, keep the release language clearly unofficial. Do not claim ownership of the underlying character, game, brand, or original art.
   - Default to a compact chibi pixel pet when the user asks for "Q", "pixel", "desktop pet", or "personal pet".

2. Prepare a `$hatch-pet` run.
   - Copy the reference into the run's `references/` folder before generation.
   - Use `prepare_pet_run.py` from `$hatch-pet` with `--style-preset pixel` or another explicit user style.
   - Put durable identity details in `--pet-notes`: hair/ears/tail, signature colors, outfit, props, and personality. Keep prompt text concise and sprite-production oriented.

3. Generate in identity gates.
   - Generate the base first, then use it as the canonical identity reference for every row.
   - Generate `idle` and `running-right` early. Inspect them before spending the whole run.
   - Generate `running-left` by mirroring `running-right` only when markings, side-specific props, lighting, and frame timing still make sense. Otherwise generate it as its own grounded row.
   - Generate all remaining rows from the canonical base and the row layout guide.

4. Clean chroma artifacts before extraction.
   - Prefer clean source rows: flat chroma background, no shadows, no glow, no scenery, no detached effects.
   - If decoded strips contain green-screen edges, run the installed imagegen chroma remover when available:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\imagegen\scripts\remove_chroma_key.py" `
  --input <decoded-row-or-folder> `
  --output <clean-output> `
  --auto-key border `
  --soft-matte `
  --transparent-threshold 12 `
  --opaque-threshold 220 `
  --despill `
  --edge-contract 1
```

   - After cleanup, run `scripts/audit_pet_assets.py` against decoded rows, final WebP, or previews. Treat visible chroma pixels touching transparency and transparent RGB residue as repair issues.
   - Do not hide a bad official `spritesheet.webp` by changing preview backgrounds. The final WebP must be transparent and clean.

5. Build, validate, and preview.
   - Run the normal `$hatch-pet` scripts: extract frames, inspect frames, compose atlas, validate atlas, make contact sheet, and render GIF previews.
   - If GIF previews show flashing colored pixels but the WebP is clean, regenerate QA GIFs with a solid matte using `scripts/render_matte_gif_previews.py`. This is for preview stability only.
   - If preview GIFs show size popping caused by extraction, rerun extraction with `$hatch-pet` stable-slot mode, then rerun inspection, composition, validation, contact sheet, and previews.

6. Optimize action semantics.
   - `running-right` and `running-left` are directional movement rows. They should visibly move with alternating legs, arms, tail, hair, or held props.
   - `running` is the Codex task-working state. Do not make it literal foot-running unless the user explicitly wants to change app semantics. Use focused working, scanning, kneading, typing, or processing motion.
   - `idle` must be calm but not inert. A blink, breath, ear twitch, tail sway, or tiny body bob is enough.
   - Reject rows that are visually static, face the wrong way, reverse timing after mirroring, drift identity, crop body parts, or introduce detached effects.

7. Package the pet.
   - Installable pet folder must contain `pet.json` and `spritesheet.webp` together.
   - Deliver a user-facing output folder with `pet.json`, `spritesheet.webp`, `contact-sheet.png`, `validation.json`, and `previews/*.gif`.
   - Keep intermediate prompts, decoded strips, frames, and raw generated images out of the final release unless the user asks for debug artifacts.

8. Prepare an open-source release when requested.
   - Use `scripts/prepare_open_source_release.py` to create a clean repo folder and optional zip.
   - Include source-control metadata files, README, NOTICE, LICENSE, `pet.json`, `spritesheet.webp`, `contact-sheet.png`, `validation.json`, and `previews/`.
   - Use local `git` only when credentials and HTTPS/SSH transport work. If local Git push is broken or binary upload through the GitHub app is impractical, create the release zip and instruct the user to upload the extracted contents through GitHub Web UI.

## Scripts

- `scripts/audit_pet_assets.py`: scan PNG/WebP/GIF assets for transparent RGB residue, semi-transparent chroma remnants, and green/chroma pixels touching transparent edges.
- `scripts/render_matte_gif_previews.py`: render matte-background GIF previews from extracted RGBA frames to avoid transparent GIF palette flicker.
- `scripts/prepare_open_source_release.py`: copy final pet files into a GitHub-ready release folder, generate README/NOTICE/LICENSE and source-control helper files, and optionally create a zip.

Read `references/release-policy.md` when publishing fan or existing-IP pets.

## Acceptance Criteria

- The final atlas is `1536x1872`, transparent-capable, and valid under `$hatch-pet` validation.
- Transparent pixels in final official assets do not retain colored RGB residue.
- Contact sheet and GIF previews have been inspected.
- Directional running rows visibly alternate and face the intended direction.
- The non-directional `running` row matches task-working semantics unless the user asked otherwise.
- The release folder excludes intermediate generation artifacts and includes clear unofficial/fan-work notices when relevant.
