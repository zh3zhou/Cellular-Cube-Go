# 技术报告 - Cellular Cube Go 网页版 (Web Edition)

> 历史报告：本文记录旧架构，不再作为运行命令或实现状态的事实来源。当前合同请参阅 `AGENTS.md`、`PROJECT_CONTEXT.md` 与 `README.md`。
>
> 本文档记录了 Conway 生命游戏与射击游戏融合项目「Cellular Cube Go」的完整技术架构，
> 重点涵盖 2026 年 5 月新增的 Pygbag 网页版部署方案。

---

## 一、项目概述

**Cellular Cube Go** 是一款将经典 Conway 生命游戏（Cellular Automaton）与玩家射击机制相融合的 Python 游戏。
玩家在不断演化的元胞网格中控制一个方块，利用子弹消灭即将成型的「有害生命结构」，同时保护「有益结构」以获得奖励。

**当前版本**: 0.1.7+
**技术栈**: Python 3.11+ | Pygame CE | NumPy | Pygbag (WebAssembly)
**分支策略**: 单库单分支（一份代码，双端运行）

---

## 二、目录结构

```
e:\PY项目\life game\
│
├── main.py                          # 🎯 主入口（本地 + Web 共用）
│
├── src/                             # 游戏核心逻辑
│   ├── core/
│   │   ├── game_engine.py          # 核心引擎（游戏状态、循环、碰撞）
│   │   ├── cellular_automaton.py   # 元胞自动机（NumPy 矩阵实现）
│   │   └── collision_detection.py  # 碰撞检测（玩家 vs 元胞）
│   ├── entities/
│   │   ├── player.py               # 玩家方块
│   │   ├── bullet.py               # 子弹管理器
│   │   └── reward.py                # 奖励系统
│   ├── graphics/
│   │   ├── renderer.py             # 渲染器
│   │   └── ui.py                   # UI 渲染（游戏结束、暂停、设置）
│   ├── patterns/
│   │   ├── pattern_generator.py    # Pattern 生成器
│   │   ├── pattern_library.py      # 预设 Pattern 库
│   │   └── progressive_pattern.py  # 渐进式 Pattern（保护区域）
│   └── utils/
│       ├── input_utils.py          # 输入处理
│       └── math_utils.py           # 数学工具
│
├── config/                         # 配置层
│   ├── game_config.py              # 游戏全局配置（含所有颜色、字体、尺寸）
│   └── pattern_config.py           # Pattern 专用配置
│
├── assets/                         # 静态资源
│   ├── fonts/
│   │   └── PixelifySans-Medium.ttf # 像素风格字体
│   └── patterns/
│       └── library.json            # 预设 Pattern 库
│
├── static/
│   └── default.tmpl                # 🕸️ Pygbag Web 模板（加载页 UI）
│
├── .github/
│   └── workflows/
│       └── deploy.yml              # 🕸️ GitHub Actions 自动部署到 GitHub Pages
│
├── pygbag.ini                      # Pygbag 打包配置（忽略文件列表）
│
├── rules.md                        # Agent 工作规范（开发准则）
│
└── 《开发》/
    ├── note.md                     # 开发日志
    └── AGENTWORKS.md               # Agent 工作记录
```

---

## 三、核心文件详解

### 3.1 main.py - 统一入口

这是**最关键的文件**，同时承担本地和 Web 端的运行职责。

**架构设计**：
- 使用 `# /// script` 元数据块（PEP 723）声明第三方依赖（Pygame CE、NumPy）
- 通过 `sys.platform in ("emscripten", "wasi")` 检测运行环境，Web 端使用 `pygbag.aio`
- 采用**手动帧率控制**（不使用 Pygame 原生的 `clock.tick()`），确保 Web 端与本地端行为一致

**核心异步主循环**：
```python
while game.running:
    current_time = time.time()
    dt = current_time - last_time
    frame_duration = 1.0 / GameConfig.FPS   # 每帧重新读取，支持动态修改 FPS

    game._handle_events()

    if dt >= frame_duration:
        last_time = current_time
        game._handle_continuous_input()  # 玩家移动 ← 必须限速
        if not game.game_over and not game.paused:
            game._update_game_logic()    # 游戏逻辑 ← 必须限速
            game._check_collisions()
        game._render()                   # 渲染    ← 必须限速

    await asyncio.sleep(0)   # 交还控制权给浏览器（Web 端必需）
```

> ⚠️ **重要警示**：`asyncio.sleep(0)` 在浏览器中等价于 `requestAnimationFrame`，
> 如果 `game._render()` 放在限速块之外，渲染会以 60~144 FPS 执行，瞬间卡死浏览器主线程。

### 3.2 src/core/game_engine.py - 游戏引擎

**状态机**：
```
running=True → 游戏主循环
paused=True  → 游戏暂停（显示暂停菜单）
game_over=True → 玩家死亡（显示结算菜单）
show_settings=True → 显示设置菜单（ESC 键触发）
```

**帧率控制**：
- 本地版使用 `self.clock.tick(GameConfig.FPS)`（同步循环）
- Web 版使用 `await asyncio.sleep(0)` + 手动 `dt` 计算（异步循环）

### 3.3 src/core/cellular_automaton.py - 元胞自动机

**实现方式**：NumPy 二维布尔数组
**演化规则**：标准 Conway 生命游戏规则（B3/S23），可配置存活/出生邻居数范围
**保护机制**：支持 `protected_mask`（奖励系统渐进式 Pattern 保护区域）

---

## 四、Web 版架构（重点）

### 4.1 Pygbag 工作原理

Pygbag 将 Python 代码编译为 WebAssembly（WASM），在浏览器的虚拟文件系统（BrowserFS）中运行。

