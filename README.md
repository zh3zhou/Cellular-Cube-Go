# Cellular Cube Go / 细胞方块漫游

## [▶ 在线游玩（推荐）](https://zh3zhou.github.io/Cellular-Cube-Go/)

## 作者的碎碎念

（只有中文的废话碎碎念；除了这些下面都是大模型生成的，欧耶）

大二上学计算物理2。顺道跟着一个python教程写了Conway's Life Game,那个学期也在扒拉着看一些复杂系统的东西，也在上一门大概叫VR游戏设计与开发的课程，于是碎碎地看了很多游戏创作的技术、哲学之类......当时每天都在YY要做什么样的游戏。后来我的UE5学习中道崩殂在调天空的材质和光线时，版本跟我看的教程不一样，于是怎么也调的不像人类。后来这段有点入魔的经历给我留下的大概就是很多有意思的故事和idea，机核这个博主，和这个当时被我掰弯成某种游戏的CUBE GO。在后来一年多断断续续地把这个小东西拿出来玩一玩，改一改，修一修。在尝试这个小项目的初期，我就已经意识到，idea很美妙，看着它的实现更美妙，甚至写程序写代码本身，略显大逆不道地讲，比做物理题OR推公式（虽然w我也不会，可能两个都不会）更有让人享受的一面。但Debug，实在是会人在几分钟或者几十秒之内意识到坚持完成它是一件非常需要毅力的事儿，对我这个会懒到不清游戏日活，不签到领月卡的人来说太地狱了。不过今年Vibe Coding的出现让我的各种进程都轻巧容易了很多，尤其是针对这样弱资源，弱代码，强IDEA的小游戏的实现，如虎添翼，再造之恩，值得磕俩，舒服舒服......

没空写太多，其实这个小小项目远远没打磨到可以让我自信推出的程度，也跟很多朋友唠了之后有一些尝试的方向，和一些显然的小BUG存在NOTE里还没琢磨。但因为想顺便给CV里一个除了邮箱以外能点开的链接想着先上架了，如果有人尝试配置游玩了它（ZZ将感动），欢迎找我唠嗑聊聊。想要接着试着在这个框架下接着开发也欢迎联系我，我将给小IDEA找新的家。

2026/01/13 0:46 宿舍楼道洗衣机上坐着

---

在持续演化的元胞自动机中控制红色方块生存。白色细胞是危险；触碰并离开彩色奖励，会在离开方向后方生成一座使用不同规则的隔离温室，不必为了躲开新 Pattern 手动折返。彩色孵化细胞可以穿过且不会致死，并会从对应奖励色逐代渐变到白色；成熟后并入 Conway 主世界。

![Cellular Cube Go 网页版实机画面](assets/screenshots/web-gameplay.png)

### 操作

| 按键 | 功能 |
| --- | --- |
| `W` `A` `S` `D` | 移动红色方块 |
| `P` | 暂停 / 继续 |
| `R` | 游戏结束后重开 |
| `Esc` | 打开 / 关闭设置 |
| 设置内 `W/S` | 选择项目 |
| 设置内 `A/D` | 调整数值 |
| 设置内 `Enter/Space` | 切换开关 |

主世界始终使用硬边界、二值 Conway Life。最多同时存在三座互不重叠且相隔一格的温室；外面的 Conway 细胞不能侵入。温室若演化灭绝会直接清除；否则由 Pattern 的包围盒大小与复杂度共同决定孵化代数，并在颜色渐变完成时成为普通白色细胞、恢复致死碰撞。

## 五种奖励生态

| 颜色 | 规则 | 规则式 / 邻域 | 游戏中的性格 |
| --- | --- | --- | --- |
| 绿色 | Conway Life | `B3/S23`，Moore 8 邻域 | 主世界规则；奖励概率永不低于 55% |
| 紫色 | HighLife | `B36/S23`，Moore 8 邻域 | 额外的六邻居出生支持复制结构 |
| 橙色 | Seeds | `B2/S`，Moore 8 邻域 | 活细胞立即死亡，新生快速爆发 |
| 青蓝色 | Day & Night | `B3678/S34678`，Moore 8 邻域 | 活/死反转对称，容易形成浓密边界 |
| 黄色 | Wolfram Code 52 | `B24/S134`，von Neumann 4 邻域 | 十字晶格中的周期块、移动边界与复杂局部结构 |

