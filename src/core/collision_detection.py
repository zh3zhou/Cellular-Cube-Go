"""
碰撞检测系统
Collision detection system
"""
import pygame
from typing import List, Tuple, Optional
from config.game_config import GameConfig

class CollisionDetector:
    """
    碰撞检测引擎
    Collision detection engine
    """
    
    @staticmethod
    def check_player_cell_collision(player_rect: pygame.Rect, 
                                  state: List[List[int]]) -> bool:
        """
        检查玩家与活细胞的碰撞
        Check collision between player and live cells
        """
        # 计算玩家覆盖的网格范围 | Compute grid coverage range by player rect
        cell = GameConfig.CELL_SIZE
        left = max(0, int(player_rect.left // cell))
        right = min(len(state[0]) - 1, int((player_rect.right - 1) // cell))
        top = max(0, int(player_rect.top // cell))
        bottom = min(len(state) - 1, int((player_rect.bottom - 1) // cell))
        for gy in range(top, bottom + 1):
            for gx in range(left, right + 1):
                if state[gy][gx] == 1:
                    return True
        return False

    @staticmethod
    def check_player_cell_collision_with_mask(player_rect: pygame.Rect,
                                              state: List[List[int]],
                                              protected_mask) -> bool:
        """
        检查玩家与活细胞的碰撞（忽略保护区中的细胞）
        Check collision between player and live cells, excluding protected zones
        """
        cell = GameConfig.CELL_SIZE
        left = max(0, int(player_rect.left // cell))
        right = min(len(state[0]) - 1, int((player_rect.right - 1) // cell))
        top = max(0, int(player_rect.top // cell))
        bottom = min(len(state) - 1, int((player_rect.bottom - 1) // cell))
        for gy in range(top, bottom + 1):
            for gx in range(left, right + 1):
                if state[gy][gx] == 1:
                    if protected_mask is not None and protected_mask[gy][gx]:
                        continue
                    return True
        return False
    
    @staticmethod
    def check_player_reward_collision(player_rect: pygame.Rect, 
                                    reward_cells: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """
        检查玩家与奖励细胞的碰撞
        Check collision between player and reward cells
        """
        grid_x = int(player_rect.centerx // GameConfig.CELL_SIZE)
        grid_y = int(player_rect.centery // GameConfig.CELL_SIZE)
        
        reward_pos = (grid_y, grid_x)
        if reward_pos in reward_cells:
            return reward_pos
        return None
    
    @staticmethod
    def find_max_rectangle_with_buffer(state: List[List[int]], buffer_size: int = 2) -> Tuple[int, int, int, int]:
        """
        查找带缓冲区的最大空矩形区域
        Find largest empty rectangle with buffer
        """
        if not state or not state[0]:
            return (0, 0, 0, 0)
        
        rows, cols = len(state), len(state[0])
        
        # 创建带缓冲区的禁止区域地图 | Create forbidden map with buffer
        forbidden = [[False for _ in range(cols)] for _ in range(rows)]
        
        # 标记所有活细胞及其缓冲区为禁止区域 | Mark live cells and buffers as forbidden
        for i in range(rows):
            for j in range(cols):
                if state[i][j] == 1:
                    # 标记周围buffer_size格为禁止区域 | Mark surrounding buffer_size cells forbidden
                    for di in range(-buffer_size, buffer_size + 1):
                        for dj in range(-buffer_size, buffer_size + 1):
                            ni, nj = i + di, j + dj
                            if 0 <= ni < rows and 0 <= nj < cols:
                                forbidden[ni][nj] = True
        
        # 在禁止区域地图上找最大空矩形 | Find largest empty rectangle on forbidden map
        heights = [0] * cols
        max_area = 0
        best_rect = (0, 0, 0, 0)
        
        for i in range(rows):
            # 更新每列的连续非禁止区域高度 | Update column heights of non-forbidden areas
            for j in range(cols):
                if not forbidden[i][j]:
                    heights[j] += 1
                else:
                    heights[j] = 0
            
            # 使用栈找到当前行的最大矩形 | Use stack to find max rectangle for current row
            area, rect = CollisionDetector._largest_rectangle_in_histogram(heights, i)
            if area > max_area:
                max_area = area
                best_rect = rect
        
        return best_rect
    
    @staticmethod
    def can_place_pattern_with_buffer(state: List[List[int]], x: int, y: int, 
                                    width: int, height: int, buffer_size: int = 2) -> bool:
        """
        检查是否可以放置带缓冲区的pattern
        Check whether a pattern with buffer can be placed
        """
        # 检查包括缓冲区的整个区域 | Check entire area including buffer
        buffer_x = max(0, x - buffer_size)
        buffer_y = max(0, y - buffer_size)
        buffer_w = min(len(state[0]) - buffer_x, width + 2 * buffer_size)
        buffer_h = min(len(state) - buffer_y, height + 2 * buffer_size)
        
        return CollisionDetector.can_place_rectangle(state, buffer_x, buffer_y, buffer_w, buffer_h)
    
    @staticmethod
    def _largest_rectangle_in_histogram(heights: List[int], 
                                      current_row: int) -> Tuple[int, Tuple[int, int, int, int]]:
        """
        在直方图中找最大矩形
        Find largest rectangle in histogram
        """
        stack = []
        max_area = 0
        best_rect = (0, 0, 0, 0)
        
        for i, h in enumerate(heights + [0]):
            while stack and heights[stack[-1]] > h:
                height = heights[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                area = height * width
                
                if area > max_area:
                    max_area = area
                    left = 0 if not stack else stack[-1] + 1
                    top = current_row - height + 1
                    best_rect = (left, top, width, height)
            
            stack.append(i)
        
        return max_area, best_rect
    
    @staticmethod
    def can_place_rectangle(state: List[List[int]], x: int, y: int, 
                          width: int, height: int) -> bool:
        """
        检查是否可以在指定位置放置矩形
        Check whether a rectangle can be placed at given position
        """
        if (x < 0 or y < 0 or 
            x + width > len(state[0]) or 
            y + height > len(state)):
            return False
        
        for i in range(y, y + height):
            for j in range(x, x + width):
                if state[i][j] == 1:
                    return False
        return True