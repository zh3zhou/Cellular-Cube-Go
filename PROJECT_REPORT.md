# Cellular Cube Go 当前项目详细报告

> 报告日期：2026-07-28  
> 报告对象：仓库当前工作区  
> 项目版本：`0.3.0`（以 `pyproject.toml` 为准）  
> 当前分支：`codex/full-incubation-offscreen-bullets`  
> 当前提交：`fa97cbd`（`docs: explain offscreen hazards and incubation ranges`）  
> 报告生成前工作区状态：干净，无未提交改动  
> 报告生成后工作区状态：仅新增本报告 `PROJECT_REPORT.md`

## 1. 执行摘要

Cellular Cube Go 是一个使用 Python、Pygame CE 与 NumPy 实现的小型生存游戏。玩家控制红色方块，在持续演化的二维元胞自动机世界中躲避白色活细胞；彩色奖励会生成临时、隔离、不可致死的局部规则区，局部 Pattern 完成孵化后再以白色 Conway 细胞并回主世界。

当前项目已从早期“生命游戏加射击”的实现演进为一个规则驱动、Pattern 目录驱动的单入口桌面/Web 双端项目。当前源码、产品说明和自动化测试之间总体一致，主要系统包括：

- 硬边界、非环绕的 Conway Life 主世界；
- 从屏幕外进入、先预警一帧再致死的 Conway glider；
- Life、HighLife、Seeds、Day & Night、Wolfram Code 52 五种奖励生态；
- 最多三座互不重叠、带缓冲区的隔离温室；
- 基于生存时间、成功温室数、复杂度、尺寸和近期历史的 Pattern 路由与选择；
- 790 条具备可发布许可与来源元数据的 schema v3 Pattern；
- 同一份 `main.py` 支持桌面和 Pygbag Web 构建；
- pytest、编译检查、Web 包内容检查和 Chromium 浏览器冒烟测试组成的 CI 发布门禁。

本次检查确认：

- `python -m pytest`：70 项全部通过；
- `python -m compileall -q main.py config src`：通过；
- schema v3 目录可由当前运行时代码成功加载；
- 生成报告前 Git 工作区干净；生成后唯一变化是新增本报告；
- 本次没有重新执行 Web 构建，也没有运行本地或线上浏览器实机检查，因此不能把 Web 构建和浏览器运行描述为“本次已通过”。

## 2. 信息来源与可信度边界

本报告按以下优先级使用证据：

1. 当前运行行为、测试和源码；
2. `PROJECT_CONTEXT.md` 与 `AGENTS.md`；
3. `README.md`；
4. 历史报告和迁移记录。

需要特别注意：

- `TECHNICAL_REPORT.md` 已明确标记为历史报告，其中的 `0.1.7+` 版本、Python 3.11、旧射击机制和旧模块结构不再代表当前项目。
- `proposal.txt` 是早期提案，不是当前产品承诺。
- `MIGRATION_AUDIT.md` 用于记录重构取舍，适合解释历史行为，但不能覆盖当前源码和测试。
- `《开发》/` 与 `.trae/documents/` 是仓库所有者的私有上下文。本报告没有读取或发布其中内容。
- `build/` 是生成目录且被 Git 忽略。本报告没有把既有构建产物当作当前源码已重新构建的证据。

## 3. 产品定位与当前范围

### 3.1 核心体验

游戏将 Conway Life 从被动观察对象改造成持续变化的生存空间：

- 红色玩家方块在 `1100×600` 像素画面内移动；
- 网格单元为 `10×10` 像素，因此主世界为 `110×60` 个单元；
- 白色活细胞和已过预警期的来袭 glider 会导致玩家死亡；
- 彩色温室中的活细胞可以穿过，不会致死；
- 温室成熟后，仍存活的局部细胞变成白色、立即恢复致死性，并进入 Conway 主世界。

### 3.2 当前明确的非目标

当前阶段不包含：

- 全局多规则混合世界；
- Brian's Brain、Langton's Ant、Lenia 或连续状态自动机；
- 生成音乐；
- 完整收集、解锁或升级系统；
- 以分数为核心的新默认模式；
- 桌面和 Web 的两套独立游戏循环。

这些边界来自 `PROJECT_CONTEXT.md`，历史笔记中超出边界的想法不能自动视为已排期功能。

