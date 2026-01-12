"""
游戏核心引擎
Game core engine
"""
import pygame
import time
from typing import List, Tuple
from config.game_config import GameConfig
from src.core.cellular_automaton import CellularAutomaton
from src.core.collision_detection import CollisionDetector
from src.entities.player import Player
from src.entities.bullet import BulletManager
from src.entities.reward import RewardManager
from src.graphics.renderer import Renderer
from src.graphics.ui import UI
from src.utils.input_utils import InputHandler

class GameEngine:
    """
    游戏核心引擎类
    Game core engine class
    """
    
    def __init__(self):
        # 初始化pygame | Initialize pygame
        pygame.init()
        
        # 创建屏幕 | Create screen
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption(GameConfig.GAME_TITLE)
        
        # 初始化游戏组件 | Initialize game components
        self.cellular_automaton = CellularAutomaton()
        self.player = Player()
        self.bullet_manager = BulletManager()
        self.reward_manager = RewardManager()
        self.renderer = Renderer(self.screen)
        self.ui = UI(self.screen)
        self.input_handler = InputHandler()
        
        # 游戏状态 | Game state
        self.running = True
        self.game_over = False
        self.paused = False
        self.iteration = 0
        
        # 时间控制 | Time control
        self.interval = 1.0 / GameConfig.FPS
        self.clock = pygame.time.Clock()
        self._game_start_iteration = 0
        self.show_settings = False
        self._settings_index = 0
        self._last_adjust_index = None
        self._last_adjust_time_ms = 0
    
    def run(self):
        """
        主游戏循环
        Main game loop
        """
        while self.running:
            start_time = time.time()
            
            # 处理事件 | Handle events
            self._handle_events()
            
            if not self.game_over and not self.paused:
                # 更新游戏逻辑 | Update game logic
                self._update_game_logic()
                
                # 检查碰撞 | Check collisions
                self._check_collisions()
            
            # 渲染 | Render
            self._render()
            
            # 控制帧率 | Control framerate
            self._control_framerate(start_time)
        
        pygame.quit()
    
    def _handle_events(self):
        """
        处理游戏事件
        Handle game events
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == GameConfig.KEY_PAUSE:
                    self.paused = not self.paused
                elif self.game_over and event.key == GameConfig.KEY_RESTART:
                    self._restart_game()
                elif event.key == pygame.K_ESCAPE:
                    self.show_settings = not self.show_settings
                elif self.show_settings:
                    self._handle_settings_event(event)
        
        # 处理持续按键 | Handle continuous key presses
        if not self.game_over and not self.paused and not self.show_settings:
            self.input_handler.handle_input(self.player)
    
    def _update_game_logic(self):
        """
        更新游戏逻辑（集成保护区域）
        Update game logic (with protected zones)
        """
        # 更新玩家 | Update player
        if self.show_settings:
            return
        self.player.update()
        
        # 更新子弹系统 | Update bullet system
        self.bullet_manager.update(self.cellular_automaton.state, self.player.get_grid_position())
        
        # 更新奖励系统 | Update reward system
        converted_reward = self.reward_manager.update(self.cellular_automaton.state, self.player)
        
        # 更新元胞自动机（传递渐进式patterns用于保护区域） | Update CA (pass progressive patterns for protected zones)
        self.cellular_automaton.update(
            self.reward_manager.reward_cells,
            self.reward_manager.progressive_patterns
        )
        
        # 增加迭代次数 | Increase iteration count
        self.iteration += 1
        try:
            scale = min(1.0, self.iteration / float(getattr(GameConfig, 'SURVIVAL_RAMP_FRAMES', 1000)))
            self.reward_manager.pattern_generator.set_survival_scale(scale)
        except Exception:
            pass
    
    def _check_collisions(self):
        """
        检查碰撞
        Check collisions
        """
        # 可配置：若关闭碰撞检测，则直接跳过 | Configurable: skip when collision detection is disabled
        if GameConfig.WU_DI_MODE:
            return
        if not GameConfig.COLLISION_DETECTION_ENABLED:
            return

        player_surface, player_rect = self.player.create_surface_and_rect()
        if CollisionDetector.check_player_cell_collision_with_mask(
            player_rect,
            self.cellular_automaton.state,
            getattr(self.cellular_automaton, '_protected_mask', None)
        ):
            self.game_over = True
            return
    
    def _render(self):
        """
        渲染游戏画面
        Render game scene
        """
        # 清空屏幕 | Clear screen
        self.renderer.clear_screen()
        
        # 渲染游戏元素 | Render game elements
        self.renderer.render_cellular_automaton(self.cellular_automaton.state)
        self.renderer.render_rewards(self.reward_manager)  # 修复：传递reward_manager对象 | Fix: pass reward_manager object
        self.renderer.render_player(self.player)
        self.renderer.render_bullets(self.bullet_manager.get_bullet_rects())
        
        # 渲染UI | Render UI
        if self.show_settings:
            self._render_settings()
        elif self.game_over:
            self.ui.render_game_over(self.iteration)
        elif self.paused:
            self.ui.render_pause()
        
        pygame.display.flip()
    
    def _control_framerate(self, start_time):
        """
        控制帧率
        Control framerate
        """
        self.clock.tick(GameConfig.FPS)
    
    def _restart_game(self):
        """
        重启游戏
        Restart game
        """
        self.__init__()
    def _handle_settings_event(self, event):
        items = self._settings_items()
        if event.key == pygame.K_w:
            self._settings_index = (self._settings_index - 1) % len(items)
        elif event.key == pygame.K_s:
            self._settings_index = (self._settings_index + 1) % len(items)
        elif event.key == pygame.K_a:
            name, kind = items[self._settings_index]
            if kind == 'bool':
                self._toggle_setting(name)
            else:
                self._adjust_setting(name, -1)
            self._last_adjust_index = self._settings_index
            self._last_adjust_time_ms = pygame.time.get_ticks()
        elif event.key == pygame.K_d:
            name, kind = items[self._settings_index]
            if kind == 'bool':
                self._toggle_setting(name)
            else:
                self._adjust_setting(name, 1)
            self._last_adjust_index = self._settings_index
            self._last_adjust_time_ms = pygame.time.get_ticks()
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            name, kind = items[self._settings_index]
            if kind == 'bool':
                self._toggle_setting(name)
                self._last_adjust_index = self._settings_index
                self._last_adjust_time_ms = pygame.time.get_ticks()

    def _settings_items(self):
        return [
            ('FPS', 'int'),
            ('Wu Di Mode', 'bool'),
            ('Reward System', 'bool'),
            ('Variety Duration', 'int')
        ]

    def _adjust_setting(self, name, delta):
        if name == 'FPS':
            GameConfig.FPS = max(5, min(60, GameConfig.FPS + delta))
        elif name in ('Survival Ramp', 'Variety Duration'):
            step = 50
            GameConfig.SURVIVAL_RAMP_FRAMES = max(200, min(5000, GameConfig.SURVIVAL_RAMP_FRAMES + delta * step))

    def _toggle_setting(self, name):
        if name == 'Wu Di Mode':
            GameConfig.WU_DI_MODE = not GameConfig.WU_DI_MODE
        elif name == 'Reward System':
            GameConfig.REWARD_SYSTEM_ENABLED = not GameConfig.REWARD_SYSTEM_ENABLED

    def _render_settings(self):
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        overlay.set_alpha(GameConfig.UI_OVERLAY_ALPHA)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        items = self._settings_items()
        title = self.ui.font_large.render("SETTINGS", True, GameConfig.PAUSE_COLOR)
        tr = title.get_rect(center=(GameConfig.SCREEN_WIDTH // 2, GameConfig.SETTINGS_TITLE_Y))
        self.screen.blit(title, tr)
        start_y = GameConfig.SETTINGS_START_Y
        spacing = GameConfig.SETTINGS_SPACING
        for idx, (name, kind) in enumerate(items):
            y = start_y + idx * spacing
            selected = (idx == self._settings_index)
            color = GameConfig.UI_TEXT_COLOR if not selected else GameConfig.PAUSE_COLOR
            val_text = ''
            if name == 'FPS':
                val_text = str(GameConfig.FPS)
            elif name in ('Survival Ramp', 'Variety Duration'):
                val_text = ''
            elif name == 'Wu Di Mode':
                val_text = 'ON' if GameConfig.WU_DI_MODE else 'OFF'
            elif name == 'Reward System':
                val_text = 'ON' if GameConfig.REWARD_SYSTEM_ENABLED else 'OFF'
            label = self.ui.font_medium.render(f"{name}: {val_text}", True, color)
            lr = label.get_rect(center=(GameConfig.SCREEN_WIDTH // 2 - GameConfig.SETTINGS_BAR_X_OFFSET, y))
            self.screen.blit(label, lr)
            bar_w = GameConfig.SETTINGS_BAR_W
            bar_h = GameConfig.SETTINGS_BAR_H
            bx = GameConfig.SCREEN_WIDTH // 2 + GameConfig.SETTINGS_BAR_X_OFFSET
            by = y - bar_h // 2
            pygame.draw.rect(self.screen, (80, 80, 80), pygame.Rect(bx, by, bar_w, bar_h))
            fill_ratio = 0.0
            if name == 'FPS':
                fill_ratio = (GameConfig.FPS - 5) / (60 - 5)
            elif name in ('Survival Ramp', 'Variety Duration'):
                fill_ratio = (GameConfig.SURVIVAL_RAMP_FRAMES - 200) / (5000 - 200)
            elif name in ('Wu Di Mode', 'Reward System'):
                fill_ratio = 1.0 if (val_text == 'ON') else 0.0
            fill_ratio = max(0.0, min(1.0, fill_ratio))
            pygame.draw.rect(self.screen, color, pygame.Rect(bx, by, int(bar_w * fill_ratio), bar_h))
            # red thin indicator at current value
            ix = bx + int(bar_w * fill_ratio) - GameConfig.SETTINGS_INDICATOR_WIDTH // 2
            pygame.draw.rect(self.screen, (255, 64, 64), pygame.Rect(ix, by - 2, GameConfig.SETTINGS_INDICATOR_WIDTH, bar_h + 4))
            # blinking cube above indicator
            recent = (self._last_adjust_index == idx) and (pygame.time.get_ticks() - self._last_adjust_time_ms <= GameConfig.SETTINGS_BLINK_MS * 6)
            if recent and selected:
                blink_on = (pygame.time.get_ticks() // GameConfig.SETTINGS_BLINK_MS) % 2 == 0
                if blink_on:
                    cube_size = GameConfig.PLAYER_SIZE
                    cube_rect = pygame.Rect(ix - cube_size // 2, by - cube_size - 8, cube_size, cube_size)
                    pygame.draw.rect(self.screen, GameConfig.PLAYER_COLOR, cube_rect)
            # optional outline for selected row
            if selected:
                pygame.draw.rect(self.screen, color, pygame.Rect(bx - 6, by - 6, bar_w + 12, bar_h + 12), 2)
        help_line1 = self.ui.font_small.render("WASD to move | A/D to adjust | Enter/Space to toggle", True, GameConfig.UI_TEXT_COLOR)
        help_line2 = self.ui.font_small.render("P pause | R restart | ESC close", True, GameConfig.UI_TEXT_COLOR)
        h1r = help_line1.get_rect(center=(GameConfig.SCREEN_WIDTH // 2, GameConfig.SCREEN_HEIGHT - GameConfig.SETTINGS_HELP_Y - 24))
        h2r = help_line2.get_rect(center=(GameConfig.SCREEN_WIDTH // 2, GameConfig.SCREEN_HEIGHT - GameConfig.SETTINGS_HELP_Y))
        self.screen.blit(help_line1, h1r)
        self.screen.blit(help_line2, h2r)