# 代码审查与优化记录 — 2026-09-06

状态：本地实现及自动验证完成；Chrome 启动/输入验证未完成；未提交、未发布。
审查基线：`fa97cbd97ba82466f45d094cca24d0c034934752`。

## 修复的问题

| 优先级 | 问题与触发条件 | 修复位置与处理 |
| --- | --- | --- |
| P1 | 一帧补算多个 tick 时，glider 首次可见预警可直接跳到致死状态 | `src/core/game_engine.py`、`src/entities/bullet.py`：首次入境后停止本帧补算，保留剩余时间 |
| P2 | 新温室在首次绘制前已被下一次补算演化，跳过初始形态与原色 | `src/entities/reward.py`、engine：创建温室和成熟提交都要求本帧先显示 |
| P2 | 设置界面停止演化却仍检查碰撞，关闭无敌等情况下可在设置中死亡 | engine：设置期间同时停止输入、模拟和碰撞 |
| P2 | 对 NumPy dataclass 实体执行非首项 `list.remove` 触发数组比较异常 | bullet：更新后保留仍在入境的实体，避免按值删除 |
| P2 | 角落 glider 穿过视口但从未完全进入，因此永不提交或回收 | bullet：曾入境且活细胞包围盒完全出界时回收；保留暂时没有可见细胞但下一代会重新出现的合法相位 |
| P2 | W+D 等组合键实际向对角移动，却记录为最后处理的水平方向，温室随之朝向错误 | `src/utils/input_utils.py`：合并位移后调用一次 move；维持原有对角速度，无输入时保留最后方向，相反键抵消 |
| P2 | 先转换到 uint8，再校验二值，会静默接受 256、-256、1.5 等输入 | `src/core/rules.py`、zone、bullet：共享 `binary_grid`，先校验二维/二值再转换 |
| P2 | 非法目录规则元数据会打断错误汇总，NaN/Infinity 权重可漏过校验 | `src/patterns/catalog.py`：类型与有限数值先行验证，仅使用已规范化的规则映射；覆盖超大 JSON 整数 |
| P2 | pygbag 过滤会放行本地回滚目录、项目报告和 docs | `pygbag.ini`：补齐排除项，重新构建并核对压缩包 |
| P3 | 持续变化的 progress 为几乎相同的候选池创建大量缓存条目 | `src/patterns/selector.py`：仅缓存规则/尺寸对应的静态池，每次按精确进度筛选 |
| P3 | 温室逐格遍历 NumPy 数组，包括所有空白格 | `src/graphics/renderer.py`：先提取活细胞坐标，再绘制；保留颜色、偏移和绘制顺序 |

前五个新回归用例在修复前实际失败，分别覆盖预警、设置碰撞、两种非首实体清理及温室初始帧。
两名同会话只读审查者分别审查运行时与数据/性能，主控统一修改与验证。

## 测量

环境：Windows，项目 `.venv`，Python 3.12.14、pygame-ce 2.5.7、NumPy 2.1.2。
用 Git 基线源码在内存中加载旧实现，与当前实现比较，无旧文件覆盖。

温室绘制：SDL dummy，1100×600 Surface，58×108 温室，padding=0，NumPy 随机种子42；
每组100次，重复5组取中位数。计时只覆盖 `render_rewards`，不是整局或 Web 帧率。

| 活细胞密度 | 修改前 ms/次 | 修改后 ms/次 |
| --- | ---: | ---: |
| 3% | 1.588 | 0.359 |
| 50% | 7.029 | 5.802 |
| 100% | 11.680 | 10.461 |

选图：同一790项目录，五条规则，尺寸108×58，progress依次为0/1000至999/1000。
tracemalloc在目录加载后开启，测量selector与context分配：

| 指标 | 修改前 | 修改后 |
| --- | ---: | ---: |
| 缓存条目 | 5000 | 5 |
| 当前跟踪分配字节 | 6,183,424 | 364,200 |
| 峰值跟踪分配字节 | 6,190,888 | 378,008 |

这些字节数不是进程总内存。原实现在默认进度到1后不再为新进度增长，不能将其描述为无限内存泄漏。
额外用同一Random(42)、五规则交替、1000个不同进度抽样，全部 Pattern ID 与基线一致。

## 验证证据