## 4. 技术栈、依赖与运行环境

### 4.1 语言与依赖

| 项目 | 当前约束 | 作用 |
| --- | --- | --- |
| Python | `>=3.12,<3.13` | 唯一运行语言 |
| NumPy | `2.1.2` | 网格状态、规则演化和局部 Pattern 运算 |
| pygame-ce | `2.5.7` | 窗口、输入、绘制、字体与矩形碰撞 |
| pytest | `8.4.2` | 自动化测试 |
| pygbag | `0.9.3` | WebAssembly/Web 打包 |
| Beautiful Soup | `4.12.3` | 离线 Pattern 获取与导入工具 |
| Requests | `2.32.3` | 离线 Pattern 获取工具 |

依赖的唯一事实来源是 `pyproject.toml`。`requirements.txt` 只是执行 `-e .` 的兼容入口。

根目录 `main.py` 的 PEP 723 依赖块故意只保留裸包名 `pygame-ce` 和 `numpy`。这是对 pygbag 0.9.3 Web wheel 解析行为的兼容要求，不应机械改成带版本号的写法。

### 4.2 已检查的本地环境

- 虚拟环境 Python：`3.12.13`
- pytest：`8.4.2`
- 当前平台：Windows
- 本次测试使用仓库内 `.venv`

### 4.3 运行与构建命令

桌面运行：

```powershell
python main.py
```

安装测试依赖：

```powershell
python -m pip install -e ".[test]"
```

完整测试与编译检查：

```powershell
python -m pytest
python -m compileall -q main.py config src
```

Web 构建：

```powershell
python -m pip install -e ".[web]"
python -m pygbag --build --width 1100 --height 600 --ume_block 0 --template static/default.tmpl .
```

## 5. 仓库规模与结构

本次统计排除了 `.git/`、虚拟环境、缓存、`build/`、私有笔记和其他生成内容。

| 指标 | 当前值 |
| --- | ---: |
| Python 文件 | 38 |
| Python 总行数 | 5,736 |
| 运行时代码行数（`main.py`、`config/`、`src/`） | 3,638 |
| 测试代码行数 | 932 |
| 自动化测试数 | 70 |
| schema v3 Pattern 数 | 790 |

主要目录：

```text
main.py                  桌面/Web 唯一入口
config/                  游戏尺寸、速度、颜色和设置项
src/core/                主引擎、CA 规则、主世界演化、碰撞
src/entities/            玩家、来袭 glider、奖励、隔离温室
src/patterns/            RLE、目录验证、复杂度分析、Pattern 选择
src/graphics/            Pygame 渲染和 UI
src/utils/               输入与小型数学工具
assets/patterns/         运行时目录、导入报告和再分发说明
assets/fonts/            Pixelify Sans 字体与说明
tools/patterns/          离线获取、导入、迁移、分析和目录构建
tests/                   规则、目录、奖励、温室、glider 和引擎测试
static/default.tmpl      Pygbag Web 加载模板
.github/workflows/       验证与 GitHub Pages 部署
```

## 6. 当前架构

### 6.1 总体运行流

```text
main.py
  └─ 创建 GameEngine
      ├─ 读取 Pygame 事件
      ├─ 固定步长累计并执行 GameEngine.step()
      │   ├─ 玩家输入与位置更新
      │   ├─ 屏外 glider 演化、进入和提交
      │   ├─ Conway 主世界演化
      │   ├─ 奖励生成、接触/离开检测
      │   ├─ 隔离温室局部演化与成熟提交
      │   └─ 玩家与危险单元碰撞检测
      ├─ GameEngine.render()
      │   ├─ 主世界
      │   ├─ 奖励与彩色温室
      │   ├─ 玩家和来袭 glider
      │   └─ 暂停、结束或设置 UI
      └─ Web 环境每帧 yield 给浏览器
```

### 6.2 统一入口与帧调度

`main.py` 根据 `sys.platform` 选择标准 `asyncio` 或 `pygbag.aio`，但两端都实例化同一个 `GameEngine`：

