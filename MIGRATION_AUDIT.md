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
- Pattern-size-sensitive incubation, now bounded by each `RuleSpec`.

## Resolved historical contradictions

1. Old executable behavior placed a Pattern forward along the exit direction,
   while one stale comment said it should trail behind. The executable behavior
   is preserved.
2. Old incubation grew with Pattern area, while the first `EvolutionZone`
   implementation only used rule-level timing. Area and measured complexity now
   adjust the minimum inside the rule's fixed minimum/maximum range.
3. The historical `assets/patterns/library.json` had 109 rows but no per-entry
   provenance or redistribution license. It is excluded from publication and
   explicitly recorded as `unknown-license` in `import-report.v3.json`.

Changing forward placement or complexity-adjusted incubation is a product
decision, not a cleanup. Tests should be updated together with such a change.
