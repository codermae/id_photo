#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整版打包 - 包含所有人脸检测库
"""

import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

PROJECT_NAME = "证件照采集系统"
PROJECT_DIR = Path(__file__).parent.absolute()

os.chdir(str(PROJECT_DIR))

# 清理
print("Cleaning old builds...")
for folder in ['build', 'dist', '__pycache__']:
    path = PROJECT_DIR / folder
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)

print("Running PyInstaller (this will take 5-10 minutes)...\n")

# 打包参数 - 包含所有库！
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

# 隐藏导入 - 包含人脸检测库
hidden_imports = [
    'PyQt5.sip',
    'PyQt5.plugins.platforms.qwindows',
    'cv2',
    'PIL',
    'numpy',
    'sqlalchemy',
    'pandas',
    'openpyxl',
    'face_recognition',  # 包含人脸识别
    'dlib',              # 包含 dlib
    'rembg',             # 背景移除
]

for imp in hidden_imports:
    args.append('--hidden-import=' + imp)

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
        print(f"\n[+] Packaging successful!")
        print(f"[+] Output: {exe_path}")
        print(f"[+] Size: {size:.1f}MB")
        print(f"\n[+] All features included (including face detection)!")
    else:
        print("\n[!] Packaging failed")
except Exception as e:
    print(f"\n[!] Error: {e}")
