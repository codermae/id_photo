#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成 NSIS 安装程序
"""

import subprocess
import os
from pathlib import Path

PROJECT_NAME = "证件照采集系统"
VERSION = "1.0.0"
PROJECT_DIR = Path(__file__).parent.absolute()

# 创建 NSIS 脚本
nsis_script = f'''Unicode true

!include "MUI2.nsh"

Name "{PROJECT_NAME} v{VERSION}"
OutFile "{str(PROJECT_DIR)}\\dist\\{PROJECT_NAME}_Setup_v{VERSION}.exe"
InstallDir "$PROGRAMFILES\\{PROJECT_NAME}"
RequestExecutionLevel admin

VIProductVersion "{VERSION}.0"
VIAddVersionKey "ProductName" "{PROJECT_NAME}"
VIAddVersionKey "FileVersion" "{VERSION}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File "{str(PROJECT_DIR)}\\dist\\{PROJECT_NAME}.exe"
  
  CreateDirectory "$SMPROGRAMS\\{PROJECT_NAME}"
  CreateShortcut "$SMPROGRAMS\\{PROJECT_NAME}\\{PROJECT_NAME}.lnk" "$INSTDIR\\{PROJECT_NAME}.exe"
  CreateShortcut "$SMPROGRAMS\\{PROJECT_NAME}\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
  CreateShortcut "$DESKTOP\\{PROJECT_NAME}.lnk" "$INSTDIR\\{PROJECT_NAME}.exe"
  
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
  MessageBox MB_YESNO "{PROJECT_NAME} installed. Run it now?" IDNO End
  Exec "$INSTDIR\\{PROJECT_NAME}.exe"
  End:
FunctionEnd
'''

nsis_path = PROJECT_DIR / "installer.nsi"
nsis_path.write_text(nsis_script, encoding='utf-8-sig')

print("[+] NSIS script created: installer.nsi")

# 查找 makensis
nsis_exe = None
for path in [r"D:\Program Files (x86)\NSIS\makensis.exe", r"D:\Program Files\NSIS\makensis.exe"]:
    if os.path.exists(path):
        nsis_exe = path
        break

if not nsis_exe:
    print("\n[!] NSIS not found!")
    print("[*] Please install NSIS from: https://nsis.sourceforge.io/")
    exit(1)

print(f"[+] Found NSIS: {nsis_exe}")
print("[*] Generating installer (1-2 minutes)...\n")

os.chdir(str(PROJECT_DIR))
result = subprocess.run([nsis_exe, "installer.nsi"], capture_output=True, text=True)

if result.returncode == 0:
    installer = PROJECT_DIR / "dist" / f"{PROJECT_NAME}_Setup_v{VERSION}.exe"
    if installer.exists():
        size = installer.stat().st_size / (1024 * 1024)
        print(f"\n[+] Success!")
        print(f"[+] Installer created: dist\\{PROJECT_NAME}_Setup_v{VERSION}.exe")
        print(f"[+] Size: {size:.1f}MB")
        print(f"\n[*] Ready to distribute!")
    else:
        print("[!] Installer file not found after build")
else:
    print("[!] NSIS error:")
    print(result.stderr)