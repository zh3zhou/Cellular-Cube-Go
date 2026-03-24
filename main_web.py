import asyncio
import pygame
import sys
import os
import time
import numpy  # Required by pygbag to load the numpy wheel

# Ensure project root is on Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.game_engine import GameEngine
from config.game_config import GameConfig

async def main():
    """
    Async main function for Web/Pygbag
    """
    game = GameEngine()
    
    # Main game loop adapted for asyncio
    while game.running:
        start_time = time.time()
        
        # Handle events
        game._handle_events()
        
        if not game.game_over and not game.paused:
            # Update game logic
            game._update_game_logic()
            
            # Check collisions
            game._check_collisions()
        
        # Render
        game._render()
        
        # Control framerate
        # In Web/WASM, asyncio.sleep(0) yields to the browser's event loop
        # which typically syncs with requestAnimationFrame (approx 60fps)
        # We still use clock.tick to cap it if needed, but 0 is usually fine for max speed
        game.clock.tick(GameConfig.FPS)
        
        await asyncio.sleep(0)
    
    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
