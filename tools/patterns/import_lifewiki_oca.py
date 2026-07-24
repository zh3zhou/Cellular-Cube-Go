"""Import the pinned, curated LifeWiki OCA snapshot into the runtime catalog."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from src.patterns.catalog import DEFAULT_CATALOG_PATH
from tools.patterns.import_rle import import_rle_files


SNAPSHOT_VERSION = "2026-07-24"
LICENSE = "GFDL-1.2"
LICENSE_URI = "https://www.gnu.org/licenses/old-licenses/fdl-1.2.html"

PATTERNS = (
    (
        "lifewiki-highlife-replicator",
        "HighLife replicator",
        "highlife",
        "https://conwaylife.com/wiki/OCA%3AHighLife/Replicator",
        "x = 5, y = 5, rule = B36/S23\n2b3o$bo2bo$o3bo$o2bo$3o!",
        "replicator",
    ),
    (
        "lifewiki-highlife-replicator-predecessor",
        "HighLife replicator predecessor",
        "highlife",
        "https://conwaylife.com/wiki/OCA%3AHighLife/Replicator",
        "x = 4, y = 4, rule = B36/S23\nb3o$o$o$o!",
        "replicator",
    ),
    (
        "lifewiki-highlife-replicator-generation-12",
        "HighLife replicator at generation 12",
        "highlife",
        "https://conwaylife.com/wiki/OCA%3AHighLife",
        "x = 9, y = 9, rule = B36/S23\n2b3o$bo2bo$o3bo$o2bo$3o3b3o$5bo2bo$4bo3bo$4bo2bo$4b3o!",
        "replicator",
    ),
    (
        "lifewiki-highlife-replicator-generation-36",
        "HighLife replicator at generation 36",
        "highlife",
        "https://conwaylife.com/wiki/OCA%3AHighLife",
        "x = 17, y = 17, rule = B36/S23\n2b3o$bo2bo$o3bo$o2bo$3o3b3o$5bo2bo$4bo3bo$4bo2bo$4b3o3b3o$9bo2bo$8bo3bo$8bo2bo$8b3o3b3o$13bo2bo$12bo3bo$12bo2bo$12b3o!",
        "replicator",
    ),
    (
        "lifewiki-highlife-period-96",
        "HighLife period-96 replicator oscillator",
        "highlife",
        "https://conwaylife.com/wiki/OCA%3AHighLife",
        "x = 35, y = 19, rule = B36/S23\n2o$2o10bo$11b2o$10bobo$9b3o2$15b3o$14bobo$14b2o$14bo8$33b2o$33b2o!",
        "oscillator",
    ),
    (
        "lifewiki-highlife-bomber",
        "HighLife bomber",
        "highlife",
        "https://conwaylife.com/wiki/OCA%3AHighLife/Bomber",
        "x = 9, y = 14, rule = B36/S23\nbo$bo$bo3$3bo$2b2o$bobo$3o2$6b3o$5bobo$5b2o$5bo!",
        "spaceship",
    ),
    (
        "lifewiki-highlife-bomber-predecessor",
        "HighLife bomber predecessor",
        "highlife",
        "https://conwaylife.com/wiki/OCA%3AHighLife/Bomber",
        "x = 10, y = 6, rule = B36/S23\nb3o$o$o$o8bo$9bo$9bo!",
        "spaceship",
    ),
    (
        "lifewiki-seeds-small-oscillators",
        "Seeds small oscillator sampler",
        "seeds",
        "https://conwaylife.com/wiki/OCA%3ASeeds",
        "x = 33, y = 5, rule = B2/S\n22bo$6bo7bo8bo5bobo$bo6bo4bo14bo3bo$o6bo8bo4bo$15bo6bo!",
        "oscillator",
    ),
    (
        "lifewiki-day-night-fireball",
        "Day & Night fireball",
        "day_night",
        "https://conwaylife.com/wiki/OCA",
        "x = 11, y = 51, rule = B3678/S34678\n6bo$6b2o2$8bo$5bo2bo$5b3o9$3bo$3bo$b3obob2o$ob3ob2obo$ob7o$b9o$3b7o$11o$obob5obo$2b6obo$bob4obo$3b6o$3b5o$3b2o$2b2o$3b2ob2o$3b2obo$4b3o$obob2obo$o2b5o$2b4obo$ob4o$b6o$2b4o$2b4obo$3b4ob2o$3b7o$4b5o$3b7o$11o$11o$b9o$8o$b8o$2b6o$3b4o$4b2o!",
        "spaceship",
    ),
)


def main() -> int:
    base = json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))
    base["patterns"] = [
        item
        for item in base["patterns"]
        if item["source"]["provider"] != "lifewiki-oca"
    ]
    sources = list(base["generated"].get("sources", []))
    label = "LifeWiki OCA curated snapshot"
    if label not in sources:
        sources.append(label)
    base["generated"]["sources"] = sources

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        files = []
        source_by_file = {}
        manifest = {"patterns": {}}
        for pattern_id, name, rule_id, url, rle, category in PATTERNS:
            path = root / f"{pattern_id}.rle"
            path.write_text(rle, encoding="utf-8")
            files.append(path)
            source_by_file[str(path)] = url
            manifest["patterns"][path.name] = {
                "id": pattern_id,
                "name": name,
                "rule_ids": [rule_id],
                "category": category,
                "tier": "large" if len(rle) > 180 else "standard",
                "weight": 1.0,
                "tags": ["lifewiki", "oca", rule_id],
                "source": {
                    "provider": "lifewiki-oca",
                    "url": url,
                    "version": SNAPSHOT_VERSION,
                    "external_id": pattern_id.removeprefix("lifewiki-"),
                    "license": LICENSE,
                    "license_uri": LICENSE_URI,
                    "attribution": "LifeWiki contributors and the pattern discoverers credited on the source page",
                    "changes": "Extracted the displayed RLE, removed viewer directives, canonicalized, and geometrically deduplicated",
                    "content_sha256": hashlib.sha256(rle.encode()).hexdigest(),
                },
            }
        updated, report = import_rle_files(
            files,
            manifest=manifest,
            base_catalog=base,
        )
        for result in report["results"]:
            result["source_file"] = source_by_file.get(
                result["source_file"], result["source_file"]
            )
    DEFAULT_CATALOG_PATH.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    DEFAULT_CATALOG_PATH.with_name("import-report.lifewiki.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
