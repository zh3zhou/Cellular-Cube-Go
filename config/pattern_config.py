"""
Pattern相关配置
"""

class PatternConfig:
    # 渐进式Pattern设置
    PROGRESSIVE_PATTERN_SPEED = 15
    PROGRESSIVE_PATTERN_MAX_AGE = 180
    
    # 尺寸选择策略
    SELECTION_STRATEGY = "size_probability"  # "single_cell" | "size_probability"
    FALLBACK_STRATEGY = "single_cell"  # "single_cell" | "min_fit" | "closest_configured_size"
    
    # 尺寸选择权重系数
    BASE_WEIGHT_MULTIPLIER = 1.0
    SIZE_DIVERSITY_FACTOR = 0.3
    MAX_PATTERN_BIAS = 2.0
    ENABLE_MAX_SIZE_BONUS = True
    DEFAULT_WEIGHT_SCALE = 0.1
    
    # 尺寸约束
    MIN_PATTERN_AREA = 1
    MAX_PATTERN_AREA = 225  # 15x15
    
    # 调试设置
    DEBUG_PATTERN_SELECTION = False  # 是否输出尺寸选择调试信息
    
    # 具体尺寸权重（覆盖所有库中的尺寸）
    # 调整权重配置，显著偏向大尺寸
    SIZE_SELECTION_WEIGHTS = {
        # 小尺寸（10%概率区间）
        (3, 3): 0.15, (4, 4): 0.18, (5, 5): 0.20,
        
        # 中等尺寸（45%概率区间）
        (6, 6): 0.25, (7, 7): 0.28, (8, 8): 0.30, (9, 9): 0.25,
        
        # 大尺寸（35%概率区间）
        (10, 10): 0.20, (11, 11): 0.18, (12, 12): 0.15,
        
        # 超大尺寸（10%概率区间）
        (13, 13): 0.12, (14, 14): 0.10, (15, 15): 0.08,
    }
    
    TYPE_QUOTAS = {
        "spaceship": 0.25,
        "oscillator": 0.25,
        "still_life": 0.20,
        "gun": 0.05,
        "other": 0.25,
    }
    WINDOW_SIZE = 200
    QUOTA_GAIN = 0.6
    INV_FREQ_ALPHA = 0.5
    RARE_THRESHOLD = 0.15
    SURVIVAL_RARE_MAX_BOOST = 0.5
    SURVIVAL_STRENGTH_MAX = 1.0
    EMPTINESS_GAIN = 0.8
    LARGE_AREA_THRESHOLD = 64
    LARGE_SIZE_EMPTY_BONUS = 0.6
    PROTECTION_DURATION_MULTIPLIER = 2.0
    
    # 难度级别预设（方便总体调整）
    DIFFICULTY_PRESETS = {
        "easy": {
            "BASE_WEIGHT_MULTIPLIER": 1.5,
            "SIZE_DIVERSITY_FACTOR": 0.1,  # 偏向大尺寸
            "MAX_PATTERN_BIAS": 3.0,
        },
        "normal": {
            "BASE_WEIGHT_MULTIPLIER": 1.0,
            "SIZE_DIVERSITY_FACTOR": 0.3,
            "MAX_PATTERN_BIAS": 2.0,
        },
        "hard": {
            "BASE_WEIGHT_MULTIPLIER": 0.8,
            "SIZE_DIVERSITY_FACTOR": 0.6,  # 偏向小尺寸
            "MAX_PATTERN_BIAS": 1.5,
        }
    }
    
    @classmethod
    def apply_difficulty_preset(cls, difficulty: str):
        """应用难度预设"""
        if difficulty in cls.DIFFICULTY_PRESETS:
            preset = cls.DIFFICULTY_PRESETS[difficulty]
            cls.BASE_WEIGHT_MULTIPLIER = preset["BASE_WEIGHT_MULTIPLIER"]
            cls.SIZE_DIVERSITY_FACTOR = preset["SIZE_DIVERSITY_FACTOR"]
            cls.MAX_PATTERN_BIAS = preset["MAX_PATTERN_BIAS"]
    
    @classmethod
    def scale_all_weights(cls, scale_factor: float):
        """按比例调整所有尺寸权重"""
        for size in cls.SIZE_SELECTION_WEIGHTS:
            cls.SIZE_SELECTION_WEIGHTS[size] *= scale_factor
    
    @classmethod
    def boost_small_patterns(cls, boost_factor: float = 1.5):
        """增强小尺寸 pattern 的权重"""
        for size, weight in cls.SIZE_SELECTION_WEIGHTS.items():
            area = size[0] * size[1]
            if area <= 16:  # 4x4 及以下
                cls.SIZE_SELECTION_WEIGHTS[size] = weight * boost_factor
    
    @classmethod
    def boost_large_patterns(cls, boost_factor: float = 1.5):
        """增强大尺寸 pattern 的权重"""
        for size, weight in cls.SIZE_SELECTION_WEIGHTS.items():
            area = size[0] * size[1]
            if area >= 64:  # 8x8 及以上
                cls.SIZE_SELECTION_WEIGHTS[size] = weight * boost_factor
    
    # 基于大小的速度调整配置
    SIZE_BASED_SPEED_ENABLED = True
    MIN_PATTERN_SPEED = 10  # 最小速度（最快）
    MAX_PATTERN_SPEED = 40  # 最大速度（最慢）
    SPEED_SCALING_FACTOR = 0.15  # 速度缩放因子

    # 最近尺寸影响（鼓励与最近两次不同的尺寸）
    RECENCY_LAST_PENALTY = 0.5        # 与最近一次相同尺寸时的权重折减比例
    RECENCY_SECOND_PENALTY = 0.25     # 与倒数第二次相同尺寸时的权重折减比例
    SIZE_VARIETY_BONUS = 0.5          # 与最近一次面积差异越大，奖励越高（0..1加权）