# Agent 工作规范 (Agent Rules)

本文件用于指导 Agent 在本项目中的工作流程和行为规范，请 Agent 在执行任务时严格遵守。

## 1. 记录工作日志到 AGENTWORKS.md

每一次完成重大的输出、功能的添加或代码的改动后，Agent **必须**主动在 `E:\PY项目\life game\《开发》\AGENTWORKS.md` 中追加一条带有时间戳的记录。

记录的格式规范如下：

```markdown
### [YYYY-MM-DD HH:MM:SS] <简短的改动标题>

- **任务目标**: <简短描述本次任务的目标>
- **主要改动**: 
  - <改动点1>
  - <改动点2>
- **关键代码改动**: 
  （如有必要，简要列出关键的代码差异或新增的核心逻辑）
  ```python
  # 示例代码
  def new_feature():
      pass
  ```
- **下一步/待办**: <接下来还需要做什么，或者遗留的问题>
```

## 2. 保持单库单分支 (Single Codebase)

- **一份代码，双端运行**：不要为了 Web 版和本地版拆分两个不同的项目。
- 所有的代码变更都必须保证既可以在本地通过 `python main.py` 运行，也可以通过 `pygbag` 打包后在浏览器中运行。
- 如果遇到平台特有的问题（如 Web 版的 `asyncio.sleep(0)` 和 `MEDIA USER ACTION REQUIRED`），请在代码中使用平台检测（如 `sys.platform in ("emscripten", "wasi")`）进行条件分支处理。

## 3. Web 端打包规范

- **打包命令**：统一使用 `pygbag --build --template static\default.tmpl .`
- **依赖声明**：所有的第三方依赖（如 `numpy`）必须在 `main.py` 顶部的 `# /// script` 元数据块中声明。
- **忽略配置**：不属于游戏运行必须的文件（如开发文档、`.git`、测试脚本等）必须在 `pygbag.ini` 中配置忽略。
- **测试服务器**：Web 端本地测试请使用 `py -m http.server <端口> -d build/web`（不要用 `pygbag .` 自带的代理，代理不稳定会导致大文件下载失败）
- **端口**：本地测试建议使用 8888 端口

## 4. UI 与配色规范

### 4.1 颜色规范

**游戏内颜色（定义在 `config/game_config.py`，RGB 元组）**：

| 用途 | RGB 值 | 说明 |
|------|--------|------|
| 玩家方块 (PLAYER_COLOR) | (255, 0, 0) | 纯红色 |
| 生命元胞 (CELL_COLOR) | (255, 255, 255) | 纯白色 |
| 背景 (BACKGROUND_COLOR) | (0, 0, 0) | 纯黑色 |
| 奖励元胞 (REWARD_COLOR) | (138, 222, 137) | 浅绿色 |
| UI 文字/暂停/结算 (UI_TEXT_COLOR, PAUSE_COLOR, GAME_OVER_COLOR) | (255, 127, 128) | 粉红色 |
| 重新开始提示 (UI_RESTART_COLOR) | (138, 222, 137) | 浅绿色 |

**Web 加载页颜色（定义在 `static/default.tmpl`，CSS 十六进制）**：

| 用途 | 颜色值 |
|------|--------|
| 加载页背景 | #1a1a1a |
| 主色调（进度条、Glider 存活格） | #4CAF50 |
| 进度条底色 | #333 |
| 玩家方块（加载动画） | #FF5722 |
| infobox 背景 | #4CAF50 |
| infobox 文字 | #1a1a1a |

### 4.2 字体规范

**游戏内字体**：
- 首选：`assets/fonts/PixelifySans-Medium.ttf`（像素风格）
- 自动降级：依次尝试 PixelifySans-SemiBold.ttf → PixelifySans.ttf → 系统默认
- 字号：
  - FONT_SIZE_LARGE = 70px（游戏标题）
  - FONT_SIZE_MEDIUM = 50px（副标题）
  - FONT_SIZE_SMALL = 40px（帮助文字）

**Web 加载页字体**：
- 字体：Courier New（等宽风格，模拟终端）
- 备选：monospace

### 4.3 UI 风格准则

- **主题**：生命游戏的科幻、像素极简风格
- **元素**：任何新增的 Web 交互元素都应尽量契合「元胞自动机」和「像素方块」的主题
- **加载动画**：推荐使用 Glider（滑翔机）或其他经典生命游戏图案作为加载动画的核心视觉元素
- **禁止**：不要引入与像素/科幻风格差距过大的 UI 元素（如圆润的按钮、渐变色背景等）

## 5. 核心代码规范

### 5.1 游戏主循环（main.py）

在 Pygbag Web 环境中，**必须严格控制渲染帧率**：

```python
while game.running:
    current_time = time.time()
    dt = current_time - last_time
    frame_duration = 1.0 / GameConfig.FPS  # ← 必须在循环内计算

    game._handle_events()

    if dt >= frame_duration:
        last_time = current_time
        game._handle_continuous_input()  # ← 必须限速
        if not game.game_over and not game.paused:
            game._update_game_logic()    # ← 必须限速
            game._check_collisions()
        game._render()                   # ← 必须限速（防止浏览器卡死）

    await asyncio.sleep(0)  # ← Web 端必需，交还控制权给浏览器
```

> ⚠️ 警告：`await asyncio.sleep(0)` 在浏览器中等价于 `requestAnimationFrame`，
> 如果渲染未限速，会以 60~144 FPS 执行，瞬间耗尽浏览器主线程资源。

### 5.2 Web 加载页隐藏逻辑

在 `static/default.tmpl` 的 Python 代码块中，游戏启动时必须同时隐藏两个容器：

```python
platform.window.infobox.style.display = "none"
platform.window.transfer.style.display = "none"  # ← 极易遗漏！
platform.window.config.gui_divider = 1
```

### 5.3 平台检测模式

```python
if sys.platform in ("emscripten", "wasi"):
    import pygbag.aio as asyncio  # Web 端
else:
    import asyncio                # 本地端
```

## 6. 维护与测试

### 6.1 本地测试流程

1. 修改代码
2. 本地运行：`python main.py`
3. 打包：`pygbag --build --template static\default.tmpl .`
4. 启动服务器：`py -m http.server 8888 -d build/web`
5. 浏览器访问：`http://localhost:8888/`
6. 点击页面解锁 Web Audio 权限
7. 测试游玩

### 6.2 关键自检项

在完成任何代码修改后，请自检以下项目：

- [ ] 本地运行 `python main.py` 无报错
- [ ] Web 打包 `pygbag --build` 成功
- [ ] 加载页面动画正常显示
- [ ] 点击后加载页正确隐藏
- [ ] 游戏主循环未被阻塞（不卡顿）
- [ ] FPS 修改在游戏中即时生效
- [ ] 更新了 `AGENTWORKS.md` 日志

## 7. GitHub Pages 部署

部署配置文件位于 `.github/workflows/deploy.yml`：

- **触发条件**：推送到 `main` 分支
- **自动流程**：构建 → 推送到 `gh-pages` 分支
- **访问地址**：`https://<用户名>.github.io/<仓库名>/`

Agent 不应手动打包和上传 Web 资源，所有 Web 部署均通过 GitHub Actions 自动完成。

---

*本文档为 Agent 开发准则，后续 Agent 请严格遵守。*
*最后更新时间：2026-05-21*
