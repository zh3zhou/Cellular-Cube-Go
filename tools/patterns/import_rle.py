"""Import explicitly licensed local RLE files into the v2 catalog.

This tool never downloads data. Every input must have a manifest entry with
non-empty provenance and license fields.
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from src.patterns.catalog import (
    CATALOG_SCHEMA_VERSION,
    NON_PUBLISHABLE_LICENSES,
    OPTIONAL_SOURCE_FIELDS,
    REQUIRED_SOURCE_FIELDS,
    CatalogValidationError,
    load_catalog,
    validate_catalog_data,
)
from src.patterns.analysis import analyze_pattern
from src.patterns.rle import encode_rle, geometric_signature, normalize_rule, parse_rle


@dataclass(frozen=True)
class ImportResult:
    source_file: str
    status: str
    pattern_id: str | None
    reason: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "source_file": self.source_file,
            "status": self.status,
            "pattern_id": self.pattern_id,
            "reason": self.reason,
        }


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not result:
        raise ValueError("pattern id becomes empty after slugging")
    return result


def _collect_rle_files(inputs: Iterable[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in inputs:
        if path.is_dir():
            files.update(item for item in path.rglob("*.rle") if item.is_file())
        elif path.is_file() and path.suffix.casefold() == ".rle":
            files.add(path)
    return sorted(files, key=lambda item: str(item).casefold())


def _metadata_for(path: Path, manifest: dict[str, Any]) -> dict[str, Any] | None:
    entries = manifest.get("patterns", {})
    candidates = (str(path).replace("\\", "/"), path.name)
    for key in candidates:
        if key in entries:
            return entries[key]
    return None


def import_rle_files(
    files: Iterable[Path],
    *,
    manifest: dict[str, Any],
    base_catalog: dict[str, Any],
    max_width: int = 108,
    max_height: int = 58,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return updated catalog data and a deterministic per-file report."""
    output = deepcopy(base_catalog)
    results: list[ImportResult] = []
    rulestring_to_id = {
        normalize_rule(rule["rulestring"]): rule_id
        for rule_id, rule in output["rules"].items()
    }
    ids = {item["id"].casefold() for item in output["patterns"]}
    names_by_rule = {
        (rule_id, item["name"].casefold())
        for item in output["patterns"]
        for rule_id in item["rule_ids"]
    }
    signatures = {
        (rule_id, geometric_signature(parse_rle(item["rle"]).cells))
        for item in output["patterns"]
        for rule_id in item["rule_ids"]
    }

    for path in sorted(files, key=lambda item: str(item).casefold()):
        metadata = _metadata_for(path, manifest)
        if metadata is None:
            results.append(ImportResult(str(path), "unknown-license", None, "missing manifest entry"))
            continue
        source = metadata.get("source")
        if not isinstance(source, dict) or any(
            not isinstance(source.get(field), str) or not source[field].strip()
            for field in REQUIRED_SOURCE_FIELDS
        ):
            results.append(
                ImportResult(str(path), "unknown-license", None, "incomplete source metadata")
            )
            continue
        if source["license"].strip().casefold() in NON_PUBLISHABLE_LICENSES:
            results.append(
                ImportResult(
                    str(path),
                    "unknown-license",
                    None,
                    "non-publishable license marker",
                )
            )
            continue
        try:
            parsed = parse_rle(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            results.append(ImportResult(str(path), "invalid", None, str(exc)))
            continue

        rule_ids = metadata.get("rule_ids")
        if not rule_ids:
            inferred = rulestring_to_id.get(parsed.rule)
            rule_ids = [inferred] if inferred else []
        if not rule_ids or any(rule_id not in output["rules"] for rule_id in rule_ids):
            results.append(
                ImportResult(str(path), "invalid", None, "unknown or missing rule mapping")
            )
            continue
        pattern_id = _slug(metadata.get("id") or path.stem)
        name = str(metadata.get("name") or path.stem).strip()
        if pattern_id.casefold() in ids:
            results.append(ImportResult(str(path), "duplicate", pattern_id, "duplicate id"))
            continue
        if any((rule_id, name.casefold()) in names_by_rule for rule_id in rule_ids):
            results.append(
                ImportResult(str(path), "duplicate", pattern_id, "case-insensitive duplicate name")
            )
            continue
        signature = geometric_signature(parsed.cells)
        if any((rule_id, signature) in signatures for rule_id in rule_ids):
            results.append(
                ImportResult(str(path), "duplicate", pattern_id, "geometric duplicate")
            )
            continue

        fits = (
            (parsed.width <= max_width and parsed.height <= max_height)
            or (parsed.height <= max_width and parsed.width <= max_height)
        )
        tier = metadata.get("tier", "standard")
        if tier not in {"standard", "large"}:
            results.append(ImportResult(str(path), "invalid", pattern_id, "invalid tier"))
            continue
        analysis_result = analyze_pattern(parsed.cells, rule_ids[0])
        record = {
            "id": pattern_id,
            "name": name,
            "rule_ids": list(rule_ids),
            "category": metadata.get("category", "other"),
            "width": parsed.width,
            "height": parsed.height,
            "population": sum(sum(row) for row in parsed.cells),
            "rle": encode_rle(parsed.cells, parsed.rule),
            "weight": float(metadata.get("weight", 1.0)),
            "tier": tier,
            "tags": list(metadata.get("tags", [])) + ([] if fits else ["catalog-only"]),
            "source": {
                field: source[field].strip()
                for field in sorted(REQUIRED_SOURCE_FIELDS | OPTIONAL_SOURCE_FIELDS)
                if isinstance(source.get(field), str) and source[field].strip()
            },
            "complexity_score": analysis_result.score,
            "complexity_tier": analysis_result.tier,
            "behavior_tags": list(analysis_result.behavior_tags),
            "analysis": analysis_result.analysis.to_dict(),
            "affinity": "rule-native" if len(rule_ids) == 1 else "polyglot",
        }
        output["patterns"].append(record)
        ids.add(pattern_id.casefold())
        for rule_id in rule_ids:
            names_by_rule.add((rule_id, name.casefold()))
            signatures.add((rule_id, signature))
        status = "imported" if fits else "too-large"
        reason = None if fits else f"does not fit {max_width}x{max_height} in either orientation"
        results.append(ImportResult(str(path), status, pattern_id, reason))

    errors = validate_catalog_data(output)
    if errors:
        raise CatalogValidationError(errors)
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    report = {
        "schema_version": 1,
        "catalog_schema_version": CATALOG_SCHEMA_VERSION,
        "summary": dict(sorted(counts.items())),
        "results": [result.as_dict() for result in results],
    }
    return output, report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Local .rle file or directory")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--catalog", type=Path, default=None)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--max-width", type=int, default=108)
    parser.add_argument("--max-height", type=int, default=58)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    catalog = load_catalog(args.catalog) if args.catalog else load_catalog()
    base_data = {
        "schema_version": catalog.schema_version,
        "rules": dict(catalog.rules),
        "generated": dict(catalog.generated),
        "patterns": [
            {
                "id": item.id,
                "name": item.name,
                "rule_ids": list(item.rule_ids),
                "category": item.category,
                "width": item.width,
                "height": item.height,
                "population": item.population,
                "rle": item.rle,
                "weight": item.weight,
                "tier": item.tier,
                "tags": list(item.tags),
                "source": {
                    "provider": item.source.provider,
                    "url": item.source.url,
                    "version": item.source.version,
                    "external_id": item.source.external_id,
                    "license": item.source.license,
                },
                "complexity_score": item.complexity_score,
                "complexity_tier": item.complexity_tier,
                "behavior_tags": list(item.behavior_tags),
                "analysis": {
                    "analyzer_version": item.analysis.analyzer_version,
                    "measured_generations": item.analysis.measured_generations,
                    "peak_population": item.analysis.peak_population,
                    "peak_area": item.analysis.peak_area,
                    "lifetime": item.analysis.lifetime,
                    "period": item.analysis.period,
                    "displacement": (
                        list(item.analysis.displacement)
                        if item.analysis.displacement is not None
                        else None
                    ),
                    "growth_rate": item.analysis.growth_rate,
                },
                "affinity": item.affinity,
            }
            for item in catalog.patterns
        ],
    }
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    files = _collect_rle_files(args.inputs)
    updated, report = import_rle_files(
        files,
        manifest=manifest,
        base_catalog=base_data,
        max_width=args.max_width,
        max_height=args.max_height,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
