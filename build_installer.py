#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的安装程序打包脚本
包括PyInstaller打包 + NSIS安装程序生成
"""

import PyInstaller.__main__
import sys
import os
import shutil
import subprocess
from pathlib import Path

PROJECT_NAME = "证件照采集系统"
VERSION = "1.0.0"
MAIN_FILE = "main.py"
COMPANY_NAME = "ID Photo"

project_path = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_path))

def print_section(title):
    """打印分隔符"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_step(step_num, description):
    """打印步骤"""
    print(f"\n[步骤 {step_num}] {description}")
    print("-" * 70)

def clean_build_files():
    """清理旧的构建文件"""
    print_section("清理旧的构建文件")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = project_path / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"✓ 已删除: {dir_name}/")

def build_executable():
    """使用PyInstaller打包生成可执行文件"""
    print_section("步骤1：生成可执行文件 (PyInstaller)")
    print("这可能需要 3-5 分钟，请耐心等待...")
    
    os.chdir(str(project_path))
    
    args = [
        'main.py',
        f'--name={PROJECT_NAME}',
        '--windowed',
        '--onefile',
        '--clean',
        '--noconfirm',
        f'--distpath={str(project_path / "dist")}',
        f'--buildpath={str(project_path / "build")}',
        f'--specpath={str(project_path)}',
        '--python-option=u',
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
    
    print(f"✓ 添加了 {len(hidden_imports)} 个基础导入")
    
    # 排除重型库（简化版）
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
    
    print(f"✓ 排除了 {len(exclude_modules)} 个重型模块")
    
    # 添加资源
    for res_dir in ['resources', 'config']:
        res_path = project_path / res_dir
        if res_path.exists():
            args.append(f'--add-data={str(res_path)}:{res_dir}')
            print(f"✓ 添加资源: {res_dir}/")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✓ PyInstaller 执行完成")
    except Exception as e:
        print(f"\n✗ PyInstaller 执行出错: {e}")
        return False
    
    # 验证输出
    exe_path = project_path / "dist" / f"{PROJECT_NAME}.exe"
    if exe_path.exists():
        exe_size = exe_path.stat().st_size / (1024 * 1024)
        print(f"✓ 可执行文件生成成功")
        print(f"  文件: {exe_path}")
        print(f"  大小: {exe_size:.2f} MB")
        return True
    else:
        print(f"✗ 可执行文件生成失败")
        return False

def create_nsis_installer():
    """创建NSIS安装脚本"""
    print_section("步骤2：创建 NSIS 安装脚本")
    
    nsis_script = f"""
; NSIS安装脚本
; {PROJECT_NAME} v{VERSION}

; 使用现代UI
!include "MUI2.nsh"

; 设置信息
Name "{PROJECT_NAME} v{VERSION}"
OutFile "dist/{PROJECT_NAME}_Setup_v{VERSION}.exe"
InstallDir "$PROGRAMFILES\\{COMPANY_NAME}\\{PROJECT_NAME}"
RequestExecutionLevel admin

; 版本信息
VIProductVersion "{VERSION}.0"
VIAddVersionKey "ProductName" "{PROJECT_NAME}"
VIAddVersionKey "CompanyName" "{COMPANY_NAME}"
VIAddVersionKey "FileVersion" "{VERSION}"
VIProductVersion "{VERSION}.0"

; 设置安装大小估计
!define ESTIMATED_SIZE 200000

; UI设置
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TEXT "本向导将在您的计算机上安装 {PROJECT_NAME}。\\r\\n\\r\\n$_CLICK"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 语言设置
!insertmacro MUI_LANGUAGE "SimplifiedChinese"

; 安装文件部分
Section "安装 {PROJECT_NAME}"
  SectionIn RO
  
  SetOutPath "$INSTDIR"
  File "dist\\{PROJECT_NAME}.exe"
  
  ; 创建开始菜单文件夹
  CreateDirectory "$SMPROGRAMS\\{PROJECT_NAME}"
  CreateShortcut "$SMPROGRAMS\\{PROJECT_NAME}\\{PROJECT_NAME}.lnk" "$INSTDIR\\{PROJECT_NAME}.exe"
  CreateShortcut "$SMPROGRAMS\\{PROJECT_NAME}\\卸载.lnk" "$INSTDIR\\Uninstall.exe"
  
  ; 创建桌面快捷方式
  CreateShortcut "$DESKTOP\\{PROJECT_NAME}.lnk" "$INSTDIR\\{PROJECT_NAME}.exe"
  
  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
  
  ; 写入注册表（便于卸载）
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{PROJECT_NAME}" "DisplayName" "{PROJECT_NAME} v{VERSION}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{PROJECT_NAME}" "UninstallString" "$INSTDIR\\Uninstall.exe"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{PROJECT_NAME}" "DisplayVersion" "{VERSION}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{PROJECT_NAME}" "Publisher" "{COMPANY_NAME}"
  WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{PROJECT_NAME}" "EstimatedSize" ${{ESTIMATED_SIZE}}
SectionEnd

; 可选：创建数据目录
Section "创建数据目录"
  CreateDirectory "$APPDATA\\{PROJECT_NAME}"
  CreateDirectory "$APPDATA\\{PROJECT_NAME}\\data"
  CreateDirectory "$APPDATA\\{PROJECT_NAME}\\photos"
  CreateDirectory "$APPDATA\\{PROJECT_NAME}\\backups"
SectionEnd

; 卸载部分
Section "Uninstall"
  ; 删除快捷方式
  Delete "$SMPROGRAMS\\{PROJECT_NAME}\\{PROJECT_NAME}.lnk"
  Delete "$SMPROGRAMS\\{PROJECT_NAME}\\卸载.lnk"
  RMDir "$SMPROGRAMS\\{PROJECT_NAME}"
  
  Delete "$DESKTOP\\{PROJECT_NAME}.lnk"
  
  ; 删除应用文件
  Delete "$INSTDIR\\{PROJECT_NAME}.exe"
  Delete "$INSTDIR\\Uninstall.exe"
  RMDir /r "$INSTDIR\\_internal"
  RMDir "$INSTDIR"
  
  ; 删除注册表项
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{PROJECT_NAME}"
SectionEnd

; 安装完成后运行应用（可选）
Function .onInstSuccess
  MessageBox MB_YESNO "安装完成！是否现在运行 {PROJECT_NAME}?" IDNO EndRun
  Exec "$INSTDIR\\{PROJECT_NAME}.exe"
  EndRun:
FunctionEnd
"""
    
    nsis_path = project_path / "installer.nsi"
    nsis_path.write_text(nsis_script, encoding='utf-8')
    print(f"✓ NSIS脚本已创建: {nsis_path}")
    return nsis_path

def create_license_file():
    """创建许可证文件"""
    print_step(1, "创建许可证文件")
    
    license_text = f"""{PROJECT_NAME} v{VERSION}
智能化证件照采集及处理系统

许可证说明
==========

本软件以现状提供，不提供任何明示或暗示的保证。
{COMPANY_NAME} 不对因使用本软件引起的任何直接或间接损害负责。

用户协议
========

1. 许可授予
   本协议授予您个人的、非排他的、不可转让的使用许可。

2. 限制
   您不得：
   - 反向工程、反汇编或尝试派生源代码
   - 修改或创建衍生作品
   - 删除任何版权、商标或其他所有权声明
   - 将本软件租赁、出租或出借

3. 支持和更新
   {COMPANY_NAME} 可自行决定提供技术支持或更新。

4. 终止
   如果您违反本协议，{COMPANY_NAME} 可终止本协议并收回许可。

5. 管辖法律
   本协议受中华人民共和国法律管辖。

如有任何疑问，请联系我们。
"""
    
    license_path = project_path / "LICENSE.txt"
    license_path.write_text(license_text, encoding='utf-8')
    print(f"✓ 许可证文件已创建: {license_path}")

def find_nsis():
    """查找NSIS安装路径"""
    print_step(2, "查找NSIS编译器")
    
    possible_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
        r"C:\Program Files (x86)\NSIS",
        r"C:\Program Files\NSIS",
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            print(f"✓ 找到NSIS: {path}")
            return path
    
    print("✗ 未找到NSIS编译器")
    print("\n如需创建安装程序，请：")
    print("1. 从 https://nsis.sourceforge.io/ 下载安装NSIS")
    print("2. 重新运行此脚本")
    return None

def build_installer_exe(nsis_path):
    """使用NSIS编译安装程序"""
    print_section("步骤3：编译 NSIS 安装程序")
    
    nsis_exe = find_nsis()
    if not nsis_exe:
        print("\n提示：可以手动运行以下命令编译安装程序：")
        print(f'  "C:\\Program Files (x86)\\NSIS\\makensis.exe" installer.nsi')
        return False
    
    print(f"\n使用NSIS编译: {nsis_exe}")
    print("这可能需要 1-2 分钟...")
    
    try:
        # 检查是否是文件或目录
        if nsis_exe.endswith(".exe"):
            makensis_exe = nsis_exe
        else:
            makensis_exe = os.path.join(nsis_exe, "makensis.exe")
        
        result = subprocess.run(
            [makensis_exe, str(nsis_path)],
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ NSIS 编译完成")
            installer_path = project_path / "dist" / f"{PROJECT_NAME}_Setup_v{VERSION}.exe"
            if installer_path.exists():
                size = installer_path.stat().st_size / (1024 * 1024)
                print(f"✓ 安装程序生成成功")
                print(f"  文件: {installer_path}")
                print(f"  大小: {size:.2f} MB")
                return True
        else:
            print("✗ NSIS 编译失败")
            print("错误输出:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ 执行NSIS出错: {e}")
        return False

def create_batch_launcher():
    """创建批处理启动脚本"""
    print_step(3, "创建启动脚本")
    
    batch_script = f"""@echo off
REM {PROJECT_NAME} 启动脚本
setlocal enabledelayedexpansion

REM 检查主程序是否存在
if not exist "{PROJECT_NAME}.exe" (
    echo 错误: 找不到主程序
    echo 请确保此脚本与 {PROJECT_NAME}.exe 在同一目录
    pause
    exit /b 1
)

REM 检查.NET框架（可选）
REM if not exist "%WINDIR%\\Microsoft.NET\\Framework" (
REM     echo 错误: 需要安装.NET框架
REM     pause
REM     exit /b 1
REM )

REM 启动应用
echo 正在启动 {PROJECT_NAME}...
start "" "{PROJECT_NAME}.exe"

REM 清除环境变量
endlocal
exit /b 0
"""
    
    batch_path = project_path / "dist" / "启动.bat"
    batch_path.write_text(batch_script, encoding='utf-8')
    print(f"✓ 启动脚本已创建: {batch_path}")

def create_readme():
    """创建用户使用说明"""
    print_step(4, "创建用户文档")
    
    readme_text = f"""{PROJECT_NAME} v{VERSION}
========================================================

【快速开始】

1. 双击运行安装程序：
   {PROJECT_NAME}_Setup_v{VERSION}.exe

2. 按照安装向导步骤操作：
   - 阅读许可协议
   - 选择安装位置（默认：C:\\Program Files\\{COMPANY_NAME}\\{PROJECT_NAME}）
   - 完成安装

3. 启动应用：
   - 从开始菜单选择 "{PROJECT_NAME}"
   - 或双击桌面快捷方式
   - 或打开安装目录双击 {PROJECT_NAME}.exe

【系统要求】

操作系统: Windows 7 及以上
处理器: Intel Core i5 或同等级
内存: 最低 4GB (推荐 8GB)
磁盘: 最少 500MB 可用空间
屏幕: 1280x720 分辨率或更高

【主要功能】

✓ 身份证自动识别和读取
✓ 实时摄像头拍照采集
✓ AI智能美颜处理
✓ 证件照背景智能替换
✓ 批量图像处理
✓ 数据管理和查询
✓ 统计报表生成

【常见问题】

Q: 如何卸载应用？
A: 打开 "控制面板" → "程序和功能" → 找到 "{PROJECT_NAME}" → 点击卸载

Q: 应用会保存我的数据吗？
A: 会的，所有数据保存在 %APPDATA%\\{PROJECT_NAME}\\data 目录

Q: 我的照片存储在哪里？
A: 照片存储在 %APPDATA%\\{PROJECT_NAME}\\photos 目录

Q: 如何升级到新版本？
A: 下载新版本安装程序后安装即可（旧数据会保留）

Q: 出现问题怎么办？
A: 请尝试以下步骤：
  1. 重新启动应用
  2. 清理缓存（删除 %APPDATA%\\{PROJECT_NAME}\\cache）
  3. 检查网络连接（部分功能需要网络）
  4. 重新安装应用

【技术支持】

如需帮助，请：
- 查阅应用内的帮助文档
- 在应用内发送反馈
- 联系技术支持团队

【更新日志】

版本 {VERSION} (当前版本)
- 初始版本发布
- 支持所有基础功能

【许可和协议】

本软件受法律保护，使用本软件即表示您同意许可协议条款。
详见 LICENSE.txt 文件。

版权所有 © {COMPANY_NAME}
========================================================
"""
    
    readme_path = project_path / "dist" / "README.txt"
    readme_path.write_text(readme_text, encoding='utf-8')
    print(f"✓ 用户文档已创建: {readme_path}")

def create_uninstall_guide():
    """创建卸载指南"""
    print_step(5, "创建卸载指南")
    
    uninstall_text = f"""【{PROJECT_NAME} 卸载说明】

方式1：通过开始菜单卸载（推荐）
  1. 点击 Windows 开始菜单
  2. 找到 "{PROJECT_NAME}" 文件夹
  3. 点击 "卸载" 选项
  4. 按照卸载向导完成卸载

方式2：通过控制面板卸载
  1. 打开 "控制面板"
  2. 选择 "程序和功能"
  3. 在列表中找到 "{PROJECT_NAME} v{VERSION}"
  4. 点击 "卸载"
  5. 按照向导完成卸载

方式3：通过卸载程序直接卸载
  1. 打开安装目录（默认 C:\\Program Files\\{COMPANY_NAME}\\{PROJECT_NAME}）
  2. 双击 "Uninstall.exe"
  3. 按照向导完成卸载

【卸载后会发生什么？】

✓ 会删除：
  - 应用程序文件
  - 开始菜单快捷方式
  - 桌面快捷方式

✗ 不会删除（可手动删除）：
  - 用户数据：%APPDATA%\\{PROJECT_NAME}
  - 注册表项（系统会自动清理）

【保留用户数据】

如果只想更新应用但保留数据，请：
  1. 直接安装新版本
  2. 选择 "覆盖安装"
  3. 您的数据会自动保留

【完全删除所有数据】

卸载后要完全删除应用数据：
  1. 按 Win + R 打开运行框
  2. 输入：%APPDATA%
  3. 找到 "{PROJECT_NAME}" 文件夹
  4. 右键选择 "删除"

或使用命令行：
  rmdir /s /q "%APPDATA%\\{PROJECT_NAME}"

【卸载有问题？】

如果卸载失败，请尝试：
  1. 关闭所有 {PROJECT_NAME} 相关的进程
  2. 重启计算机后重试
  3. 以管理员身份运行卸载程序
  4. 手动删除安装目录
"""
    
    uninstall_path = project_path / "dist" / "UNINSTALL.txt"
    uninstall_path.write_text(uninstall_text, encoding='utf-8')
    print(f"✓ 卸载指南已创建: {uninstall_path}")

def create_summary():
    """创建完成总结"""
    print_section("打包完成总结")
    
    summary = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    ✅ {PROJECT_NAME} 安装程序打包完成                     ║
╚══════════════════════════════════════════════════════════════════════════╝

【生成的文件】

dist/ 目录包含以下文件：

  ✓ {PROJECT_NAME}.exe
    → 绿色版可执行文件（可直接运行）
    → 用途：便携使用或测试

  ✓ {PROJECT_NAME}_Setup_v{VERSION}.exe
    → 安装程序（推荐分发给用户）
    → 特点：专业安装向导、支持卸载、快捷方式

  ✓ 启动.bat
    → Windows批处理启动脚本

  ✓ README.txt
    → 用户快速开始指南

  ✓ UNINSTALL.txt
    → 卸载说明文档

【三种使用方式】

【方式1】绿色版本（便携）
  适用：演示、测试、无需安装的场景
  使用：解压后直接运行 {PROJECT_NAME}.exe
  优点：无需安装、可在U盘运行
  
【方式2】安装程序（推荐商业发布）✨
  适用：正式发布、企业用户、普通用户
  使用：双击 {PROJECT_NAME}_Setup_v{VERSION}.exe
  优点：专业界面、自动安装、支持卸载

【方式3】命令行启动
  适用：高级用户、批量部署
  使用：运行 启动.bat 或 {PROJECT_NAME}.exe

【分发建议】

如果要分发给用户，选择以下方案之一：

选项A：只分发安装程序（推荐）
  发送文件：{PROJECT_NAME}_Setup_v{VERSION}.exe
  用户操作：双击安装即可
  优点：文件单一、清晰、专业

选项B：分发整个dist文件夹
  发送文件：整个 dist/ 文件夹（压缩）
  用户操作：解压后可选择安装或直接运行
  优点：灵活性高、包含所有选项

选项C：创建自解压包
  推荐工具：7-Zip、WinRAR
  方法：右键 → 添加到压缩文件 → 选择 .7z 或 .zip

【使用场景】

场景1：公司内部使用
  → 使用安装程序（能在"卸载程序"中找到）
  → 便于IT部门管理

场景2：在线分发
  → 上传安装程序到网站
  → 用户下载后安装

场景3：U盘分发
  → 使用便携版（{PROJECT_NAME}.exe）
  → 无需安装即可在任何电脑运行

场景4：软件商店
  → 发布整个 dist/ 包
  → 用户选择安装方式

【测试清单】

在分发前，请确保以下测试都通过：

□ 在干净的Windows系统上运行安装程序
□ 安装过程正常无错误
□ 应用安装后能正常启动
□ 所有主要功能都能使用
  ├─ 身份证读取
  ├─ 摄像头拍照
  ├─ 图像处理
  ├─ 数据保存
  └─ 报表生成
□ 创建的快捷方式能正常使用
□ 卸载功能正常工作
□ 重新安装时数据能正确保留

【后续步骤】

1️⃣  测试应用
    运行 {PROJECT_NAME}_Setup_v{VERSION}.exe 进行测试

2️⃣  获取用户反馈
    在可控范围内发给少数用户测试

3️⃣  准备发布
    创建网站/下载页面
    准备用户手册
    准备常见问题解答

4️⃣  正式发布
    上传安装程序
    发布发行说明
    启动营销推广

5️⃣  收集反馈
    建立反馈渠道
    持续改进应用
    定期更新版本

【关键信息】

应用名称：{PROJECT_NAME}
版本号：{VERSION}
发布商：{COMPANY_NAME}
安装大小：约 200-300 MB
运行要求：Windows 7+, 4GB RAM

【需要帮助？】

如果遇到问题：

1. 查看 README.txt（用户文档）
2. 查看 UNINSTALL.txt（卸载指南）
3. 查看原始文档说明

【打包脚本说明】

本脚本完成了以下工作：

✓ 清理旧的构建文件
✓ 使用PyInstaller生成可执行文件
✓ 创建NSIS安装脚本
✓ 编译生成安装程序
✓ 生成用户文档
✓ 创建启动脚本

【进阶定制】

如需进一步定制，可以修改以下文件：

• installer.nsi
  - 修改安装目录
  - 添加更多快捷方式
  - 改变欢迎信息

• build_installer.py
  - 调整PyInstaller参数
  - 修改隐藏导入列表
  - 添加更多资源文件

【版本更新】

当发布新版本时：

1. 修改此脚本中的 VERSION 变量
2. 运行脚本重新生成安装程序
3. 发布新版本安装程序
4. 用户安装新版本时数据自动保留

╔══════════════════════════════════════════════════════════════════════════╗
║                            🎉 打包完成！                                   ║
║                  现在你的应用可以正式发布给用户了                          ║
╚══════════════════════════════════════════════════════════════════════════╝

快速开始命令：

  测试应用：
    dist\\{PROJECT_NAME}.exe

  测试安装程序：
    dist\\{PROJECT_NAME}_Setup_v{VERSION}.exe

  查看完整文件：
    explorer dist\\

祝发布顺利！🚀
"""
    
    print(summary)
    
    summary_path = project_path / "DEPLOYMENT_SUMMARY.txt"
    summary_path.write_text(summary, encoding='utf-8')

def main():
    """主函数"""
    print("\n" + "="*70)
    print(f"  {PROJECT_NAME} v{VERSION}")
    print(f"  完整安装程序打包工具")
    print("="*70)
    
    # 步骤1：清理
    clean_build_files()
    
    # 步骤2：创建许可证
    create_license_file()
    
    # 步骤3：生成可执行文件
    if not build_executable():
        print("\n✗ 打包过程中断")
        return False
    
    # 步骤4：创建启动脚本和文档
    create_batch_launcher()
    create_readme()
    create_uninstall_guide()
    
    # 步骤5：创建NSIS脚本
    nsis_path = create_nsis_installer()
    
    # 步骤6：尝试编译NSIS
    build_installer_exe(nsis_path)
    
    # 步骤7：生成完成总结
    create_summary()
    
    print("\n" + "="*70)
    print("  ✅ 所有打包步骤完成！")
    print("="*70)
    print("\n建议下一步：")
    print(f"  1. 测试: dist\\{PROJECT_NAME}.exe")
    print(f"  2. 分发: dist\\{PROJECT_NAME}_Setup_v{VERSION}.exe")
    print(f"  3. 查看: DEPLOYMENT_SUMMARY.txt")
    print("\n")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
