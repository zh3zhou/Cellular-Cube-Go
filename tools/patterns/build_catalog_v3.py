"""Build the annotated v3 runtime catalog from the licensed v2 snapshot.

The command is deterministic and performs no network access. Existing licensed
entries are retained, measured with the versioned complexity analyzer, and
small project-generated seeds fill rule libraries that have fewer than twenty
playable geometrically unique entries.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np

from src.core.rules import RULES
from src.patterns.analysis import BEHAVIOR_TAGS, analyze_pattern
from src.patterns.rle import (
    encode_rle,
    geometric_signature,
    parse_rle,
    trim_cells,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "assets" / "patterns" / "catalog.v2.json"
OUTPUT_PATH = ROOT / "assets" / "patterns" / "catalog.v3.json"
REPORT_PATH = ROOT / "assets" / "patterns" / "import-report.v3.json"
GENERATOR_VERSION = "complexity-search-v1"
GENERATOR_SEED = 20260724
TARGET_PLAYABLE_PER_SECONDARY_RULE = 20
SECONDARY_RULES = (
    "highlife",
    "seeds",
    "day_night",
    "wolfram_code_52",
)


def _rule_seed(rule_id: str) -> int:
    return GENERATOR_SEED + SECONDARY_RULES.index(rule_id) * 1009


def _merge_behavior_tags(category: str, measured: tuple[str, ...]) -> list[str]:
    tags = set(measured)
    category_tag = {
        "still_life": "stable",
        "oscillator": "oscillator",
        "oscillator_seed": "oscillator",
        "spaceship": "spaceship",
        "replicator": "replicator",
        "growth_seed": "expanding",
        "methuselah": "localized",
        "gun": "localized",
    }.get(category)
    if category_tag in BEHAVIOR_TAGS:
        tags.add(category_tag)
    return sorted(tags)


def _annotate(item: dict) -> dict:
    parsed = parse_rle(item["rle"])
    result = analyze_pattern(parsed.cells, item["rule_ids"][0])
    annotated = dict(item)
    annotated.update(
        {
            "complexity_score": result.score,
            "complexity_tier": result.tier,
            "behavior_tags": _merge_behavior_tags(
                item["category"], result.behavior_tags
            ),
            "analysis": result.analysis.to_dict(),
            "affinity": "rule-native",
        }
    )
    return annotated


def _category(tags: tuple[str, ...]) -> str:
    tag_set = set(tags)
    if "spaceship" in tag_set:
        return "spaceship"
    if "oscillator" in tag_set:
        return "oscillator"
    if "replicator" in tag_set:
        return "replicator"
    if "stable" in tag_set:
        return "still_life"
    if tag_set.intersection({"expanding", "explosive"}):
        return "growth_seed"
    return "project_seed"


def _candidate_matrix(rng: random.Random) -> tuple[tuple[int, ...], ...]:
    height = rng.randint(3, 11)
    width = rng.randint(3, 11)
    density = rng.uniform(0.18, 0.48)
    cells = [
        [int(rng.random() < density) for _ in range(width)]
        for _ in range(height)
    ]
    if sum(map(sum, cells)) < 3:
        for _ in range(3):
            cells[rng.randrange(height)][rng.randrange(width)] = 1
    return trim_cells(cells)


def _generated_item(
    rule_id: str,
    cells: tuple[tuple[int, ...], ...],
    index: int,
    result,
) -> dict:
    rule = RULES[rule_id]
    rle = encode_rle(cells, rule.rulestring)
    digest = hashlib.sha256(rle.encode("utf-8")).hexdigest()
    short_name = {
        "highlife": "HighLife",
        "seeds": "Seeds",
        "day_night": "Day & Night",
        "wolfram_code_52": "Code 52",
    }[rule_id]
    pattern_id = f"generated-{rule_id.replace('_', '-')}-{index:03d}"
    return {
        "id": pattern_id,
        "name": f"{short_name} generated seed {index:03d}",
        "rule_ids": [rule_id],
        "category": _category(result.behavior_tags),
        "width": len(cells[0]),
        "height": len(cells),
        "population": sum(map(sum, cells)),
        "rle": rle,
        "weight": 0.75,
        "tier": "standard",
        "tags": [
            "deterministic-search",
            GENERATOR_VERSION,
            rule_id,
        ],
        "source": {
            "provider": "cellular-cube-go-generator",
            "url": (
                "https://github.com/zh3zhou/Cellular-Cube-Go/"
                "blob/main/tools/patterns/build_catalog_v3.py"
            ),
            "version": GENERATOR_VERSION,
            "generator_seed": _rule_seed(rule_id),
            "external_id": pattern_id,
            "license": "MIT",
            "license_uri": (
                "https://github.com/zh3zhou/Cellular-Cube-Go/blob/main/LICENSE"
            ),
            "attribution": "Cellular Cube Go deterministic Pattern search",
            "changes": "Generated and measured without external Pattern data",
            "content_sha256": digest,
        },
        "complexity_score": result.score,
        "complexity_tier": result.tier,
        "behavior_tags": list(result.behavior_tags),
        "analysis": result.analysis.to_dict(),
        "affinity": "rule-native",
    }


def _generate_fillers(
    patterns: list[dict],
    report: dict,
) -> None:
    signatures: dict[str, set[str]] = {
        rule_id: set() for rule_id in SECONDARY_RULES
    }
    for item in patterns:
        signature = geometric_signature(parse_rle(item["rle"]).cells)
        for rule_id in item["rule_ids"]:
            if rule_id in signatures:
                signatures[rule_id].add(signature)

    for rule_id in SECONDARY_RULES:
        existing = [
            item
            for item in patterns
            if rule_id in item["rule_ids"]
            and (
                (item["width"] <= 108 and item["height"] <= 58)
                or (item["height"] <= 108 and item["width"] <= 58)
            )
        ]
        needed = max(0, TARGET_PLAYABLE_PER_SECONDARY_RULE - len(existing))
        rng = random.Random(_rule_seed(rule_id))
        accepted = 0
        attempts = 0
        rejections = Counter()
        while accepted < needed and attempts < 10_000:
            attempts += 1
            cells = _candidate_matrix(rng)
            if not cells:
                rejections["invalid"] += 1
                continue
            signature = geometric_signature(cells)
            if signature in signatures[rule_id]:
                rejections["duplicate"] += 1
                continue
            result = analyze_pattern(cells, rule_id)
            if (
                result.analysis.lifetime is not None
                and result.analysis.lifetime < 6
            ):
                rejections["low-interest"] += 1
                continue
            if result.analysis.growth_rate > 64:
                rejections["performance-rejected"] += 1
                continue
            accepted += 1
            signatures[rule_id].add(signature)
            patterns.append(
                _generated_item(
                    rule_id,
                    cells,
                    len(existing) + accepted,
                    result,
                )
            )
        if accepted < needed:
            raise RuntimeError(
                f"Could only generate {accepted} of {needed} fillers for {rule_id}"
            )
        report["generated"][rule_id] = {
            "existing": len(existing),
            "target": TARGET_PLAYABLE_PER_SECONDARY_RULE,
            "accepted": accepted,
            "attempts": attempts,
            "rejections": dict(sorted(rejections.items())),
        }


def build_catalog() -> tuple[dict, dict]:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    patterns = []
    report = {
        "schema_version": 3,
        "source": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "analyzed": 0,
        "generated": {},
        "legacy_unpublished": {
            "source": "assets/patterns/library.json@86aaf6c",
            "entries": 109,
            "case_insensitive_unique_names": 55,
            "outcome": "unknown-license",
            "reason": (
                "The historical bulk library has no per-entry source or "
                "redistribution license and is therefore intentionally absent "
                "from the publishable runtime catalog."
            ),
        },
        "summary": {},
    }
    for item in source["patterns"]:
        patterns.append(_annotate(item))
        report["analyzed"] += 1

    _generate_fillers(patterns, report)
    rules = {
        rule_id: {
            "name": rule.name,
            "rulestring": rule.rulestring,
            "neighborhood_id": rule.neighborhood.id,
        }
        for rule_id, rule in RULES.items()
    }
    generated = dict(source["generated"])
    generated.update(
        {
            "format": "annotated-rule-aware-rle-catalog",
            "version": "2026-07-24-v3",
            "generated_at": "2026-07-24",
            "analyzer_version": "1.0",
            "generator_version": GENERATOR_VERSION,
            "generator_seed": GENERATOR_SEED,
            "note": (
                "Licensed v2 entries annotated by deterministic simulation; "
                "small secondary libraries are filled by project-generated seeds."
            ),
        }
    )
    catalog = {
        "schema_version": 3,
        "rules": rules,
        "generated": generated,
        "patterns": sorted(patterns, key=lambda item: item["id"]),
    }
    report["summary"] = {
        rule_id: sum(rule_id in item["rule_ids"] for item in patterns)
        for rule_id in rules
    }
    report["summary"]["total"] = len(patterns)
    return catalog, report


def main() -> int:
    catalog, report = build_catalog()
    OUTPUT_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
