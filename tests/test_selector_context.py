from dataclasses import replace

from src.patterns.catalog import PatternCatalog
from src.patterns.selector import PatternSelector


def test_continuous_progress_uses_fixed_geometry_pool_and_exact_thresholds():
    # One real record preserves the production shape without reloading the
    # entire catalog on every selection or progress threshold.
    catalog = PatternCatalog.load_default()
    seed = catalog.patterns_for("life")[0]
    patterns = tuple(replace(seed, id=f"test-{i}", complexity_score=score)
                     for i, score in enumerate((30.0, 30.035, 65.0, 100.0)))
    catalog = PatternCatalog(3, {"life": catalog.rules["life"]}, {}, patterns)
    selector = PatternSelector(catalog)
    for i in range(1001):
        progress = i / 1000
        context = selector.build_context(progress, max_width=108, max_height=58)
        expected = tuple(item for item in patterns if item.complexity_score <= 30 + 70 * progress)
        assert context.candidates["life"] == expected
    assert len(selector._pool_cache) == 1
    first = selector.build_context(0, max_width=108, max_height=58)
    selector.record_choice("life", first.candidates["life"][0])
    refreshed = selector.build_context(0, max_width=108, max_height=58)
    assert first.fresh_candidates["life"] == first.candidates["life"]
    assert refreshed.fresh_candidates["life"] == ()
    tiny = selector.build_context(1, max_width=0, max_height=0)
    assert tiny.candidates["life"] == ()
