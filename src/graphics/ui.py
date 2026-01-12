"""
用户界面系统
"""
import pygame
from config.game_config import GameConfig

class UI:
    """用户界面类"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._load_fonts()
    
    def _load_fonts(self):
        """加载字体"""
        try:
            self.font_large = pygame.font.Font(GameConfig.FONT_PATH, GameConfig.FONT_SIZE_LARGE)
            self.font_medium = pygame.font.Font(GameConfig.FONT_PATH, GameConfig.FONT_SIZE_MEDIUM)
            self.font_small = pygame.font.Font(GameConfig.FONT_PATH, GameConfig.FONT_SIZE_SMALL)
        except:
            # 如果自定义字体加载失败，使用系统默认字体
            self.font_large = pygame.font.Font(None, GameConfig.FONT_SIZE_LARGE)
            self.font_medium = pygame.font.Font(None, GameConfig.FONT_SIZE_MEDIUM)
            self.font_small = pygame.font.Font(None, GameConfig.FONT_SIZE_SMALL)
    
    def render_game_over(self, iteration: int):
        """渲染游戏结束界面"""
        # 创建半透明遮罩
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        overlay.set_alpha(GameConfig.UI_OVERLAY_ALPHA)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 渲染文本
        text_line1 = self.font_large.render(f"after {iteration} iterations", True, GameConfig.UI_TEXT_COLOR)
        text_line1_rect = text_line1.get_rect(center=(GameConfig.SCREEN_WIDTH // 2, GameConfig.SCREEN_HEIGHT // 2 - 35))
        self.screen.blit(text_line1, text_line1_rect)
        
        text_line2 = self.font_large.render("the world went SILENCE again", True, GameConfig.UI_TEXT_COLOR)
        text_line2_rect = text_line2.get_rect(center=(GameConfig.SCREEN_WIDTH // 2, GameConfig.SCREEN_HEIGHT // 2 + 35))
        self.screen.blit(text_line2, text_line2_rect)
        
        text_line3 = self.font_small.render("Press R to create a new one", True, GameConfig.UI_RESTART_COLOR)
        text_line3_rect = text_line3.get_rect(center=(GameConfig.SCREEN_WIDTH // 2, GameConfig.SCREEN_HEIGHT // 2 + 105))
        self.screen.blit(text_line3, text_line3_rect)
    
    def render_pause(self):
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        overlay.set_alpha(GameConfig.UI_OVERLAY_ALPHA)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        pause_text = self.font_large.render("PAUSED", True, GameConfig.PAUSE_COLOR)
        pause_rect = pause_text.get_rect(center=(GameConfig.SCREEN_WIDTH // 2, GameConfig.SCREEN_HEIGHT // 2))
        self.screen.blit(pause_text, pause_rect)