"""
简化启动脚本 - 减少警告输出
"""
import os
import sys
import warnings

# 抑制警告
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 设置环境变量抑制 TensorFlow 警告
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYTHONWARNINGS'] = 'ignore'

# 临时修复 NumPy 兼容性
try:
    import numpy as np
    if not hasattr(np, 'complex_'):
        np.complex_ = np.complex128
except:
    pass

def main():
    """主函数"""
    try:
        print("🚀 启动证件照系统...")
        print("📝 正在初始化组件...")
        
        # 导入主程序
        from main import main as main_func
        
        print("✅ 系统启动成功！")
        print("=" * 50)
        
        # 运行主程序
        main_func()
        
    except KeyboardInterrupt:
        print("\n👋 用户取消，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n🔧 故障排除建议:")
        print("1. 检查 Python 环境和依赖包")
        print("2. 运行: pip install -r requirements.txt")
        print("3. 确保 NumPy 版本 < 2.0")
        sys.exit(1)

if __name__ == "__main__":
    main()