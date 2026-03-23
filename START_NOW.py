"""
立即启动系统 - 无需等待任何安装
"""
import sys
import subprocess
from pathlib import Path

def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  ID证照片系统 - 立即启动".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝\n")
    
    print("[INFO] 检查依赖...")
    
    # 检查必需的库
    required = ['cv2', 'numpy', 'PIL', 'sqlalchemy']
    missing = []
    
    for lib in required:
        try:
            __import__(lib)
            print(f"  [OK] {lib}")
        except ImportError:
            print(f"  [NO] {lib}")
            missing.append(lib)
    
    if missing:
        print(f"\n[INFO] 缺少依赖: {', '.join(missing)}")
        print("[INFO] 正在安装...")
        
        for lib in missing:
            if lib == 'cv2':
                subprocess.run([sys.executable, "-m", "pip", "install", "opencv-python", "-q"])
            elif lib == 'PIL':
                subprocess.run([sys.executable, "-m", "pip", "install", "pillow", "-q"])
            elif lib == 'sqlalchemy':
                subprocess.run([sys.executable, "-m", "pip", "install", "sqlalchemy", "-q"])
            elif lib == 'numpy':
                subprocess.run([sys.executable, "-m", "pip", "install", "numpy", "-q"])
    
    print("\n[OK] 所有依赖已准备")
    print("\n[INFO] 启动系统...")
    print("="*70 + "\n")
    
    # 启动主程序
    try:
        subprocess.run([sys.executable, "main.py"], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n\n[INFO] 系统已关闭")
    except Exception as e:
        print(f"\n[ERROR] 启动失败: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
