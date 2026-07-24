"""Progress-aware, rule-aware Pattern selection.

The selector is pure Python and deliberately independent from Pygame.  A
``SelectionContext`` freezes the eligible candidates used both by reward
routing and by the subsequent Pattern choice, so a color is never offered for
an empty library.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Mapping, Sequence

from src.patterns.catalog import PatternCatalog, PatternRecord


@dataclass(frozen=True)
class SelectionContext:
    progress: float
    max_width: int
    max_height: int
    complexity_ceiling: float
    target_complexity: float
    large_fraction: float
    candidates: Mapping[str, tuple[PatternRecord, ...]]
    fresh_candidates: Mapping[str, tuple[PatternRecord, ...]]


class PatternSelector:
    """Select Patterns while restoring the original game's variety controls."""

    def __init__(
        self,
        catalog: PatternCatalog,
        *,
        rng: random.Random | None = None,
        history_size: int = 4,
        window_size: int = 200,
    ):
        if history_size < 0 or window_size < 1:
            raise ValueError("history sizes must be non-negative")
        self.catalog = catalog
        self.rng = rng or random.Random()
        self._history_size = history_size
        self._recent: dict[str, deque[str]] = defaultdict(
            lambda: deque(maxlen=self._history_size)
        )
        self._recent_sizes: dict[str, deque[int]] = defaultdict(
            lambda: deque(maxlen=2)
        )
        self._history: dict[str, deque[tuple[str, str]]] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self._pool_cache: dict[
            tuple[str, float, int, int], tuple[PatternRecord, ...]
        ] = {}

    def recent_ids(self, rule_id: str) -> tuple[str, ...]:
        return tuple(self._recent[rule_id])

    @staticmethod
    def normalize_progress(progress: float) -> float:
        return max(0.0, min(1.0, float(progress)))

    def build_context(
        self,
        progress: float,
        *,
        max_width: int,
        max_height: int,
        rule_ids: Sequence[str] | None = None,
    ) -> SelectionContext:
        progress = self.normalize_progress(progress)
        ceiling = 30.0 + 70.0 * progress
        target = 15.0 + 85.0 * progress
        large_fraction = 0.03 + 0.12 * progress
        selected_rules = tuple(rule_ids or self.catalog.rules)
        candidates: dict[str, tuple[PatternRecord, ...]] = {}
        fresh: dict[str, tuple[PatternRecord, ...]] = {}
        for rule_id in selected_rules:
            cache_key = (rule_id, progress, max_width, max_height)
            pool = self._pool_cache.get(cache_key)
            if pool is None:
                pool = tuple(
                    item
                    for item in self.catalog.patterns_for(
                        rule_id, max_width=max_width, max_height=max_height
                    )
                    if item.complexity_score <= ceiling
                )
                self._pool_cache[cache_key] = pool
            recent = set(self._recent[rule_id])
            candidates[rule_id] = pool
            fresh[rule_id] = tuple(item for item in pool if item.id not in recent)
        return SelectionContext(
            progress,
            max_width,
            max_height,
            ceiling,
            target,
            large_fraction,
            candidates,
            fresh,
        )

    def select(
        self,
        rule_id: str,
        *,
        max_width: int,
        max_height: int,
        allow_large: bool = True,
        progress: float = 1.0,
    ) -> PatternRecord | None:
        context = self.build_context(
            progress,
            max_width=max_width,
            max_height=max_height,
            rule_ids=(rule_id,),
        )
        return self.select_from_context(
            rule_id, context, allow_large=allow_large, record=True
        )

    def select_from_context(
        self,
        rule_id: str,
        context: SelectionContext,
        *,
        allow_large: bool = True,
        record: bool = True,
    ) -> PatternRecord | None:
        pool = list(context.candidates.get(rule_id, ()))
        if not allow_large:
            pool = [item for item in pool if item.tier == "standard"]
        if not pool:
            return None

        recent = set(self._recent[rule_id])
        non_recent = [item for item in pool if item.id not in recent]
        if non_recent:
            pool = non_recent
        elif len(pool) > 1 and self._recent[rule_id]:
            previous = self._recent[rule_id][-1]
            pool = [item for item in pool if item.id != previous]

        standard = [item for item in pool if item.tier == "standard"]
        large = [item for item in pool if item.tier == "large"]
        if allow_large and standard and large:
            pool = (
                large
                if self.rng.random() < context.large_fraction
                else standard
            )
        else:
            pool = large or standard
        chosen = self._weighted_choice(rule_id, pool, context.target_complexity)
        if record:
            self.record_choice(rule_id, chosen)
        return chosen

    def record_choice(self, rule_id: str, chosen: PatternRecord) -> None:
        self._recent[rule_id].append(chosen.id)
        self._recent_sizes[rule_id].append(chosen.width * chosen.height)
        self._history[rule_id].append((chosen.id, chosen.category))

    def _weighted_choice(
        self,
        rule_id: str,
        candidates: list[PatternRecord],
        target_complexity: float,
    ) -> PatternRecord:
        category_counts = Counter(category for _, category in self._history[rule_id])
        id_counts = Counter(pattern_id for pattern_id, _ in self._history[rule_id])
        available_categories = {item.category for item in candidates}
        history_total = max(1, len(self._history[rule_id]))
        recent_sizes = tuple(self._recent_sizes[rule_id])
        weights: list[float] = []
        for item in candidates:
            gaussian = math.exp(
                -0.5 * ((item.complexity_score - target_complexity) / 18.0) ** 2
            )
            inverse_frequency = 1.0 / math.sqrt(1.0 + id_counts[item.id])
            observed = category_counts[item.category] / history_total
            category_target = 1.0 / max(1, len(available_categories))
            category_factor = max(
                0.4, 1.0 + (category_target - observed) * 0.6
            )
            size_factor = 1.0
            area = item.width * item.height
            if recent_sizes:
                if area == recent_sizes[-1]:
                    size_factor *= 0.5
                difference = abs(area - recent_sizes[-1]) / max(area, recent_sizes[-1])
                size_factor *= 1.0 + 0.5 * difference
            if len(recent_sizes) > 1 and area == recent_sizes[-2]:
                size_factor *= 0.75
            weights.append(
                max(
                    1e-12,
                    item.weight
                    * gaussian
                    * inverse_frequency
                    * category_factor
                    * size_factor,
                )
            )

        threshold = self.rng.random() * sum(weights)
        cumulative = 0.0
        for item, weight in zip(candidates, weights):
            cumulative += weight
            if threshold <= cumulative:
                return item
        return candidates[-1]
