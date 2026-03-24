# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pygame-ce",
#   "numpy",
# ]
# ///

import asyncio
import pygame
import sys
import os
import time
import numpy

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.game_engine import GameEngine
from config.game_config import GameConfig

async def main():
    game = GameEngine()

    while game.running:
        game._handle_events()

        if not game.game_over and not game.paused:
            game._update_game_logic()
            game._check_collisions()

        game._render()
        game.clock.tick(GameConfig.FPS)

        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
