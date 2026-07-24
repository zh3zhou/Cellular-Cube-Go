import random
from collections import Counter

import numpy as np
import pygame
import pytest

from src.core.cellular_automaton import CellularAutomaton
from src.core.collision_detection import CollisionDetector
from src.core.game_engine import GameEngine
from src.entities.reward import REWARD_TYPES, RewardInstance, RewardManager


class _BlockDefinition:
    def __init__(self, cells=None):
        self.cells = cells or [[1, 1], [1, 1]]

    def to_matrix(self):
        return self.cells


class _BlockCatalog:
    def select(self, *args, **kwargs):
        if args and args[0] == "wolfram_code_52":
            return _BlockDefinition(
                [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
            )
        return _BlockDefinition()


class _Player:
    last_direction = "right"

    def __init__(self, rect):
        self.rect = rect

    def create_surface_and_rect(self):
        return None, self.rect


def test_reward_type_distribution_matches_documented_weights():
    manager = RewardManager(rng=random.Random(20260724))
    manager.survival_seconds = 129
    counts = Counter(manager.choose_reward_type().id for _ in range(10_000))
    expected = {
        "life": 0.55,
        "highlife": 0.1125,
        "seeds": 0.1125,
        "day_night": 0.1125,
        "wolfram_code_52": 0.1125,
    }
    for reward_type, target in expected.items():
        assert abs(counts[reward_type] / 10_000 - target) < 0.03


@pytest.mark.parametrize(
    ("type_id", "rule_id"),
    [
        ("life", "life"),
        ("highlife", "highlife"),
        ("seeds", "seeds"),
        ("day_night", "day_night"),
        ("wolfram_code_52", "wolfram_code_52"),
    ],
)
def test_each_reward_type_creates_its_bound_rule_zone(type_id, rule_id):
    state = np.zeros((60, 110), dtype=np.uint8)
    manager = RewardManager(rng=random.Random(9), catalog=_BlockCatalog())
    manager.creation_counter = -100
    manager.rewards = [RewardInstance(30, 55, type_id)]
    player = _Player(pygame.Rect(550, 300, 10, 10))
    manager.update(state, player)
    player.rect = pygame.Rect(0, 0, 10, 10)
    manager.update(state, player)
    assert len(manager.evolution_zones) == 1
    zone = manager.evolution_zones[0]
    assert zone.rule.id == rule_id
    assert zone.base_color == next(
        item.color for item in REWARD_TYPES if item.id == type_id
    )


def test_green_floor_and_small_library_share_return():
    manager = RewardManager(rng=random.Random(3))
    manager.survival_seconds = 0
    weights = manager.reward_route_weights()
    assert weights["life"] >= 0.55
    assert abs(sum(weights.values()) - 1.0) < 1e-12
    assert weights["life"] > 0.55


def test_progress_uses_survival_and_successful_greenhouses():
    manager = RewardManager(rng=random.Random(4))
    manager.survival_seconds = 90
    assert manager.progress == pytest.approx(0.7)
    manager.successful_rewards = 8
    assert manager.progress == 1.0


def test_contact_leave_creates_nonlethal_zone_then_commits():
    state = np.zeros((60, 110), dtype=np.uint8)
    manager = RewardManager(
        rng=random.Random(7),
        catalog=_BlockCatalog(),
    )
    manager.creation_counter = -100
    manager.rewards = [RewardInstance(30, 55, "life")]
    reward_rect = pygame.Rect(550, 300, 10, 10)
    player = _Player(reward_rect)

    manager.update(state, player)
    assert manager.reward_cells == [(30, 55)]
    assert not manager.evolution_zones

    player.rect = pygame.Rect(0, 0, 10, 10)
    manager.update(state, player)
    assert not manager.reward_cells
    assert len(manager.evolution_zones) == 1
    zone = manager.evolution_zones[0]
    r0, c0, r1, c1 = zone.reserved_rect
    assert not state[r0:r1, c0:c1].any()

    zone.min_generations = 0
    for _ in range(4):
        manager.update(state, player)
        if not manager.evolution_zones:
            break
    assert not manager.evolution_zones
    assert state.sum() == 4


def test_committed_cells_are_immediately_unprotected():
    automaton = CellularAutomaton(width=110, height=60)
    automaton.state.fill(0)
    manager = RewardManager(rng=random.Random(7), catalog=_BlockCatalog())
    manager.creation_counter = -100
    manager.rewards = [RewardInstance(30, 55, "life")]
    player = _Player(pygame.Rect(550, 300, 10, 10))
    manager.update(automaton.state, player)
    player.rect = pygame.Rect(0, 0, 10, 10)
    manager.update(automaton.state, player)
    zone = manager.evolution_zones[0]
    zone.min_generations = 0
    automaton.sync_evolution_zones(manager.evolution_zones)

    for _ in range(4):
        manager.update(automaton.state, player)
        automaton.sync_evolution_zones(manager.evolution_zones)
        if manager.committed_this_update:
            break

    assert manager.committed_this_update
    assert automaton._protected_mask is None
    assert automaton.state.sum() == 4
    row, col = np.argwhere(automaton.state)[0]
    player_rect = pygame.Rect(col * 10, row * 10, 10, 10)
    assert CollisionDetector.check_player_cell_collision_with_mask(
        player_rect,
        automaton.state,
        automaton._protected_mask,
    )


def test_engine_stops_catchup_after_zone_commit(monkeypatch):
    engine = GameEngine()
    updates = []

    def update_logic():
        updates.append(None)
        engine.reward_manager.committed_this_update = True

    monkeypatch.setattr(engine, "_update_game_logic", update_logic)
    monkeypatch.setattr(engine, "_check_collisions", lambda: None)
    try:
        engine.step([], 0.25)
        assert len(updates) == 1
    finally:
        engine.shutdown()
