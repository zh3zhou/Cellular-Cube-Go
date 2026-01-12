"""
数学工具函数
Math utility functions
"""
import math
from typing import Tuple

def distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    计算两点间距离
    Calculate distance between two points
    """
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    将值限制在指定范围内
    Clamp value to the specified range
    """
    return max(min_val, min(value, max_val))

def normalize_vector(vector: Tuple[float, float]) -> Tuple[float, float]:
    """
    归一化向量
    Normalize a 2D vector
    """
    length = math.sqrt(vector[0]**2 + vector[1]**2)
    if length == 0:
        return (0, 0)
    return (vector[0] / length, vector[1] / length)