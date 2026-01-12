"""
渲染引擎
"""
import pygame
from typing import List, Tuple, Optional
from config.game_config import GameConfig

class Renderer:
    """主渲染引擎"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.cell_size = GameConfig.CELL_SIZE
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self._load_fonts()
    
    def _load_fonts(self) -> None:
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
    
    def clear_screen(self) -> None:
        """清空屏幕"""
        self.screen.fill(GameConfig.BACKGROUND_COLOR)
    
    def render_cellular_automaton(self, state: List[List[int]]) -> None:
        """渲染元胞自动机状态"""
        try:
            import numpy as np
            if isinstance(state, np.ndarray):
                ys, xs = (state == 1).nonzero()
                cs = self.cell_size
                for i, j in zip(ys.tolist(), xs.tolist()):
                    pygame.draw.rect(self.screen, GameConfig.CELL_COLOR,
                                     pygame.Rect(j * cs, i * cs, cs, cs))
                return
        except Exception:
            pass
        for i, row in enumerate(state):
            for j, cell in enumerate(row):
                if cell == 1:
                    rect = pygame.Rect(j * self.cell_size, i * self.cell_size,
                                     self.cell_size, self.cell_size)
                    pygame.draw.rect(self.screen, GameConfig.CELL_COLOR, rect)
    
    def render_rewards(self, reward_manager):
        """渲染奖励细胞（支持配置开关）"""
        if not GameConfig.REWARD_SYSTEM_ENABLED:
            return
        
        # 渲染奖励细胞
        for reward_pos in reward_manager.get_reward_cells():
            row, col = reward_pos
            rect = pygame.Rect(col * self.cell_size, row * self.cell_size,
                               self.cell_size, self.cell_size)
            pygame.draw.rect(self.screen, GameConfig.REWARD_COLOR, rect)
        
        # 渲染渐进式patterns
        for prog_pattern in reward_manager.get_progressive_patterns():
            color = prog_pattern.get_color()
            pattern = prog_pattern.pattern
            start_row = prog_pattern.start_row
            start_col = prog_pattern.start_col
            
            for i, row in enumerate(pattern):
                for j, cell in enumerate(row):
                    if cell == 1:
                        rect = pygame.Rect(
                            (start_col + j) * self.cell_size,
                            (start_row + i) * self.cell_size,
                            self.cell_size, self.cell_size
                        )
                        pygame.draw.rect(self.screen, color, rect)
    
    def render_player(self, player) -> None:
        """渲染玩家"""
        player_surface, player_rect = player.create_surface_and_rect()
        self.screen.blit(player_surface, player_rect)
    
    def render_bullets(self, bullet_rects: List[pygame.Rect]) -> None:
        """渲染子弹"""
        for rect in bullet_rects:
            pygame.draw.rect(self.screen, GameConfig.CELL_COLOR, rect)
    
    def render_game_over_screen(self, iteration: int) -> None:
        """渲染游戏结束界面"""
        # 创建半透明遮罩
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 渲染游戏结束文字
        game_over_text = self.font_large.render("GAME OVER", True, GameConfig.GAME_OVER_COLOR)
        game_over_rect = game_over_text.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(game_over_text, game_over_rect)
        
        # 渲染迭代次数
        iteration_text = self.font_medium.render(f"Iterations: {iteration}", True, GameConfig.GAME_OVER_COLOR)
        iteration_rect = iteration_text.get_rect(center=(self.screen.get_rect().centerx, 
                                                       self.screen.get_rect().centery + 60))
        self.screen.blit(iteration_text, iteration_rect)
        
        # 渲染重新开始提示
        restart_text = self.font_small.render("Press R to restart", True, GameConfig.GAME_OVER_COLOR)
        restart_rect = restart_text.get_rect(center=(self.screen.get_rect().centerx, 
                                                   self.screen.get_rect().centery + 100))
        self.screen.blit(restart_text, restart_rect)
    
    def render_pause_screen(self) -> None:
        """渲染暂停界面"""
        pause_text = self.font_large.render("PAUSED", True, GameConfig.PAUSE_COLOR)
        pause_rect = pause_text.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(pause_text, pause_rect)
        
        resume_text = self.font_small.render("Press P to resume", True, GameConfig.PAUSE_COLOR)
        resume_rect = resume_text.get_rect(center=(self.screen.get_rect().centerx, 
                                                 self.screen.get_rect().centery + 50))
        self.screen.blit(resume_text, resume_rect)
    
    def render_debug_info(self, fps: float, pattern_count: int, 
                         reward_count: int) -> None:
        """渲染调试信息"""
        debug_texts = [
            f"FPS: {fps:.1f}",
            f"Patterns: {pattern_count}",
            f"Rewards: {reward_count}"
        ]
        
        for i, text in enumerate(debug_texts):
            rendered_text = self.font_small.render(text, True, (255, 255, 255))
            self.screen.blit(rendered_text, (10, 10 + i * 25))