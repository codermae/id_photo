#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 一键打包脚本 - 生成安装程序
适用于：证件照采集系统
用法：python pack.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# ==================== 配置 ====================
PROJECT_NAME = "证件照采集系统"
VERSION = "1.0.0"
COMPANY = "ID Photo"
PROJECT_DIR = Path(__file__).parent.absolute()

# ==================== 颜色和符号 ====================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

# ==================== 步骤1：生成可执行文件 ====================
def build_exe():
    section("步骤1️⃣：生成可执行文件 (PyInstaller)")
    
    info("检查PyInstaller...")
    try:
        import PyInstaller
        success("PyInstaller已安装")
    except ImportError:
        error("PyInstaller未安装，正在安装...")
        os.system("pip install pyinstaller -q")
        success("PyInstaller安装完成")
    
    # 清理旧文件
    info("清理旧的构建文件...")
    for folder in ['build', 'dist', '__pycache__']:
        folder_path = PROJECT_DIR / folder
        if folder_path.exists():
            shutil.rmtree(folder_path)
    
    # 构建参数
    args = [
        'main.py',
        f'--name={PROJECT_NAME}',
        '--windowed',
        '--onefile',
        '--clean',
        '--noconfirm',
        f'--distpath={PROJECT_DIR / "dist"}',
        f'--workpath={PROJECT_DIR / "build"}',
        f'--specpath={PROJECT_DIR}',
    ]
    
    # 添加隐藏导入
    hidden_imports = [
        'PyQt5.sip',
        'PyQt5.plugins.platforms.qwindows',
        'cv2', 'PIL', 'numpy', 'sqlalchemy', 'pandas', 'openpyxl'
    ]
    for imp in hidden_imports:
        args.append(f'--hidden-import={imp}')
    
    # 排除重型和有问题的库（解决onnxruntime/insightface崩溃）
    for exclude in ['face_recognition', 'dlib', 'rembg', 'gfpgan', 'tensorflow', 'torch', 
                    'onnxruntime', 'insightface', 'tensorrt', 'cuda', 'cudnn', 'numba']:
        args.append(f'--exclude-module={exclude}')
    
    # 添加资源
    for res in ['resources', 'config']:
        res_path = PROJECT_DIR / res
        if res_path.exists():
            args.append(f'--add-data={res_path}:{res}')
    
    info("执行PyInstaller打包 (这需要2-5分钟)...")
    
    try:
        import PyInstaller.__main__
        os.chdir(str(PROJECT_DIR))
        PyInstaller.__main__.run(args)
        
        exe_path = PROJECT_DIR / 'dist' / f'{PROJECT_NAME}.exe'
        if exe_path.exists():
            size = exe_path.stat().st_size / (1024 * 1024)
            success(f"可执行文件生成成功 ({size:.1f}MB)")
            return True
        else:
            error("可执行文件生成失败")
            return False
    except Exception as e:
        error(f"PyInstaller执行出错: {e}")
        return False

# ==================== 步骤2：创建NSIS安装脚本 ====================
def create_nsis_script():
    section("步骤2️⃣：创建NSIS安装脚本")
    
    nsis_content = f'''
; NSIS安装脚本 - {PROJECT_NAME}

!include "MUI2.nsh"

Name "{PROJECT_NAME} v{VERSION}"
OutFile "dist/{PROJECT_NAME}_Setup.exe"
InstallDir "$PROGRAMFILES\\{COMPANY}\\{PROJECT_NAME}"
RequestExecutionLevel admin

VIProductVersion "{VERSION}.0"
VIAddVersionKey "ProductName" "{PROJECT_NAME}"
VIAddVersionKey "CompanyName" "{COMPANY}"

!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimplifiedChinese"

Section "安装"
  SetOutPath "$INSTDIR"
  File "dist\\{PROJECT_NAME}.exe"
  
  CreateDirectory "$SMPROGRAMS\\{PROJECT_NAME}"
  CreateShortcut "$SMPROGRAMS\\{PROJECT_NAME}\\{PROJECT_NAME}.lnk" "$INSTDIR\\{PROJECT_NAME}.exe"
  CreateShortcut "$SMPROGRAMS\\{PROJECT_NAME}\\卸载.lnk" "$INSTDIR\\Uninstall.exe"
  CreateShortcut "$DESKTOP\\{PROJECT_NAME}.lnk" "$INSTDIR\\{PROJECT_NAME}.exe"
  
  CreateDirectory "$APPDATA\\{PROJECT_NAME}\\data"
  
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
  
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{PROJECT_NAME}" "DisplayName" "{PROJECT_NAME} v{VERSION}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{PROJECT_NAME}" "UninstallString" "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\\{PROJECT_NAME}\\*"
  RMDir "$SMPROGRAMS\\{PROJECT_NAME}"
  Delete "$DESKTOP\\{PROJECT_NAME}.lnk"
  Delete "$INSTDIR\\{PROJECT_NAME}.exe"
  Delete "$INSTDIR\\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{PROJECT_NAME}"
SectionEnd

Function .onInstSuccess
  MessageBox MB_YESNO "安装完成！\\n现在运行 {PROJECT_NAME}?" IDNO End
  Exec "$INSTDIR\\{PROJECT_NAME}.exe"
  End:
FunctionEnd
'''
    
    nsis_path = PROJECT_DIR / 'installer.nsi'
    nsis_path.write_text(nsis_content, encoding='utf-8-sig')
    success(f"NSIS脚本已创建: {nsis_path}")
    return nsis_path

