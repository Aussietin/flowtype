; Inno Setup script for flowtype — per-user install, no admin prompt.
; Build:  iscc installer.iss   (after pyinstaller flowtype.spec)
; Needs Inno Setup 6:  winget install JRSoftware.InnoSetup

#define AppName "flowtype"
#define AppVersion "1.0.0"
#define AppPublisher "Austin Crozier"
#define AppExeName "flowtype.exe"

[Setup]
AppId={{7F3A9C2E-4B1D-4E8A-9C6F-FL0WTYPE0001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer-output
OutputBaseFilename=flowtype-setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "startup"; Description: "Start flowtype automatically when I sign in"; GroupDescription: "Startup:"

[Files]
Source: "build\dist\flowtype\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Start flowtype now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\flowtype\logs"
