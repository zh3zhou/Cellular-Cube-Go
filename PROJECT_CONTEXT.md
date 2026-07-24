# Project Context

## Product intent

Cellular Cube Go turns Conway's Game of Life from a passive simulation into a
small survival-and-exploration game. The player is a red square moving through
an evolving black-and-white world. White live cells are hazards. Colored
rewards create visible interventions in the world's evolution.

The intended experience is:

- readable, minimal pixel art;
- interesting emergent structures with low repetition;
- a world that visibly evolves instead of behaving like a conventional score
  chase;
- one codebase that behaves consistently on desktop and in the browser.

The default mode remains a survival challenge. Exploration, visual emergence,
and rule interaction matter more than adding a large progression system.

## Current rule-zone design

The main world is binary Conway Life (`B3/S23`) with hard, non-wrapping
boundaries. A colored reward selects one of four rules:

| Color | Rule | Rulestring | Default weight |
| --- | --- | --- | ---: |
| Green | Conway Life | `B3/S23` | 55% |
| Purple | HighLife | `B36/S23` | 20% |
| Orange | Seeds | `B2/S` | 15% |
| Cyan-blue | Day & Night | `B3678/S34678` | 10% |

After the player touches and leaves a reward, its Pattern evolves inside an
isolated local zone. The outside Conway world cannot enter the zone, and the
incubating colored cells are non-lethal. A stable, periodic, extinct, or
time-limited zone resolves deterministically; surviving cells then become white
Conway cells in the main world.

## Pattern data policy

The runtime catalog is rule-first and versioned. Entries need a stable ID,
rulestring compatibility, category, dimensions, population, RLE, selection
metadata, source, and license/provenance metadata.

Importing is an offline development operation. Runtime gameplay never scrapes
the network. A source may be useful for research without granting
redistribution rights; entries with missing or unclear redistribution
information must stay out of the published catalog.

The 2026-07-24 catalog snapshot contains project-owned seed Patterns and
licensed Conway entries from the PlayGameOfLife Life Lexicon, plus a pinned
curated set of LifeWiki OCA entries for HighLife, Seeds, and Day & Night.
Network acquisition is isolated to a development tool; the strict RLE
importer, validation, deduplication, and runtime are local and deterministic.

All valid entries may be retained in the catalog, but gameplay eligibility also
depends on fitting the visible world. Large entries form a low-frequency tier
instead of overwhelming ordinary reward selection.

## Deliberate non-goals for this phase

- a globally multi-rule world;
- Brian's Brain, Langton's Ant, Lenia, or continuous-state automata;
- generated music;
- collection, unlock, or full upgrade systems;
- a new score-centric default mode;
- separate desktop and Web forks.

Historical reports and private brainstorming contain ideas outside these
boundaries. They are not commitments unless promoted here by a current user
decision.
