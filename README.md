（只有中文的废话碎碎念；除了这些下面都是大模型生成的，欧耶）
大二上学计算物理2。顺道跟着一个python教程写了Conway's Life Game,那个学期也在扒拉着看一些复杂系统的东西



# Cellular Cube Go / 细胞自动机游戏

A Pygame-based cellular automaton game with player movement, bullets, rewards, and dynamic pattern generation. Includes a size diversity algorithm that discourages repeating recent pattern sizes and rewards variety.

一个基于 Pygame 的细胞自动机游戏，包含玩家移动、子弹、奖励系统以及动态图案生成。支持“最近尺寸惩罚 + 尺寸差异奖励”的选择算法，鼓励生成不同大小的图案。

---

## Features / 功能特性
- Cellular automaton world with configurable rules (`GameConfig`)
- Player, bullets, and reward cells rendering
- Pattern library with multiple sizes and shapes
- Progressive patterns that move over time
- Size diversity in pattern selection (recent sizes penalty + variety bonus)
- Configurable difficulty presets and weights (`PatternConfig`)

- 可配置的细胞自动机世界与规则（`GameConfig`）
- 玩家、子弹与奖励细胞渲染
- 多尺寸与形状的图案库（`PatternLibrary`）
- 随时间移动的渐进式图案
- 尺寸选择多样性（最近尺寸惩罚 + 面积差异奖励）
- 难度预设与权重可配置（`PatternConfig`）

## Quick Start / 快速开始
- Install dependencies with Conda or Pip.
- Conda:
  - `conda create -n cube-go python=3.12 -y`
  - `conda activate cube-go`
  - `pip install -r requirements.txt`
- Pip:
  - `pip install -r requirements.txt`
- Run from the project root:
  - `python main.py` (or `python -m src.main`)
- Gameplay:
  - Control a red square; move with `W/A/S/D`
  - Avoid white squares; eat green squares to spawn a progressive pattern
  - Press `P` to pause; press `R` to restart
- Optional fonts:
  - Place a `.ttf` in `assets/fonts/` (auto-detects `PixelifySans-SemiBold.ttf` or `PixelifySans.ttf`)
- Troubleshooting:
  - If `ModuleNotFoundError: numpy`, install deps in the active environment
  - If `No module named 'src'`, run from project root or use `python -m src.main`

- 使用 Conda 或 Pip 安装依赖。
- Conda：
  - `conda create -n cube-go python=3.12 -y`
  - `conda activate cube-go`
  - `pip install -r requirements.txt`
- Pip：
  - `pip install -r requirements.txt`
- 从项目根目录运行：
  - `python main.py`（或 `python -m src.main`）
- 游戏玩法：
  - 操作红色方块，使用 `W/A/S/D` 移动
  - 避开白色方块；吃下绿色方块会生成随时间渐进的图案
  - 按 `P` 暂停；按 `R` 重新开始
- 可选字体：
  - 在 `assets/fonts/` 放置 `.ttf` 字体（自动检测 `PixelifySans-SemiBold.ttf` 或 `PixelifySans.ttf`）
- 常见问题：
  - 若出现 `ModuleNotFoundError: numpy`，请在当前激活环境安装依赖
  - 若出现 `No module named 'src'`，请从项目根目录运行或使用 `python -m src.main`

## Requirements / 运行环境
- Python 3.11+ (tested on 3.12)
- `pygame` and `numpy` (see `requirements.txt`)

- Python 3.11+（建议 3.12）
- 依赖：`pygame`、`numpy`（见 `requirements.txt`）

## Install / 安装

### Option A: Conda
```
conda create -n cube-go python=3.12 -y
conda activate cube-go
pip install -r requirements.txt
```

### Option B: Pip (System Python)
```
pip install -r requirements.txt
```

## Run / 运行
```
python main.py
```

- Run from the project root. Use `python main.py` or `python -m src.main`. Do not run `src/main.py` directly.
- 请在项目根目录运行。使用 `python main.py` 或 `python -m src.main`。不要直接运行 `src/main.py`。

