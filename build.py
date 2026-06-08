"""
证件照采集系统 - PyInstaller打包脚本
自动将PyQt5应用打包成可执行文件(.exe)
"""

import PyInstaller.__main__
import sys
import os
import shutil
import subprocess
from pathlib import Path

# 配置信息
PROJECT_NAME = "证件照采集系统"
VERSION = "1.0.0"
MAIN_FILE = "main.py"
ICON_FILE = "resources/icons/app.ico"

# 项目路径
project_path = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_path))

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def clean_build_files():
    """清理旧的构建文件"""
    print_section("清理旧的构建文件")
    
    dirs_to_clean = ['build', 'dist', '__pycache__', '.eggs']
    for dir_name in dirs_to_clean:
        dir_path = project_path / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"✓ 已删除: {dir_name}/")
    
    spec_files = project_path.glob("*.spec")
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"✓ 已删除: {spec_file.name}")

def check_requirements():
    """检查必要文件和依赖"""
    print_section("检查项目文件")
    
    required_files = [
        'main.py',
        'config/__init__.py',
        'models/__init__.py',
        'controllers/__init__.py',
        'views/__init__.py',
        'utils/__init__.py',
        'requirements.txt'
    ]
    
    missing = []
    for file_path in required_files:
        full_path = project_path / file_path
        if full_path.exists():
            print(f"✓ 发现: {file_path}")
        else:
            print(f"✗ 缺失: {file_path}")
            missing.append(file_path)
    
    if missing:
        print(f"\n警告: 缺少{len(missing)}个文件")
        return False
    
    print(f"\n✓ 所有必要文件都已找到")
    return True

def create_build_script():
    """生成PyInstaller参数"""
    print_section("准备打包参数")
    
    # 基础参数
    args = [
        'main.py',
        f'--name={PROJECT_NAME}',
        '--windowed',  # 隐藏控制台窗口
        '--onefile',   # 单文件模式
        '--clean',     # 清理临时文件
        '--noconfirm',  # 不询问
        f'--distpath={str(project_path / "dist")}',
        f'--workpath={str(project_path / "build")}',
        f'--specpath={str(project_path)}',
        '--python-option=u',  # 使用unbuffered输出
    ]
    
    # 添加图标
    icon_path = project_path / ICON_FILE
    if icon_path.exists():
        args.append(f'--icon={str(icon_path)}')
        print(f"✓ 使用图标: {ICON_FILE}")
    else:
        print(f"⚠ 未找到图标文件: {ICON_FILE}")
    
    # 添加资源文件
    resource_dirs = [
        'resources',
        'config',
    ]
    
    for res_dir in resource_dirs:
        res_path = project_path / res_dir
        if res_path.exists():
            args.append(f'--add-data={str(res_path)}:{res_dir}')
            print(f"✓ 添加资源: {res_dir}/")
    
    # 收集face_recognition模型
    args.extend([
        '--collect-submodules=face_recognition',
        '--collect-submodules=face_recognition_models',
    ])
    
    # 隐藏导入（避免找不到依赖）
    hidden_imports = [
        'PyQt5.sip',
        'PyQt5.plugins.platforms.qwindows',
        'PyQt5.plugins.platforms.qxcb',
        'PyQt5.plugins.platforms.qcocoa',
        'PyQt5.plugins.imageformats',
        'face_recognition',
        'dlib',
        'cv2',
        'PIL',
        'rembg',
        'gfpgan',
        'basicsr',
        'facexlib',
        'insightface',
        'numpy',
        'sqlalchemy',
        'pandas',
        'sklearn',
        'face_recognition_models',  # 添加face_recognition模型
    ]
    
    for hidden_import in hidden_imports:
        args.append(f'--hidden-import={hidden_import}')
    
    print(f"✓ 添加了{len(hidden_imports)}个隐藏导入")
    
    # 排除不必要的模块（减小文件大小）
    exclude_modules = [
        'matplotlib',
        'scipy',
        'statsmodels',
        'sympy',
    ]
    
    for exclude in exclude_modules:
        args.append(f'--exclude-module={exclude}')
    
    print(f"✓ 排除了{len(exclude_modules)}个不必要模块")
    
    return args

