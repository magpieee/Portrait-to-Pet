# Release Policy

Use this reference when preparing a public repository for a pet based on a game, anime, brand, mascot, or other existing character.

## Public Repository Rules

- State that the project is unofficial and fan-made when the source character is not owned by the user.
- Separate the license for code/docs from the artwork. A common pattern is: code/docs under MIT; generated fan artwork is provided for personal, non-commercial use; underlying IP remains with its owners.
- Do not include raw prompts, generated-image cache folders, private chat screenshots, or unrelated local files.
- Do not claim affiliation with the original game, publisher, brand, artist, or character owner unless the user provides proof.
- Keep README installation instructions short and concrete: copy `pet.json` and `spritesheet.webp` into the Codex custom pets folder.

## Recommended Repository Files

- `README.md`: what the pet is, preview links, install path, asset list, and unofficial notice.
- `NOTICE.md`: fan-work and ownership disclaimer.
- `LICENSE.md`: license text for code/docs and a note that it does not grant rights to underlying IP.
- `.gitattributes`: mark binary image assets as binary.
- `.gitignore`: ignore local run folders, generated caches, and OS/editor files.
- `pet.json`
- `spritesheet.webp`
- `contact-sheet.png`
- `validation.json`
- `previews/*.gif`
