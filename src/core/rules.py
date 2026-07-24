"""Pure, reusable definitions for two-state Life-like cellular automata."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple, Union

import numpy as np


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class RuleSpec:
    """A non-wrapping, two-state Life-like rule."""

    id: str
    name: str
    birth_counts: frozenset[int]
    survival_counts: frozenset[int]
    color: Color
    min_generations: int
    max_generations: int
    stable_period_max: int
    pattern_library_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "birth_counts", frozenset(self.birth_counts))
        object.__setattr__(self, "survival_counts", frozenset(self.survival_counts))
        counts = self.birth_counts | self.survival_counts
        if any(not isinstance(value, int) or not 0 <= value <= 8 for value in counts):
            raise ValueError("Birth and survival counts must be integers from 0 to 8")
        if self.min_generations < 0 or self.max_generations < 1:
            raise ValueError("Generation limits must be non-negative and non-zero")
        if self.min_generations > self.max_generations:
            raise ValueError("min_generations cannot exceed max_generations")
        if not 1 <= self.stable_period_max <= 8:
            raise ValueError("stable_period_max must be between 1 and 8")

    @property
    def rulestring(self) -> str:
        births = "".join(str(value) for value in sorted(self.birth_counts))
        survives = "".join(str(value) for value in sorted(self.survival_counts))
        return f"B{births}/S{survives}"

    def apply(self, current_cell: int, neighbor_count: int) -> int:
        allowed = self.survival_counts if current_cell else self.birth_counts
        return int(neighbor_count in allowed)

    def evolve(self, state: Iterable[Iterable[int]]) -> np.ndarray:
        """Return one generation using zero-filled, non-wrapping boundaries."""
        cells = np.asarray(state, dtype=np.uint8)
        if cells.ndim != 2:
            raise ValueError("Cell state must be a two-dimensional array")
        if cells.size == 0:
            return cells.copy()
        if np.any(cells > 1):
            raise ValueError("Cell state must contain only 0 and 1")
        padded = np.pad(cells, 1, mode="constant", constant_values=0)
        neighbors = (
            padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:]
            + padded[1:-1, :-2] + padded[1:-1, 2:]
            + padded[2:, :-2] + padded[2:, 1:-1] + padded[2:, 2:]
        )
        born = (cells == 0) & np.isin(neighbors, tuple(self.birth_counts))
        survives = (cells == 1) & np.isin(neighbors, tuple(self.survival_counts))
        return (born | survives).astype(np.uint8)


CONWAY_LIFE = RuleSpec(
    "life", "Conway's Life", frozenset({3}), frozenset({2, 3}),
    (138, 222, 137), 12, 48, 8, "life",
)
HIGHLIFE = RuleSpec(
    "highlife", "HighLife", frozenset({3, 6}), frozenset({2, 3}),
    (185, 120, 255), 48, 144, 8, "highlife",
)
SEEDS = RuleSpec(
    "seeds", "Seeds", frozenset({2}), frozenset(),
    (255, 165, 64), 32, 96, 8, "seeds",
)
DAY_AND_NIGHT = RuleSpec(
    "day_night", "Day & Night", frozenset({3, 6, 7, 8}),
    frozenset({3, 4, 6, 7, 8}), (90, 210, 235), 48, 160, 8,
    "day_night",
)

RULES: Mapping[str, RuleSpec] = MappingProxyType({
    rule.id: rule for rule in (CONWAY_LIFE, HIGHLIFE, SEEDS, DAY_AND_NIGHT)
})
_RULE_ALIASES = {
    "conway": "life",
    "conway_life": "life",
    "b3/s23": "life",
    "b36/s23": "highlife",
    "b2/s": "seeds",
    "daynight": "day_night",
    "day-and-night": "day_night",
    "day_and_night": "day_night",
    "b3678/s34678": "day_night",
}


def get_rule(rule: Union[str, RuleSpec]) -> RuleSpec:
    """Resolve a rule id, common alias, or canonical rulestring."""
    if isinstance(rule, RuleSpec):
        return rule
    key = str(rule).strip().lower()
    key = _RULE_ALIASES.get(key, key)
    try:
        return RULES[key]
    except KeyError as exc:
        raise KeyError(f"Unknown cellular automaton rule: {rule!r}") from exc
