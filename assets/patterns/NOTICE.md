# Pattern dataset notice

This runtime catalog contains material under more than one license.

## PlayGameOfLife Life Lexicon snapshot

The entries whose `source.provider` is
`playgameoflife-life-lexicon` are derived from the Life Lexicon compiled by
Stephen A. Silver from contributions credited by the upstream project.

- rendered source: https://playgameoflife.com/lexicon
- index: https://playgameoflife.com/list.html
- original credits: https://conwaylife.com/ref/lexicon/lex.htm
- license: Creative Commons Attribution-ShareAlike 3.0 Unported
- license URI: https://creativecommons.org/licenses/by-sa/3.0/

For this game, the displayed binary grids were converted to RLE, empty outer
rows and columns were trimmed, RLE syntax was canonicalized, and entries
equivalent under translation, rotation, or reflection were deduplicated.
Names and per-entry source URLs are retained in `catalog.v2.json`. These
normalized catalog records remain under CC BY-SA 3.0; the project's MIT
license does not replace that license.

## Project-owned seed Patterns

Entries whose `source.provider` is `cellular-cube-go` are distributed under
the repository's MIT license. Their per-entry metadata identifies the source
revision.

## LifeWiki OCA snapshot

Entries whose `source.provider` is `lifewiki-oca` were extracted from the
linked LifeWiki pages and remain under the GNU Free Documentation License 1.2.

- source: https://conwaylife.com/wiki/OCA
- attribution: LifeWiki contributors and the discoverers credited per page
- license URI: https://www.gnu.org/licenses/old-licenses/fdl-1.2.html

Viewer directives were removed and the displayed RLE was canonicalized and
geometrically deduplicated. Per-entry source pages, hashes, attribution, and
change notices are retained in `catalog.v2.json`.
