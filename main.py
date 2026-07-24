#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pygame-ce",
#   "numpy",
# ]
# ///
"""
游戏主入口文件
Game main entry point
"""
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if sys.platform in ("emscripten", "wasi"):
    import pygbag.aio as asyncio
else:
    import asyncio


async def main():
    import pygame
    from config.game_config import GameConfig
    from src.core.game_engine import GameEngine

    game = GameEngine()
    clock = pygame.time.Clock()
    is_web = sys.platform in ("emscripten", "wasi")

    while game.running:
        # Clock.tick is the desktop frame limiter. In browsers pygbag owns the
        # pacing, so the loop only measures elapsed time and yields every frame.
        dt_ms = clock.tick(0 if is_web else GameConfig.FPS)
        game.step(pygame.event.get(), min(dt_ms / 1000.0, 0.25))
        game.render()

        if is_web:
            _mark_web_state("running", game)
        await asyncio.sleep(0)

    game.shutdown()


def _mark_web_state(state: str, game=None) -> None:
    """Expose a minimal, platform-guarded browser smoke-test signal."""
    if sys.platform not in ("emscripten", "wasi"):
        return
    try:
        from platform import window
        window.document.body.dataset.lifeGameState = state
        if game is not None:
            window.document.body.dataset.lifeGameSettings = (
                "open" if game.show_settings else "closed"
            )
            window.document.body.dataset.lifeGamePlayer = (
                f"{int(game.player.x)},{int(game.player.y)}"
            )
            window.document.body.dataset.lifeGameIteration = str(game.iteration)
    except Exception:
        # The game must remain playable if a template does not expose the DOM.
        pass


if __name__ == "__main__":
    asyncio.run(main())
