"""Deterministic, rule-aware weighted pattern selection."""

from __future__ import annotations

import random
from collections import defaultdict, deque

from src.patterns.catalog import PatternCatalog, PatternRecord


class PatternSelector:
    """Select by rule and tier while suppressing the last four per rule."""

    def __init__(
        self,
        catalog: PatternCatalog,
        *,
        rng: random.Random | None = None,
        large_fraction: float = 0.15,
        history_size: int = 4,
    ):
        if not 0.0 <= large_fraction <= 1.0:
            raise ValueError("large_fraction must be between 0 and 1")
        if history_size < 0:
            raise ValueError("history_size cannot be negative")
        self.catalog = catalog
        self.rng = rng or random.Random()
        self.large_fraction = large_fraction
        self._history_size = history_size
        self._recent: dict[str, deque[str]] = defaultdict(
            lambda: deque(maxlen=self._history_size)
        )

    def recent_ids(self, rule_id: str) -> tuple[str, ...]:
        return tuple(self._recent[rule_id])

    def select(
        self,
        rule_id: str,
        *,
        max_width: int,
        max_height: int,
        allow_large: bool = True,
    ) -> PatternRecord | None:
        if max_width <= 0 or max_height <= 0:
            return None
        candidates = self.catalog.patterns_for(
            rule_id, max_width=max_width, max_height=max_height
        )
        if not allow_large:
            candidates = tuple(item for item in candidates if item.tier == "standard")
        if not candidates:
            return None
        standard = [item for item in candidates if item.tier == "standard"]
        large = [item for item in candidates if item.tier == "large"]
        if standard and large:
            tier_candidates = large if self.rng.random() < self.large_fraction else standard
        else:
            tier_candidates = large or standard

        recent = set(self._recent[rule_id])
        non_recent = [item for item in tier_candidates if item.id not in recent]
        if non_recent:
            tier_candidates = non_recent
        elif len(tier_candidates) > 1 and self._recent[rule_id]:
            # A small rule library cannot always satisfy a four-item cooldown,
            # but it should still never repeat immediately when an alternative
            # exists.
            previous = self._recent[rule_id][-1]
            tier_candidates = [item for item in tier_candidates if item.id != previous]
        chosen = self._weighted_choice(tier_candidates)
        self._recent[rule_id].append(chosen.id)
        return chosen

    def _weighted_choice(self, candidates: list[PatternRecord]) -> PatternRecord:
        total = sum(item.weight for item in candidates)
        threshold = self.rng.random() * total
        cumulative = 0.0
        for item in candidates:
            cumulative += item.weight
            if threshold <= cumulative:
                return item
        return candidates[-1]