- 桌面端由 `pygame.time.Clock.tick(GameConfig.FPS)` 限帧；
- Web 端不让 Pygame 限帧，而是测量经过时间并在每帧 `await asyncio.sleep(0)`；
- 每帧 `dt` 最大限制为 0.25 秒，防止长暂停后产生过大的追赶步数；
- `GameEngine.step()` 使用时间累加器和当前 FPS 计算固定模拟步长；
- 一个温室刚提交为白色时会中止本帧剩余追赶步，让成熟 Pattern 至少完整渲染一帧后再接受 Conway 演化。

Web 环境还会把最小状态写入 `document.body.dataset`，供 CI 检查游戏启动、设置开关、玩家位置和迭代数。

### 6.3 主世界元胞自动机

`src/core/rules.py` 提供不可变的规则与邻域定义。规则演化使用 NumPy、零填充边界，不发生环绕。

`CellularAutomaton` 负责：

- 生成初始随机二值世界；
- 清空玩家出生点附近安全区；
- 使用 Conway Life 演化主世界；
- 为活动温室建立保留区掩码；
- 在主世界演化时强制清空温室保留区，阻止外部 Conway 细胞侵入；
- 为碰撞检测同步同一份保护掩码。

纯规则层不依赖 Pygame，可以独立测试和用于离线 Pattern 分析。

### 6.4 五种规则生态

| 奖励色 | 规则 | 规则式 | 邻域 | 孵化范围 |
| --- | --- | --- | --- | ---: |
| 绿色 | Conway Life | `B3/S23` | Moore 8 邻域 | 12–48 代 |
| 紫色 | HighLife | `B36/S23` | Moore 8 邻域 | 48–144 代 |
| 橙色 | Seeds | `B2/S` | Moore 8 邻域 | 32–96 代 |
| 青蓝色 | Day & Night | `B3678/S34678` | Moore 8 邻域 | 48–160 代 |
| 黄色 | Wolfram Code 52 | `B24/S134` | von Neumann 4 邻域 | 48–160 代 |

所有规则都是二状态、外总和规则。Code 52 是当前唯一使用四邻域的生态。

### 6.5 来袭 glider

历史上的“子弹”模块当前实际管理的是 Conway glider：

- 使用一个已验证的 3×3 glider 的四种旋转；
- 完整生成在可见硬边界之外；
- 在自身局部无界网格中演化；
- 第一次有细胞进入画面时只显示、不致死；
- 从第二个可见世代开始参与玩家碰撞；
- 全部活细胞进入世界后写入主状态，随后由普通 Conway 规则继续演化。

默认每 9 个模拟 tick 尝试生成一个来袭结构。以默认 13 FPS 计算，间隔约为 0.69 秒；修改 FPS 会改变其实际秒间隔，因为该配置按 tick 计数。

### 6.6 奖励、路由和 Pattern 选择

默认每 18 个模拟 tick 尝试生成奖励。生成点必须：

- 位于非边界单元；
- 周围 3×3 主世界区域为空；
- 不落在现有温室保留矩形中；
- 不与已有奖励重合。

绿色 Life 路由权重始终至少为 55%。剩余权重按副规则可用候选数的平方根分配；若某副规则的新鲜候选不足，其未使用份额回流 Life。

路由颜色和 Pattern 选择共享同一个冻结的 `SelectionContext`，避免出现“先选中某颜色，随后发现该规则无可用 Pattern”的不一致。

进度值为：

```text
progress = min(
    1,
    0.7 × survival_seconds / variety_duration
    + 0.3 × successful_greenhouses / 8
)
```

进度驱动：

- 复杂度上限从 30 平滑增加到 100；
- 目标复杂度从 15 增加到 100；
- 大型 Pattern 选择概率从 3% 增加到 15%；
- 最近四个 Pattern 优先排除；
- 最近两个尺寸参与差异化加权；
- 最近 200 次选择用于 Pattern 逆频和类别平衡；
- 后期仍允许低复杂度候选出现。

### 6.7 温室生命周期

玩家需要先碰到奖励，再离开奖励格，才会尝试创建温室。种子完整包围盒被放在离开方向的后方，并按方向旋转。

温室的关键性质：