## Configuration / 配置
- `config/game_config.py`
  - World, screen, player, bullets, colors, FPS
  - Fonts: if `assets/fonts/PixelifySans.ttf` exists, it is auto-used; otherwise falls back to system font
  - Collision detection: toggle with `COLLISION_DETECTION_ENABLED` (default: True)
  
  - 世界、屏幕、玩家、子弹、颜色、FPS 等
  - 字体：如果项目内存在 `assets/fonts/PixelifySans.ttf` 将自动使用；否则回退系统默认字体
  - 碰撞检测：通过 `COLLISION_DETECTION_ENABLED` 开关（默认：开启）

- `config/pattern_config.py`
  - Selection strategy, size weights, difficulty presets
  - Size diversity parameters: `RECENCY_LAST_PENALTY`, `RECENCY_SECOND_PENALTY`, `SIZE_VARIETY_BONUS`
  
  - 选择策略、尺寸权重、难度预设
  - 尺寸多样性参数：`RECENCY_LAST_PENALTY`、`RECENCY_SECOND_PENALTY`、`SIZE_VARIETY_BONUS`

## Fonts / 字体打包
- Create `assets/fonts/` and place your font file, e.g., `PixelifySans.ttf`
- By default, `GameConfig` will auto-detect `assets/fonts/PixelifySans.ttf`
- If missing, the game uses system default font via `pygame.font.Font(None, size)`
- Ensure the font license allows redistribution (e.g., Pixelify Sans is under SIL Open Font License 1.1)

- 创建 `assets/fonts/` 并放入字体文件，如 `PixelifySans.ttf`
- `GameConfig` 会自动检测并使用该字体；不存在则回退系统字体
- 确认字体授权允许随项目分发（例如 Pixelify Sans 使用 SIL OFL 1.1）

## Controls / 操作
- Movement: `W/A/S/D`
- Pause: `P`
- Restart: `R`

- 移动：`W/A/S/D`
- 暂停：`P`
- 重新开始：`R`

## Gameplay / 游戏玩法
- You control a red square. Move with `W/A/S/D`. Avoid white squares (hazards). Eating a green square will spawn a pattern that progressively renders over time. Press `P` to pause, press `R` to restart.
- 你将操作一个红色方块，使用 `W/A/S/D` 移动；不要碰到白色方块（危险）；吃下绿色方块会生成图案并随时间渐进显示；按 `P` 暂停，按 `R` 重新开始。

## Project Structure / 项目结构
```
life game/
├── config/
│   ├── game_config.py
│   └── pattern_config.py
├── assets/
│   └── fonts/
│       └── PixelifySans.ttf (optional)
├── src/
│   ├── core/
│   │   ├── cellular_automaton.py
│   │   ├── collision_detection.py
│   │   └── game_engine.py
│   ├── graphics/
│   │   ├── renderer.py
│   │   └── ui.py
│   ├── entities/
│   │   ├── player.py
│   │   ├── bullet.py
│   │   └── reward.py
│   └── patterns/
│       ├── pattern_library.py
│       ├── pattern_generator.py
│       └── progressive_pattern.py
├── requirements.txt
└── main.py
```

## Advanced Configuration / 配置项详解（高级）
- Edit `config/game_config.py` and `config/pattern_config.py`. Each option below shows defaults, effects, safe ranges, and risks.
- 修改 `config/game_config.py` 与 `config/pattern_config.py`。下列条目给出默认值、作用、建议范围与风险提示。

### GameConfig
- `WORLD_WIDTH` (default: `120`) — World width in cells | 世界宽度（格子数）。Risk: very large values increase CPU/GPU, rendering and collision checks scale with `width*height`.
- `WORLD_HEIGHT` (default: `70`) — World height in cells | 世界高度（格子数）。Risk: extremely small worlds (< 15×15) reduce pattern fit; boundary spawns may rarely trigger.
- `CELL_SIZE` (default: `10`) — Pixels per cell | 单个格子的像素尺寸。Important: current bullet boundary math assumes 10px cells; changing this can break bullet-pattern spawning; keep `10` unless you adjust bullet math accordingly.
- `CELLULAR_AUTOMATON_PROBABILITY` (default: `0.5`) — Initial live-cell probability | 初始活细胞概率。Range `[0.0,1.0]`; high values cause dense starts and slower first frames.

