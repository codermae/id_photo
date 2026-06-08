#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终打包脚本 - 修复了所有参数问题
"""

import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

# 修复 Windows 编码
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

PROJECT_NAME = "证件照采集系统"
PROJECT_DIR = Path(__file__).parent.absolute()

os.chdir(str(PROJECT_DIR))

# 清理
for folder in ['build', 'dist', '__pycache__']:
    path = PROJECT_DIR / folder
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
        print("[+] Cleaned %s/" % folder)

print("\nRunning PyInstaller (2-5 minutes)...\n")

print("\n执行 PyInstaller 打包 (这需要2-5分钟)...\n")

# 打包参数（全部修正）
args = [
    str(PROJECT_DIR / 'main.py'),
    '--name=' + PROJECT_NAME,
    '--windowed',
    '--onefile',
    '--clean',
    '--noconfirm',
    '--distpath=' + str(PROJECT_DIR / 'dist'),
    '--workpath=' + str(PROJECT_DIR / 'build'),
    '--specpath=' + str(PROJECT_DIR),
]

# 隐藏导入
for imp in ['PyQt5.sip', 'PyQt5.plugins.platforms.qwindows', 'cv2', 'PIL', 'numpy', 'sqlalchemy']:
    args.append('--hidden-import=' + imp)

# 排除问题库
for exc in ['face_recognition', 'dlib', 'rembg', 'gfpgan', 'tensorflow', 'torch', 
            'onnxruntime', 'insightface', 'tensorrt']:
    args.append('--exclude-module=' + exc)

# 添加资源
for res in ['resources', 'config']:
    res_path = PROJECT_DIR / res
    if res_path.exists():
        args.append('--add-data=' + str(res_path) + ':' + res)

# 执行打包
try:
    PyInstaller.__main__.run(args)
    
    exe_path = PROJECT_DIR / 'dist' / (PROJECT_NAME + '.exe')
    if exe_path.exists():
        size = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✓ 打包成功！")
        print(f"  输出: {exe_path}")
        print(f"  大小: {size:.1f}MB")
        print(f"\n可执行文件已生成！")
        print(f"路径: dist/{PROJECT_NAME}.exe")
    else:
        print("\n✗ 打包失败：未生成可执行文件")
except Exception as e:
    print(f"\n✗ 打包出错: {e}")
