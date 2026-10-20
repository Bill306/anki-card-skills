# Repository instructions

- Keep `skills/pdf-to-anki/SKILL.md` concise and in Chinese. Detailed card rules belong in `references/card-rules.md`.
- Preserve source evidence, physical PDF page numbers, stable note identity, and existing user files.
- The Agent generates and reviews card content; scripts only preprocess, validate, and export. Never describe structural checks as proof of semantic accuracy.
- Keep private PDFs, credentials, research captures, virtual environments, and user Anki collections out of Git.
- Use the synthetic example in `examples/lumabox` for tests. `python tests/checks.py` writes to an isolated system temporary directory.
- Changes to schema/model fields must consider Anki re-import compatibility. Do not change the fields of an existing model ID silently.
