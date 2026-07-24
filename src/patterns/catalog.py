"""Versioned, validated runtime catalog for rule-aware patterns."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.core.rules import NEIGHBORHOODS
from src.patterns.analysis import (
    ANALYZER_VERSION,
    BEHAVIOR_TAGS,
    MEASURED_GENERATIONS,
    complexity_tier,
)
from src.patterns.rle import RLEError, geometric_signature, normalize_rule, parse_rle


CATALOG_SCHEMA_VERSION = 3
DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "patterns" / "catalog.v3.json"
)
REQUIRED_PATTERN_FIELDS = frozenset(
    {
        "id",
        "name",
        "rule_ids",
        "category",
        "width",
        "height",
        "population",
        "rle",
        "weight",
        "tier",
        "tags",
        "source",
        "complexity_score",
        "complexity_tier",
        "behavior_tags",
        "analysis",
        "affinity",
    }
)
REQUIRED_SOURCE_FIELDS = frozenset(
    {"provider", "url", "version", "external_id", "license"}
)
OPTIONAL_SOURCE_FIELDS = frozenset(
    {"license_uri", "attribution", "changes", "content_sha256"}
)
NON_PUBLISHABLE_LICENSES = frozenset(
    {
        "unknown",
        "unknown-license",
        "unclear",
        "unlicensed",
        "unspecified",
        "none",
        "n/a",
        "pending",
        "tbd",
        "to-be-determined",
    }
)


class CatalogValidationError(ValueError):
    """Raised when a catalog violates the versioned data contract."""

    def __init__(self, errors: Iterable[str]):
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


@dataclass(frozen=True)
class PatternSource:
    provider: str
    url: str
    version: str
    external_id: str
    license: str


@dataclass(frozen=True)
class PatternAnalysisRecord:
    analyzer_version: str
    measured_generations: int
    peak_population: int
    peak_area: int
    lifetime: int | None
    period: int | None
    displacement: tuple[int, int] | None
    growth_rate: float


@dataclass(frozen=True)
class PatternRecord:
    id: str
    name: str
    rule_ids: tuple[str, ...]
    category: str
    width: int
    height: int
    population: int
    rle: str
    weight: float
    tier: str
    tags: tuple[str, ...]
    source: PatternSource
    complexity_score: float
    complexity_tier: int
    behavior_tags: tuple[str, ...]
    analysis: PatternAnalysisRecord
    affinity: str
    cells: tuple[tuple[int, ...], ...]

    @property
    def pattern(self) -> list[list[int]]:
        """Return a mutable matrix for an EvolutionZone."""
        return [list(row) for row in self.cells]

    def to_matrix(self) -> list[list[int]]:
        """Return a mutable copy suitable for an EvolutionZone."""
        return self.pattern


# Product-facing name; PatternRecord remains for compatibility with early callers.
PatternDefinition = PatternRecord


@dataclass
class PatternCatalog:
    schema_version: int
    rules: Mapping[str, Mapping[str, Any]]
    generated: Mapping[str, Any]
    patterns: tuple[PatternRecord, ...]

    def __post_init__(self) -> None:
        self._selectors: dict[tuple[int, bool], Any] = {}

    @classmethod
    def load_default(cls) -> "PatternCatalog":
        return load_catalog()

    def patterns_for(
        self,
        rule_id: str,
        *,
        max_width: int | None = None,
        max_height: int | None = None,
        tier: str | None = None,
    ) -> tuple[PatternRecord, ...]:
        return tuple(
            pattern
            for pattern in self.patterns
            if rule_id in pattern.rule_ids
            and (
                (
                    (max_width is None or pattern.width <= max_width)
                    and (max_height is None or pattern.height <= max_height)
                )
                or (
                    (max_width is None or pattern.height <= max_width)
                    and (max_height is None or pattern.width <= max_height)
                )
            )
            and (tier is None or pattern.tier == tier)
        )

    def by_id(self, pattern_id: str) -> PatternRecord:
        for pattern in self.patterns:
            if pattern.id == pattern_id:
                return pattern
        raise KeyError(pattern_id)

    def select(
        self,
        rule_id: str,
        rng: random.Random,
        *,
        allow_large: bool = True,
        max_width: int = 108,
        max_height: int = 58,
    ) -> PatternDefinition | None:
        """Convenience selection API with history retained per RNG instance."""
        from src.patterns.selector import PatternSelector

        key = (id(rng), allow_large)
        selector = self._selectors.get(key)
        if selector is None or selector.rng is not rng:
            selector = PatternSelector(self, rng=rng)
            self._selectors[key] = selector
        return selector.select(
            rule_id,
            max_width=max_width,
            max_height=max_height,
            allow_large=allow_large,
            progress=1.0,
        )


def _text(value: Any, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return ""
    return value.strip()


def validate_catalog_data(data: Any) -> tuple[str, ...]:
    """Return all catalog errors without mutating or partially accepting data."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ("catalog root must be an object",)
    if data.get("schema_version") != CATALOG_SCHEMA_VERSION:
        errors.append(f"schema_version must be {CATALOG_SCHEMA_VERSION}")
    rules = data.get("rules")
    if not isinstance(rules, dict) or not rules:
        errors.append("rules must be a non-empty object")
        rules = {}
    else:
        for rule_id, rule in rules.items():
            if not isinstance(rule, dict):
                errors.append(f"rules.{rule_id} must be an object")
                continue
            _text(rule.get("name"), f"rules.{rule_id}.name", errors)
            try:
                normalize_rule(rule.get("rulestring"))
            except RLEError as exc:
                errors.append(f"rules.{rule_id}.rulestring: {exc}")
            neighborhood_id = _text(
                rule.get("neighborhood_id"),
                f"rules.{rule_id}.neighborhood_id",
                errors,
            )
            if neighborhood_id and neighborhood_id not in NEIGHBORHOODS:
                errors.append(
                    f"rules.{rule_id}.neighborhood_id is unknown: "
                    f"{neighborhood_id!r}"
                )
    if not isinstance(data.get("generated"), dict):
        errors.append("generated must be an object")
    patterns = data.get("patterns")
    if not isinstance(patterns, list) or not patterns:
        errors.append("patterns must be a non-empty array")
        return tuple(errors)

    ids: set[str] = set()
    casefolded_ids: set[str] = set()
    signatures: dict[tuple[str, str], str] = {}
    names: set[tuple[str, str]] = set()
    for index, item in enumerate(patterns):
        label = f"patterns[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = REQUIRED_PATTERN_FIELDS - item.keys()
        if missing:
            errors.append(f"{label} missing fields: {', '.join(sorted(missing))}")
            continue
        pattern_id = _text(item["id"], f"{label}.id", errors)
        if pattern_id in ids:
            errors.append(f"{label}.id duplicates {pattern_id!r}")
        if pattern_id.casefold() in casefolded_ids:
            errors.append(f"{label}.id is a case-insensitive duplicate: {pattern_id!r}")
        ids.add(pattern_id)
        casefolded_ids.add(pattern_id.casefold())
        _text(item["name"], f"{label}.name", errors)
        _text(item["category"], f"{label}.category", errors)
        rule_ids = item["rule_ids"]
        if not isinstance(rule_ids, list) or not rule_ids:
            errors.append(f"{label}.rule_ids must be a non-empty array")
            rule_ids = []
        for rule_id in rule_ids:
            if rule_id not in rules:
                errors.append(f"{label}.rule_ids references unknown rule {rule_id!r}")
            name_key = (rule_id, str(item["name"]).casefold())
            if name_key in names:
                errors.append(
                    f"{label}.name is a case-insensitive duplicate for {rule_id}: "
                    f"{item['name']!r}"
                )
            names.add(name_key)
        if item["tier"] not in {"standard", "large"}:
            errors.append(f"{label}.tier must be standard or large")
        score = item["complexity_score"]
        if (
            not isinstance(score, (int, float))
            or isinstance(score, bool)
            or not 0 <= score <= 100
        ):
            errors.append(f"{label}.complexity_score must be between 0 and 100")
        tier_value = item["complexity_tier"]
        if not isinstance(tier_value, int) or isinstance(tier_value, bool):
            errors.append(f"{label}.complexity_tier must be an integer from 1 to 5")
        elif not 1 <= tier_value <= 5:
            errors.append(f"{label}.complexity_tier must be an integer from 1 to 5")
        elif isinstance(score, (int, float)) and not isinstance(score, bool):
            if tier_value != complexity_tier(float(score)):
                errors.append(
                    f"{label}.complexity_tier does not match complexity_score"
                )
        if not isinstance(item["tags"], list) or any(
            not isinstance(tag, str) or not tag for tag in item["tags"]
        ):
            errors.append(f"{label}.tags must be an array of non-empty strings")
        behavior_tags = item["behavior_tags"]
        if (
            not isinstance(behavior_tags, list)
            or not behavior_tags
            or any(tag not in BEHAVIOR_TAGS for tag in behavior_tags)
        ):
            errors.append(
                f"{label}.behavior_tags must use the controlled behavior vocabulary"
            )
        if item["affinity"] not in {"rule-native", "polyglot"}:
            errors.append(f"{label}.affinity must be rule-native or polyglot")
        elif len(rule_ids) > 1 and item["affinity"] != "polyglot":
            errors.append(
                f"{label}.affinity must be polyglot for multiple rule_ids"
            )
        analysis = item["analysis"]
        required_analysis = {
            "analyzer_version",
            "measured_generations",
            "peak_population",
            "peak_area",
            "lifetime",
            "period",
            "displacement",
            "growth_rate",
        }
        if not isinstance(analysis, dict):
            errors.append(f"{label}.analysis must be an object")
        else:
            missing_analysis = required_analysis - analysis.keys()
            if missing_analysis:
                errors.append(
                    f"{label}.analysis missing fields: "
                    f"{', '.join(sorted(missing_analysis))}"
                )
            if analysis.get("analyzer_version") != ANALYZER_VERSION:
                errors.append(
                    f"{label}.analysis.analyzer_version must be {ANALYZER_VERSION}"
                )
            if analysis.get("measured_generations") != MEASURED_GENERATIONS:
                errors.append(
                    f"{label}.analysis.measured_generations must be "
                    f"{MEASURED_GENERATIONS}"
                )
            for field in ("measured_generations", "peak_population", "peak_area"):
                value = analysis.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"{label}.analysis.{field} must be non-negative")
            for field in ("lifetime", "period"):
                value = analysis.get(field)
                if value is not None and (
                    not isinstance(value, int)
                    or isinstance(value, bool)
                    or value < 1
                ):
                    errors.append(
                        f"{label}.analysis.{field} must be null or a positive integer"
                    )
            displacement = analysis.get("displacement")
            if displacement is not None and (
                not isinstance(displacement, list)
                or len(displacement) != 2
                or any(
                    not isinstance(value, int) or isinstance(value, bool)
                    for value in displacement
                )
            ):
                errors.append(
                    f"{label}.analysis.displacement must be null or [row, col]"
                )
            growth_rate = analysis.get("growth_rate")
            if (
                not isinstance(growth_rate, (int, float))
                or isinstance(growth_rate, bool)
                or growth_rate < 0
            ):
                errors.append(
                    f"{label}.analysis.growth_rate must be non-negative"
                )
        if not isinstance(item["weight"], (int, float)) or item["weight"] <= 0:
            errors.append(f"{label}.weight must be positive")
        source = item["source"]
        if not isinstance(source, dict):
            errors.append(f"{label}.source must be an object")
        else:
            missing_source = REQUIRED_SOURCE_FIELDS - source.keys()
            if missing_source:
                errors.append(
                    f"{label}.source missing fields: {', '.join(sorted(missing_source))}"
                )
            for field in REQUIRED_SOURCE_FIELDS:
                _text(source.get(field), f"{label}.source.{field}", errors)
            for field in OPTIONAL_SOURCE_FIELDS & source.keys():
                _text(source.get(field), f"{label}.source.{field}", errors)
            digest = source.get("content_sha256")
            if isinstance(digest, str) and not re.fullmatch(
                r"[0-9a-f]{64}", digest
            ):
                errors.append(
                    f"{label}.source.content_sha256 must be a lowercase SHA-256"
                )
            license_name = source.get("license")
            if (
                isinstance(license_name, str)
                and license_name.strip().casefold() in NON_PUBLISHABLE_LICENSES
            ):
                errors.append(
                    f"{label}.source.license must identify a redistributable license"
                )
        try:
            parsed = parse_rle(item["rle"])
        except (RLEError, TypeError) as exc:
            errors.append(f"{label}.rle: {exc}")
            continue
        assigned_rulestrings = {
            normalize_rule(rules[rule_id]["rulestring"])
            for rule_id in rule_ids
            if rule_id in rules
        }
        if parsed.rule and parsed.rule not in assigned_rulestrings:
            errors.append(
                f"{label}.rle rule {parsed.rule} does not match assigned rule_ids"
            )
        if parsed.width != item["width"] or parsed.height != item["height"]:
            errors.append(
                f"{label} dimensions say {item['width']}x{item['height']} "
                f"but RLE is {parsed.width}x{parsed.height}"
            )
        population = sum(sum(row) for row in parsed.cells)
        if population != item["population"]:
            errors.append(
                f"{label}.population says {item['population']} but RLE has {population}"
            )
        for rule_id in rule_ids:
            key = (rule_id, geometric_signature(parsed.cells))
            if key in signatures:
                errors.append(
                    f"{label} geometrically duplicates {signatures[key]!r} for {rule_id}"
                )
            else:
                signatures[key] = pattern_id
    return tuple(errors)


