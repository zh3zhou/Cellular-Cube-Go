"""One-time deterministic migration of the project's Python pattern literals.

The source revision is pinned so this maintenance helper does not pull network
content or accidentally treat the unverified scraped JSON as project-owned.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from src.patterns.catalog import DEFAULT_CATALOG_PATH, validate_catalog_data
from src.patterns.rle import encode_rle, geometric_signature, trim_cells


PINNED_SOURCE_REVISION = "f513f63"
SOURCE_PATH = "src/patterns/pattern_library.py"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")


def _category(name: str) -> str:
    folded = name.casefold()
    groups = (
        ("gun", ("gun",)),
        ("spaceship", ("glider", "lwss", "spaceship", "copperhead", "weekender")),
        ("oscillator", ("blinker", "pulsar", "toad", "beacon", "clock", "galaxy", "pentadecathlon")),
        ("still_life", ("block", "beehive", "loaf", "boat", "tub", "barge", "pond", "snake")),
        ("methuselah", ("acorn", "diehard", "pentomino")),
    )
    for category, keywords in groups:
        if any(keyword in folded for keyword in keywords):
            return category
    return "project_seed"


def _literal_patterns(source: str) -> dict[tuple[int, int], dict[str, Any]]:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_initialize_patterns":
            for statement in node.body:
                if isinstance(statement, ast.Return):
                    return ast.literal_eval(statement.value)
    raise ValueError("could not find _initialize_patterns return literal")


def migrate(catalog: dict[str, Any], patterns: dict[tuple[int, int], dict[str, Any]]) -> int:
    known_ids = {item["id"].casefold() for item in catalog["patterns"]}
    known_names = {
        item["name"].casefold()
        for item in catalog["patterns"]
        if "life" in item["rule_ids"]
    }
    known_signatures = {
        geometric_signature(trim_cells(parse_matrix(item["rle"])))
        for item in catalog["patterns"]
        if "life" in item["rule_ids"]
    }
    added = 0
    for _, named_patterns in patterns.items():
        for name, info in named_patterns.items():
            cells = trim_cells(info["pattern"])
            if not cells:
                continue
            signature = geometric_signature(cells)
            pattern_id = f"life-{_slug(name)}"
            display_name = name.replace("_", " ").title()
            if (
                pattern_id.casefold() in known_ids
                or display_name.casefold() in known_names
                or signature in known_signatures
            ):
                continue
            height = len(cells)
            width = len(cells[0])
            fits = (width <= 108 and height <= 58) or (height <= 108 and width <= 58)
            catalog["patterns"].append(
                {
                    "id": pattern_id,
                    "name": display_name,
                    "rule_ids": ["life"],
                    "category": _category(name),
                    "width": width,
                    "height": height,
                    "population": sum(map(sum, cells)),
                    "rle": encode_rle(cells, "B3/S23"),
                    "weight": float(info.get("probability", 0.2)),
                    "tier": "large" if width * height > 64 else "standard",
                    "tags": ["legacy-built-in"] + ([] if fits else ["catalog-only"]),
                    "source": {
                        "provider": "cellular-cube-go",
                        "url": (
                            "https://github.com/zh3zhou/Cellular-Cube-Go/blob/"
                            f"{PINNED_SOURCE_REVISION}/{SOURCE_PATH}"
                        ),
                        "version": PINNED_SOURCE_REVISION,
                        "external_id": name,
                        "license": "MIT",
                    },
                }
            )
            known_ids.add(pattern_id.casefold())
            known_names.add(display_name.casefold())
            known_signatures.add(signature)
            added += 1
    catalog["patterns"].sort(key=lambda item: item["id"])
    migrated_total = sum(
        item["source"].get("version") == PINNED_SOURCE_REVISION
        for item in catalog["patterns"]
    )
    catalog["generated"]["legacy_migration"] = {
        "source_revision": PINNED_SOURCE_REVISION,
        "source_path": SOURCE_PATH,
        "unique_patterns": migrated_total,
    }
    return added


def parse_matrix(rle: str) -> tuple[tuple[int, ...], ...]:
    # Local import keeps the migration's AST/provenance path obvious above.
    from src.patterns.rle import parse_rle

    return parse_rle(rle).cells


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG_PATH)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    source = subprocess.run(
        ["git", "show", f"{PINNED_SOURCE_REVISION}:{SOURCE_PATH}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    added = migrate(catalog, _literal_patterns(source))
    errors = validate_catalog_data(catalog)
    if errors:
        raise ValueError("\n".join(errors))
    args.catalog.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"added": added, "total": len(catalog["patterns"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
