"""
依赖修复脚本
"""
import subprocess
import sys
import os

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            return True
        else:
            print(f"❌ {description} 失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} 异常: {e}")
        return False

def main():
    """主修复流程"""
    print("🛠️  证件照系统依赖修复工具")
    print("=" * 50)
    
    # 1. 升级 pip
    run_command("python -m pip install --upgrade pip", "升级 pip")
    
    # 2. 修复 NumPy 版本
    print("\n📦 修复 NumPy 版本兼容性...")
    run_command("pip uninstall numpy -y", "卸载当前 NumPy")
    run_command("pip install 'numpy>=1.26.0,<2.0.0'", "安装兼容版本 NumPy")
    
    # 3. 重新安装 TensorFlow
    print("\n🧠 重新安装 TensorFlow...")
    run_command("pip uninstall tensorflow -y", "卸载 TensorFlow")
    run_command("pip install 'tensorflow>=2.16.0,<2.17.0'", "安装 TensorFlow")
    
    # 4. 安装其他依赖
    print("\n📋 安装其他依赖...")
    if os.path.exists("requirements.txt"):
        run_command("pip install -r requirements.txt", "安装 requirements.txt")
    else:
        print("⚠️  requirements.txt 不存在，手动安装核心依赖...")
        core_deps = [
            "PyQt5>=5.15.0",
            "opencv-python>=4.5.0",
            "Pillow>=9.0.0",
            "pandas>=1.3.0",
            "openpyxl>=3.0.0",
            "SQLAlchemy>=1.4.0",
            "rembg>=2.0.0",
            "onnxruntime>=1.23.0"
        ]
        for dep in core_deps:
            run_command(f"pip install '{dep}'", f"安装 {dep}")
    
    # 5. 验证安装
    print("\n🔍 验证安装...")
    try:
        import numpy as np
        print(f"✅ NumPy 版本: {np.__version__}")
        
        import cv2
        print(f"✅ OpenCV 版本: {cv2.__version__}")
        
        import PyQt5
        print(f"✅ PyQt5 可用")
        
        try:
            import tensorflow as tf
            print(f"✅ TensorFlow 版本: {tf.__version__}")
        except:
            print("⚠️  TensorFlow 不可用（可选）")
        
        try:
            import rembg
            print(f"✅ rembg 可用")
        except:
            print("⚠️  rembg 不可用（可选）")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 依赖修复完成！")
    print("💡 建议使用 'python start_clean.py' 启动程序")

if __name__ == "__main__":
    main()