def load_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> PatternCatalog:
    """Load a catalog atomically; invalid entries are never silently skipped."""
    catalog_path = Path(path)
    try:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogValidationError((f"cannot load {catalog_path}: {exc}",)) from exc
    errors = validate_catalog_data(data)
    if errors:
        raise CatalogValidationError(errors)
    records: list[PatternRecord] = []
    for item in data["patterns"]:
        parsed = parse_rle(item["rle"])
        source = item["source"]
        analysis = item["analysis"]
        displacement = analysis["displacement"]
        records.append(
            PatternRecord(
                id=item["id"],
                name=item["name"],
                rule_ids=tuple(item["rule_ids"]),
                category=item["category"],
                width=item["width"],
                height=item["height"],
                population=item["population"],
                rle=item["rle"],
                weight=float(item["weight"]),
                tier=item["tier"],
                tags=tuple(item["tags"]),
                source=PatternSource(
                    provider=source["provider"],
                    url=source["url"],
                    version=source["version"],
                    external_id=source["external_id"],
                    license=source["license"],
                ),
                complexity_score=float(item["complexity_score"]),
                complexity_tier=item["complexity_tier"],
                behavior_tags=tuple(item["behavior_tags"]),
                analysis=PatternAnalysisRecord(
                    analyzer_version=analysis["analyzer_version"],
                    measured_generations=analysis["measured_generations"],
                    peak_population=analysis["peak_population"],
                    peak_area=analysis["peak_area"],
                    lifetime=analysis["lifetime"],
                    period=analysis["period"],
                    displacement=(
                        tuple(displacement) if displacement is not None else None
                    ),
                    growth_rate=float(analysis["growth_rate"]),
                ),
                affinity=item["affinity"],
                cells=parsed.cells,
            )
        )
    return PatternCatalog(
        schema_version=data["schema_version"],
        rules=data["rules"],
        generated=data["generated"],
        patterns=tuple(records),
    )
