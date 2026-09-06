import json
from copy import deepcopy

import pytest

from src.patterns.catalog import DEFAULT_CATALOG_PATH, validate_catalog_data


@pytest.fixture
def catalog_data():
    data = json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))
    data["patterns"] = [next(item for item in data["patterns"] if item["rule_ids"] == ["life"])]
    return data


@pytest.mark.parametrize("rule", [None, {}, {"rulestring": "invalid"}, {"rulestring": 42}])
def test_malformed_rule_metadata_is_reported_without_crashing(catalog_data, rule):
    catalog_data["rules"]["life"] = rule
    errors = validate_catalog_data(catalog_data)
    assert any("rules.life" in error for error in errors)


@pytest.mark.parametrize("field,value", [
    ("weight", float("nan")), ("weight", float("inf")), ("weight", True),
    ("weight", 10**400),
    ("complexity_score", float("nan")), ("complexity_score", float("inf")),
    ("rule_ids", [{}]), ("tier", []), ("affinity", {}),
    ("behavior_tags", [{}]), ("rle", None),
])
def test_malformed_pattern_fields_are_reported(catalog_data, field, value):
    catalog_data["patterns"][0][field] = value
    before = deepcopy(catalog_data)
    errors = validate_catalog_data(catalog_data)
    assert any(f"patterns[0].{field}" in error for error in errors)
    assert catalog_data == before


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, 10**400])
def test_nonfinite_or_boolean_growth_rate_is_rejected(catalog_data, value):
    catalog_data["patterns"][0]["analysis"]["growth_rate"] = value
    assert any("growth_rate" in error for error in validate_catalog_data(catalog_data))