- `SCREEN_WIDTH` / `SCREEN_HEIGHT` — Derived: `WORLD_* * CELL_SIZE - 100` | 由上式计算，不建议单独改。Change world/cell instead; player start and bounds depend on these.

- `PLAYER_SIZE` (default: `20`) — Player square size (px) | 玩家方块像素大小。Large values make collisions easier; ensure `PLAYER_SIZE <= min(SCREEN_*)`.
- `PLAYER_SPEED` (default: `10`) — Pixels per tick | 每帧移动像素。If too high, you may skip over reward cells in a single frame, missing conversions.
- `PLAYER_COLOR` — RGB tuple | 颜色配置。Safe to change.
- `PLAYER_START_X` / `PLAYER_START_Y` — Initial pixel position | 初始像素坐标。Defaults to screen center; keep within screen bounds.
- `PLAYER_SAFE_ZONE_RADIUS` (default: `10`) — Cells around center cleared on start | 开局清空的安全区半径（格）。Large radius wipes more initial cells.

- `BULLET_CREATE_INTERVAL` (default: `9`) — Frames between boundary bullet-pattern spawns | 边界子弹图案生成的帧间隔。Lower values increase spawn rate and CPU.
- `BULLET_SPEED` (default: `CELL_SIZE`) — Bullet pixel step | 子弹像素步长。Currently bullets are not instantiated visually; boundary patterns use the interval. Safe to leave default.

- `REWARD_SYSTEM_ENABLED` (default: `True`) — Toggle reward cells & progressive patterns | 奖励系统开关（绿色格与渐进式图案）。
- `REWARD_COLOR` — RGB for reward cells | 奖励细胞颜色。
- `REWARD_CREATE_INTERVAL` (default: `18`) — Reward spawn cadence | 奖励生成频率（帧）。Too small creates many rewards, potential slowdowns.

- `LIVE_MIN_NEIGHBORS` / `LIVE_MAX_NEIGHBORS` / `BORN_MIN_NEIGHBORS` / `BORN_MAX_NEIGHBORS` — CA rule parameters now applied in engine | 元胞规则参数，现已接入引擎。
  - Defaults reproduce Conway B3/S23; tweak to experiment with variants. | 默认等价 B3/S23，可自行实验其它规则。

- `CELL_COLOR` / `BACKGROUND_COLOR` — Cell and background colors | 细胞与背景颜色。Safe.
- `FPS` (default: `13`) — Target frames per second | 目标帧率。Higher FPS increases CPU usage; too low reduces responsiveness.
- `GAME_TITLE` — Window title | 窗口标题。
- `COLLISION_DETECTION_ENABLED` (default: `True`) — Player vs. live-cell collision toggle | 玩家与活细胞碰撞开关。Turn off for sandbox exploration.

- Fonts / 字体
  - `FONT_PATH` — Auto-detected from `assets/fonts/` (`*.ttf`); `None` falls back to system font. | 自动检测 `assets/fonts/*.ttf`；为 `None` 时使用系统字体。
  - `FONT_SIZE_LARGE` / `MEDIUM` / `SMALL` — UI font sizes | UI 字号。Large sizes may overflow screen on small resolutions.

- UI Colors / UI 颜色
  - `UI_TEXT_COLOR`, `UI_RESTART_COLOR`, `GAME_OVER_COLOR`, `PAUSE_COLOR`, `UI_OVERLAY_ALPHA` — Safe visual tweaks | 安全的视觉微调。

- Key Bindings / 按键
  - `KEY_UP/DOWN/LEFT/RIGHT` (defaults: `W/S/A/D`) — Movement
  - `KEY_PAUSE` (`P`), `KEY_RESTART` (`R`) — Pause/Restart
  - Use `pygame.K_*` constants; avoid duplicates. | 使用 `pygame.K_*` 常量，避免重复绑定。

### PatternConfig
- Progressive patterns / 渐进式图案
- `PROGRESSIVE_PATTERN_SPEED` (default: `15`) — Base steps; size-based scaling increases total steps for larger patterns. | 基础步数；按尺寸放大总步数，越大越慢。
  - `PROGRESSIVE_PATTERN_MAX_AGE` (default: `180`) — Hard cap on total steps. | 总步数上限。
  - `SPEED_SCALING_FACTOR` (default: `0.15`) — Bounding-box-based scaling factor. | 基于包围盒的缩放系数。
  - `MIN_PATTERN_SPEED` / `MAX_PATTERN_SPEED` — Now enforced as min/max total steps clamps. | 作为总步数的上下界已生效。

