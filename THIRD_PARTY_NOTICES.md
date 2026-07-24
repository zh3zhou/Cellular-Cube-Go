# Third-party notices

This file records only provenance and license facts that can currently be
verified from files in this repository. It is not a substitute for the
per-entry `source` metadata in the Pattern catalog.

## Pixelify Sans

Bundled file: `assets/fonts/PixelifySans-Medium.ttf`

The font's embedded metadata identifies:

- family: Pixelify Sans;
- copyright: “Copyright 2021 The Pixelify Sans Project Authors”;
- project reference: `https://github.com/eifetx/PixelifySans`;
- license: SIL Open Font License, Version 1.1;
- license reference: `https://scripts.sil.org/OFL`.

The repository did not previously retain the exact download URL, release tag,
or source commit for this binary. That provenance remains unknown. The binary's
SHA-256 digest is:

`8c69050fc0565d57be8cd841c876c3af920a46d539c487cfec47d228823c79a3`

The SIL Open Font License 1.1 text is available from the license reference
embedded in the font. A future font update must preserve the license and record
the exact upstream version and download source.

## Cellular-automaton Patterns

Each publishable Pattern must carry its own provider, source URL or source file,
source version/commit, external identifier, and redistribution license in the
versioned Pattern catalog. A website being publicly readable is not evidence of
permission to redistribute its data.

Legacy Pattern data without this metadata is unverified. Import reports may
record such candidates, but unknown-license entries must not be added to the
published runtime catalog.

### PlayGameOfLife Life Lexicon

The catalog snapshot dated 2026-07-24 includes 663 geometrically unique
Conway Life Patterns acquired from the PlayGameOfLife rendering of Stephen A.
Silver's Life Lexicon. Every such entry records its individual source page and
external identifier.

- provider: `https://playgameoflife.com/lexicon`
- index: `https://playgameoflife.com/list.html`
- upstream credits: `https://conwaylife.com/ref/lexicon/lex.htm`
- license: Creative Commons Attribution-ShareAlike 3.0 Unported
- license text: `https://creativecommons.org/licenses/by-sa/3.0/`

Those catalog records remain available under CC BY-SA 3.0; the repository's
MIT license does not replace their upstream content license. The generated
import report records 659 game-eligible imports, 4 catalog-only oversized
imports, and 69 geometric or naming duplicates.

### LifeWiki OCA

The pinned curated snapshot contains 9 rule-explicit HighLife, Seeds, and
Day & Night Patterns extracted from the per-entry LifeWiki pages recorded in
the catalog.

- provider: `https://conwaylife.com/wiki/OCA`
- attribution: LifeWiki contributors and the discoverers credited per page
- license: GNU Free Documentation License 1.2
- license text: `https://www.gnu.org/licenses/old-licenses/fdl-1.2.html`

Viewer directives were removed, and the displayed RLE was canonicalized and
geometrically deduplicated. Source URLs, content hashes, attribution, and
change notices are retained per entry. The runtime copy of these notices is
`assets/patterns/NOTICE.md`, which is intentionally included in Web artifacts.

### Project-generated secondary-rule Patterns

The v3 catalog includes 59 fixed-seed, algorithmically searched Patterns whose
provider is `cellular-cube-go-generator`. They are project output under MIT,
not copied from external diagrams. The catalog stores generator version,
random seed, source digest, and 256-generation analysis metadata. The v3
report records accepted and rejected candidates.

The Code 52 rule was selected with research context from Packard and Wolfram's
two-dimensional cellular-automaton work and later Code 52 analysis:

- `https://content.wolfram.com/sw-publications/2020/07/two-dimensional-cellular-automata.pdf`
- `https://www.complex-systems.com/abstracts/v17_i02_a05/`

No paper figure or Pattern was copied into the catalog.

The historical `assets/patterns/library.json` contained 109 records without
per-entry source or redistribution terms. It remains excluded; the v3 report
records the whole source as `unknown-license` so the exclusion is auditable.

## BrowserFS

The Web loader references BrowserFS 1.4.3 from jsDelivr because pygbag 0.9.3's
own BrowserFS URL currently does not provide the required script. BrowserFS is
distributed under the MIT License:

- project: `https://github.com/jvilk/BrowserFS`;
- pinned asset: `https://cdn.jsdelivr.net/npm/browserfs@1.4.3/dist/browserfs.min.js`;
- license: `https://github.com/jvilk/BrowserFS/blob/v1.4.3/LICENSE`.
