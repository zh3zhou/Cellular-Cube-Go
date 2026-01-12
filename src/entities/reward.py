"""
奖励系统
Reward system
"""
import random
import pygame
from typing import List, Tuple, Optional
from config.game_config import GameConfig
from src.patterns.pattern_generator import PatternGenerator
from src.patterns.progressive_pattern import ProgressivePattern

class RewardManager:
    """
    奖励管理器 - 添加基于速度方向的生成位置
    Reward manager - add spawn positions based on movement direction
    """
    
    def __init__(self):
        self.reward_cells: List[Tuple[int, int]] = []
        self.contacted_rewards: List[Tuple[int, int]] = []
        self.progressive_patterns: List[ProgressivePattern] = []
        self.pattern_generator = PatternGenerator()
        self.creation_counter = 0
        self._current_state = None  # 缓存当前状态 | Cache current state
        # 新增：8方向偏移映射 | Added: 8-direction offset mapping
        self.direction_offsets = {
            'up': (-3, 0),
            'down': (3, 0),
            'left': (0, -3),
            'right': (0, 3),
            'up-left': (-2, -2),
            'up-right': (-2, 2),
            'down-left': (2, -2),
            'down-right': (2, 2),
            'center': (0, 0)
        }
    
    def update(self, state: List[List[int]], player) -> Optional[Tuple[int, int]]:
        """
        更新奖励系统（支持配置开关）
        Update reward system (respect feature toggle)
        """
        # 检查奖励系统是否启用 | Check whether reward system is enabled
        if not GameConfig.REWARD_SYSTEM_ENABLED:
            # 如果禁用，清空所有奖励相关数据 | If disabled, clear reward-related data
            self.reward_cells.clear()
            self.contacted_rewards.clear()
            self.progressive_patterns.clear()
            return None
        
        # 缓存当前状态供其他方法使用 | Cache current state for helper methods
        self._current_state = state
        
        # 清理被占用的奖励细胞 | Cleanup occupied reward cells
        self._cleanup_occupied_rewards(state)
        
        # 尝试创建新的奖励细胞 | Try to create new reward cells
        self._try_create_reward(state)
        
        # 检查玩家接触 | Check player contact
        converted_reward = self._check_player_contact(player)
        
        # 更新渐进式patterns | Update progressive patterns
        self._update_progressive_patterns(state)
        
        return converted_reward
    
    def get_reward_cells(self) -> List[Tuple[int, int]]:
        """
        获取当前奖励细胞列表（支持配置开关）
        Get current reward cells (respect feature toggle)
        """
        if not GameConfig.REWARD_SYSTEM_ENABLED:
            return []
        return self.reward_cells
    
    def get_progressive_patterns(self) -> List[ProgressivePattern]:
        """
        获取当前渐进式patterns列表（支持配置开关）
        Get current progressive patterns (respect feature toggle)
        """
        if not GameConfig.REWARD_SYSTEM_ENABLED:
            return []
        return self.progressive_patterns
    
    def _cleanup_occupied_rewards(self, state: List[List[int]]):
        """
        清理被普通细胞占用的奖励细胞
        Clean up reward cells occupied by normal cells
        """
        cells_to_remove = []
        
        for i, (row, col) in enumerate(self.reward_cells):
            if state[row][col] == 1:
                cells_to_remove.append(i)
        
        for i in reversed(cells_to_remove):
            self.reward_cells.pop(i)
    
    def _try_create_reward(self, state: List[List[int]]):
        """
        尝试创建新的奖励细胞
        Try to create new reward cells
        """
        self.creation_counter += 1
        
        if self.creation_counter >= GameConfig.REWARD_CREATE_INTERVAL:
            self.creation_counter = 0
            self._create_reward_cell(state)
    
    def _create_reward_cell(self, state: List[List[int]]):
        """
        创建奖励细胞
        Create a reward cell
        """
        width = len(state[0])
        height = len(state)
        
        for _ in range(100):  # 最多尝试100次 | Try at most 100 times
            center_row = random.randint(1, height - 2)
            center_col = random.randint(1, width - 2)
            
            if (center_row, center_col) in self.reward_cells:
                continue
            
            if self._is_3x3_area_empty(state, center_row, center_col):
                self.reward_cells.append((center_row, center_col))
                break
    
    def _is_3x3_area_empty(self, state: List[List[int]], center_row: int, center_col: int) -> bool:
        """
        检查3x3区域是否为空
        Check whether a 3x3 area is empty
        """
        for i in range(center_row - 1, center_row + 2):
            for j in range(center_col - 1, center_col + 2):
                if (i < 0 or i >= len(state) or j < 0 or j >= len(state[0]) or 
                    state[i][j] == 1):
                    return False
        return True
    
    def _check_player_contact(self, player) -> Optional[Tuple[int, int]]:
        """
        检查玩家与奖励细胞的接触（更新版）
        Check player contact with reward cells (updated)
        """
        player_surface, player_rect = player.create_surface_and_rect()
        
        for reward in self.reward_cells[:]:
            reward_rect = pygame.Rect(reward[1] * GameConfig.CELL_SIZE, 
                                    reward[0] * GameConfig.CELL_SIZE, 
                                    GameConfig.CELL_SIZE, GameConfig.CELL_SIZE)
            
            if player_rect.colliderect(reward_rect):
                if reward not in self.contacted_rewards:
                    self.contacted_rewards.append(reward)
            else:
                if reward in self.contacted_rewards:
                    self.contacted_rewards.remove(reward)
                    # 传递玩家方向 | Pass player direction
                    return self._convert_reward_to_pattern(reward, player.last_direction)
        
        return None
    
    def _calculate_pattern_position(self, reward_pos: Tuple[int, int], 
                                  direction: str, pattern: List[List[int]]) -> Tuple[int, int]:
        """
        基于方向计算pattern生成位置
        Compute pattern spawn position based on direction
        """
        reward_row, reward_col = reward_pos
        pattern_height = len(pattern)
        pattern_width = len(pattern[0]) if pattern_height > 0 else 0
        
        # 获取方向偏移 | Get directional offset
        offset_row, offset_col = self.direction_offsets.get(direction, (0, 0))
        
        # 计算中心位置 | Compute center position
        center_row = reward_row + offset_row
        center_col = reward_col + offset_col
        
        # 边界检查 | Boundary check
        state_height = len(self._get_current_state())
        state_width = len(self._get_current_state()[0]) if state_height > 0 else 0
        
        # 调整位置确保pattern完全在边界内 | Adjust position to keep pattern within bounds
        final_row = max(0, min(center_row - pattern_height // 2, 
                              state_height - pattern_height))
        final_col = max(0, min(center_col - pattern_width // 2, 
                              state_width - pattern_width))
        
        return (final_row, final_col)
    
    def _convert_reward_to_pattern(self, reward_pos: Tuple[int, int], 
                                player_direction: str) -> Tuple[int, int]:
        """
        将奖励细胞转换为pattern（使用方向算法）
        Convert reward cell to pattern (direction-based algorithm)
        """
        if reward_pos in self.reward_cells:
            # 获取当前状态 | Get current state
            state = self._get_current_state()
            
            # 使用尺寸概率系统生成pattern | Generate pattern using size-probability system
            pattern_obj = self.pattern_generator.create_pattern_with_size_probability(
                state, reward_pos, GameConfig.REWARD_COLOR
            )
            
            if pattern_obj and hasattr(pattern_obj, 'pattern'):
                pattern = pattern_obj.pattern
                
                # 基于玩家方向计算新位置 | Compute new position based on player direction
                new_position = self._calculate_pattern_position(
                    reward_pos, player_direction, pattern
                )
                
                # 创建新的pattern对象 | Create new pattern object
                new_pattern = ProgressivePattern(
                    pattern, new_position[0], new_position[1], 
                    GameConfig.REWARD_COLOR, use_size_based_speed=True
                )
                
                self.progressive_patterns.append(new_pattern)
            
            # 从奖励列表中移除 | Remove from reward list
            self.reward_cells.remove(reward_pos)
        
        return reward_pos
    
    def _get_current_state(self) -> List[List[int]]:
        """
        获取当前游戏状态
        Get current game state
        """
        return self._current_state if self._current_state is not None else []
    
    def _update_progressive_patterns(self, state: List[List[int]]):
        """
        更新渐进式patterns（集成保护区域）
        Update progressive patterns (with protected zones)
        """
        patterns_to_remove = []
        
        for i, prog_pattern in enumerate(self.progressive_patterns):
            if prog_pattern.step():
                # Pattern完成，移除保护区域 | Pattern finished, remove protected zone
                self._remove_pattern_protection(prog_pattern)
                
                # Pattern完成，转化为真实细胞 | Pattern finished, convert to real cells
                self.pattern_generator.apply_pattern_to_state(
                    state, prog_pattern.pattern, 
                    prog_pattern.start_row, prog_pattern.start_col
                )
                patterns_to_remove.append(i)
        
        # 移除已完成的patterns | Remove completed patterns
        for i in reversed(patterns_to_remove):
            self.progressive_patterns.pop(i)
    
    def _add_pattern_protection(self, prog_pattern):
        """
        添加pattern保护区域
        Add pattern protected zone
        """
        pattern_height = len(prog_pattern.pattern)
        pattern_width = len(prog_pattern.pattern[0]) if pattern_height > 0 else 0
        
        # 通过游戏引擎添加保护区域 | Add protected zone via game engine
        # 这里需要游戏引擎的引用，或者通过其他方式传递 | This requires a reference to the game engine or another mechanism
        pass
    
    def _remove_pattern_protection(self, prog_pattern):
        """
        移除pattern保护区域
        Remove pattern protected zone
        """
        pass
    
    # [DEPRECATED] 旧版：直接在奖励细胞位置生成pattern
    # def _convert_reward_to_pattern_old(self, reward_pos: Tuple[int, int]) -> Tuple[int, int]:
    #     """旧版：直接在奖励细胞位置生成pattern（已废弃）"""
    #     # 2025-08-20: 被基于速度方向的生成算法替代
    #     # 原因：直接在奖励细胞位置生成会导致pattern堆叠，游戏流畅性差
    #     # 改进：根据玩家移动方向在相反方向生成，提供更自然的游戏体验
    #     pass
