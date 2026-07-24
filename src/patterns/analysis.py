"""Deterministic offline measurements for catalog Pattern complexity."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import log1p
from typing import Iterable

import numpy as np

from src.core.rules import RuleSpec, get_rule


ANALYZER_VERSION = "1.0"
MEASURED_GENERATIONS = 256
BEHAVIOR_TAGS = frozenset(
    {
        "stable",
        "oscillator",
        "spaceship",
        "replicator",
        "localized",
        "expanding",
        "explosive",
        "extinct",
    }
)


@dataclass(frozen=True)
class PatternAnalysis:
    analyzer_version: str
    measured_generations: int
    peak_population: int
    peak_area: int
    lifetime: int | None
    period: int | None
    displacement: tuple[int, int] | None
    growth_rate: float

    def to_dict(self) -> dict:
        data = asdict(self)
        if self.displacement is not None:
            data["displacement"] = list(self.displacement)
        return data


@dataclass(frozen=True)
class ComplexityResult:
    score: float
    tier: int
    behavior_tags: tuple[str, ...]
    analysis: PatternAnalysis


def complexity_tier(score: float) -> int:
    """Map an absolute 0..100 score to one of five stable bands."""
    return min(5, max(1, int(float(score) // 20) + 1))


def _live_bounds(state: np.ndarray):
    live = np.argwhere(state == 1)
    if not live.size:
        return None
    top, left = live.min(axis=0)
    bottom, right = live.max(axis=0) + 1
    return (
        int(top),
        int(left),
        int(bottom),
        int(right),
        int(live.shape[0]),
    )


def _signature(state: np.ndarray, bounds) -> tuple[tuple[int, int], bytes] | None:
    if bounds is None:
        return None
    top, left, bottom, right, _ = bounds
    cropped = np.ascontiguousarray(state[top:bottom, left:right])
    return cropped.shape, cropped.tobytes()


def analyze_pattern(
    cells: Iterable[Iterable[int]],
    rule: str | RuleSpec,
    *,
    generations: int = MEASURED_GENERATIONS,
    margin: int = 16,
) -> ComplexityResult:
    """Measure one seed without mutating the input or using Pygame.

    The analysis arena grows with the input and uses the same hard boundary
    semantics as an EvolutionZone. The score is a project-specific gameplay
    measure, not a claim that one Pattern belongs to a formal Wolfram class.
    """
    seed = np.asarray(cells, dtype=np.uint8)
    if seed.ndim != 2 or not seed.size or np.any(seed > 1):
        raise ValueError("cells must be a non-empty binary matrix")
    if generations < 1 or margin < 1:
        raise ValueError("generations and margin must be positive")
    resolved_rule = get_rule(rule)

    height = max(seed.shape[0] + margin * 2, 64)
    width = max(seed.shape[1] + margin * 2, 96)
    state = np.zeros((height, width), dtype=np.uint8)
    row = (height - seed.shape[0]) // 2
    col = (width - seed.shape[1]) // 2
    state[row:row + seed.shape[0], col:col + seed.shape[1]] = seed

    initial_bounds = _live_bounds(state)
    if initial_bounds is None:
        raise ValueError("cells must contain at least one live cell")
    initial_population = initial_bounds[4]
    initial_area = (
        (initial_bounds[2] - initial_bounds[0])
        * (initial_bounds[3] - initial_bounds[1])
    )
    peak_population = initial_population
    peak_area = initial_area
    populations = [initial_population]
    areas = [initial_area]
    seen = {
        _signature(state, initial_bounds): (
            0,
            initial_bounds[0],
            initial_bounds[1],
        )
    }
    lifetime: int | None = None
    period: int | None = None
    displacement: tuple[int, int] | None = None
    touched_boundary = False

    for step in range(1, generations + 1):
        state = resolved_rule.evolve(state)
        bounds = _live_bounds(state)
        if bounds is None:
            lifetime = step
            populations.append(0)
            areas.append(0)
            break
        top, left, bottom, right, population = bounds
        area = (bottom - top) * (right - left)
        populations.append(population)
        areas.append(area)
        peak_population = max(peak_population, population)
        peak_area = max(peak_area, area)
        if top == 0 or left == 0 or bottom == height or right == width:
            touched_boundary = True

        signature = _signature(state, bounds)
        previous = seen.get(signature)
        if previous is not None:
            previous_step, previous_top, previous_left = previous
            period = step - previous_step
            displacement = (top - previous_top, left - previous_left)
            break
        seen[signature] = (step, top, left)
        if touched_boundary:
            break

    growth_rate = peak_population / max(1, initial_population)
    population_range = max(populations) - min(populations)
    area_range = max(areas) - min(areas)
    dynamism = 0.5 * (
        population_range / max(1, peak_population)
        + area_range / max(1, peak_area)
    )
    observed_steps = len(populations) - 1
    longevity = observed_steps / generations
    scale = 0.5 * (
        min(1.0, log1p(initial_population) / log1p(128))
        + min(1.0, log1p(initial_area) / log1p(1024))
    )
    growth_extent = min(1.0, max(0.0, growth_rate - 1.0) / 15.0)

    tags: set[str] = set()
    structure = 0.0
    if lifetime is not None:
        tags.add("extinct")
    elif period == 1 and displacement == (0, 0):
        tags.update(("stable", "localized"))
        structure = 0.35
    elif period is not None and displacement == (0, 0):
        tags.update(("oscillator", "localized"))
        structure = min(0.75, 0.45 + period / 64)
    elif period is not None:
        tags.add("spaceship")
        structure = 0.9
    elif touched_boundary or growth_rate >= 8:
        tags.add("expanding")
        structure = 0.8
    else:
        tags.add("localized")
        structure = 0.55
    if growth_rate >= 4 and period is None:
        tags.add("replicator")
        structure = max(structure, 0.85)
    if growth_rate >= 10 or dynamism >= 0.8:
        tags.add("explosive")

    score = round(
        min(
            100.0,
            20 * scale
            + 25 * longevity
            + 25 * min(1.0, dynamism)
            + 20 * structure
            + 10 * growth_extent,
        ),
        3,
    )
    analysis = PatternAnalysis(
        analyzer_version=ANALYZER_VERSION,
        measured_generations=generations,
        peak_population=int(peak_population),
        peak_area=int(peak_area),
        lifetime=lifetime,
        period=period,
        displacement=displacement,
        growth_rate=round(float(growth_rate), 6),
    )
    return ComplexityResult(
        score=score,
        tier=complexity_tier(score),
        behavior_tags=tuple(sorted(tags)),
        analysis=analysis,
    )
