# Web Version Guide / 网页版制作指南

This guide explains how to convert "Cellular Cube Go" into a web game playable in the browser using `pygbag`.
本指南介绍如何使用 `pygbag` 将 "Cellular Cube Go" 转换为可在浏览器直接游玩的网页游戏。

## 1. Prerequisites / 准备工作

You need `pygbag` installed. It is a tool that packages Python/Pygame games for the web (WebAssembly).
你需要安装 `pygbag`。这是一个将 Python/Pygame 游戏打包为网页版（WebAssembly）的工具。

```bash
pip install pygbag
```

## 2. Build for Web / 构建网页版

I have created a dedicated entry point `main_web.py` that is compatible with the web browser's event loop (using `asyncio`).
我已经创建了一个专门的入口文件 `main_web.py`，它兼容浏览器的事件循环（使用 `asyncio`）。

To build and run the game locally:
构建并在本地运行：

```bash
# Run pygbag on the project folder (current directory)
# 运行 pygbag 打包当前目录
# Note: pygbag expects to run on a directory containing main.py or similar.
# Since we have main_web.py, we tell it to use that.

pygbag main_web.py
```

However, `pygbag` usually works best when pointing to a folder. If `main_web.py` is the entry, you can run:
`pygbag` 通常直接指向文件夹。如果入口是 `main_web.py`，可以这样运行：

```bash
python -m pygbag main_web.py
```

This command will:
1.  Analyze imports.
2.  Package assets.
3.  Start a local web server (usually port 8000).
4.  Open your browser to the game.

该命令将会：
1.  分析依赖。
2.  打包资源。
3.  启动本地 Web 服务器（通常是 8000 端口）。
4.  自动打开浏览器进入游戏。

## 3. Deploying / 部署上线

When `pygbag` finishes, it creates a `build/web` folder.
当 `pygbag` 运行完成后，会生成一个 `build/web` 文件夹。

To publish your game (e.g., on GitHub Pages or Itch.io):
要发布你的游戏（例如 GitHub Pages 或 Itch.io）：

1.  Locate the `build/web` folder.
    找到 `build/web` 文件夹。
2.  Upload the contents of this folder to your web host.
    将该文件夹的内容上传到你的 Web 主机。
3.  **Itch.io**: Zip the contents of `build/web` (not the folder itself, but the files inside) and upload as an HTML5 game.
    **Itch.io**: 将 `build/web` 内的所有文件压缩成 zip 包（不要包含外层文件夹），然后作为 HTML5 游戏上传。
4.  **GitHub Pages**: Push the contents to a `gh-pages` branch or configure Pages to serve from that folder.
    **GitHub Pages**: 将内容推送到 `gh-pages` 分支，或配置 Pages 从该文件夹服务。

## 4. Notes / 注意事项

- **Performance**: WebAssembly performance is generally good but slower than native. If the game lags, try reducing `WORLD_WIDTH` / `WORLD_HEIGHT` in `config/game_config.py`.
  **性能**：WebAssembly 性能通常不错但低于原生应用。如果卡顿，尝试在配置中减小世界尺寸。
- **Audio**: Audio usually requires a user interaction (click) to start in browsers.
  **音频**：浏览器中音频通常需要用户点击一次后才能播放。
- **Dependencies**: `requests` and `bs4` (used for the scraper) are ignored in the web build because they are not imported in `main_web.py`.
  **依赖**：`requests` 和 `bs4`（爬虫用）在网页构建中会被忽略，因为 `main_web.py` 没有导入它们。

## 5. Troubleshooting / 常见问题

- **Black Screen**: Open browser console (F12). If you see import errors, ensure all `src/` files are correctly referenced.
  **黑屏**：打开浏览器控制台 (F12)。如果看到导入错误，请检查文件引用。
- **No Assets**: Ensure `assets/` folder is in the same directory as `main_web.py` when building.
  **无资源**：确保构建时 `assets/` 文件夹与 `main_web.py` 同级。
