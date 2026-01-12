"""
Pattern生成逻辑
"""
import random
from typing import List, Tuple, Optional, Dict, Any
from src.patterns.pattern_library import PatternLibrary
from src.patterns.progressive_pattern import ProgressivePattern
from config.pattern_config import PatternConfig
from src.core.collision_detection import CollisionDetector
from collections import deque

class PatternGenerator:
    """Pattern生成器"""
    
    def __init__(self):
        self.pattern_library = PatternLibrary()
        self.collision_detector = CollisionDetector()
        # 记录近期选择，避免短时间内重复同一图案
        self._recent_by_size = {}
        # 记录最近两次选择的尺寸，用于概率调整（鼓励尺寸差异）
        self._recent_sizes = deque(maxlen=2)
        self._history = deque(maxlen=getattr(PatternConfig, 'WINDOW_SIZE', 200))
        self._survival_scale = 0.0
    
    def create_progressive_pattern(self, position: Tuple[int, int], 
                                 color: Tuple[int, int, int]) -> Optional[ProgressivePattern]:
        """创建渐进式pattern"""
        row, col = position
        
        # 选择一个简单的pattern作为示例
        pattern = [[1]]  # 单细胞pattern
        
        return ProgressivePattern(pattern, row, col, color)
    
    def create_pattern_with_size_probability(self, state: List[List[int]], 
                                           position: Tuple[int, int], 
                                           color: Tuple[int, int, int]) -> Optional[ProgressivePattern]:
        """按尺寸概率选择，并避免短时重复；边界自适应"""
        row, col = position
        state_height = len(state)
        state_width = len(state[0]) if state_height > 0 else 0
        
        # 1) 计算每个尺寸在当前位置的可用比例，过滤至少50%可用的尺寸
        available_sizes = []
        emptiness_map = {}
        for size in list(self.pattern_library.get_all_sizes()):
            pattern_height, pattern_width = size
            start_row = max(0, min(row - pattern_height // 2, state_height - pattern_height))
            start_col = max(0, min(col - pattern_width // 2, state_width - pattern_width))
            
            available_area = 0
            total_area = pattern_height * pattern_width
            for i in range(pattern_height):
                for j in range(pattern_width):
                    if (0 <= start_row + i < state_height and 
                        0 <= start_col + j < state_width):
                        available_area += 1
            if total_area == 0:
                continue
            if available_area / total_area >= 0.5:
                available_sizes.append(size)
                free = 0
                for i in range(pattern_height):
                    for j in range(pattern_width):
                        rr = start_row + i
                        cc = start_col + j
                        if (0 <= rr < state_height and 0 <= cc < state_width):
                            if state[rr][cc] == 0:
                                free += 1
                emptiness_map[size] = free / total_area if total_area else 0.0
        
        if not available_sizes:
            return None
        
        # 2) 使用配置权重计算尺寸选择概率，并随机选一个尺寸
        size_probs = self._calculate_size_probabilities(available_sizes, (state_height, state_width), emptiness_map)
        selected_size = self._select_pattern_size_by_probability(size_probs)
        if selected_size is None:
            return None
        
        # 记录最近选择的尺寸（用于下一次概率调整）
        self._recent_sizes.append(selected_size)

        pattern_height, pattern_width = selected_size
        start_row = max(0, min(row - pattern_height // 2, state_height - pattern_height))
        start_col = max(0, min(col - pattern_width // 2, state_width - pattern_width))
        
        # 3) 在该尺寸下按pattern概率选择一个具体图案，并避免短时重复
        patterns = self.pattern_library.get_patterns_by_size(selected_size)
        name, selected_pattern = self._select_pattern_non_repeating(patterns, selected_size)
        if selected_pattern is None:
            return None
        
        # 不再提前杀死区域，保护逻辑由CA的protected_zones负责
        return ProgressivePattern(selected_pattern, start_row, start_col, 
                                  color, use_size_based_speed=True)
    
    
    
    def _calculate_size_probabilities(self, available_sizes: List[Tuple[int, int]], 
                                   max_rect: Tuple[int, int], emptiness_map: Dict[Tuple[int,int], float] = None) -> Dict[Tuple[int, int], float]:
        """计算尺寸选择概率"""
        if not available_sizes:
            return {}
        
        # 获取配置的权重
        weights = PatternConfig.SIZE_SELECTION_WEIGHTS
        
        # 计算每个尺寸的权重
        size_weights = {}
        max_area = max_rect[0] * max_rect[1]
        last_sizes = list(self._recent_sizes)
        last_1 = last_sizes[-1] if len(last_sizes) >= 1 else None
        last_2 = last_sizes[-2] if len(last_sizes) >= 2 else None
        
        size_counts = {}
        for s, t, n in list(self._history):
            size_counts[s] = size_counts.get(s, 0) + 1
        for size in available_sizes:
            area = size[0] * size[1]
            
            # 基础权重：使用配置中的权重，如果没有则根据面积计算
            if size in weights:
                base_weight = weights[size] * PatternConfig.BASE_WEIGHT_MULTIPLIER
            else:
                base_weight = area / max_area * PatternConfig.DEFAULT_WEIGHT_SCALE
            
            # 应用多样性因子
            diversity_bonus = (1 - area / max_area) * PatternConfig.SIZE_DIVERSITY_FACTOR
            
            # 最大尺寸奖励
            max_bonus = 0
            if PatternConfig.ENABLE_MAX_SIZE_BONUS and area == max_area:
                max_bonus = PatternConfig.MAX_PATTERN_BIAS
            
            final_weight = base_weight + diversity_bonus + max_bonus

            # 引入“最近两次尺寸”惩罚与差异奖励：尽量选不同大小
            penalty_multiplier = 1.0
            if last_1 is not None and size == last_1:
                penalty_multiplier *= (1.0 - getattr(PatternConfig, 'RECENCY_LAST_PENALTY', 0.5))
            if last_2 is not None and size == last_2:
                penalty_multiplier *= (1.0 - getattr(PatternConfig, 'RECENCY_SECOND_PENALTY', 0.25))

            # 与最近一次的面积差异越大，奖励越高
            variety_multiplier = 1.0
            if last_1 is not None:
                last_area = last_1[0] * last_1[1]
                diff_norm = abs(area - last_area) / max_area  # 0..1
                variety_multiplier += diff_norm * getattr(PatternConfig, 'SIZE_VARIETY_BONUS', 0.5)

            inv_alpha = getattr(PatternConfig, 'INV_FREQ_ALPHA', 0.5) * (1.0 + self._survival_scale)
            inv_size = 1.0 / ((1.0 + inv_alpha * size_counts.get(size, 0)) ** 0.5)
            empty = 0.0
            if emptiness_map is not None and size in emptiness_map:
                empty = emptiness_map[size]
            empty_gain = 1.0 + empty * getattr(PatternConfig, 'EMPTINESS_GAIN', 0.8)
            large_bonus = 1.0
            if (size[0] * size[1]) >= getattr(PatternConfig, 'LARGE_AREA_THRESHOLD', 64):
                large_bonus = 1.0 + empty * getattr(PatternConfig, 'LARGE_SIZE_EMPTY_BONUS', 0.6)
            final_weight = max(0.01, final_weight * penalty_multiplier * variety_multiplier * inv_size * empty_gain * large_bonus)
            size_weights[size] = max(0.01, final_weight)  # 确保最小权重
        
        # 归一化概率
        total_weight = sum(size_weights.values())
        probabilities = {size: weight / total_weight for size, weight in size_weights.items()}
        
        # 调试输出
        if PatternConfig.DEBUG_PATTERN_SELECTION:
            print(f"可用尺寸: {available_sizes}")
            print(f"最大区域: {max_rect}")
            print(f"尺寸概率: {probabilities}")
        
        return probabilities
    
    def _select_pattern_size_by_probability(self, size_probabilities: Dict[Tuple[int, int], float]) -> Optional[Tuple[int, int]]:
        """根据概率选择pattern尺寸"""
        if not size_probabilities:
            return None
        
        rand_val = random.random()
        cumulative_prob = 0.0
        
        for size, prob in size_probabilities.items():
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                return size
        
        # 如果没有选中，返回最后一个
        return list(size_probabilities.keys())[-1]
    
    
    
    def _select_pattern_non_repeating(self, patterns: Dict[str, Any], size: Tuple[int, int]):
        """按概率选择具体pattern，同时避免近期重复（循环队列）"""
        if not patterns:
            return None, None
        
        names = list(patterns.keys())
        if size not in self._recent_by_size:
            self._recent_by_size[size] = deque(maxlen=min(3, len(names)))
        recent = set(self._recent_by_size[size])
        window_types = {}
        for s, t, n in list(self._history):
            window_types[t] = window_types.get(t, 0) + 1
        total_hist = max(1, len(self._history))
        weights = []
        for n in names:
            info = patterns[n]
            base = float(info.get('probability', 0.2))
            t = info.get('type', 'other')
            quota = getattr(PatternConfig, 'TYPE_QUOTAS', {}).get(t, 0.0)
            ratio = window_types.get(t, 0) / total_hist
            quota_gain = getattr(PatternConfig, 'QUOTA_GAIN', 0.6) * (1.0 + self._survival_scale)
            quota_boost = max(0.0, quota - ratio) * quota_gain
            recency_mult = 0.5 if n in recent else 1.0
            rare_boost = 0.0
            if base < getattr(PatternConfig, 'RARE_THRESHOLD', 0.15):
                rare_boost = min(getattr(PatternConfig, 'SURVIVAL_RARE_MAX_BOOST', 0.5), self._survival_scale)
            w = max(0.001, base) * (1.0 + quota_boost) * recency_mult * (1.0 + rare_boost)
            weights.append((n, w))
        total_w = sum(w for _, w in weights)
        r = random.random() * (total_w if total_w > 0 else 1.0)
        acc = 0.0
        chosen_name = weights[0][0]
        for n, w in weights:
            acc += w
            if r <= acc:
                chosen_name = n
                break
        chosen_pattern = patterns[chosen_name]['pattern']
        self._recent_by_size[size].append(chosen_name)
        t = patterns[chosen_name].get('type', 'other')
        self._history.append((size, t, chosen_name))
        return chosen_name, chosen_pattern

    def set_survival_scale(self, scale: float):
        m = getattr(PatternConfig, 'SURVIVAL_STRENGTH_MAX', 1.0)
        if scale < 0.0:
            scale = 0.0
        if scale > m:
            scale = m
        self._survival_scale = scale
    
    def apply_pattern_to_state(self, state: List[List[int]], pattern: List[List[int]], 
                             start_row: int, start_col: int):
        """将pattern应用到游戏状态"""
        for i, row in enumerate(pattern):
            for j, cell in enumerate(row):
                if cell == 1:
                    target_row = start_row + i
                    target_col = start_col + j
                    
                    if (0 <= target_row < len(state) and 
                        0 <= target_col < len(state[0])):
                        state[target_row][target_col] = 1