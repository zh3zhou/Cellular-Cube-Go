"""Rule-aware pattern catalog public API."""

from src.patterns.catalog import (
    CATALOG_SCHEMA_VERSION,
    DEFAULT_CATALOG_PATH,
    CatalogValidationError,
    PatternCatalog,
    PatternDefinition,
    PatternRecord,
    load_catalog,
    validate_catalog_data,
)
from src.patterns.rle import (
    RLEError,
    RLEPattern,
    encode_rle,
    geometric_signature,
    normalize_rule,
    parse_rle,
)
from src.patterns.selector import PatternSelector, SelectionContext

__all__ = [
    "CATALOG_SCHEMA_VERSION",
    "DEFAULT_CATALOG_PATH",
    "CatalogValidationError",
    "PatternCatalog",
    "PatternDefinition",
    "PatternRecord",
    "PatternSelector",
    "SelectionContext",
    "RLEError",
    "RLEPattern",
    "encode_rle",
    "geometric_signature",
    "load_catalog",
    "normalize_rule",
    "parse_rle",
    "validate_catalog_data",
]
