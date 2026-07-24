from __future__ import annotations

import json
import random
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from src.patterns.catalog import (
    DEFAULT_CATALOG_PATH,
    PatternCatalog,
    load_catalog,
    validate_catalog_data,
)
from src.patterns.rle import encode_rle, geometric_signature, parse_rle
from src.patterns.selector import PatternSelector
from tools.patterns.import_rle import import_rle_files


class RLETests(unittest.TestCase):
    def test_round_trip_trims_empty_borders(self) -> None:
        matrix = [
            [0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 1, 1, 1, 0],
        ]
        encoded = encode_rle(matrix, "b3/s23")
        parsed = parse_rle(encoded)
        self.assertEqual(parsed.rule, "B3/S23")
        self.assertEqual(parsed.width, 3)
        self.assertEqual(parsed.height, 3)
        self.assertEqual(sum(map(sum, parsed.cells)), 5)

    def test_signature_ignores_rotation_reflection_and_translation(self) -> None:
        first = parse_rle("x = 3, y = 2\n2o$bo!").cells
        rotated = parse_rle("x = 2, y = 3\no$2o!").cells
        self.assertEqual(geometric_signature(first), geometric_signature(rotated))


class CatalogTests(unittest.TestCase):
    def test_default_catalog_is_strictly_valid(self) -> None:
        catalog = load_catalog()
        self.assertEqual(catalog.schema_version, 2)
        self.assertGreaterEqual(len(catalog.patterns), 700)
        self.assertEqual(
            {rule: len(catalog.patterns_for(rule)) for rule in catalog.rules},
            {"life": 710, "highlife": 11, "seeds": 5, "day_night": 5},
        )
        providers = {item.source.provider for item in catalog.patterns}
        self.assertIn("playgameoflife-life-lexicon", providers)
        self.assertIn("lifewiki-oca", providers)
        raw = json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))
        external = [
            item
            for item in raw["patterns"]
            if item["source"]["provider"] != "cellular-cube-go"
        ]
        self.assertTrue(external)
        for item in external:
            source = item["source"]
            self.assertTrue(source["license_uri"].startswith("https://"))
            self.assertTrue(source["attribution"])
            self.assertTrue(source["changes"])
            self.assertRegex(source["content_sha256"], r"^[0-9a-f]{64}$")

    def test_missing_license_and_geometric_duplicate_are_reported(self) -> None:
        data = json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))
        broken = deepcopy(data)
        del broken["patterns"][0]["source"]["license"]
        duplicate = deepcopy(broken["patterns"][0])
        duplicate["id"] = "rotated-block"
        duplicate["name"] = "Rotated block"
        duplicate["source"]["license"] = "MIT"
        broken["patterns"].append(duplicate)
        errors = validate_catalog_data(broken)
        self.assertTrue(any("source missing fields: license" in item for item in errors))
        self.assertTrue(any("geometrically duplicates" in item for item in errors))

    def test_convenience_api_returns_mutable_copy(self) -> None:
        catalog = PatternCatalog.load_default()
        definition = catalog.select("seeds", random.Random(11), allow_large=False)
        self.assertIsNotNone(definition)
        matrix = definition.to_matrix()
        matrix[0][0] = 1 - matrix[0][0]
        self.assertNotEqual(matrix, definition.to_matrix())

    def test_unknown_license_marker_is_rejected(self) -> None:
        data = json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))
        data["patterns"][0]["source"]["license"] = "unknown"
        errors = validate_catalog_data(data)
        self.assertTrue(
            any("redistributable license" in item for item in errors),
            errors,
        )


class SelectorTests(unittest.TestCase):
    def test_recent_four_are_suppressed_when_alternatives_exist(self) -> None:
        selector = PatternSelector(load_catalog(), rng=random.Random(7))
        chosen: list[str] = []
        for _ in range(9):
            pattern = selector.select(
                "life", max_width=108, max_height=58, allow_large=False
            )
            self.assertIsNotNone(pattern)
            self.assertNotIn(pattern.id, chosen[-4:])
            chosen.append(pattern.id)

    def test_large_tier_targets_fifteen_percent(self) -> None:
        selector = PatternSelector(load_catalog(), rng=random.Random(20260724))
        large = 0
        trials = 10_000
        for _ in range(trials):
            pattern = selector.select("life", max_width=108, max_height=58)
            large += pattern.tier == "large"
        self.assertGreater(large / trials, 0.13)
        self.assertLess(large / trials, 0.17)

    def test_size_filter_and_missing_rule_return_none(self) -> None:
        selector = PatternSelector(load_catalog(), rng=random.Random(3))
        self.assertIsNone(selector.select("unknown", max_width=10, max_height=10))
        self.assertIsNone(selector.select("life", max_width=1, max_height=1))

    def test_size_filter_accepts_a_rotated_fit(self) -> None:
        catalog = load_catalog()
        candidates = catalog.patterns_for("life", max_width=58, max_height=108)
        self.assertTrue(
            any(item.width > 58 and item.height <= 58 for item in candidates)
        )

    def test_small_rule_library_never_repeats_immediately(self) -> None:
        selector = PatternSelector(load_catalog(), rng=random.Random(19))
        previous = None
        for _ in range(30):
            pattern = selector.select(
                "highlife", max_width=108, max_height=58, allow_large=False
            )
            self.assertNotEqual(pattern.id, previous)
            previous = pattern.id


class ImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))

    def test_import_requires_provenance_and_reports_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing.rle"
            duplicate = root / "duplicate.rle"
            new_pattern = root / "new.rle"
            missing.write_text("x = 3, y = 1, rule = B2/S\n3o!", encoding="utf-8")
            duplicate.write_text("x = 1, y = 2, rule = B2/S\no$o!", encoding="utf-8")
            new_pattern.write_text(
                "x = 4, y = 3, rule = B2/S\no2bo$bo$2bo!", encoding="utf-8"
            )
            source = {
                "provider": "fixture",
                "url": "https://example.invalid/fixture",
                "version": "1",
                "external_id": "fixture",
                "license": "CC0-1.0",
            }
            manifest = {
                "patterns": {
                    "duplicate.rle": {
                        "id": "duplicate-seeds-pair",
                        "name": "Duplicate seeds pair",
                        "source": source,
                    },
                    "new.rle": {
                        "id": "new-seeds-seed",
                        "name": "New Seeds seed",
                        "category": "growth_seed",
                        "source": source,
                    },
                }
            }
            updated, report = import_rle_files(
                [missing, duplicate, new_pattern],
                manifest=manifest,
                base_catalog=self.base,
            )
            self.assertEqual(
                report["summary"],
                {"duplicate": 1, "imported": 1, "unknown-license": 1},
            )
            self.assertEqual(len(updated["patterns"]), len(self.base["patterns"]) + 1)
            self.assertFalse(validate_catalog_data(updated))

    def test_import_rejects_unknown_license_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.rle"
            path.write_text("x = 3, y = 1, rule = B2/S\n3o!", encoding="utf-8")
            manifest = {
                "patterns": {
                    path.name: {
                        "id": "unknown-license-candidate",
                        "name": "Unknown license candidate",
                        "source": {
                            "provider": "fixture",
                            "url": "https://example.invalid/fixture",
                            "version": "1",
                            "external_id": "unknown",
                            "license": "unclear",
                        },
                    }
                }
            }
            updated, report = import_rle_files(
                [path],
                manifest=manifest,
                base_catalog=self.base,
            )
            self.assertEqual(report["summary"], {"unknown-license": 1})
            self.assertEqual(len(updated["patterns"]), len(self.base["patterns"]))


if __name__ == "__main__":
    unittest.main()