- 原始全套：70 passed；原有 pytest 缓存目录不可写，出现一条 cache warning。
- 修复后针对性检查：72 passed；独立复查补充角落生命周期与超大整数后，相关检查32 passed。
- 最终完整检查：`.venv/Scripts/python.exe -m pytest -p no:cacheprovider`，**111 passed，107.84秒**。
  仅关闭不可写缓存插件，没有跳过测试或更改文件权限。
- `.venv/Scripts/python.exe -m compileall -q main.py config src` 通过。
- dummy桌面实际 `main.main()` 运行6帧，包括QUIT，确认pygame退出。
- dummy压力运行：1200 tick，每tick生成一个glider，玩家轮换四角，无敌仅用于测试；
  seed=20260906，两个manager seed=42。运行通过，最多14个入境实体，没有持续增长。
- 像素等价测试覆盖温室空白、3%、50%、100%密度与非零偏移。
- `git diff --check -- pygbag.ini src tests` 通过；Git仅提示Windows换行策略。
- Web构建命令：
  `.venv/Scripts/python.exe -m pygbag --build --width 1100 --height 600 --ume_block 0 --template static/default.tmpl .`
- `build/web/life.game.tar.gz` 和 `.apk` 均恰含29个运行文件；使用运行文件白名单核对，
  包含唯一入口、src、config、字体、目录与NOTICE，每个文件与当前源码逐字节相等。
- 最终tarball SHA-256：`de0c958009a5a0eb30cdc2dad1bf007188099d456c36c92c8ac12eb7c4d059d2`。
- 最终apk SHA-256：`cea43c73e03c47452934a6addc9e0e6cd8c5525c6335fd1b93ab0d4b9d548ce1`。

Chrome通过扩展打开localhost，观测到下载画面，但后续截图超时、控制连接报告未连接。
**启动与输入冒烟未通过验证，原因尚未定位**；不据此断言游戏或外部运行时故障。
未使用被禁止的内置Browser，临时localhost服务已关闭。未部署或检查线上版本。

## 复杂度与后续边界

保留现有纯规则、目录/选择器、局部演化区、引擎与渲染分层；没有增加依赖、
第二套循环、插件框架或GPU实现。共享二值检查有三个实际调用模块，避免数据入口校验漂移。
现有110×60世界没有支持改写引擎的测量依据。当前五种4/8邻居规则已验证；
本次不宣称任意大邻域都受支持，例如扩到256个邻居时需另行处理uint8邻居计数容量。

保留会话开始时已有的 `.gitignore`、`AGENTS.md`、`PROJECT_REPORT.md`、`docs/DECISIONS.md` 内容。
README作者序言、产品范围、硬边界和五种生态规则保持原样。
完成决策检查：本轮恢复现有行为契约并优化实现，没有新增产品、架构或长期工作流决策；
无需新建决策条目。以下方向均为讨论提案，不是已接受需求。

## 后续方向：Proposed

1. **生态干预游戏**：先让一个可控动作产生清晰的环境后果，例如选择温室成熟时机。
   做单场景、小规模原型，检验玩家能否预测、利用并解释变化。
   [Noita官方介绍](https://noitagame.com/)展示了物质模拟与玩家法术相互作用；
   可借鉴其系统互动思路，不复制其整套物理与内容规模。
2. **小型规则谜题**：固定种子、有限操作、明确目标，先做三个能证明玩法的关卡。
   [Baba Is You作者页面](https://hempuli.itch.io/baba)以玩家改变规则为核心；
   可借鉴规则可操作、结果可理解的设计，但关卡策划与撤销系统会增加成本。
3. **演化影像/版画**：围绕“短暂规则—孵化—同化—消散”，选少数种子，
   用细胞年龄、残影、有限色板呈现时间，先做60秒作品或9帧组图。
   [Casey Reas的Software Structures，Whitney Museum](https://whitney.org/exhibitions/software-structures)
   展示了从少量关系规则发展一组软件作品的实践。
   若保留玩家漫游，可参考[Flower官方介绍](https://thatgamecompany.com/flower/)中的环境变化体验。

优先验证体验，再决定是否增加模式、重放、导出或新的规则。生存挑战与沉浸观看的节奏可能冲突，
可用共享演化核心的独立实验模式验证；本轮未实施这些新功能。