def run_pyinstaller(args):
    """运行PyInstaller"""
    print_section("运行PyInstaller打包")
    
    print("命令: pyinstaller " + " ".join(args[:5]) + " ...\n")
    print("这可能需要2-5分钟，请耐心等待...")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✓ PyInstaller执行完成")
        return True
    except Exception as e:
        print(f"\n✗ PyInstaller执行出错: {e}")
        return False

def create_launch_scripts():
    """创建启动脚本"""
    print_section("创建启动脚本")
    
    # Windows批处理文件
    batch_script = f"""@echo off
REM {PROJECT_NAME} 启动脚本
REM 检查主程序是否存在
if not exist "{PROJECT_NAME}.exe" (
    echo 错误：找不到主程序文件 "{PROJECT_NAME}.exe"
    echo 请确保在正确的目录中运行此脚本
    pause
    exit /b 1
)

REM 启动应用
start "" "{PROJECT_NAME}.exe"
exit /b 0
"""
    
    batch_path = project_path / "dist" / "启动.bat"
    batch_path.write_text(batch_script, encoding='utf-8')
    print(f"✓ 已创建: 启动.bat")
    
    # 数据目录初始化脚本
    init_script = """@echo off
REM 初始化数据目录
if not exist "data\\database" mkdir data\\database
if not exist "data\\photos" mkdir data\\photos
if not exist "data\\photos\\raw" mkdir data\\photos\\raw
if not exist "data\\photos\\processed" mkdir data\\photos\\processed
if not exist "data\\exports" mkdir data\\exports
echo 数据目录初始化完成
"""
    
    init_path = project_path / "dist" / "初始化.bat"
    init_path.write_text(init_script, encoding='utf-8')
    print(f"✓ 已创建: 初始化.bat")

def create_readme():
    """创建README"""
    print_section("创建使用说明")
    
    readme_content = f"""# {PROJECT_NAME} v{VERSION}

## 快速开始

### 方式1：直接运行（推荐）
双击 "启动.bat" 文件即可启动应用

### 方式2：命令行
在命令行中运行：
```
{PROJECT_NAME}.exe
```

## 系统要求

- Windows 7 及以上
- 8GB RAM 以上
- 显卡支持（NVIDIA显卡性能更好）

## 主要功能

✓ 身份证读取
✓ 摄像头拍照
✓ AI美颜处理
✓ 智能背景替换
✓ 批量处理
✓ 数据管理
✓ 统计分析

## 文件说明

- {PROJECT_NAME}.exe    - 主程序
- 启动.bat             - 启动脚本
- 初始化.bat           - 初始化脚本
- data/                - 数据存储目录
- resources/           - 资源文件

## 注意事项

1. 首次运行时会初始化数据库，请耐心等待
2. 摄像头功能需要系统中有摄像头设备
3. AI处理需要较好的系统性能
4. 数据保存在 data/ 目录中，请定期备份

## 问题排查

问题：无法启动
解决：
1. 确认系统要求满足
2. 尝试右键管理员运行
3. 检查是否被安全软件拦截

问题：摄像头无法使用
解决：
1. 检查系统中是否有摄像头
2. 检查摄像头驱动是否正常
3. 确认应用有摄像头访问权限

## 更新日志

### v1.0.0 (2024-12-31)
- 初始版本发布
- 完整的AI处理功能
- 支持多种证件照规格
- 批量处理和数据管理

## 联系方式

如有问题或建议，请联系技术支持

---
感谢您使用 {PROJECT_NAME}！
"""
    
    readme_path = project_path / "dist" / "README.txt"
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"✓ 已创建: README.txt")

def create_shortcut():
    """创建桌面快捷方式（Windows）"""
    print_section("创建快捷方式")
    
    vbscript = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.SpecialFolders("Desktop") & "\\{PROJECT_NAME}.lnk"
