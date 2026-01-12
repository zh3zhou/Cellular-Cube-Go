"""
游戏核心配置参数
Game core configuration parameters
"""
import os
import pygame

class GameConfig:
    # 游戏世界设置 | Game world settings
    WORLD_WIDTH = 120
    WORLD_HEIGHT = 70
    CELL_SIZE = 10
    CELLULAR_AUTOMATON_PROBABILITY = 0.5

    # 屏幕设置 | Screen settings
    SCREEN_WIDTH = WORLD_WIDTH * CELL_SIZE - 100
    SCREEN_HEIGHT = WORLD_HEIGHT * CELL_SIZE - 100

    # 玩家设置 | Player settings
    PLAYER_SIZE = 20
    PLAYER_SPEED = 10
    PLAYER_COLOR = (255, 0, 0)  # 红色 | Red
    PLAYER_START_X = SCREEN_WIDTH // 2
    PLAYER_START_Y = SCREEN_HEIGHT // 2
    PLAYER_SAFE_ZONE_RADIUS = 10  # 玩家周围的安全区域半径 | Player safe zone radius

    # 子弹设置 | Bullet settings
    BULLET_CREATE_INTERVAL = 9
    BULLET_SPEED = CELL_SIZE

    # 奖励系统设置 | Reward system settings
    REWARD_SYSTEM_ENABLED = True  # 新增：奖励系统开关 | Added: reward system switch
    REWARD_COLOR = (138, 222, 137)  # 绿色 | Green
    REWARD_CREATE_INTERVAL = 18  # 子弹生成频率的2倍 | Twice the bullet spawn interval

    # 元胞自动机规则 | Cellular automaton rules
    LIVE_MIN_NEIGHBORS = 2
    LIVE_MAX_NEIGHBORS = 3
    BORN_MIN_NEIGHBORS = 3
    BORN_MAX_NEIGHBORS = 3

    # 渲染设置 | Rendering settings
    CELL_COLOR = (255, 255, 255)  # 白色 | White
    BACKGROUND_COLOR = (0, 0, 0)  # 黑色 | Black

    # 游戏设置 | Game settings
    FPS = 13  # 17是一开始的 | 17 was the initial value
    GAME_TITLE = "Cellular Cube Go"
    # 碰撞检测开关（默认启用）| Collision detection toggle (enabled by default)
    COLLISION_DETECTION_ENABLED = True

    # 字体设置 | Font settings
    # 自动检测项目中的字体文件，优先使用半粗体，其次常规体；否则使用系统默认字体
    # Auto-detect project fonts: prefer SemiBold, then Regular; else fall back to system font
    FONT_PATH = None
    _ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
    _FONTS_DIR = os.path.join(_ROOT_DIR, "assets", "fonts")
    _CANDIDATES = [
        "PixelifySans-Medium.ttf",
        "PixelifySans-SemiBold.ttf",
        "PixelifySans.ttf",
    ]
    try:
        # 优先候选 | Preferred candidates
        for _name in _CANDIDATES:
            _p = os.path.join(_FONTS_DIR, _name)
            if os.path.isfile(_p):
                FONT_PATH = _p
                break
        # 兜底：任意 .ttf | Fallback: any .ttf
        if FONT_PATH is None and os.path.isdir(_FONTS_DIR):
            for _f in os.listdir(_FONTS_DIR):
                if _f.lower().endswith(".ttf"):
                    FONT_PATH = os.path.join(_FONTS_DIR, _f)
                    break
    except Exception:
        # 出错时保持为 None，让渲染层回退系统字体 | On error keep None to fall back to system font
        FONT_PATH = None
    FONT_SIZE_LARGE = 70
    FONT_SIZE_MEDIUM = 50
    FONT_SIZE_SMALL = 40

    # UI颜色设置 | UI color settings
    UI_TEXT_COLOR = (255, 127, 128)
    UI_RESTART_COLOR = (138, 222, 137)
    UI_OVERLAY_ALPHA = 150
    GAME_OVER_COLOR = (255, 127, 128)  # 添加缺失的颜色 | Added missing color
    PAUSE_COLOR = (255, 127, 128)  # 添加缺失的颜色 | Added missing color

    # 按键设置 | Key bindings
    KEY_UP = pygame.K_w
    KEY_DOWN = pygame.K_s
    KEY_LEFT = pygame.K_a
    KEY_RIGHT = pygame.K_d
    KEY_PAUSE = pygame.K_p
    KEY_RESTART = pygame.K_r
    SURVIVAL_RAMP_FRAMES = 1000
    WU_DI_MODE = False
    # Settings UI layout
    SETTINGS_TITLE_Y = 100
    SETTINGS_START_Y = 200
    SETTINGS_SPACING = 72
    SETTINGS_BAR_W = 360
    SETTINGS_BAR_H = 14
    SETTINGS_BAR_X_OFFSET = 120
    SETTINGS_HELP_Y = 60
    SETTINGS_INDICATOR_WIDTH = 6
    SETTINGS_BLINK_MS = 400