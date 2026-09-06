import random

import numpy as np
import pytest

from src.entities.bullet import (
    BulletManager,
    InboundGlider,
    _INWARD_GLIDERS,
)


@pytest.mark.parametrize(
    ("direction_num", "expected_displacement"),
    [
        (1, (1, -1)),
        (2, (1, 1)),
        (3, (-1, 1)),
        (4, (-1, -1)),
    ],
)
def test_all_inbound_glider_orientations_remain_valid_and_move_inward(
    direction_num,
    expected_displacement,
):
    glider = InboundGlider(
        _INWARD_GLIDERS[direction_num],
        start_row=20,
        start_col=20,
    )
    before = np.asarray(tuple(glider.iter_world_cells())).mean(axis=0)
    for _ in range(4):
        assert glider.step((100, 100))
    after_cells = tuple(glider.iter_world_cells())
    after = np.asarray(after_cells).mean(axis=0)

    assert len(after_cells) == 5
    assert tuple((after - before).astype(int)) == expected_displacement


@pytest.mark.parametrize("direction_num", [1, 2, 3, 4])
def test_new_glider_is_fully_outside_and_does_not_mutate_world(
    monkeypatch,
    direction_num,
):
    state = np.zeros((60, 110), dtype=np.uint8)
    manager = BulletManager(rng=random.Random(4))
    monkeypatch.setattr(manager, "_choose_direction", lambda: direction_num)

    manager._create_bullet_pattern(state, (30, 55))

    assert state.sum() == 0
    assert len(manager.bullets) == 1
    assert not manager.get_bullet_rects()
    assert all(
        row < 0 or row >= 60 or col < 0 or col >= 110
        for row, col in manager.bullets[0].iter_world_cells()
    )


def test_entering_glider_has_a_visible_warning_then_commits(monkeypatch):
    state = np.zeros((60, 110), dtype=np.uint8)
    manager = BulletManager(rng=random.Random(7))
    monkeypatch.setattr(manager, "_choose_direction", lambda: 1)
    manager._create_bullet_pattern(state, (2, 50))
    manager.creation_counter = -1_000

    for _ in range(20):
        manager.update(state, (2, 50))
        if manager.get_bullet_rects():
            break

    assert manager.get_bullet_rects()
    assert not manager.get_dangerous_bullet_rects()
    assert state.sum() == 0

    manager.update(state, (2, 50))
    assert manager.get_dangerous_bullet_rects()
    assert state.sum() == 0

    for _ in range(30):
        manager.update(state, (2, 50))
        if state.sum():
            break

    assert state.sum() == 5
    assert not manager.bullets


@pytest.mark.parametrize("finishing_pattern", [[[1]], [[1, 1], [1, 1]]])
def test_nonfirst_glider_can_die_or_commit_without_array_comparison(finishing_pattern):
    state = np.zeros((60, 110), dtype=np.uint8)
    manager = BulletManager()
    incoming = InboundGlider(_INWARD_GLIDERS[2], -30, 20)
    finishing = InboundGlider(finishing_pattern, 20, 50)
    manager.bullets = [incoming, finishing]

    manager.update(state, (30, 55))

    assert len(manager.bullets) == 1
    assert manager.bullets[0] is incoming
    assert state.sum() == (4 if len(finishing_pattern) == 2 else 0)


def test_corner_glider_is_retired_after_crossing_and_leaving_viewport(monkeypatch):
    state = np.zeros((60, 110), dtype=np.uint8)
    manager = BulletManager()
    monkeypatch.setattr(manager, "_choose_direction", lambda: 3)
    manager._create_bullet_pattern(state, (58, 109))
    manager.creation_counter = -100
    seen = False
    for _ in range(20):
        manager.update(state, (58, 109))
        seen |= bool(manager.get_bullet_rects())
    assert seen
    assert not manager.bullets
    assert not state.any()


def test_corner_glider_survives_a_phase_with_no_visible_live_cells():
    state = np.zeros((60, 110), dtype=np.uint8)
    manager = BulletManager()
    manager.bullets = [InboundGlider(_INWARD_GLIDERS[3], 60, 107)]
    manager.creation_counter = -100
    for _ in range(7):
        manager.update(state, (58, 109))
    assert len(manager.bullets) == 1
    assert not manager.get_bullet_rects()
    manager.update(state, (58, 109))
    assert manager.get_bullet_rects()
    for _ in range(12):
        manager.update(state, (58, 109))
    assert not manager.bullets