绿色先保留 55%。剩余 45%按各副规则当前可用 Pattern 数量的平方根分配；若某规则暂时没有足够的新 Pattern，份额自动回流绿色。因此绿色通常会高于 55%，副规则扩库也不会突然淹没主玩法。

Code 52 的规则选择参考了 Packard/Wolfram 的[二维元胞自动机研究](https://content.wolfram.com/sw-publications/2020/07/two-dimensional-cellular-automata.pdf)与后续的[复杂行为研究](https://www.complex-systems.com/abstracts/v17_i02_a05/)。论文只用于规则灵感和技术说明，目录没有复制论文图像。

## 复杂度会随游戏成长

开局优先提供紧凑、可读的 Pattern。进程同时考虑生存时间与成功创建的温室：

```text
progress = min(1, 0.7 × survival_time / Variety Duration + 0.3 × rewards / 8)
```

`Variety Duration` 默认 90 秒，可在设置中以秒调整。当前复杂度上限为 `30 + 70 × progress`，抽样目标从 15 平滑移动到 100；大型 Pattern 的机会从约 3%增长到最高 15%。低复杂度结构后期仍会出现。每条规则还会避开最近四个 Pattern，并结合最近尺寸、类别配额和最近 200 次历史的逆频调节来减少机械重复。

## Quick Play (English)

[Play the Web version](https://zh3zhou.github.io/Cellular-Cube-Go/) and move the red cube with `WASD`. Avoid white cells. Touch and then leave a colored reward to incubate a Pattern behind your exit direction under its color's rule. Greenhouse cells fade from the reward color to white and are safe to cross while colored; once mature, they join the lethal Conway world. Use `P` to pause, `R` to restart after game over, and `Esc` for settings.

## 桌面版

需要 Python 3.12：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
python main.py
```

Linux/macOS 使用 `source .venv/bin/activate`。桌面与 Web 唯一入口都是根目录的 `main.py`。

## Pattern 目录

schema v3 目录当前有 790 个可发布、几何去重的 Pattern：

| 规则 | 目录总数 | 可放入 `108×58` 有效区 |
| --- | ---: | ---: |
| Life | 710 | 706 |
| HighLife | 20 | 20 |
| Seeds | 20 | 20 |
| Day & Night | 20 | 20 |
| Code 52 | 20 | 20 |

每条记录包含稳定 ID、RLE、规则、分类、来源与许可，以及可重复的 256 代分析结果：复杂度分数/等级、寿命、峰值人口与面积、周期、位移、增长率和受控行为标签。外部来源不足的副规则使用固定种子算法搜索补充，并保留生成器版本和拒绝报告。历史 `library.json` 的 109 条无来源数据没有静默丢弃：它们以 `unknown-license` 记录在 v3 报告中，但不会进入发布目录。

离线导入和重建：

```powershell
python -m tools.patterns.import_rle <inputs> --manifest <manifest.json> --output <catalog.json> --report <report.json>
python -m tools.patterns.build_catalog_v3
```

运行时不会抓取网络。许可与归属见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)、[Pattern NOTICE](assets/patterns/NOTICE.md) 和 [v3 导入报告](assets/patterns/import-report.v3.json)。

## 验证与 Web 构建

```powershell
python -m pytest
python -m compileall -q main.py config src
python -m pip install -e ".[web]"
python -m pygbag --build --width 1100 --height 600 --ume_block 0 --template static/default.tmpl .
```

CI 会运行规则、目录、10,000 次路由/选择统计和 SDL 集成测试，检查 Web 归档没有私人文档或导入工具，再用 Chromium 验证 Canvas 启动、键盘输入和设置界面。`main` 通过后使用 GitHub Pages 官方 artifact 部署。

## 项目结构与许可

```text
main.py                 桌面与 Web 通用入口
config/                 世界与游戏配置
src/core/               游戏循环和纯 CA 规则
src/entities/           玩家、奖励和隔离温室
src/patterns/           v3 目录、分析和进程选择
src/graphics/           Pygame 渲染与 UI
assets/                 运行时 Pattern、字体和截图
tools/patterns/          离线导入、分析与目录构建
tests/                  自动化验证
```

项目代码使用 [MIT License](LICENSE)。第三方 Pattern 与 Pixelify Sans 保留各自许可；完整边界见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。产品意图与工程合同见 [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) 和 [AGENTS.md](AGENTS.md)；重构前后行为核对见 [MIGRATION_AUDIT.md](MIGRATION_AUDIT.md)。
