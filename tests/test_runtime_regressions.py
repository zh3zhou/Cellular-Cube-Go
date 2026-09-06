import os
from collections import defaultdict

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
import pygame
import pytest

from config.game_config import GameConfig
from src.core.rules import CONWAY_LIFE
from src.entities.bullet import InboundGlider
from src.entities.evolution_zone import EvolutionZone
from src.entities.player import Player
from src.graphics.renderer import Renderer
from src.utils.input_utils import InputHandler


@pytest.mark.parametrize("value", [256, -256, 1.5, float("nan"), float("inf")])
def test_binary_entrypoints_reject_values_before_uint8_conversion(value):
    cells = np.array([[value]])
    with pytest.raises(ValueError):
        CONWAY_LIFE.evolve(cells)
    with pytest.raises(ValueError):
        InboundGlider(cells, 0, 0)
    with pytest.raises(ValueError):
        EvolutionZone(cells, 0, 0, CONWAY_LIFE, padding=0)
    zone = EvolutionZone([[1]], 0, 0, CONWAY_LIFE, padding=0)
    with pytest.raises(ValueError):
        zone.pattern = cells
    np.testing.assert_array_equal(zone.pattern, [[1]])


@pytest.mark.parametrize(
    "pressed,direction,delta",
    [
        ((pygame.K_w, pygame.K_d), "up-right", (1, -1)),
        ((pygame.K_w, pygame.K_a), "up-left", (-1, -1)),
        ((pygame.K_s, pygame.K_d), "down-right", (1, 1)),
        ((pygame.K_s, pygame.K_a), "down-left", (-1, 1)),
    ],
)
def test_diagonal_input_records_actual_movement(monkeypatch, pressed, direction, delta):
    keys = defaultdict(bool, {key: True for key in pressed})
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: keys)
    player = Player()
    before = player.x, player.y
    InputHandler().handle_input(player)
    expected = tuple(component * GameConfig.PLAYER_SPEED for component in delta)
    assert (player.x - before[0], player.y - before[1]) == expected
    assert (player.last_dx, player.last_dy) == expected
    assert player.last_direction == direction


def test_opposing_keys_at_boundary_cancel_without_losing_last_direction(monkeypatch):
    keys = defaultdict(bool, {pygame.K_a: True, pygame.K_d: True})
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: keys)
    player = Player()
    player.x = player.size // 2
    player.last_direction = "up-right"
    handler = InputHandler()
    handler.handle_input(player)
    assert player.x == player.size // 2
    keys.clear()
    handler.handle_input(player)
    assert player.last_direction == "up-right"


@pytest.mark.parametrize("density", [0, 0.03, 0.5, 1])
def test_zone_render_matches_cell_by_cell_reference(density):
    pygame.init()
    try:
        screen = pygame.Surface((240, 180))
        expected = screen.copy()
        zone = EvolutionZone(
            (np.random.default_rng(42).random((10, 12)) < density).astype(np.uint8),
            3, 4, CONWAY_LIFE, padding=0,
        )
        zone.current_step = 5

        class Rewards:
            def iter_rewards(self):
                return ()

            def get_evolution_zones(self):
                return [zone]

        Renderer(screen).render_rewards(Rewards())
        for row, values in enumerate(zone.pattern):
            for col, cell in enumerate(values):
                if cell == 1:
                    pygame.draw.rect(expected, zone.get_color(), (
                        (col + 4) * 10, (row + 3) * 10, 10, 10,
                    ))
        assert pygame.image.tobytes(screen, "RGB") == pygame.image.tobytes(expected, "RGB")
    finally:
        pygame.quit()