# ==================== 步骤3：编译NSIS ====================
def build_nsis_installer():
    section("步骤3️⃣：编译NSIS安装程序")
    
    # 查找NSIS
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]
    
    nsis_exe = None
    for path in nsis_paths:
        if Path(path).exists():
            nsis_exe = path
            break
    
    if not nsis_exe:
        error("未找到NSIS编译器")
        info("请从 https://nsis.sourceforge.io/ 下载安装NSIS")
        info("或者使用便携版可执行文件: dist\\{PROJECT_NAME}.exe")
        return False
    
    info(f"使用NSIS: {nsis_exe}")
    
    try:
        info("编译中 (这需要1-2分钟)...")
        result = subprocess.run(
            [nsis_exe, "installer.nsi"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            installer = PROJECT_DIR / 'dist' / f'{PROJECT_NAME}_Setup.exe'
            if installer.exists():
                size = installer.stat().st_size / (1024 * 1024)
                success(f"安装程序生成成功 ({size:.1f}MB)")
                return True
        
        error("NSIS编译失败")
        return False
        
    except Exception as e:
        error(f"执行NSIS出错: {e}")
        return False

# ==================== 步骤4：生成文档 ====================
def create_docs():
    section("步骤4️⃣：生成用户文档")
    
    # README
    readme = f"""{PROJECT_NAME} v{VERSION}
========================================

【用户安装说明】

1. 下载安装程序：
   {PROJECT_NAME}_Setup.exe

2. 双击运行安装程序

3. 按照安装向导步骤操作

4. 安装完成后会自动创建：
   • 开始菜单快捷方式
   • 桌面快捷方式

5. 点击快捷方式运行应用

【系统要求】
• Windows 7 及以上
• 处理器: Intel i5 或同等
• 内存: 4GB+ (推荐8GB)
• 磁盘: 500MB+ 可用空间

【卸载方法】
1. 打开 控制面板 → 程序和功能
2. 找到 {PROJECT_NAME}
3. 点击卸载

【常见问题】

Q: 需要安装Python吗?
A: 不需要! 程序已包含所有依赖

Q: 数据会保存在哪?
A: 保存在 %APPDATA%\\{PROJECT_NAME}\\data

Q: 如何升级?
A: 下载新版本重新安装即可，数据自动保留

祝使用愉快! 🎉
"""
    
    readme_path = PROJECT_DIR / 'dist' / 'README.txt'
    readme_path.write_text(readme, encoding='utf-8')
    success("用户文档已生成")

# ==================== 主函数 ====================
def main():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║            🚀 {PROJECT_NAME} 一键打包工具                     ║
║                   v{VERSION}                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # 步骤1
    if not build_exe():
        error("打包中断")
        return False
    
    # 步骤2
    create_nsis_script()
    
    # 步骤3
    build_nsis_installer()
    
    # 步骤4
    create_docs()
    
    # 完成
    section("✅ 打包完成!")
    
    print(f"""
【生成的文件】

dist/ 目录中：

  {PROJECT_NAME}.exe
  → 绿色版本 (无需安装，直接使用)

  {PROJECT_NAME}_Setup.exe
  → 安装程序 (推荐发送给用户) ⭐

  README.txt
  → 用户使用说明

【三种使用方式】

1️⃣  只发送安装程序给用户
   发送: {PROJECT_NAME}_Setup.exe
   用户: 双击安装即可

2️⃣  发送便携版本
   发送: {PROJECT_NAME}.exe
   用户: 直接运行，无需安装

3️⃣  发送整个dist文件夹
   发送: dist/ (压缩)
   用户: 解压后选择安装或直接运行

【推荐方案】
   发送 {PROJECT_NAME}_Setup.exe 给用户
   用户体验最佳，最专业

【下一步】

1. 测试安装程序:
   dist\\{PROJECT_NAME}_Setup.exe

2. 分发给用户:
   dist\\{PROJECT_NAME}_Setup.exe

3. 或使用便携版:
   dist\\{PROJECT_NAME}.exe

祝发布顺利! 🎉
""")
    
    return True

if __name__ == '__main__':
    success_flag = main()
    sys.exit(0 if success_flag else 1)
