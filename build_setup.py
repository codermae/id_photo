#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 InnoSetup 生成专业安装程序
"""

import subprocess
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.absolute()

# 查找 InnoSetup 编译器
inno_paths = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    r"C:\Program Files\Inno Setup 5\ISCC.exe",
]

inno_exe = None
for path in inno_paths:
    if os.path.exists(path):
        inno_exe = path
        break

if not inno_exe:
    print("[!] InnoSetup not found!")
    print("[*] Please install from: https://jrsoftware.org/isdl.php")
    print("\n[*] Or use NSIS instead:")
    print("[*]   https://nsis.sourceforge.io/")
    sys.exit(1)

print(f"[+] Found InnoSetup: {inno_exe}")
print("[*] Generating installer (1-2 minutes)...\n")

# 执行编译
iss_file = PROJECT_DIR / "create_installer.iss"
os.chdir(str(PROJECT_DIR))

try:
    result = subprocess.run(
        [inno_exe, "/O", "dist", str(iss_file)],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode == 0:
        setup_exe = PROJECT_DIR / "dist" / "证件照采集系统_Setup_v1.0.0.exe"
        if setup_exe.exists():
            size = setup_exe.stat().st_size / (1024 * 1024)
            print(f"\n[+] Success!")
            print(f"[+] Installer: dist\\证件照采集系统_Setup_v1.0.0.exe")
            print(f"[+] Size: {size:.1f}MB")
            print(f"\n[+] Ready to distribute!")
        else:
            print("[!] Installer not found")
    else:
        print(f"[!] Error: {result.stderr}")
        
except Exception as e:
    print(f"[!] Error: {e}")
    sys.exit(1)
