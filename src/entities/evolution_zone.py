"""Isolated local evolution zones that later commit into the main world."""
from __future__ import annotations

from enum import Enum
from typing import Iterable, Iterator, Optional, Tuple, Union

import numpy as np

from src.core.rules import RuleSpec, get_rule


class ZoneStatus(str, Enum):
    ACTIVE = "active"
    MATURE = "mature"
    EXTINCT = "extinct"


class EvolutionZone:
    """Evolve a padded seed independently under one Life-like rule.

    Constructor ``start_row``/``start_col`` locate the seed. Public
    ``start_row``/``start_col`` locate the padded arena, matching ``pattern``.
    Bounds and coordinates use row/column order and exclusive lower bounds.
    """

    def __init__(
        self,
        pattern: Iterable[Iterable[int]],
        start_row: int,
        start_col: int,
        rule: Union[str, RuleSpec],
        padding: int = 8,
        *,
        base_color: Optional[Tuple[int, int, int]] = None,
        world_shape: Optional[Tuple[int, int]] = None,
        min_generations: Optional[int] = None,
        max_generations: Optional[int] = None,
        stable_period_max: Optional[int] = None,
    ) -> None:
        seed = np.asarray(pattern, dtype=np.uint8)
        if seed.ndim != 2 or not seed.shape[0] or not seed.shape[1]:
            raise ValueError("pattern must be a non-empty two-dimensional array")
        if np.any(seed > 1):
            raise ValueError("pattern must contain only 0 and 1")
        if start_row < 0 or start_col < 0 or padding < 0:
            raise ValueError("coordinates and padding must be non-negative")

        self.rule = get_rule(rule)
        self.base_color = base_color or self.rule.color
        self.seed_start_row = start_row
        self.seed_start_col = start_col
        top = max(0, start_row - padding)
        left = max(0, start_col - padding)
        bottom = start_row + seed.shape[0] + padding
        right = start_col + seed.shape[1] + padding
        if world_shape is not None:
            world_height, world_width = world_shape
            if start_row + seed.shape[0] > world_height or start_col + seed.shape[1] > world_width:
                raise ValueError("seed pattern does not fit inside world_shape")
            bottom = min(bottom, world_height)
            right = min(right, world_width)
        self.start_row = top
        self.start_col = left
        self._grid = np.zeros((bottom - top, right - left), dtype=np.uint8)
        local_row = start_row - top
        local_col = start_col - left
        self._grid[
            local_row:local_row + seed.shape[0],
            local_col:local_col + seed.shape[1],
        ] = seed

        self.min_generations = (
            self.rule.min_generations if min_generations is None else min_generations
        )
        self.max_generations = (
            self.rule.max_generations if max_generations is None else max_generations
        )
        self.stable_period_max = (
            self.rule.stable_period_max
            if stable_period_max is None else stable_period_max
        )
        if not 0 <= self.min_generations <= self.max_generations:
            raise ValueError("invalid generation limits")
        if not 1 <= self.stable_period_max <= 8:
            raise ValueError("stable_period_max must be between 1 and 8")

        self.current_step = 0
        self.total_steps = self.max_generations
        self.status = ZoneStatus.ACTIVE
        self.finish_reason: Optional[str] = None
        self.stable_period: Optional[int] = None
        self._signatures = [self._normalized_signature()]
        self._candidate_signature = None
        self._candidate_period: Optional[int] = None
        self._candidate_last_step: Optional[int] = None
        self._candidate_repeats = 0

    @property
    def pattern(self) -> np.ndarray:
        return self._grid

    @pattern.setter
    def pattern(self, value: Iterable[Iterable[int]]) -> None:
        cells = np.asarray(value, dtype=np.uint8)
        if cells.ndim != 2 or cells.shape != self._grid.shape or np.any(cells > 1):
            raise ValueError("replacement pattern must be binary and preserve arena shape")
        self._grid = cells.copy()

    @property
    def reserved_rect(self) -> Tuple[int, int, int, int]:
        return (
            self.start_row,
            self.start_col,
            self.start_row + self._grid.shape[0],
            self.start_col + self._grid.shape[1],
        )

    @property
    def active(self) -> bool:
        return self.status is ZoneStatus.ACTIVE

    @property
    def finished(self) -> bool:
        return not self.active

    @property
    def extinct(self) -> bool:
        return self.status is ZoneStatus.EXTINCT

    def get_color(self) -> Tuple[int, int, int]:
        progress = min(1.0, self.current_step / max(1, self.max_generations))
        return tuple(int(channel * progress) for channel in self.base_color)

    def step(self) -> bool:
        """Advance once; return True when the zone is mature or extinct."""
        if self.finished:
            return True
        self._grid = self.rule.evolve(self._grid)
        self.current_step += 1
        signature = self._normalized_signature()
        self._signatures.append(signature)

        if signature is None:
            self.status = ZoneStatus.EXTINCT
            self.finish_reason = "extinct"
            return True
        if self.current_step >= self.min_generations:
            self._update_stability_candidate(signature)
            if self._candidate_repeats >= 3:
                self.status = ZoneStatus.MATURE
                self.stable_period = self._candidate_period
                self.finish_reason = "stable"
                return True
        if self.current_step >= self.max_generations:
            self.status = ZoneStatus.MATURE
            self.finish_reason = "max_generations"
            return True
        return False

    def iter_world_cells(self) -> Iterator[Tuple[int, int]]:
        for row, col in np.argwhere(self._grid == 1):
            yield self.start_row + int(row), self.start_col + int(col)

    def commit_coordinates(self) -> Tuple[Tuple[int, int], ...]:
        return tuple(self.iter_world_cells()) if self.status is ZoneStatus.MATURE else ()

    def overlaps(self, other: "EvolutionZone", buffer: int = 1) -> bool:
        if buffer < 0:
            raise ValueError("buffer must be non-negative")
        a0, a1, a2, a3 = self.reserved_rect
        b0, b1, b2, b3 = other.reserved_rect
        return not (
            a2 + buffer <= b0 or b2 + buffer <= a0
            or a3 + buffer <= b1 or b3 + buffer <= a1
        )

    def _normalized_signature(self):
        live = np.argwhere(self._grid == 1)
        if not live.size:
            return None
        top, left = live.min(axis=0)
        bottom, right = live.max(axis=0) + 1
        cropped = np.ascontiguousarray(self._grid[top:bottom, left:right])
        return cropped.shape, cropped.tobytes()

    def _update_stability_candidate(self, signature) -> None:
        if self._candidate_period is not None:
            due = self._candidate_last_step + self._candidate_period
            if self.current_step == due:
                if signature == self._candidate_signature:
                    self._candidate_repeats += 1
                    self._candidate_last_step = self.current_step
                    return
                self._reset_candidate()
            elif self.current_step < due:
                return
            else:
                self._reset_candidate()

        max_period = min(self.stable_period_max, self.current_step)
        for period in range(1, max_period + 1):
            if signature == self._signatures[self.current_step - period]:
                self._candidate_signature = signature
                self._candidate_period = period
                self._candidate_last_step = self.current_step
                self._candidate_repeats = 1
                return

    def _reset_candidate(self) -> None:
        self._candidate_signature = None
        self._candidate_period = None
        self._candidate_last_step = None
        self._candidate_repeats = 0
