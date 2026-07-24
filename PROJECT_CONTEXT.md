# Project Context

## Product intent

Cellular Cube Go turns Conway's Game of Life from a passive simulation into a
small survival-and-exploration game. The player is a red square moving through
an evolving black-and-white world. White live cells are hazards. Colored
rewards create visible interventions in the world's evolution.

The intended experience is readable minimal pixel art, interesting emergence
with low repetition, and one codebase that behaves consistently on desktop and
in the browser. The default remains a survival challenge; exploration and rule
interaction matter more than a conventional score chase.

## Current rule-zone design

The main world is binary Conway Life (`B3/S23`) with hard, non-wrapping
boundaries. Rewards use five ecosystems:

| Color | Rule | Rulestring / neighborhood | Routing |
| --- | --- | --- | --- |
| Green | Conway Life | `B3/S23`, Moore | minimum 55% |
| Purple | HighLife | `B36/S23`, Moore | dynamic |
| Orange | Seeds | `B2/S`, Moore | dynamic |
| Cyan-blue | Day & Night | `B3678/S34678`, Moore | dynamic |
| Yellow | Wolfram Code 52 | `B24/S134`, von Neumann | dynamic |

The secondary share is based on the square root of each usable library size
and its fresh candidates; unavailable share returns to Conway. The route and
Pattern choice use the same candidate snapshot.

After the player touches and leaves a reward, its complete Pattern bounding box
is placed behind the exit direction and evolves inside an isolated local zone.
The outside Conway world cannot enter the zone, and the incubating colored
cells are non-lethal. They interpolate from the reward color toward white over
a fixed schedule derived from Pattern area and measured complexity inside each
rule's published generation range. Extinction clears a zone early; otherwise
the schedule ends with surviving cells becoming lethal white Conway cells.

## Complexity and variety

Pattern complexity opens continuously from survival time and successfully
created greenhouses. The default 90-second Variety Duration supplies 70% of
progress and eight successful greenhouses supply the remaining 30%. Large
Pattern probability rises from about 3% to at most 15%.

Recent Pattern IDs, the last two sizes, category history, and the most recent
200 choices restore the variety goals that existed before the rule-zone
refactor. Low-complexity Patterns remain possible late in a run.

## Pattern data policy

The schema-v3 runtime catalog is rule-first and versioned. Entries need a
stable ID, rulestring compatibility, category, dimensions, population, RLE,
selection metadata, deterministic complexity analysis, source, and
license/provenance metadata.

The 2026-07-24 snapshot contains project-owned seeds, licensed Conway entries
from the PlayGameOfLife Life Lexicon, and a pinned curated set of LifeWiki OCA
entries for HighLife, Seeds, and Day & Night. Deterministic project-owned
search fills every secondary rule, including Code 52, to at least 20 playable
geometric uniques.

Importing and analysis are offline development operations. Runtime gameplay
never scrapes the network. Unknown-license data remains out of the published
catalog but must be visible in import reports. All valid entries may remain in
the catalog; gameplay eligibility additionally requires fitting the visible
world.

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
