# Cellular Cube Go / 细胞方块漫游

[在线游玩 / Play in browser](https://zh3zhou.github.io/Cellular-Cube-Go/)

Cellular Cube Go 是一个基于 `pygame-ce` 的二维元胞自动机生存游戏。玩家控制红色方块穿过持续演化的 Conway Life 世界，避开白色活细胞，并用不同颜色的奖励开启短暂的“隔离温室”。温室使用自己的规则演化，成熟后再并入主世界。

The repository uses one Python entrypoint for desktop and WebAssembly. The main
world follows Conway's Life; colored rewards can incubate Life, HighLife, Seeds,
or Day & Night Patterns before merging them back into the world.

## 快速开始

需要 Python 3.12。

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
python main.py
```

Linux/macOS 激活环境时使用 `source .venv/bin/activate`。唯一受支持的入口是项目根目录下的 `main.py`；项目中没有 `src.main` 或单独的 Web 入口。

### 操作

- `W/A/S/D`：移动
- `P`：暂停或继续
- `R`：游戏结束后重新开始
- `Esc`：打开或关闭设置
- 设置面板中使用 `W/S` 选择、`A/D` 调整、`Enter/Space` 切换

白色细胞会导致游戏结束。彩色奖励需要先接触、再离开，随后在附近创建一个非致死的隔离演化区。

## 四种奖励

| 颜色 | 规则 | Rulestring | 默认权重 |
| --- | --- | --- | ---: |
| 绿色 | Conway Life | `B3/S23` | 55% |
| 紫色 | HighLife | `B36/S23` | 20% |
| 橙色 | Seeds | `B2/S` | 15% |
| 青蓝色 | Day & Night | `B3678/S34678` | 10% |

主世界始终是硬边界、二值 Conway Life。其他规则只存在于隔离演化区中，不会改变全局规则。

## 验证

```bash
python -m pytest
python -m compileall -q main.py config src
```

无显示器环境下可设置 SDL dummy 驱动后执行测试：

```bash
# PowerShell
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
python -m pytest
```

测试覆盖规则演化、隔离区生命周期、Pattern 目录和核心游戏循环。手工桌面验收仍应直接运行 `python main.py`。

Pattern 导入属于开发流程而非运行时。对已经离线保存、来源和许可明确的 RLE，
使用 `python -m tools.patterns.import_rle ...`；更新已授权的 Life Lexicon 快照时，
使用 `python -m tools.patterns.fetch_playgameoflife`。两者都会经过规则头、尺寸、
人口、大小写名称和旋转/镜像几何去重校验，后者同时生成逐项导入报告。

## Web 构建

安装 Web 依赖并使用固定版本的 pygbag：

```bash
python -m pip install -e ".[web]"
python -m pygbag --build --width 1100 --height 600 --ume_block 0 --template static/default.tmpl .
```

构建输出位于 `build/web/`。本地交互调试使用 pygbag 自带服务器，以便正确提供 Python/WASM 运行时：

```bash
python -m pygbag --width 1100 --height 600 --ume_block 0 --template static/default.tmpl .
```

然后打开 <http://localhost:8000/>；当前游戏不使用音频，因此网页运行时会自动启动，不要求媒体授权点击。不要把 `build/` 提交到仓库；推送到 `main` 后，GitHub Actions 会重新测试、构建、检查归档内容，并通过 GitHub Pages 官方 artifact 流程部署。

## 项目结构

```text
main.py                 桌面与 Web 通用入口
config/                 世界、规则与选择配置
src/core/               游戏循环和元胞自动机
src/entities/           玩家、奖励及边界生成器
src/patterns/           Pattern 目录、选择与隔离演化区
src/graphics/           Pygame 渲染和 UI
assets/                 运行时 Pattern 与字体
static/default.tmpl     pygbag 加载页模板
tests/                  自动化测试
```

产品意图和工程边界见 [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) 与
[AGENTS.md](AGENTS.md)。Pattern 和字体的来源/许可说明见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 数据与许可

代码使用 [MIT License](LICENSE)。当前 v2 目录包含 731 个去重 Pattern：
59 个项目内置种子和 663 个来自 PlayGameOfLife Life Lexicon 的
CC BY-SA 3.0 Conway 条目；其中 659 个外部条目可进入游戏抽取，4 个仅保留在
目录；另有 9 个来自 LifeWiki OCA、使用 GFDL 1.2 的 HighLife、Seeds 和
Day & Night 条目。第三方 Pattern 只有在来源和再分发信息明确时才进入发布目录；抓取和
导入工具不属于运行时，也不会被打进网页应用。仓库中的 Pixelify Sans
字体文件自带 SIL Open Font License 1.1 元数据，完整归属、许可边界和导入
统计见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与
`assets/patterns/import-report.v2.json`、
`assets/patterns/import-report.lifewiki.json`。
