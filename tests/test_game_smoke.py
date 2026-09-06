import os

import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from src.core.game_engine import GameEngine
from config.game_config import GameConfig
from src.entities.bullet import InboundGlider, _INWARD_GLIDERS
from src.patterns.catalog import PatternCatalog


def test_game_engine_public_step_render_shutdown():
    game = GameEngine()
    try:
        game.step([], 1 / 13)
        game.render()
        assert game.iteration == 1
        assert game.screen.get_width() == 1100
        assert game.screen.get_height() == 600
        assert game.cellular_automaton.state.shape == (60, 110)
    finally:
        game.shutdown()


def test_web_sized_frames_use_fixed_simulation_rate():
    game = GameEngine()
    try:
        for _ in range(4):
            game.step([], 1 / 60)
        assert game.iteration == 0
        game.step([], 1 / 60)
        assert game.iteration == 1
    finally:
        game.shutdown()


def test_restart_reuses_validated_pattern_catalog(monkeypatch):
    game = GameEngine()
    catalog = game.reward_manager.catalog
    try:
        def fail_if_reloaded():
            raise AssertionError("restart reloaded the Pattern catalog")

        monkeypatch.setattr(
            PatternCatalog,
            "load_default",
            staticmethod(fail_if_reloaded),
        )
        game._restart_game()
        assert game.reward_manager.catalog is catalog
        assert game.iteration == 0
        assert game.survival_time_seconds == 0.0
    finally:
        game.shutdown()


def test_inbound_bullet_warns_before_becoming_lethal():
    game = GameEngine()
    try:
        game.cellular_automaton.state.fill(0)
        glider = InboundGlider([[1]], 30, 55, visible_generations=1)
        game.bullet_manager.bullets = [glider]

        game._check_collisions()
        assert not game.game_over

        glider.visible_generations = 2
        game._check_collisions()
        assert game.game_over
    finally:
        game.shutdown()


def test_catchup_renders_inbound_warning_before_lethal_tick():
    game = GameEngine()
    try:
        game.cellular_automaton.state.fill(0)
        game.player.x, game.player.y = 550, 10
        glider = InboundGlider(_INWARD_GLIDERS[2], -3, 54)
        game.bullet_manager.bullets = [glider]
        game.bullet_manager.creation_counter = -100
        assert not game.bullet_manager.get_bullet_rects()

        game.step([], 2 / GameConfig.FPS)
        assert not game.game_over
        assert game.iteration == 1
        assert glider.visible_generations == 1
        game.render()
        warning_rect = game.bullet_manager.get_bullet_rects()[0]
        assert game.screen.get_at(warning_rect.center)[:3] == GameConfig.CELL_COLOR

        game.step([], 0)
        assert game.iteration == 2
        assert game.game_over
    finally:
        game.shutdown()


def test_settings_freeze_collisions_and_simulation(monkeypatch):
    game = GameEngine()
    monkeypatch.setattr(GameConfig, "WU_DI_MODE", False)
    try:
        game.cellular_automaton.state.fill(0)
        game.cellular_automaton.state[29:31, 54:56] = 1
        game.step([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)], 0.25)
        assert game.show_settings
        assert game.iteration == 0
        assert not game.game_over
        game.step([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)], 1 / GameConfig.FPS)
        assert not game.show_settings
        assert game.iteration == 1
        assert game.game_over
    finally:
        game.shutdown()
