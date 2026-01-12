"""
子弹系统
Bullet system
"""
import random
import numpy as np
import pygame
from typing import List, Tuple
from config.game_config import GameConfig

class Bullet:
    """
    子弹实体
    Bullet entity
    """
    
    def __init__(self, x: int, y: int, direction: Tuple[int, int]):
        self.x = x
        self.y = y
        self.direction = direction  # (dx, dy)
        self.speed = GameConfig.BULLET_SPEED
        self.size = GameConfig.CELL_SIZE
    
    def update(self) -> None:
        """
        更新子弹位置
        Update bullet position
        """
        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed
    
    def is_out_of_bounds(self, screen_width: int, screen_height: int) -> bool:
        """
        检查子弹是否超出边界
        Check whether bullet is out of bounds
        """
        return (self.x < 0 or self.x > screen_width or 
                self.y < 0 or self.y > screen_height)
    
    def get_rect(self) -> pygame.Rect:
        """
        获取子弹的矩形
        Get bullet rect
        """
        return pygame.Rect(self.x, self.y, self.size, self.size)

class BulletManager:
    """
    子弹管理器
    Bullet manager
    """
    
    def __init__(self):
        self.bullets: List[Bullet] = []
        self.creation_counter = 0
        self.last_direction = 1
    
    def update(self, state: List[List[int]], player_pos: Tuple[int, int]) -> None:
        """
        更新子弹系统
        Update bullet system
        """
        # 更新现有子弹 | Update existing bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.is_out_of_bounds(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT):
                self.bullets.remove(bullet)
        
        # 尝试创建新子弹 | Try to create new bullet
        self._try_create_bullet(state, player_pos)
    
    def _try_create_bullet(self, state: List[List[int]], player_pos: Tuple[int, int]) -> None:
        """
        尝试创建新子弹
        Try to create a new bullet
        """
        self.creation_counter += 1
        
        if self.creation_counter >= GameConfig.BULLET_CREATE_INTERVAL:
            self._create_bullet_pattern(state, player_pos)
            self.creation_counter = 0
    
    def _create_bullet_pattern(self, state: List[List[int]], player_pos: Tuple[int, int]) -> None:
        """
        在边界创建子弹pattern
        Create bullet pattern at boundaries
        """
        # 转换玩家位置到像素坐标 | Convert player position to pixel coordinates
        p_center_x = (player_pos[1] + 0.5) * GameConfig.CELL_SIZE
        p_center_y = (player_pos[0] + 0.5) * GameConfig.CELL_SIZE
        
        # 随机选择方向，确保与上次不同 | Randomly choose direction, ensure different from last
        while True:
            direction_num = random.randint(1, 4)  # 1: pi/4 2: 3pi/4 3: 5pi/4 4: 7pi/4
            if direction_num != self.last_direction:
                self.last_direction = direction_num
                break
        
        # 检测边界并生成子弹pattern | Detect boundary and generate bullet pattern
        for i in range(len(state)):
            # 计算投射位置 | Compute projection position
            l_distance_x = round(np.sqrt(2) * i * np.cos((2 * (direction_num - 1) + 1) * np.pi/4))
            l_distance_y = -round(np.sqrt(2) * i * np.sin((2 * (direction_num - 1) + 1) * np.pi/4))
            
            # 将像素转换为格子坐标，适配可变CELL_SIZE | Convert pixels to grid coords using CELL_SIZE
            cell_x = round(p_center_x / GameConfig.CELL_SIZE)
            cell_y = round(p_center_y / GameConfig.CELL_SIZE)

            l_x = cell_x + l_distance_x
            l_y = cell_y + l_distance_y
            
            # 检查边界条件并生成相应的3x3 pattern | Check boundary and create 3x3 pattern accordingly
            if self._check_boundary_and_create_pattern(state, l_x, l_y, direction_num):
                break
    
    def _check_boundary_and_create_pattern(self, state: List[List[int]], l_x: int, l_y: int, direction_num: int) -> bool:
        """
        检查边界并创建对应的pattern
        Check boundary and create corresponding pattern
        """
        width = len(state[0])
        height = len(state)
        
        # 左边界 | Left boundary
        if l_x == 4:
            if direction_num == 2:
                return self._create_3x3_pattern(state, l_x - 1, l_y - 1, [
                    [0, 0, 1],
                    [1, 0, 1],
                    [0, 1, 1]
                ])
        
        # 右边界 | Right boundary
        elif l_x == width - 4:
            if direction_num == 1:
                return self._create_3x3_pattern(state, l_x + 1, l_y - 1, [
                    [0, 1, 0],
                    [1, 0, 0],
                    [1, 1, 1]
                ])
            elif direction_num == 4:
                return self._create_3x3_pattern(state, l_x + 1, l_y + 1, [
                    [1, 1, 1],
                    [1, 0, 0],
                    [1, 0, 0]
                ])
        
        # 上边界 | Top boundary
        elif l_y == 4:
            if direction_num == 1:
                return self._create_3x3_pattern(state, l_x + 1, l_y - 1, [
                    [0, 1, 0],
                    [1, 0, 0],
                    [1, 1, 1]
                ])
            elif direction_num == 2:
                return self._create_3x3_pattern(state, l_x - 1, l_y - 1, [
                    [0, 0, 1],
                    [1, 0, 1],
                    [0, 1, 1]
                ])
        
        # 下边界 | Bottom boundary
        elif l_y == height - 4:
            if direction_num == 3:
                return self._create_3x3_pattern(state, l_x - 1, l_y + 1, [
                    [1, 1, 1],
                    [1, 0, 1],
                    [0, 0, 0]
                ])
            elif direction_num == 4:
                return self._create_3x3_pattern(state, l_x + 1, l_y + 1, [
                    [1, 1, 1],
                    [1, 0, 0],
                    [1, 0, 0]
                ])
        
        return False
    
    def _create_3x3_pattern(self, state: List[List[int]], center_x: int, center_y: int, pattern: List[List[int]]) -> bool:
        """
        在指定位置创建3x3 pattern
        Create a 3x3 pattern at the specified position
        """
        try:
            for i in range(3):
                for j in range(3):
                    if pattern[i][j] == 1:
                        target_row = center_y - 1 + i
                        target_col = center_x - 1 + j
                        
                        if (0 <= target_row < len(state) and 
                            0 <= target_col < len(state[0])):
                            state[target_row][target_col] = 1
            return True
        except (IndexError, ValueError):
            return False
    
    def get_bullet_rects(self) -> List[pygame.Rect]:
        """
        获取所有子弹的矩形
        Get rects of all bullets
        """
        return [bullet.get_rect() for bullet in self.bullets]
    
    def clear(self) -> None:
        """
        清空所有子弹
        Clear all bullets
        """
        self.bullets.clear()
        self.creation_counter = 0