"""
主程序入口
"""
from src.core.game_engine import GameEngine

def main():
    """主函数"""
    game = GameEngine()
    game.run()

if __name__ == "__main__":
    main()