- Selection strategy / 选择策略
  - `SELECTION_STRATEGY`: `"single_cell"` | `"size_probability"` (default) — Size-probability picks sizes with weights. | 通过权重选择尺寸。
  - `FALLBACK_STRATEGY`: `"single_cell"` | `"min_fit"` | `"closest_configured_size"` — Used when preferred size not available. | 首选尺寸不可用时的兜底策略。

- Size weights and diversity / 尺寸权重与多样性
  - `SIZE_SELECTION_WEIGHTS` — Dict keyed by `(w,h)` with float weights. | 以 `(w,h)` 为键的权重表。Keys must be tuples of ints; missing keys fall back via `DEFAULT_WEIGHT_SCALE`. | 键须为整数元组；未配置尺寸按面积比例与 `DEFAULT_WEIGHT_SCALE` 计算。
  - `BASE_WEIGHT_MULTIPLIER`, `SIZE_DIVERSITY_FACTOR`, `MAX_PATTERN_BIAS`, `ENABLE_MAX_SIZE_BONUS`, `DEFAULT_WEIGHT_SCALE` — Tune overall bias. | 调整整体偏向。
  - Recent-size effects / 最近尺寸影响：`RECENCY_LAST_PENALTY`、`RECENCY_SECOND_PENALTY`、`SIZE_VARIETY_BONUS` ∈ `[0,1]` recommended. | 建议取值 `[0,1]`。

- Size constraints / 尺寸约束
  - `MIN_PATTERN_AREA` / `MAX_PATTERN_AREA` — Area in cells of bounding box. | 以包围盒面积计。Ensure `MAX_PATTERN_AREA <= WORLD_WIDTH*WORLD_HEIGHT` and pattern sizes fit world dims. | 保证不超过世界可容纳范围。

- Changing `CELL_SIZE` — bullet boundary logic now adapts to `CELL_SIZE`; safe to change, but very large values reduce grid resolution and may affect gameplay feel. | 修改 `CELL_SIZE`：边界生成已适配 `CELL_SIZE`，可安全调整；但过大将降低网格分辨率并改变操作手感。
- Very large `WORLD_WIDTH`/`WORLD_HEIGHT` — per-frame loops for rendering, collision, and CA updates scale with the number of cells; test performance gradually. | 非常大的世界尺寸：渲染、碰撞、演化均随细胞数线性增长，请逐步调大并测试性能。
- Excessive `PLAYER_SPEED` — can skip over 1-cell rewards between frames, preventing conversions. | 过高玩家速度：可能跨帧越过 1 格奖励而未被判定接触。
- Very small worlds (< 15×15) — many library patterns will not fit; boundary spawning triggers less often. | 过小世界：多数图案无法放置，边界生成触发概率降低。

### How to Apply / 修改方法
- Edit and save the config file(s), then run `python main.py`. No rebuild step is required. | 直接修改配置文件并保存，然后运行 `python main.py`，无需额外构建步骤。

## Notes / 说明
- To tune selection behavior, tweak `PatternConfig.SIZE_SELECTION_WEIGHTS` and diversity parameters.
- Set `PatternConfig.DEBUG_PATTERN_SELECTION = True` to log size probabilities.
- Publishing to GitHub: include this README, `.gitignore`, and (optionally) a `LICENSE` (e.g., MIT). If bundling fonts, include their license.

- 调整选择行为：修改 `PatternConfig.SIZE_SELECTION_WEIGHTS` 及多样性参数
- 设置 `PatternConfig.DEBUG_PATTERN_SELECTION = True` 输出尺寸选择概率
- 发布到 GitHub：提交本 README、`.gitignore`，可选添加 `LICENSE`（如 MIT）；如随库分发字体，请附带许可证

---

## AI Assistant Prompt (Copy-Paste) / 面向AI的提示词（可直接复制）

Use the following prompt to help an AI assistant understand and safely modify this project. Keep changes scoped, update docs, and validate imports.

