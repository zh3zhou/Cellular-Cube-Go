import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from src.core.game_engine import GameEngine


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
