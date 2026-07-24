from __future__ import annotations

from src.patterns.analysis import analyze_pattern


def test_complexity_analysis_is_reproducible():
    seed = [[0, 1, 0], [0, 0, 1], [1, 1, 1]]
    first = analyze_pattern(seed, "life")
    second = analyze_pattern(seed, "life")
    assert first == second
    assert 0 <= first.score <= 100
    assert first.analysis.measured_generations == 256
    assert first.analysis.period == 4
    assert first.analysis.displacement == (1, 1)
    assert "spaceship" in first.behavior_tags


def test_code_52_cross_is_detected_as_period_two():
    cross = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    result = analyze_pattern(cross, "wolfram_code_52")
    assert result.analysis.period == 2
    assert result.analysis.displacement == (0, 0)
    assert "oscillator" in result.behavior_tags
