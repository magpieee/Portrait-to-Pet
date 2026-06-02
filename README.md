# Portrait To Pet

Reusable Codex skill for turning a single character portrait into a validated animated desktop pet, with chroma cleanup, motion QA, packaging, and GitHub release helpers.

## What It Does

`portrait-to-pet` is a high-level production workflow for Codex custom pets. It wraps the existing `hatch-pet` and `imagegen` skills with the extra QA steps that tend to matter in real pet-making runs:

- generate a Codex-compatible animated pet from one character reference image
- preserve character identity across all required animation rows
- remove or audit green-screen/chroma artifacts and transparent RGB residue
- render matte GIF previews to avoid transparent GIF color flicker
- distinguish directional movement rows from Codex's task-running state
- package final pet assets and prepare a GitHub-ready release folder

## Install

Copy this folder into your Codex skills directory:

```text
%USERPROFILE%\.codex\skills\portrait-to-pet
```

Restart Codex so the skill is discovered.

## Usage

Example prompt:

```text
Use $portrait-to-pet to turn this character reference into a Codex pet and prepare a GitHub-ready release.
```

The skill expects `hatch-pet` and the system `imagegen` skill to be available in the same Codex environment.

## Included Scripts

- `scripts/audit_pet_assets.py`: audits PNG/WebP/GIF assets for transparency residue and chroma halos
- `scripts/render_matte_gif_previews.py`: renders stable matte-background GIF previews from extracted RGBA pet frames
- `scripts/prepare_open_source_release.py`: builds a clean repository folder for a finished pet release

## Notes

For pets based on existing games, anime, brands, mascots, or other third-party characters, keep public releases clearly marked as unofficial fan work. See `references/release-policy.md`.

## License

MIT. See `LICENSE.md`.
