"""
元胞自动机核心逻辑
Cellular automaton core logic
"""
import numpy as np
import random as rd
from typing import List, Tuple
from config.game_config import GameConfig

class CellularAutomaton:
    """
    元胞自动机引擎
    Cellular automaton engine
    """
    
    def __init__(self, width: int = None, height: int = None):
        self.width = width or GameConfig.WORLD_WIDTH
        self.height = height or GameConfig.WORLD_HEIGHT
        self.state = self.create_random_state()
        self._protected_mask = None
        self.protected_zones: List[Tuple[int, int, int, int]] = []  # 保护区域列表
    
    def _create_dead_state(self) -> List[List[int]]:
        """
        创建全死寂状态
        Create an all-dead state
        """
        return np.zeros((self.height, self.width), dtype=np.uint8)
    
    def create_random_state(self, probability: float = None) -> List[List[int]]:
        """
        生成随机初始状态
        Generate a random initial state
        """
        if probability is None:
            probability = GameConfig.CELLULAR_AUTOMATON_PROBABILITY
            
        state = (np.random.rand(self.height, self.width) < probability).astype(np.uint8)
        
        # 确保玩家周围安全区域 | Ensure player safe zone around center
        self._clear_player_safe_zone(state)
        return state
    
    def _clear_player_safe_zone(self, state: List[List[int]]) -> None:
        """
        清空玩家周围安全区域
        Clear the player's surrounding safe zone
        """
        center_x = self.width // 2
        center_y = self.height // 2
        radius = GameConfig.PLAYER_SAFE_ZONE_RADIUS
        
        x0 = max(0, center_x - radius)
        x1 = min(self.width, center_x + radius)
        y0 = max(0, center_y - radius)
        y1 = min(self.height, center_y + radius)
        state[y0:y1, x0:x1] = 0
    
    def count_neighbors(self, state: List[List[int]], x: int, y: int) -> int:
        """
        计算指定位置的活邻居数量
        Count live neighbors at the specified position
        """
        # 兼容旧接口：单点邻居统计（用于可能的外部调用）
        xs = slice(max(0, x-1), min(state.shape[1], x+2))
        ys = slice(max(0, y-1), min(state.shape[0], y+2))
        sub = state[ys, xs]
        return int(sub.sum() - state[y, x])
    
    def apply_rules(self, current_cell: int, neighbor_count: int) -> int:
        """
        应用康威生命游戏规则
        Apply Conway's Game of Life rules
        """
        if current_cell == 1:  # 活细胞 | Live cell
            # 使用可配置的存活邻居范围 | Use configurable live-neighbor range
            return 1 if (GameConfig.LIVE_MIN_NEIGHBORS <= neighbor_count <= GameConfig.LIVE_MAX_NEIGHBORS) else 0
        else:  # 死细胞 | Dead cell
            # 使用可配置的出生邻居范围 | Use configurable birth-neighbor range
            return 1 if (GameConfig.BORN_MIN_NEIGHBORS <= neighbor_count <= GameConfig.BORN_MAX_NEIGHBORS) else 0
    
    def add_protected_zone(self, center_row: int, center_col: int, 
                          pattern_height: int, pattern_width: int):
        """
        添加pattern保护区域（2格缓冲区）
        Add a pattern protected zone (2-cell buffer)
        """
        # 计算包含2格缓冲区的保护区域 | Compute protected zone including 2-cell buffer
        start_row = max(0, center_row - 2)
        start_col = max(0, center_col - 2)
        end_row = min(self.height, center_row + pattern_height + 2)
        end_col = min(self.width, center_col + pattern_width + 2)
        
        self.protected_zones.append((start_row, start_col, end_row, end_col))
    
    def remove_protected_zone(self, center_row: int, center_col: int, 
                            pattern_height: int, pattern_width: int):
        """
        移除pattern保护区域
        Remove pattern protected zone
        """
        start_row = max(0, center_row - 2)
        start_col = max(0, center_col - 2)
        end_row = min(self.height, center_row + pattern_height + 2)
        end_col = min(self.width, center_col + pattern_width + 2)
        
        zone_to_remove = (start_row, start_col, end_row, end_col)
        if zone_to_remove in self.protected_zones:
            self.protected_zones.remove(zone_to_remove)
    
    def _is_in_protected_zone(self, row: int, col: int) -> bool:
        """
        检查坐标是否在任一保护区域内
        Check whether coordinates lie in any protected zone
        """
        for start_row, start_col, end_row, end_col in self.protected_zones:
            if start_row <= row < end_row and start_col <= col < end_col:
                return True
        return False
    
    def next_generation(self, state: List[List[int]]) -> List[List[int]]:
        """
        计算下一代状态（包含保护区域逻辑）
        Compute next generation (including protected zone logic)
        """
        s = state
        # 邻居计数向量化：零填充 + 切片累加（边界不环绕）
        p = np.pad(s, 1, mode='constant', constant_values=0)
        n = (
            p[0:-2, 0:-2] + p[0:-2, 1:-1] + p[0:-2, 2:  ] +
            p[1:-1, 0:-2] +                 p[1:-1, 2:  ] +
            p[2:  , 0:-2] + p[2:  , 1:-1] + p[2:  , 2:  ]
        )
        live = ((s == 1) & (n >= GameConfig.LIVE_MIN_NEIGHBORS) & (n <= GameConfig.LIVE_MAX_NEIGHBORS))
        born = ((s == 0) & (n >= GameConfig.BORN_MIN_NEIGHBORS) & (n <= GameConfig.BORN_MAX_NEIGHBORS))
        new_state = np.where(live | born, 1, 0).astype(np.uint8)
        # 保护区掩码：强制清零
        if self._protected_mask is not None:
            new_state[self._protected_mask] = 0
        return new_state
    
    def update(self, reward_cells: List[Tuple[int, int]], 
               progressive_patterns: List = None) -> None:
        """
        更新元胞自动机状态（接收渐进式patterns用于保护区域）
        Update automaton state (receive progressive patterns for protected zones)
        """
        # 清理旧的保护区域，并预计算掩码 | Clear old zones and precompute mask
        self.protected_zones.clear()
        self._protected_mask = None
        
        # 根据当前的渐进式patterns设置保护区域 | Set protected zones based on progressive patterns
        if progressive_patterns:
            mask = np.zeros((self.height, self.width), dtype=bool)
            for pattern in progressive_patterns:
                ph = len(pattern.pattern)
                pw = len(pattern.pattern[0]) if ph > 0 else 0
                # 计算包含2格缓冲区的范围
                sr = max(0, pattern.start_row - 2)
                sc = max(0, pattern.start_col - 2)
                er = min(self.height, pattern.start_row + ph + 2)
                ec = min(self.width, pattern.start_col + pw + 2)
                mask[sr:er, sc:ec] = True
            self._protected_mask = mask
        
        # 计算下一代状态 | Compute next generation
        new_state = self.next_generation(self.state)
        # 在保护区域内叠加当前渐进式 pattern 的细胞，覆盖重叠
        if progressive_patterns:
            for pattern in progressive_patterns:
                ph = len(pattern.pattern)
                pw = len(pattern.pattern[0]) if ph > 0 else 0
                for i in range(ph):
                    for j in range(pw):
                        if pattern.pattern[i][j] == 1:
                            ri = pattern.start_row + i
                            rj = pattern.start_col + j
                            if 0 <= ri < self.height and 0 <= rj < self.width:
                                new_state[ri][rj] = 1
        self.state = new_state
        
        # 清理被占用的奖励细胞 | Cleanup reward cells that became occupied
        for row, col in reward_cells[:]:
            if self.state[row][col] == 1:
                reward_cells.remove((row, col))