- 局部状态与 Conway 主世界分离；
- 规则、颜色和 padding 由奖励类型决定；
- 最多同时存在三座；
- 温室之间至少保留一格缓冲；
- 主世界保留矩形会被清空，外部细胞无法侵入；
- 彩色细胞不参与致死碰撞；
- 颜色从奖励原色连续插值到白色；
- Pattern 灭绝时提前清除，不提交任何细胞；
- 存活至固定孵化终点后提交到主世界；
- 提交后的白色细胞立即失去保护并恢复致死性。

孵化时长由复杂度和包围盒面积以 2:1 权重合成，然后在每条规则当前可玩目录的信号范围内归一化，映射到该规则的完整孵化区间。这个“复杂度”是项目内部的玩法指标，不是对 Pattern 所属形式复杂性类别的科学断言。

## 7. Pattern 数据系统

### 7.1 目录规模

当前运行目录：`assets/patterns/catalog.v3.json`

| 规则 | 目录总数 | 可放入 `108×58` 有效区（允许旋转） |
| --- | ---: | ---: |
| Life | 710 | 706 |
| HighLife | 20 | 20 |
| Seeds | 20 | 20 |
| Day & Night | 20 | 20 |
| Code 52 | 20 | 20 |
| 合计 | 790 | 786 |

其中：

- `standard`：300；
- `large`：490；
- 复杂度分数范围：12.731–87.4；
- 分析器版本：`1.0`；
- 每条记录的标准测量窗口：最多 256 代。

“可放入”统计由当前 `PatternCatalog.patterns_for()` 计算，允许宽高互换，因此不能用简单的原始宽高比较替代。

### 7.2 schema v3 的关键字段

每条 Pattern 包含：

- 稳定 ID、名称和规则 ID；
- 分类、宽高、人口和 RLE；
- 权重、大小 tier 和标签；
- 复杂度分数、复杂度等级和受控行为标签；
- 峰值人口、峰值面积、寿命、周期、位移和增长率；
- 来源、版本、外部 ID、许可及可选内容摘要；
- `rule-native` 或 `polyglot` 规则亲和性。

加载器会一次性验证整个目录。若出现未知规则、无效 RLE、维度/人口不一致、ID 冲突、同规则几何重复、不可发布许可或分析字段不一致，目录加载整体失败，不会静默跳过坏记录。

### 7.3 来源与许可分布

| 许可 | Pattern 数 |
| --- | ---: |
| MIT | 118 |
| CC BY-SA 3.0 | 663 |
| GFDL 1.2 | 9 |

当前来源包括：

- 项目自有种子和固定随机种子搜索生成内容；
- PlayGameOfLife 提供的 Life Lexicon 快照；
- LifeWiki OCA 的固定精选快照。

旧 `library.json` 中 109 条缺少逐条来源和再分发许可的数据没有进入发布目录；其排除原因保留在导入报告中。

### 7.4 离线工具边界

`tools/patterns/` 负责：

- 严格 RLE 导入；
- PlayGameOfLife Life Lexicon 快照刷新；
- LifeWiki OCA 固定快照重建；
- 旧内置 Pattern 迁移；
- schema v3 分析、几何去重和补库。

这些操作属于离线开发流程。运行时不会抓取网络，也不会修改 Pattern 目录。

## 8. 渲染、输入与设置

### 8.1 默认操作

| 输入 | 行为 |
| --- | --- |
| `W/A/S/D` | 移动 |
| `P` | 暂停或继续 |
| `R` | 游戏结束后重开 |
| `Esc` | 打开或关闭设置 |
| 设置内 `W/S` | 切换项目 |
| 设置内 `A/D` | 调整数值或切换布尔值 |
| 设置内 `Enter/Space` | 切换布尔值 |

### 8.2 可调设置

- FPS：5–60；
- Wu Di Mode：跳过碰撞检查；
- Reward System：启用或关闭奖励与温室系统；
- Variety Duration：30–180 秒，以 5 秒为步长。

重开游戏会复用已验证、不可变的 Pattern 目录，只清空单局状态和选择历史，避免在 WebAssembly 环境重复解析大型 JSON。

## 9. Web 构建与发布

### 9.1 打包边界

`pygbag.ini` 明确排除：

- Git 和 GitHub 元数据；
- 测试、导入工具、缓存和虚拟环境；
- 私有笔记、CV、截图和历史文档；
- 旧目录、导入报告与开发配置；
- 已生成的 `build/`。

Web 运行包需要保留：