**关键文件**：
| 文件 | 作用 |
|------|------|
| `static/default.tmpl` | Web 加载页 HTML 模板（可自定义 UI） |
| `pygbag.ini` | 打包配置，声明忽略哪些文件/文件夹 |
| `build/web/` | 打包输出目录（提交到 GitHub Pages 的内容） |

**生命周期**：
```
1. 加载 index.html
2. 下载 Python WASM 运行时（从 CDN）
3. 下载并解压 life.game.tar.gz（游戏代码包）
4. 提示用户点击页面（MEDIA USER ACTION REQUIRED - Web Audio 限制）
5. 执行 main.py → 游戏主循环
6. 游戏运行
```

### 4.2 static/default.tmpl - 自定义加载 UI

**设计原则**：
- 深色主题背景（`#1a1a1a`）
- 绿色进度条和文字（`#4CAF50`）
- CSS 动画模拟滑翔机（Glider）向右移动
- 橙红色玩家方块（`#FF5722`）在滑翔机上跳跃

**关键元素**：

| 元素 ID | 用途 |
|---------|------|
| `#transfer` | 加载界面容器（含动画） |
| `#infobox` | 提示文字容器（"请点击开始"） |
| `#progress` | 加载进度条 |
| `#canvas` | 游戏画布（Pygame 渲染目标） |

### 4.3 自动化部署（GitHub Actions）

`.github/workflows/deploy.yml` 实现：
- 触发条件：`push` 到 `main` 分支
- 自动执行：`pygbag --build --template static\default.tmpl .`
- 自动部署：使用 `peaceiris/actions-gh-pages@v4` 推送到 `gh-pages` 分支

**启用步骤**：
1. 将代码推送到 GitHub
2. 在 GitHub 仓库 `Settings` → `Pages` 中选择 `gh-pages` 分支作为 Source
3. 等待 Actions 自动执行（通常 2-3 分钟）
4. 访问 `https://<用户名>.github.io/<仓库名>/`

---

## 五、全局配置规范

### 5.1 配色方案

所有颜色定义在 `config/game_config.py` 中，**Web 加载页使用近似颜色**（CSS 十六进制）。

**游戏内颜色**（RGB 元组）：
| 用途 | RGB | 说明 |
|------|-----|------|
| PLAYER_COLOR | (255, 0, 0) | 红色 |
| CELL_COLOR | (255, 255, 255) | 白色 |
| BACKGROUND_COLOR | (0, 0, 0) | 黑色 |
| REWARD_COLOR | (138, 222, 137) | 浅绿色 |
| UI_TEXT_COLOR | (255, 127, 128) | 粉红色 |
| PAUSE_COLOR | (255, 127, 128) | 粉红色（与 UI 文字相同） |
| GAME_OVER_COLOR | (255, 127, 128) | 粉红色 |
| UI_RESTART_COLOR | (138, 222, 137) | 浅绿色 |

**Web 加载页颜色**（CSS 十六进制）：
| 用途 | 颜色 |
|------|------|
| 背景 | `#1a1a1a` |
| 主色调（进度条、Glider 存活格） | `#4CAF50` |
| 进度条底色 | `#333` |
| 玩家方块 | `#FF5722` |
| infobox 背景 | `#4CAF50` |
| infobox 文字 | `#1a1a1a` |

### 5.2 字体规范

**游戏内字体**：
- 首选：`assets/fonts/PixelifySans-Medium.ttf`（像素风格）
- 备选：系统默认等宽字体
- 大号（标题）：70px
- 中号（副标题）：50px
- 小号（帮助文字）：40px

**Web 加载页字体**：
- 主字体：Courier New（等宽风格，模拟终端）
- 备选：monospace

### 5.3 关键尺寸参数

| 参数 | 值 |
|------|-----|
| CELL_SIZE | 10px |
| PLAYER_SIZE | 20px |
| PLAYER_SPEED | 10px/帧 |
| FPS（默认） | 13 |
| WORLD_WIDTH | 120 格 |
| WORLD_HEIGHT | 70 格 |
| 屏幕尺寸 | 1100 × 600px |

---

## 六、常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Web 版加载后灰屏 | 加载界面未隐藏 | 检查 `platform.window.transfer.style.display = "none"` |
| 玩家移动速度过快 | `_handle_continuous_input()` 未限速 | 移入 `if dt >= frame_duration:` 块 |
| 修改 FPS 无效 | `frame_duration` 在循环外计算 | 移入循环内每帧重新计算 |
| 浏览器卡死 | `game._render()` 未限速 | 移入限速块 |
| numpy 下载失败 | pygbag 代理不稳定 | 使用 `python -m http.server` 而非 `pygbag .` |
| 点击后无反应 | Web Audio 权限未解锁 | 必须有用户点击页面动作 |

---

## 七、维护指南

### 7.1 修改游戏逻辑
1. 在 `src/core/` 下修改对应模块
2. 本地运行 `python main.py` 测试
3. 运行 `pygbag --build --template static\default.tmpl .` 打包
4. 用 `python -m http.server 8080 -d build/web` 启动测试服务器

### 7.2 修改 Web 加载 UI
1. 编辑 `static/default.tmpl`
2. 仅修改 HTML/CSS 部分（Python 代码块修改需谨慎）
3. 重新打包部署

### 7.3 添加新的第三方依赖
1. 在 `main.py` 顶部的 `# /// script` 块中添加依赖名称
2. 确保依赖有对应的 WASM 版本（通过 Pyodide 生态）

### 7.4 推送更新
1. 提交代码到 `main` 分支
2. GitHub Actions 自动构建并部署
3. 约 2-3 分钟后生效

---

*文档生成时间：2026-05-21*
*最后更新版本：0.1.7+*
