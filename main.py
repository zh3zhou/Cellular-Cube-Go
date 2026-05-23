#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
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
    print("DEBUG: main() started")
    sys.stdout.flush()

    import pygame
    print("DEBUG: pygame import ok")
    sys.stdout.flush()

    pygame.init()
    print("DEBUG: pygame.init() done")
    sys.stdout.flush()

    import sys as _sys
    print(f"DEBUG: sys.path = {_sys.path[:3]}")
    sys.stdout.flush()

    from config.game_config import GameConfig
    print("DEBUG: GameConfig imported")
    sys.stdout.flush()

    screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
    pygame.display.set_caption(GameConfig.GAME_TITLE)
    screen.fill(GameConfig.BACKGROUND_COLOR)
    pygame.display.flip()
    print("DEBUG: display set up")
    sys.stdout.flush()

    from src.core.game_engine import GameEngine
    print("DEBUG: GameEngine class imported")
    sys.stdout.flush()

    game = GameEngine()
    print("DEBUG: GameEngine() created")
    sys.stdout.flush()

    import time
    last_time = time.time()

    print("DEBUG: game loop starting")
    sys.stdout.flush()

    while game.running:
        current_time = time.time()
        dt = current_time - last_time
        frame_duration = 1.0 / GameConfig.FPS

        game._handle_events()

        if dt >= frame_duration:
            last_time = current_time
            game._handle_continuous_input()
            if not game.game_over and not game.paused:
                game._update_game_logic()
                game._check_collisions()
            game._render()

        await asyncio.sleep(0)

    pygame.quit()
    print("DEBUG: game exited")


if __name__ == "__main__":
    asyncio.run(main())
