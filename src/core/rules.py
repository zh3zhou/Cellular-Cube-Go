"""Pure, reusable definitions for two-state cellular automata."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple, Union

import numpy as np


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class NeighborhoodSpec:
    """A finite, translation-invariant neighborhood around one cell."""

    id: str
    name: str
    offsets: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        offsets = tuple(tuple(offset) for offset in self.offsets)
        if not offsets:
            raise ValueError("A neighborhood must contain at least one offset")
        if any(
            len(offset) != 2
            or not all(isinstance(value, int) for value in offset)
            for offset in offsets
        ):
            raise ValueError("Neighborhood offsets must be integer row/column pairs")
        if (0, 0) in offsets:
            raise ValueError("Neighborhood offsets must not include the center cell")
        if len(set(offsets)) != len(offsets):
            raise ValueError("Neighborhood offsets must be unique")
        object.__setattr__(self, "offsets", offsets)

    @property
    def max_neighbors(self) -> int:
        return len(self.offsets)


MOORE_NEIGHBORHOOD = NeighborhoodSpec(
    "moore",
    "Moore (8 neighbors)",
    tuple(
        (row, col)
        for row in (-1, 0, 1)
        for col in (-1, 0, 1)
        if (row, col) != (0, 0)
    ),
)
VON_NEUMANN_NEIGHBORHOOD = NeighborhoodSpec(
    "von_neumann",
    "von Neumann (4 neighbors)",
    ((-1, 0), (0, -1), (0, 1), (1, 0)),
)
NEIGHBORHOODS: Mapping[str, NeighborhoodSpec] = MappingProxyType(
    {
        neighborhood.id: neighborhood
        for neighborhood in (MOORE_NEIGHBORHOOD, VON_NEUMANN_NEIGHBORHOOD)
    }
)


@dataclass(frozen=True)
class RuleSpec:
    """A non-wrapping, two-state outer-totalistic rule."""

    id: str
    name: str
    birth_counts: frozenset[int]
    survival_counts: frozenset[int]
    color: Color
    min_generations: int
    max_generations: int
    stable_period_max: int
    pattern_library_id: str
    neighborhood: NeighborhoodSpec = MOORE_NEIGHBORHOOD

    def __post_init__(self) -> None:
        object.__setattr__(self, "birth_counts", frozenset(self.birth_counts))
        object.__setattr__(self, "survival_counts", frozenset(self.survival_counts))
        if not isinstance(self.neighborhood, NeighborhoodSpec):
            raise ValueError("neighborhood must be a NeighborhoodSpec")
        counts = self.birth_counts | self.survival_counts
        if any(
            not isinstance(value, int)
            or not 0 <= value <= self.neighborhood.max_neighbors
            for value in counts
        ):
            raise ValueError(
                "Birth and survival counts must fit the selected neighborhood"
            )
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
        pad = max(
            max(abs(row), abs(col))
            for row, col in self.neighborhood.offsets
        )
        padded = np.pad(cells, pad, mode="constant", constant_values=0)
        height, width = cells.shape
        neighbors = np.zeros_like(cells)
        for row_offset, col_offset in self.neighborhood.offsets:
            row_start = pad + row_offset
            col_start = pad + col_offset
            neighbors += padded[
                row_start:row_start + height,
                col_start:col_start + width,
            ]
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
WOLFRAM_CODE_52 = RuleSpec(
    "wolfram_code_52",
    "Wolfram Code 52",
    frozenset({2, 4}),
    frozenset({1, 3, 4}),
    (250, 214, 64),
    48,
    160,
    8,
    "wolfram_code_52",
    VON_NEUMANN_NEIGHBORHOOD,
)

RULES: Mapping[str, RuleSpec] = MappingProxyType({
    rule.id: rule
    for rule in (
        CONWAY_LIFE,
        HIGHLIFE,
        SEEDS,
        DAY_AND_NIGHT,
        WOLFRAM_CODE_52,
    )
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
    "code52": "wolfram_code_52",
    "code_52": "wolfram_code_52",
    "wolfram-code-52": "wolfram_code_52",
    "b24/s134": "wolfram_code_52",
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