- `main.py`；
- `src/`；
- `config/`；
- 运行时 `assets/`；
- `assets/patterns/NOTICE.md`。

### 9.2 CI/CD

`.github/workflows/deploy.yml` 在 pull request、`main` 推送或手动触发时执行：

1. 使用 Python 3.12；
2. 安装测试和 Web 依赖；
3. 运行 pytest 与 compileall；
4. 使用固定参数执行 Pygbag 构建；
5. 检查归档必需内容与敏感/非运行内容泄漏；
6. 安装 Playwright Chromium；
7. 启动本地 HTTP 服务；
8. 验证 Canvas 启动和页面无 JavaScript 错误；
9. 模拟 `Esc`，验证设置页可开关；
10. 仅在 `main` 推送时上传并部署 GitHub Pages artifact。

当前发布使用 GitHub 官方 Pages artifact 与 `actions/deploy-pages`，不是历史报告所述的 `gh-pages` 分支推送方案。

### 9.3 外部运行依赖

Web 模板从 jsDelivr 加载 BrowserFS 1.4.3，并使用 Pygbag 模板提供的 CDN 地址加载 Python/WebAssembly 运行环境。因此首次启动不仅依赖仓库发布产物，也依赖外部 CDN 可用性。

## 10. 自动化验证现状

### 10.1 本次实际执行结果

执行日期：2026-07-28

```text
Python 3.12.13
pytest 8.4.2
70 passed in 83.83s
compileall passed
```

测试覆盖的行为类别：

- 五种规则和两种邻域的演化；
- 非环绕硬边界；
- EvolutionZone 成熟、灭绝、稳定性、颜色与重叠；
- 四种来袭 glider 的合法性、移动方向、屏外生成、预警和提交；
- schema v3 目录验证、RLE 编解码和几何去重；
- 复杂度分析的可重复性；
- Pattern 进度、近期历史、类别与尺寸选择；
- 奖励路由权重；
- 奖励接触后离开、后向放置、温室生成与提交；
- 每条规则孵化范围的完整映射；
- GameEngine 的公开 step/render/shutdown 接口；
- 固定模拟步长、重开目录复用和提交帧行为。

### 10.2 验证警告与未执行项

pytest 报告一个非功能性警告：

```text
PytestCacheWarning: cache could not write ... .pytest_cache\v\cache\nodeids
```

这表示本次环境无法更新已有 pytest 缓存，不表示测试失败。所有 70 项测试仍通过。

本次未执行：

- Pygbag Web 重新构建；
- 当前构建归档的人工复核；
- 本地 Chromium 冒烟测试；
- GitHub Pages 线上冒烟测试；
- 可见窗口下的人工游戏体验与视觉检查。

因此，上述项目只能描述为“CI 已配置覆盖”，不能描述为“本次检查已通过”。

## 11. 代码质量与工程判断

### 11.1 已确认的优势

- 单一桌面/Web 入口，避免双实现漂移；
- CA 规则、RLE、目录与选择逻辑大体独立于 Pygame；
- 主世界和局部生态的状态所有权清晰；
- 目录在运行时严格、原子地验证；
- Pattern 来源和许可按记录保存；
- 测试围绕重构中曾发生回归的行为建立了明确断言；
- Web 包对隐私文件和非运行内容设有可执行泄漏检查；
- 重启复用目录，针对 WebAssembly 解析成本做了实际优化；
- 产品决策、工程合同和历史迁移说明已分层存放。

### 11.2 基于源码的维护风险

以下是工程判断，不代表当前存在已复现故障：

1. **历史文档仍可能误导维护者。**  
   `TECHNICAL_REPORT.md` 虽有醒目历史声明，但篇幅长且细节丰富，搜索时仍可能盖过当前结构。维护工作应优先从 `AGENTS.md`、`PROJECT_CONTEXT.md`、`README.md` 和源码开始。

2. **固定版本带来复现性，也带来升级集中风险。**  
   Python 被限制在 3.12，运行库与工具链全部精确锁定。升级 Pygbag、Pygame CE、NumPy 或 Python 时需要同时验证桌面、Web wheel 解析、模板和浏览器冒烟测试。

