"""
玩家实体系统
Player entity system
"""
import pygame
from typing import Tuple
from config.game_config import GameConfig

class Player:
    """
    玩家类 - 添加速度方向记录
    Player class - record movement direction
    """
    
    def __init__(self):
        self.x = GameConfig.PLAYER_START_X
        self.y = GameConfig.PLAYER_START_Y
        self.speed = GameConfig.PLAYER_SPEED
        self.size = GameConfig.PLAYER_SIZE
        self.surface = pygame.Surface((self.size, self.size))
        self.surface.fill(GameConfig.PLAYER_COLOR)
        try:
            self.surface = self.surface.convert()
        except Exception:
            pass
        self.rect = self.surface.get_rect(center=(self.x, self.y))
        # 新增：速度方向记录 | Added: movement direction tracking
        self.last_dx = 0
        self.last_dy = 0
        self.last_direction = None  # 存储8方向字符串 | Store 8-direction string
    
    def move(self, dx: int, dy: int) -> None:
        """
        移动玩家并记录速度方向
        Move player and record movement direction
        """
        self.x += dx
        self.y += dy
        
        # 记录移动方向 | Record movement direction
        self.last_dx = dx
        self.last_dy = dy
        self.last_direction = self._calculate_direction(dx, dy)
        
        # 边界检查 | Boundary check
        self.x = max(self.size // 2, min(self.x, GameConfig.SCREEN_WIDTH - self.size // 2))
        self.y = max(self.size // 2, min(self.y, GameConfig.SCREEN_HEIGHT - self.size // 2))
    
    def _calculate_direction(self, dx: int, dy: int) -> str:
        """
        计算8方向：根据dx,dy返回方向字符串
        Calculate 8-direction string based on dx, dy
        """
        if dx == 0 and dy == 0:
            return 'center'
        
        # 8方向映射 | 8-direction mapping
        angle = (180 + 180 * (0 if dx == 0 else (dy/dx if dx != 0 else 0))) % 360
        
        if dx > 0 and dy == 0:
            return 'right'
        elif dx < 0 and dy == 0:
            return 'left'
        elif dx == 0 and dy > 0:
            return 'down'
        elif dx == 0 and dy < 0:
            return 'up'
        elif dx > 0 and dy > 0:
            return 'down-right'
        elif dx > 0 and dy < 0:
            return 'up-right'
        elif dx < 0 and dy > 0:
            return 'down-left'
        elif dx < 0 and dy < 0:
            return 'up-left'
        
        return 'center'
    
    def update(self) -> None:
        """
        更新玩家状态
        Update player state
        """
        # 更新矩形位置
        if self.rect:
            self.rect.center = (self.x, self.y)
    
    def create_surface_and_rect(self) -> Tuple[pygame.Surface, pygame.Rect]:
        """
        创建玩家的表面和矩形
        Create player's surface and rect
        """
        if self.surface is None:
            self.surface = pygame.Surface((self.size, self.size))
            self.surface.fill(GameConfig.PLAYER_COLOR)
            try:
                self.surface = self.surface.convert()
            except Exception:
                pass
        if self.rect is None:
            self.rect = self.surface.get_rect(center=(self.x, self.y))
        else:
            self.rect.center = (self.x, self.y)
        return self.surface, self.rect
    
    def get_grid_position(self) -> Tuple[int, int]:
        """
        获取玩家在网格中的位置
        Get player's position in grid
        """
        grid_x = int(self.x // GameConfig.CELL_SIZE)
        grid_y = int(self.y // GameConfig.CELL_SIZE)
        return grid_y, grid_x
    
    def reset_position(self) -> None:
        """
        重置玩家位置到初始状态
        Reset player position to initial state
        """
        self.x = GameConfig.PLAYER_START_X
        self.y = GameConfig.PLAYER_START_Y