Set oLink = oWS.CreateShortLink(sLinkFile)
oLink.TargetPath = "{project_path}\\dist\\{PROJECT_NAME}.exe"
oLink.WorkingDirectory = "{project_path}\\dist"
oLink.Description = "{PROJECT_NAME} v{VERSION}"
oLink.Save
"""
    
    vbs_path = project_path / "create_shortcut.vbs"
    vbs_path.write_text(vbscript)
    
    try:
        subprocess.run(['cscript', str(vbs_path)], shell=True, capture_output=True)
        print(f"✓ 已在桌面创建快捷方式")
    except Exception as e:
        print(f"⚠ 创建快捷方式失败: {e}")
    finally:
        if vbs_path.exists():
            vbs_path.unlink()

def generate_package_info():
    """生成打包信息文件"""
    print_section("生成打包信息")
    
    info_content = f"""# 打包信息

## 基本信息
- 软件名称: {PROJECT_NAME}
- 版本号: {VERSION}
- 打包时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 打包工具: PyInstaller
- Python版本: {sys.version}

## 文件信息
- 主程序: {PROJECT_NAME}.exe
- 大小: 见dist文件夹
- 构建目录: build/
- 输出目录: dist/

## 依赖信息
- PyQt5: UI框架
- OpenCV: 图像处理
- TensorFlow: 人脸检测
- GFPGAN: AI美颜
- rembg: 背景移除
- SQLAlchemy: 数据库ORM

## 测试清单
□ 在干净系统上测试
□ 测试所有核心功能
□ 测试数据保存
□ 测试错误处理
□ 测试卸载

## 发布检查
□ 文件完整性检查
□ 签名验证
□ 病毒扫描
□ 性能测试
□ 文档完整
"""
    
    info_path = project_path / "PACKAGE_INFO.txt"
    info_path.write_text(info_content, encoding='utf-8')
    print(f"✓ 已创建: PACKAGE_INFO.txt")

def print_summary():
    """打印总结"""
    print_section("打包完成总结")
    
    exe_path = project_path / "dist" / f"{PROJECT_NAME}.exe"
    
    if exe_path.exists():
        exe_size = exe_path.stat().st_size / (1024 * 1024)
        print(f"✓ 打包成功！")
        print(f"\n输出文件:")
        print(f"  路径: {exe_path}")
        print(f"  大小: {exe_size:.2f} MB")
        print(f"\n快速开始:")
        print(f"  1. 打开 dist/ 目录")
        print(f"  2. 双击 启动.bat 运行应用")
        print(f"  3. 或直接双击 {PROJECT_NAME}.exe")
        print(f"\n可选步骤:")
        print(f"  - 复制 dist/ 目录到其他计算机")
        print(f"  - 使用NSIS创建安装程序")
        print(f"  - 创建便携版压缩包")
        return True
    else:
        print(f"✗ 打包失败！未找到输出文件")
        return False

def main():
    """主函数"""
    os.chdir(str(project_path))
    
    print("\n" + "="*60)
    print(f"  {PROJECT_NAME} v{VERSION} - PyInstaller打包工具")
    print("="*60)
    
    # 检查项目文件
    if not check_requirements():
        print("\n✗ 项目文件检查失败，请检查项目结构")
        return False
    
    # 清理旧文件
    clean_build_files()
    
    # 准备参数
    args = create_build_script()
    
    # 执行打包
    if not run_pyinstaller(args):
        print("\n✗ PyInstaller执行失败")
        return False
    
    # 创建启动脚本
    try:
        create_launch_scripts()
        create_readme()
        create_shortcut()
        generate_package_info()
    except Exception as e:
        print(f"⚠ 创建辅助文件时出错: {e}")
    
    # 打印总结
    return print_summary()

if __name__ == '__main__':
    success = main()
    
    print("\n" + "="*60)
    if success:
        print("  ✅ 所有步骤完成！")
    else:
        print("  ❌ 打包过程中出现问题")
    print("="*60 + "\n")
    
    sys.exit(0 if success else 1)
