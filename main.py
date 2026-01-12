#!/usr/bin/env python3
"""
游戏主入口文件
Game main entry point
"""
import sys
import os

# 确保项目根目录在 Python 路径中 | Ensure project root is on Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.main import main

if __name__ == "__main__":
    main()