使用以下提示词帮助 AI 安全理解并修改本项目。限制改动范围、同步文档，并进行导入校验。

```
You are an expert Python/Pygame engineer assisting on a cellular automaton game.
Goal:
- Implement the following change: [clearly describe the change here]
- Keep existing behavior as default unless specified; add toggles when appropriate.

Repository context (key files):
- Entry: `main.py` (root) calls `src.main.main`; run from project root with `python main.py`.
- Core: `src/core/game_engine.py` (loop, updates, render), `src/core/cellular_automaton.py` (CA rules, protected zones), `src/core/collision_detection.py` (helpers).
- Entities: `src/entities/player.py` (movement, rect), `src/entities/bullet.py` (boundary pattern spawns, uses `GameConfig.CELL_SIZE`), `src/entities/reward.py` (rewards → progressive patterns, respects `REWARD_SYSTEM_ENABLED`).
- Patterns: `src/patterns/pattern_generator.py`, `src/patterns/pattern_library.py`, `src/patterns/progressive_pattern.py` (size-based speed, clamped by `MIN/MAX_PATTERN_SPEED` and `PROGRESSIVE_PATTERN_MAX_AGE`).
- Graphics/UI: `src/graphics/renderer.py` (colors, fonts), `src/graphics/ui.py`.
- Input: `src/utils/input_utils.py` (uses `GameConfig.KEY_*`).
- Config: `config/game_config.py` (world, screen, player, bullets, rewards, colors, FPS, fonts, UI, keys, collision toggle), `config/pattern_config.py` (progressive timing, selection strategy and weights, diversity, size constraints, recency penalties, difficulty presets).

Important constraints:
- Follow project style; keep changes minimal and scoped to the request.
- Defaults must preserve current behavior unless the request says otherwise.
- Gate new behavior via config when it can affect gameplay; document in README (bilingual section).
- Do not add new deps or change file layout unless necessary.
- Avoid breaking `CELL_SIZE`-dependent logic; bullets already adapt to `CELL_SIZE`.
- CA rules come from `GameConfig` (LIVE/BORN min/max) and must remain configurable.

Performance & risks to consider:
- Large `WORLD_WIDTH/HEIGHT` scales work per frame (render, CA, collisions).
- Pattern speed uses size-based scaling and clamps; avoid unbounded timings.
- High `PLAYER_SPEED` may skip 1-cell rewards in a single frame.

Acceptance criteria:
- Code compiles and module imports succeed.
- The change works for default config and is behind a toggle when needed.
- README “Advanced Configuration” reflects any new/changed settings.
- No unrelated refactors; no silent behavior changes.

Validation steps to run:
1) From project root: `pip install -r requirements.txt`
2) Import sanity check:
   `python -c "import sys, os; sys.path.insert(0, os.getcwd()); import main, src.core.game_engine, src.core.collision_detection, src.core.cellular_automaton, src.entities.player, src.entities.reward, src.entities.bullet, src.patterns.progressive_pattern; print('Imports OK')"`
3) Start the game: `python main.py` (or `python -m src.main`).

If anything is ambiguous, ask me:
- Should changes be toggleable? Default on/off?
- Are there performance targets (FPS, world size)?
- Which parts of README need updates (Quick Start, Advanced Configuration)?

Plan before changes:
1) Identify affected modules (search for related symbols/usages).
2) Implement minimal changes with clear config flags if needed.
3) Update README (bilingual), focusing on Advanced Configuration.
4) Run the import sanity check; provide instructions to run.
5) Present a concise diff and rationale.

Deliverables:
- Code changes (targeted and minimal), updated README, brief test notes.
```

### Quick Prompt Snippet / 快速提示片段

- Task: [要做什么]
- Constraints: keep defaults; add config toggle if gameplay changes; update README (CN/EN).
- Touch files: [列出你预计修改的文件]
- Validate: run import sanity check; launch with `python main.py`.

- 任务：[要做什么]
- 约束：默认行为不变；影响玩法需加开关；更新 README（中英双语）。
- 修改文件：[列出你预计修改的文件]
- 验证：执行导入校验；用 `python main.py` 启动。
2026年1月13日 1:05:26


