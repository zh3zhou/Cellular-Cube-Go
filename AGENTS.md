# Cellular Cube Go Agent Contract

## Mission

Maintain a small survival game in which a red player moves through a living
two-dimensional cellular-automaton world. The main world uses Conway's Life;
colored rewards create temporary, isolated rule zones that later merge back
into the main world.

`PROJECT_CONTEXT.md` contains the public product intent and scope. Private notes
under `《开发》/` and `.trae/documents/` are context for the repository owner
only and must not be published.

## Source of truth

Use this order when sources disagree:

1. The current user request.
2. Runtime behavior, tests, and current source code.
3. `PROJECT_CONTEXT.md` and this file.
4. `README.md`.
5. Historical reports and ignored private notes.

Do not restore obsolete commands or architecture from generated reports.

## Entrypoints and commands

- Universal local/Web entrypoint: `main.py`
- Runtime code: `src/`, `config/`
- Runtime assets: `assets/`
- Desktop: `python main.py`
- Tests: `python -m pytest`
- Web build:
  `python -m pygbag --build --width 1100 --height 600 --ume_block 0 --template static/default.tmpl .`
- Strict local RLE import:
  `python -m tools.patterns.import_rle <inputs> --manifest <manifest.json> --output <catalog.json> --report <report.json>`
- Licensed Life Lexicon snapshot refresh:
  `python -m tools.patterns.fetch_playgameoflife`
- Pinned LifeWiki OCA snapshot rebuild:
  `python -m tools.patterns.import_lifewiki_oca`

Use Python 3.12 and install the declared extras from `pyproject.toml`. Do not
introduce a second Web entrypoint or a second implementation of the game loop.
`pyproject.toml` is the version source of truth. The PEP 723 block in `main.py`
must keep bare `pygame-ce` and `numpy` names because pygbag 0.9.3 treats pinned
specifiers as import names while resolving Web wheels.

## Boundaries

- Keep cellular-automaton, rule, and Pattern selection logic independent from
  Pygame wherever practical.
- Preserve hard, non-wrapping world boundaries unless a task explicitly changes
  that product decision.
- Runtime code must not fetch, scrape, or modify the Pattern catalog.
- Every published Pattern and bundled asset must retain verifiable provenance
  and redistribution information. Unknown-license material is not publishable.
- Do not edit generated files under `build/`; rebuild them instead.
- Do not commit `《开发》/`, `.trae/documents/`, environments, caches, test
  output, or importer working data.
- Preserve the author's handwritten Chinese preface under `作者的碎碎念` in
  `README.md` verbatim. It is intentional public self-expression, not obsolete
  technical documentation; do not remove, rewrite, translate, or collapse it
  unless the repository owner explicitly requests that change.
- Do not add hooks, durable automations, remote writes, or new public features
  without explicit authorization.

## Verification and release gate

Before claiming a change works:

1. Run focused tests, then `python -m pytest`.
2. Run `python -m compileall -q main.py config src`.
3. For Web-affecting changes, build with the command above and inspect the
   archive: it must include `main.py`, `src/`, `config/`, and runtime assets,
   while excluding private notes, tests, import tools, and caches.
4. Smoke-test the desktop loop with SDL's dummy driver when a visible run is not
   possible.
5. For a release, let GitHub Actions deploy the verified `build/web` artifact,
   then repeat the browser start/input smoke test against GitHub Pages.

Never describe an unrun manual or live-browser check as passed.
