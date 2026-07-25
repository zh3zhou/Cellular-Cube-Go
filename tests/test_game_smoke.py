import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from src.core.game_engine import GameEngine
from src.entities.bullet import InboundGlider
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
