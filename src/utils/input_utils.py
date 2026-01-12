"""
输入处理工具
Input handling utilities
"""
import pygame
import ctypes
from config.game_config import GameConfig

class InputHandler:
    """
    输入处理器
    Input handler
    """
    
    def __init__(self):
        self._switch_to_english_input()
    
    def _switch_to_english_input(self):
        """
        切换到英文输入法
        Switch to English input method
        """
        try:
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            hkl = user32.GetKeyboardLayout(0)
            if hkl != 0x04090409:
                user32.ActivateKeyboardLayout(0x04090409, 0)
        except:
            pass  # 忽略错误，继续运行 | Ignore errors and continue
    
    def handle_input(self, player):
        """
        处理玩家输入
        Handle player input
        """
        keys = pygame.key.get_pressed()
        
        if keys[GameConfig.KEY_UP]:
            player.move(0, -GameConfig.PLAYER_SPEED)
        if keys[GameConfig.KEY_DOWN]:
            player.move(0, GameConfig.PLAYER_SPEED)
        if keys[GameConfig.KEY_LEFT]:
            player.move(-GameConfig.PLAYER_SPEED, 0)
        if keys[GameConfig.KEY_RIGHT]:
            player.move(GameConfig.PLAYER_SPEED, 0)
    def handle_settings_input(self, engine):
        pass