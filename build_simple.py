"""
简化版打包脚本 - 跳过有问题的重型库
"""

import PyInstaller.__main__
import sys
import os
import shutil
from pathlib import Path

PROJECT_NAME = "证件照采集系统"
VERSION = "1.0.0"
MAIN_FILE = "main.py"

project_path = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_path))

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def clean_build_files():
    print_section("清理旧的构建文件")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = project_path / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"✓ 已删除: {dir_name}/")

def main():
    os.chdir(str(project_path))
    
    print("\n" + "="*60)
    print(f"  {PROJECT_NAME} v{VERSION} - 简化打包工具")
    print("="*60)
    
    clean_build_files()
    
    print_section("准备打包参数")
    
    args = [
        'main.py',
        f'--name={PROJECT_NAME}',
        '--windowed',
        '--onefile',
        '--clean',
        '--noconfirm',
        f'--distpath={str(project_path / "dist")}',
        f'--workpath={str(project_path / "build")}',
        f'--specpath={str(project_path)}',
    ]
    
    # 基础隐藏导入
    hidden_imports = [
        'PyQt5.sip',
        'PyQt5.plugins.platforms.qwindows',
        'cv2',
        'PIL',
        'numpy',
        'sqlalchemy',
        'pandas',
        'openpyxl',
    ]
    
    for hidden_import in hidden_imports:
        args.append(f'--hidden-import={hidden_import}')
    
    print(f"✓ 添加了{len(hidden_imports)}个基础导入")
    
    # 排除重型库
    exclude_modules = [
        'face_recognition',
        'dlib',
        'rembg',
        'gfpgan',
        'tensorflow',
        'torch',
        'matplotlib',
        'scipy',
    ]
    
    for exclude in exclude_modules:
        args.append(f'--exclude-module={exclude}')
    
    print(f"✓ 排除了{len(exclude_modules)}个重型模块")
    
    # 添加资源
    for res_dir in ['resources', 'config']:
        res_path = project_path / res_dir
        if res_path.exists():
            args.append(f'--add-data={str(res_path)}:{res_dir}')
            print(f"✓ 添加资源: {res_dir}/")
    
    print_section("运行PyInstaller打包")
    print("这可能需要1-2分钟，请耐心等待...\n")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✓ PyInstaller执行完成")
    except Exception as e:
        print(f"\n✗ PyInstaller执行出错: {e}")
        return False
    
    # 创建启动脚本
    print_section("创建辅助文件")
    
    batch_script = f"""@echo off
echo 正在启动 {PROJECT_NAME}...
start "" "{PROJECT_NAME}.exe"
"""
    
    batch_path = project_path / "dist" / "启动.bat"
    batch_path.write_text(batch_script, encoding='utf-8')
    print(f"✓ 已创建: 启动.bat")
    
    # 验证输出
    exe_path = project_path / "dist" / f"{PROJECT_NAME}.exe"
    
    print_section("打包完成")
    
    if exe_path.exists():
        exe_size = exe_path.stat().st_size / (1024 * 1024)
        print(f"✓ 打包成功！")
        print(f"\n输出文件:")
        print(f"  {exe_path}")
        print(f"  大小: {exe_size:.2f} MB")
        print(f"\n启动方式:")
        print(f"  1. 双击 dist/启动.bat")
        print(f"  2. 或直接双击 dist/{PROJECT_NAME}.exe")
        return True
    else:
        print(f"✗ 打包失败")
        return False

if __name__ == '__main__':
    success = main()
    print("\n" + "="*60)
    if success:
        print("  ✅ 所有步骤完成！")
    else:
        print("  ❌ 打包失败")
    print("="*60 + "\n")
    sys.exit(0 if success else 1)
