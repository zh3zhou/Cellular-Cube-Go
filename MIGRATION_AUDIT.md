# Refactor migration audit

This note records the 2026-07-24 audit against behavior that existed before the
rule-zone refactor. It separates intentional replacements from recovered
features so later cleanup does not repeat the same regressions.

## Preserved intentional replacements

- one `main.py` and one `GameEngine.step/render/shutdown` loop for desktop/Web;
- a visible `110×60` hard-boundary Conway world;
- isolated, non-lethal incubation zones, at most three, with one-cell buffers;
- touch-then-leave reward activation and direction-based rotation;
- mature cells immediately becoming lethal white Conway cells;
- 52 old embedded Pattern rows migrated to 47 geometric uniques rather than
  being silently dropped.

## Recovered behavior goals

- progress-dependent Pattern complexity and size;
- last-two-size variation;
- category balancing;
- a 200-choice inverse-frequency window;
- a working, seconds-based `Variety Duration` setting;
- Pattern-size-sensitive fixed incubation, now bounded by each `RuleSpec`;
- a visible reward-color-to-white gradient for every rule ecosystem;
- restart without reloading and reparsing the immutable Pattern catalog.

## Resolved historical contradictions

1. Old executable behavior placed a Pattern forward along the exit direction,
   while its own migration comment said it should trail behind. On 2026-07-25
   the owner explicitly selected trailing placement. The complete Pattern
   bounding box now starts behind the exit direction when boundary space allows,
   rather than merely moving its center.
2. Old incubation grew with Pattern area, while the first `EvolutionZone`
   implementation only used rule-level timing. A later migration connected area
   and complexity only to `min_generations`, so stability or the hard maximum
   could still determine a different lifetime. Area and measured complexity now
   determine the actual fixed incubation schedule.
3. The historical `assets/patterns/library.json` had 109 rows but no per-entry
   provenance or redistribution license. It is excluded from publication and
   explicitly recorded as `unknown-license` in `import-report.v3.json`.
4. The historical source faded black toward green, while the owner's intended
   presentation is the reward color fading toward mature white. The current
   owner decision is applied consistently to all five rules, with the exact base
   color visible for the first frame.

Changing trailing placement, the incubation mapping, or the color endpoints is
a product decision. Tests must be updated together with such a change.
