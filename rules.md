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

- 打包命令统一使用 `pygbag --build --template static\default.tmpl .`
- 所有的第三方依赖（如 `numpy`）必须在 `main.py` 顶部的 `# /// script` 元数据块中声明。
- 不属于游戏运行必须的文件（如开发文档、`.git`、测试脚本等）必须在 `pygbag.ini` 中配置忽略，以减少打包体积。

## 4. UI 与交互准则

- 保持生命游戏的科幻、像素极简风格。
- 任何新增的 Web 交互元素（如加载页面的动画）都应尽量契合“元胞自动机”和“像素方块”的主题。