3. **Web 首次启动依赖外部 CDN。**  
   BrowserFS 和 Pygbag/Python Web 运行时的远程资源不可用时，仓库自身产物完整也可能无法启动。

4. **视觉与手感仍主要依赖人工验收。**  
   当前自动化验证了启动、输入和规则行为，但不会判断移动手感、危险密度、色彩可读性、UI 排版或长局节奏。

5. **随机系统的长期分布需要持续统计。**  
   现有测试覆盖路由和选择约束，但实际游玩中的长期体验还受世界初始随机状态、奖励空位、Pattern 可放置性和温室重叠共同影响。单元测试通过不等于体验分布已经稳定。

6. **复杂度指标具有项目特定边界。**  
   离线分析使用有限 arena、硬边界和最多 256 代测量。它适合项目内部选择与孵化映射，但不应被解释为完整的数学分类或无限平面行为证明。

7. **字体上游版本仍不完整。**  
   Pixelify Sans 的字体内许可和 SHA-256 已记录，但精确下载 URL、release tag 或 source commit 仍未知。

8. **测试缓存权限需要环境清理。**  
   当前警告不影响正确性，但会减少 pytest 缓存能力，并可能掩盖未来真正的缓存异常。应在不破坏用户文件的前提下检查 `.pytest_cache` 所有权或重建方式。

## 12. 建议的下一步

### 优先级 A：建立完整的当前发布证据

在准备合并或发布前执行：

1. 运行完整 pytest 与 compileall；
2. 重新执行 Pygbag 构建；
3. 检查归档的必需/禁止内容；
4. 在本地浏览器完成启动、移动、设置开关冒烟；
5. 合并后由 GitHub Actions 部署；
6. 对 GitHub Pages 再做一次线上启动与输入冒烟。

这是当前最有价值的下一步，因为本次报告验证了核心 Python 状态，但没有重新验证 Web 产物。

### 优先级 B：处理文档发现路径

可以考虑在历史 `TECHNICAL_REPORT.md` 顶部增加更短、更醒目的当前文档链接，或者将历史资料集中到明确的历史目录。任何移动前都应检查已有外部链接，不能直接删除历史记录。

### 优先级 C：补充体验层验收

建立轻量人工检查表，至少覆盖：

- 开局可读性与出生安全；
- glider 首帧预警是否足够明显；
- 五种温室颜色与白色成熟状态是否容易区分；
- 30、90、180 秒 Variety Duration 的节奏差异；
- 低 FPS 与高 FPS 下实际秒节奏的变化；
- 三座温室并存时的可读性和性能；
- 桌面与 Web 的移动手感一致性。

### 优先级 D：升级与供应链准备

在单独分支中周期性验证：

- Python 3.12 最新补丁版本；
- Pygame CE、NumPy、pytest 和 Pygbag 的候选升级；
- Pygbag 模板差异；
- BrowserFS/CDN 依赖是否仍必要；
- 字体精确上游版本能否补全。

这类升级不应与玩法改动混在同一变更中。

## 13. 当前开放问题

这些问题无法仅从本次源码与自动化结果得出结论：

- 当前线上 GitHub Pages 是否与 `fa97cbd` 对应；
- 当前分支是否计划直接合并到 `main`，还是仍需额外玩法验收；
- 长局中五类奖励的实际感知频率是否符合设计预期；
- 13 FPS 默认值与可调 FPS 对 glider/奖励按秒节奏的影响是否是有意设计；
- 外部 CDN 失效时是否需要离线或自托管回退；
- Pixelify Sans 的精确上游版本是否还能追溯；
- 当前忽略的 `build/` 是否由最新源码生成。

## 14. 结论

当前项目处于“核心架构和自动化行为相对稳定、发布体验仍需重新验证”的状态。

从源码和测试看，规则系统、屏外 glider、奖励路由、Pattern 目录、隔离温室和单入口双端架构已经形成一致的工程闭环；70 项测试和编译检查均通过，许可与隐私边界也有明确的机器检查。当前最大的不确定性不在核心 Python 正确性，而在本次没有重建和实测 Web 产物，以及随机玩法的长期体验与视觉手感仍需要人工验证。

在没有新增产品决策的情况下，最安全的下一步是按现有发布门禁重建 Web、完成本地浏览器冒烟，再交由 GitHub Actions 部署并做线上复验。

