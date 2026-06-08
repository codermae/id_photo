[Setup]
AppName=证件照采集系统
AppVersion=1.0.0
AppPublisher=ID Photo
AppPublisherURL=https://example.com
AppSupportURL=https://example.com
AppUpdatesURL=https://example.com
DefaultDirName={pf}\证件照采集系统
DefaultGroupName=证件照采集系统
AllowNoIcons=yes
LicenseFile=LICENSE.txt
SourceDir=.
OutputDir=dist
OutputBaseFilename=证件照采集系统_Setup_v1.0.0
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
ShowLanguageDialog=no

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\证件照采集系统.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\证件照采集系统"; Filename: "{app}\证件照采集系统.exe"
Name: "{group}\{cm:UninstallProgram,证件照采集系统}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\证件照采集系统"; Filename: "{app}\证件照采集系统.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\证件照采集系统.exe"; Description: "{cm:LaunchProgram,证件照采集系统}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: dirifempty; Name: "{app}"
