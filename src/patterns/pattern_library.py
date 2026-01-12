"""
Pattern库管理
"""
from typing import Dict, List, Tuple, Any
import json
from pathlib import Path
from config.pattern_config import PatternConfig

class PatternLibrary:
    """Pattern库管理类"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        extra = self._load_external_patterns()
        if extra:
            for size, patterns in extra.items():
                if size not in self.patterns:
                    self.patterns[size] = {}
                for name, info in patterns.items():
                    if name not in self.patterns[size]:
                        self.patterns[size][name] = info
        self._ensure_types()

    def _classify_type(self, name: str) -> str:
        n = name.lower()
        if any(k in n for k in ["glider", "lwss", "mwss", "hwss", "spaceship"]):
            return "spaceship"
        if any(k in n for k in ["gun", "glider_gun"]):
            return "gun"
        if any(k in n for k in ["blinker", "pulsar", "toad", "clock", "figure_eight", "pentadecathlon"]):
            return "oscillator"
        if any(k in n for k in ["block", "beehive", "loaf", "boat", "tub", "barge", "pond", "snake", "ship", "aircraft_carrier"]):
            return "still_life"
        return "other"

    def _ensure_types(self) -> None:
        for size, patterns in self.patterns.items():
            for name, info in patterns.items():
                if "type" not in info:
                    info["type"] = self._classify_type(name)

    def _load_external_patterns(self) -> Dict[Tuple[int, int], Dict[str, Any]]:
        try:
            root = Path(__file__).resolve().parents[2]
            p = root / 'assets' / 'patterns' / 'library.json'
            if not p.exists():
                return {}
            with p.open('r', encoding='utf-8') as f:
                data = json.load(f)
            result: Dict[Tuple[int, int], Dict[str, Any]] = {}
            for size_str, patterns in data.items():
                if 'x' not in size_str:
                    continue
                h, w = size_str.split('x')
                try:
                    key = (int(h), int(w))
                except ValueError:
                    continue
                conv = {}
                for name, info in patterns.items():
                    pat = info.get('pattern')
                    prob = float(info.get('probability', 0.2))
                    if not pat or not isinstance(pat, list):
                        continue
                    t = info.get('type')
                    if not t:
                        t = self._classify_type(name)
                    conv[name] = {'pattern': pat, 'probability': prob, 'type': t}
                if conv:
                    result[key] = conv
            return result
        except Exception:
            return {}
    
    def _initialize_patterns(self) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """初始化Pattern库"""
        return {
            # 3x3 patterns
            (3, 3): {
                'glider': {
                    'pattern': [
                        [0, 1, 0],
                        [0, 0, 1],
                        [1, 1, 1]
                    ],
                    'probability': 0.3
                },
                'block': {
                    'pattern': [
                        [1, 1, 0],
                        [1, 1, 0],
                        [0, 0, 0]
                    ],
                    'probability': 0.1
                },
                'blinker': {
                    'pattern': [
                        [0, 0, 0],
                        [1, 1, 1],
                        [0, 0, 0]
                    ],
                    'probability': 0.1
                },
                'r_pentomino': {
                    'pattern': [
                        [0, 1, 1],
                        [1, 1, 0],
                        [0, 1, 0]
                    ],
                    'probability': 0.5
                }
            },
            
            # 2x4 patterns (长方形)
            (2, 4): {
                'traffic_light': {
                    'pattern': [
                        [1, 1, 1, 0],
                        [0, 1, 1, 1]
                    ],
                    'probability': 0.6
                },
                'double_blinker': {
                    'pattern': [
                        [1, 1, 1, 1],
                        [0, 0, 0, 0]
                    ],
                    'probability': 0.4
                }
            },
            
            # 4x2 patterns (长方形)
            (4, 2): {
                'vertical_blinker': {
                    'pattern': [
                        [1, 0],
                        [1, 0],
                        [1, 0],
                        [1, 0]
                    ],
                    'probability': 0.5
                },
                'ladder': {
                    'pattern': [
                        [1, 1],
                        [0, 0],
                        [1, 1],
                        [0, 0]
                    ],
                    'probability': 0.5
                }
            },
            
            # 3x5 patterns (长方形)
            (3, 5): {
                'lightweight_spaceship': {
                    'pattern': [
                        [0, 1, 1, 1, 1],
                        [1, 0, 0, 0, 1],
                        [0, 0, 0, 0, 1]
                    ],
                    'probability': 0.7
                },
                'wave': {
                    'pattern': [
                        [1, 0, 1, 0, 1],
                        [0, 1, 1, 1, 0],
                        [1, 0, 1, 0, 1]
                    ],
                    'probability': 0.3
                }
            },
            
            # 5x3 patterns (长方形)
            (5, 3): {
                'vertical_spaceship': {
                    'pattern': [
                        [0, 1, 0],
                        [1, 0, 1],
                        [1, 0, 1],
                        [1, 0, 1],
                        [0, 1, 0]
                    ],
                    'probability': 0.6
                },
                'tower': {
                    'pattern': [
                        [1, 1, 1],
                        [0, 1, 0],
                        [0, 1, 0],
                        [0, 1, 0],
                        [1, 1, 1]
                    ],
                    'probability': 0.4
                }
            },
            
            # 4x4 patterns (正方形)
            (4, 4): {
                'beacon': {
                    'pattern': [
                        [1, 1, 0, 0],
                        [1, 1, 0, 0],
                        [0, 0, 1, 1],
                        [0, 0, 1, 1]
                    ],
                    'probability': 0.5
                },
                'toad': {
                    'pattern': [
                        [0, 0, 0, 0],
                        [0, 1, 1, 1],
                        [1, 1, 1, 0],
                        [0, 0, 0, 0]
                    ],
                    'probability': 0.5
                }
            },
            
            # 2x6 patterns (长方形)
            (2, 6): {
                'long_blinker': {
                    'pattern': [
                        [1, 1, 1, 1, 1, 1],
                        [0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.4
                },
                'alternating': {
                    'pattern': [
                        [1, 0, 1, 0, 1, 0],
                        [0, 1, 0, 1, 0, 1]
                    ],
                    'probability': 0.6
                }
            },
            
            # 6x2 patterns (长方形)
            (6, 2): {
                'vertical_long_blinker': {
                    'pattern': [
                        [1, 0],
                        [1, 0],
                        [1, 0],
                        [1, 0],
                        [1, 0],
                        [1, 0]
                    ],
                    'probability': 0.5
                },
                'double_column': {
                    'pattern': [
                        [1, 1],
                        [0, 0],
                        [1, 1],
                        [0, 0],
                        [1, 1],
                        [0, 0]
                    ],
                    'probability': 0.5
                }
            },
            
            # 3x8 patterns (垂直长条图案)
            (3, 8): {
                'vertical_double_cluster': {
                    'pattern': [
                        [0, 1, 0, 0, 0, 0, 0, 0],
                        [1, 1, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 1, 0, 0]
                    ],
                    'probability': 0.3
                },
                'separated_vertical_groups': {
                    'pattern': [
                        [0, 1, 0, 0, 0, 0, 0, 0],
                        [1, 1, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 1, 1, 0]
                    ],
                    'probability': 0.2
                },
                'diehard': {
                    'pattern': [
                        [0, 0, 0, 0, 0, 0, 0, 1],
                        [0, 1, 1, 0, 0, 0, 0, 0],
                        [1, 0, 0, 0, 1, 0, 0, 0]
                    ],
                    'probability': 0.5
                }
            },
            
            # 5x5 patterns (正方形)
            (5, 5): {
                'pulsar_fragment': {
                    'pattern': [
                        [0, 0, 1, 0, 0],
                        [0, 0, 1, 0, 0],
                        [0, 0, 1, 0, 0],
                        [0, 0, 0, 0, 0],
                        [1, 1, 1, 1, 1]
                    ],
                    'probability': 0.6
                },
                'cross': {
                    'pattern': [
                        [0, 0, 1, 0, 0],
                        [0, 1, 1, 1, 0],
                        [1, 1, 1, 1, 1],
                        [0, 1, 1, 1, 0],
                        [0, 0, 1, 0, 0]
                    ],
                    'probability': 0.4
                }
            },
            
            # 9x9 patterns (中型复杂十字图案)
            (9, 9): {
                'complex_cross_pattern': {
                    'pattern': [
                        [0, 0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 1, 1, 1, 1, 0, 0, 0, 0],
                        [0, 1, 1, 0, 1, 1, 1, 0, 0],
                        [1, 1, 0, 0, 0, 0, 1, 1, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0, 1],
                        [0, 1, 1, 0, 0, 0, 0, 1, 1],
                        [0, 0, 1, 1, 1, 0, 1, 1, 0],
                        [0, 0, 0, 0, 1, 1, 1, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0, 0]
                    ],
                    'probability': 0.3
                },
                'scattered_cross_variant': {
                    'pattern': [
                        [0, 0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 1, 1, 1, 1, 0, 0, 0, 0],
                        [0, 1, 1, 0, 1, 1, 1, 0, 0],
                        [1, 1, 0, 0, 0, 0, 1, 1, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0, 1],
                        [0, 1, 1, 0, 0, 0, 0, 1, 1],
                        [0, 0, 1, 1, 1, 0, 1, 1, 0],
                        [0, 0, 0, 0, 1, 1, 1, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0, 0]
                    ],
                    'probability': 0.25
                }
            },
            
            # 11x11 patterns (大型对称图案)
            (11, 11): {
                'large_symmetric_cross': {
                    'pattern': [
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0],
                        [0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0],
                        [1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1],
                        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1],
                        [1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0],
                        [0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0],
                        [0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.15
                },
                'complex_diamond_cross': {
                    'pattern': [
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0],
                        [0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0],
                        [1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1],
                        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1],
                        [1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0],
                        [0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0],
                        [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.15
                }
            },
            
            # 10x12 patterns (大型分散图案)
            (10, 12): {
                'scattered_clusters': {
                    'pattern': [
                        [0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0],
                        [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1],
                        [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
                        [1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],
                        [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.2
                },
                'multi_cluster_pattern': {
                    'pattern': [
                        [0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0],
                        [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1],
                        [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
                        [1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0],
                        [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.2
                }
            },
            
            # 6x14 patterns (超大横向分散图案)
            (6, 14): {
                'mega_horizontal_scatter': {
                    'pattern': [
                        [0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0],
                        [0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0],
                        [1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1],
                        [1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0],
                        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.1
                },
                'complex_horizontal_clusters': {
                    'pattern': [
                        [0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0],
                        [0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0],
                        [1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1],
                        [1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0],
                        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.15
                }
            },
            
            # 12x12 patterns (超大复杂图案)
            (12, 12): {
                'mega_complex_structure': {
                    'pattern': [
                        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1],
                        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
                    ],
                    'probability': 0.1
                },
                'scattered_mega_pattern': {
                    'pattern': [
                        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1],
                        [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
                    ],
                    'probability': 0.1
                },
                # 新增：经典的Gosper滑翔机枪的简化版本
                'gosper_gun_fragment': {
                    'pattern': [
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                        [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        [1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0]
                    ],
                    'probability': 0.05
                }
            },
            
            # 新增：经典元胞自动机patterns
            
            # 7x7 patterns (中型经典图案)
            (7, 7): {
                'pentadecathlon': {
                    'pattern': [
                        [0, 0, 1, 0, 1, 0, 0],
                        [1, 1, 0, 0, 0, 1, 1],
                        [0, 0, 1, 0, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 1, 0, 0],
                        [1, 1, 0, 0, 0, 1, 1],
                        [0, 0, 1, 0, 1, 0, 0]
                    ],
                    'probability': 0.3
                },
                'pulsar_core': {
                    'pattern': [
                        [0, 0, 1, 1, 1, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0],
                        [1, 0, 0, 1, 0, 0, 1],
                        [1, 1, 1, 0, 1, 1, 1],
                        [1, 0, 0, 1, 0, 0, 1],
                        [0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 1, 1, 1, 0, 0]
                    ],
                    'probability': 0.4
                },
                'figure_eight': {
                    'pattern': [
                        [0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 1, 1, 1, 0, 0],
                        [0, 1, 1, 0, 1, 1, 0],
                        [1, 1, 0, 0, 0, 1, 1],
                        [0, 1, 1, 0, 1, 1, 0],
                        [0, 0, 1, 1, 1, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0]
                    ],
                    'probability': 0.3
                }
            },
            
            # 8x8 patterns (中大型图案)
            (8, 8): {
                'clock': {
                    'pattern': [
                        [0, 0, 1, 1, 0, 0, 0, 0],
                        [0, 0, 1, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 1, 0, 0],
                        [0, 0, 0, 0, 1, 1, 0, 0],
                        [0, 0, 1, 1, 0, 0, 0, 0],
                        [0, 0, 1, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 1, 0, 0],
                        [0, 0, 0, 0, 1, 1, 0, 0]
                    ],
                    'probability': 0.4
                },
                'galaxy': {
                    'pattern': [
                        [1, 1, 0, 1, 1, 0, 0, 0],
                        [1, 1, 0, 1, 1, 0, 0, 0],
                        [0, 0, 0, 1, 1, 0, 0, 0],
                        [1, 1, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 1, 1, 1],
                        [0, 0, 0, 1, 1, 0, 0, 0],
                        [0, 0, 0, 1, 1, 0, 1, 1],
                        [0, 0, 0, 1, 1, 0, 1, 1]
                    ],
                    'probability': 0.3
                },
                'spider': {
                    'pattern': [
                        [0, 1, 0, 0, 0, 0, 1, 0],
                        [0, 0, 1, 0, 0, 1, 0, 0],
                        [1, 1, 0, 1, 1, 0, 1, 1],
                        [0, 0, 1, 0, 0, 1, 0, 0],
                        [0, 0, 1, 0, 0, 1, 0, 0],
                        [1, 1, 0, 1, 1, 0, 1, 1],
                        [0, 0, 1, 0, 0, 1, 0, 0],
                        [0, 1, 0, 0, 0, 0, 1, 0]
                    ],
                    'probability': 0.3
                }
            },
            
            # 6x6 patterns (中型对称图案)
            (6, 6): {
                'hexapod': {
                    'pattern': [
                        [0, 1, 1, 1, 1, 0],
                        [1, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 1],
                        [0, 1, 1, 1, 1, 0]
                    ],
                    'probability': 0.4
                },
                'flower': {
                    'pattern': [
                        [0, 0, 1, 1, 0, 0],
                        [0, 1, 0, 0, 1, 0],
                        [1, 0, 1, 1, 0, 1],
                        [1, 0, 1, 1, 0, 1],
                        [0, 1, 0, 0, 1, 0],
                        [0, 0, 1, 1, 0, 0]
                    ],
                    'probability': 0.3
                },
                'butterfly': {
                    'pattern': [
                        [1, 0, 0, 0, 0, 1],
                        [0, 1, 1, 1, 1, 0],
                        [0, 1, 0, 0, 1, 0],
                        [0, 1, 0, 0, 1, 0],
                        [0, 1, 1, 1, 1, 0],
                        [1, 0, 0, 0, 0, 1]
                    ],
                    'probability': 0.3
                }
            },
            
            # 10x10 patterns (大型复杂图案)
            (10, 10): {
                'copperhead': {
                    'pattern': [
                        [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
                        [1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
                        [1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
                        [0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
                        [1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
                        [1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
                        [0, 1, 1, 0, 0, 0, 0, 1, 1, 0]
                    ],
                    'probability': 0.2
                },
                'weekender': {
                    'pattern': [
                        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
                        [0, 1, 0, 0, 1, 1, 0, 0, 1, 0],
                        [1, 0, 1, 0, 0, 0, 0, 1, 0, 1],
                        [1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
                        [0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
                        [0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
                        [1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
                        [1, 0, 1, 0, 0, 0, 0, 1, 0, 1],
                        [0, 1, 0, 0, 1, 1, 0, 0, 1, 0],
                        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
                    ],
                    'probability': 0.15
                },
                'twin_bees_shuttle': {
                    'pattern': [
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
                        [0, 1, 0, 0, 1, 1, 0, 0, 1, 0],
                        [0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
                        [0, 1, 0, 0, 1, 1, 0, 0, 1, 0],
                        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.1
                }
            },
            
            # 15x15 patterns (超大型复杂图案)
            (15, 15): {
                'pulsar': {
                    'pattern': [
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
                        [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
                        [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.05
                },
                'big_s': {
                    'pattern': [
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                        [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
                        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ],
                    'probability': 0.03
                }
            },
            # 3x7 patterns (Acorn)
            (3, 7): {
                'acorn': {
                    'pattern': [
                        [0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0],
                        [1, 1, 0, 0, 1, 1, 1]
                    ],
                    'probability': 0.6
                }
            },
            # 4x5 patterns (LWSS)
            (4, 5): {
                'lwss': {
                    'pattern': [
                        [0, 0, 1, 0, 1],
                        [1, 0, 0, 0, 0],
                        [1, 0, 0, 0, 1],
                        [1, 1, 1, 1, 0]
                    ],
                    'probability': 0.5
                }
            },
            # 10x3 patterns (Pentadecathlon)
            (10, 3): {
                'pentadecathlon_10x3': {
                    'pattern': [
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [1, 1, 0, 1, 1, 1, 1, 0, 1, 1],
                        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0]
                    ],
                    'probability': 0.5
                }
            },
            # 13x13 patterns (Pulsar canonical)
            (13, 13): {
                'pulsar_canonical': {
                    'pattern': [
                        [0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
                        [0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
                        [0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
                        [0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0],
                        [0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
                        [0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
                        [0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0]
                    ],
                    'probability': 0.4
                }
            }
        }
    
    def get_patterns_by_size(self, size: Tuple[int, int]) -> Dict[str, Any]:
        """根据尺寸获取patterns"""
        return self.patterns.get(size, {})
    
    def get_all_sizes(self) -> List[Tuple[int, int]]:
        """获取所有可用的pattern尺寸"""
        return list(self.patterns.keys())
    
    def get_max_pattern_size(self) -> Tuple[int, int]:
        """获取最大的pattern尺寸"""
        sizes = self.get_all_sizes()
        if not sizes:
            return (0, 0)
        return max(sizes, key=lambda x: x[0] * x[1])
    
    def get_patterns_that_fit(self, max_width: int, max_height: int) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """获取能够适应指定尺寸的所有patterns"""
        fitting_patterns = {}
        for size, patterns in self.patterns.items():
            if size[0] <= max_width and size[1] <= max_height:
                fitting_patterns[size] = patterns
        return fitting_patterns
    
    def add_pattern(self, size: Tuple[int, int], name: str, 
                   pattern: List[List[int]], probability: float) -> None:
        """添加新的pattern"""
        if size not in self.patterns:
            self.patterns[size] = {}
        
        self.patterns[size][name] = {
            'pattern': pattern,
            'probability': probability
        }
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """获取pattern库统计信息"""
        total_patterns = sum(len(patterns) for patterns in self.patterns.values())
        size_distribution = {size: len(patterns) for size, patterns in self.patterns.items()}
        
        return {
            'total_patterns': total_patterns,
            'total_sizes': len(self.patterns),
            'size_distribution': size_distribution,
            'max_size': self.get_max_pattern_size()
        }
    
    def get_classic_patterns(self) -> List[str]:
        """获取经典pattern列表"""
        classic_patterns = [
            'glider', 'block', 'blinker', 'beacon', 'toad',
            'r_pentomino', 'diehard', 'acorn',
            'lightweight_spaceship', 'lwss',
            'pulsar', 'pulsar_canonical',
            'pentadecathlon', 'pentadecathlon_10x3',
            'gosper_gun_fragment', 'copperhead', 'galaxy'
        ]
        return classic_patterns
    
    def get_pattern_by_name(self, name: str) -> Dict[str, Any]:
        """根据名称查找pattern"""
        for size_patterns in self.patterns.values():
            if name in size_patterns:
                return size_patterns[name]
        return {}