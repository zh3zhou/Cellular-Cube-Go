"""
渐进式Pattern实现
Progressive pattern implementation
"""
from typing import List, Tuple
from config.pattern_config import PatternConfig
from config.game_config import GameConfig

class ProgressivePattern:
    """
    渐进式Pattern类
    Progressive pattern class
    """
    
    def __init__(self, pattern: List[List[int]], start_row: int, start_col: int, 
                 base_color: Tuple[int, int, int], use_size_based_speed: bool = False):
        self.pattern = pattern
        self.start_row = start_row
        self.start_col = start_col
        self.base_color = base_color
        
        # 计算pattern面积与包围盒面积 | Compute pattern area and bounding box area
        pattern_area = sum(sum(row) for row in pattern)
        pattern_height = len(pattern)
        pattern_width = len(pattern[0]) if pattern_height > 0 else 0
        bounding_area = pattern_height * pattern_width
        
        # 计算基础步数：按面积或按包围盒缩放 | Compute base steps, scaled by area or bounding box
        if use_size_based_speed and getattr(PatternConfig, "SIZE_BASED_SPEED_ENABLED", True):
            base_steps = PatternConfig.PROGRESSIVE_PATTERN_SPEED
            size_scale = max(1.0, bounding_area * PatternConfig.SPEED_SCALING_FACTOR)
            total_steps = int(base_steps * size_scale)
        else:
            # 兼容旧逻辑：按实际活细胞面积放大 | Backward-compatible: scale by live-cell area
            area = max(1, pattern_area)
            total_steps = int(PatternConfig.PROGRESSIVE_PATTERN_SPEED * area)

        # 扩展保护持续时间（时间 X2） | Extend protection duration (time x2)
        mult = getattr(PatternConfig, "PROTECTION_DURATION_MULTIPLIER", 1.0)
        try:
            total_steps = int(total_steps * mult)
        except Exception:
            pass
        # 先应用全局上限 | Cap by global max age
        total_steps = min(total_steps, PatternConfig.PROGRESSIVE_PATTERN_MAX_AGE)

        # 应用最小/最大步数夹取（将“速度”作为总步数上下界理解） | Clamp by min/max steps
        min_steps = int(getattr(PatternConfig, "MIN_PATTERN_SPEED", 1))
        max_steps = int(getattr(PatternConfig, "MAX_PATTERN_SPEED", PatternConfig.PROGRESSIVE_PATTERN_MAX_AGE))
        lo, hi = (min(min_steps, max_steps), max(min_steps, max_steps))
        total_steps = max(1, max(lo, min(total_steps, hi)))

        self.total_steps = total_steps
        
        self.current_step = 0
        self.active = True
        self.pattern_area = pattern_area
        self._evolution_started = False
        self._half_step = max(1, self.total_steps // 2)
    
    def get_color(self) -> Tuple[int, int, int]:
        """
        获取当前渐变颜色
        Get current gradient color
        """
        if not self.active:
            return self.base_color
        
        # 计算渐变进度 (0.0 到 1.0) | Compute gradient progress (0.0 to 1.0)
        progress = 1.0 if self.total_steps <= 0 else (self.current_step / self.total_steps)
        
        # 从透明到完全不透明的渐变 | Gradient from transparent to fully opaque
        r, g, b = self.base_color
        
        # 应用渐变效果 | Apply gradient effect
        fade_factor = progress
        r = int(r * fade_factor)
        g = int(g * fade_factor)
        b = int(b * fade_factor)
        
        # 确保颜色值在有效范围内 | Ensure color values within valid range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        return (r, g, b)
    
    def step(self) -> bool:
        """
        执行一步渐变
        Perform one gradient step
        """
        if self.active:
            self.current_step += 1
            if (not self._evolution_started) and (self.current_step > self._half_step):
                self._evolution_started = True
            if self._evolution_started and self.current_step < self.total_steps:
                self._evolve_once()
            if self.current_step >= self.total_steps:
                self.active = False
                return True  # 准备转化为真实细胞 | Ready to convert into real cells
        return False

    def _evolve_once(self) -> None:
        """
        在包围盒内执行一次独立演化（B3/S23，与 GameConfig 一致）
        Evolve pattern one step inside its bounding box, independently
        """
        h = len(self.pattern)
        w = len(self.pattern[0]) if h > 0 else 0
        if h == 0 or w == 0:
            return
        cur = self.pattern
        # 计算邻居（零填充，不环绕）
        def count_neighbors(y: int, x: int) -> int:
            cnt = 0
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    ny, nx = y + di, x + dj
                    if 0 <= ny < h and 0 <= nx < w:
                        cnt += cur[ny][nx]
            return cnt
        new = [[0] * w for _ in range(h)]
        for i in range(h):
            for j in range(w):
                n = count_neighbors(i, j)
                if cur[i][j] == 1:
                    new[i][j] = 1 if (GameConfig.LIVE_MIN_NEIGHBORS <= n <= GameConfig.LIVE_MAX_NEIGHBORS) else 0
                else:
                    new[i][j] = 1 if (GameConfig.BORN_MIN_NEIGHBORS <= n <= GameConfig.BORN_MAX_NEIGHBORS) else 0
        self.pattern = new