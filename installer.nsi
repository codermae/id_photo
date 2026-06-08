Unicode true

!include "MUI2.nsh"

Name "证件照采集系统 v1.0.0"
OutFile "D:\1BYSJ\id_photo_system\dist\证件照采集系统_Setup_v1.0.0.exe"
InstallDir "$PROGRAMFILES\证件照采集系统"
RequestExecutionLevel admin

VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "证件照采集系统"
VIAddVersionKey "FileVersion" "1.0.0"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File "D:\1BYSJ\id_photo_system\dist\证件照采集系统.exe"
  
  CreateDirectory "$SMPROGRAMS\证件照采集系统"
  CreateShortcut "$SMPROGRAMS\证件照采集系统\证件照采集系统.lnk" "$INSTDIR\证件照采集系统.exe"
  CreateShortcut "$SMPROGRAMS\证件照采集系统\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\证件照采集系统.lnk" "$INSTDIR\证件照采集系统.exe"
  
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\证件照采集系统" "DisplayName" "证件照采集系统 v1.0.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\证件照采集系统" "UninstallString" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\证件照采集系统\*"
  RMDir "$SMPROGRAMS\证件照采集系统"
  Delete "$DESKTOP\证件照采集系统.lnk"
  Delete "$INSTDIR\证件照采集系统.exe"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\证件照采集系统"
SectionEnd

Function .onInstSuccess
  MessageBox MB_YESNO "证件照采集系统 installed. Run it now?" IDNO End
  Exec "$INSTDIR\证件照采集系统.exe"
  End:
FunctionEnd
