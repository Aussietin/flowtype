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
LicenseFile=EULA.txt
UninstallDisplayIcon={app}\{#AppExeName}
; Version resource on flowtype-setup.exe itself (Properties -> Details) - an
; installer with blank metadata looks like a dropper to AV heuristics.
AppCopyright=Copyright (c) 2026 {#AppPublisher}
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} installer
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
VersionInfoCopyright=Copyright (c) 2026 {#AppPublisher}
; flowtype.py holds this mutex while running. Setup and the uninstaller check
; it and ask the user to quit flowtype first, so the uninstall can't leave a
; locked flowtype.exe (and a live keyboard hook) behind.
AppMutex=Global\flowtype_singleton
; Code signing (not bought yet - see docs/TRUST-AUDIT.md). Once there's a cert,
; define a sign tool named "signtool" (Inno IDE: Tools -> Configure Sign Tools,
; or iscc "/Ssigntool=signtool.exe sign /fd sha256 /tr http://timestamp.digicert.com /td sha256 /a $f")
; and uncomment both lines so setup.exe AND the uninstaller are signed.
;SignTool=signtool
;SignedUninstaller=yes
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "startup"; Description: "Start flowtype automatically when I sign in"; GroupDescription: "Startup:"

[Files]
Source: "build\dist\flowtype\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "EULA.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD-PARTY-NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Start flowtype now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Everything flowtype writes lives here: config.json (hotkeys, glossary) and
; logs\transcripts.jsonl (plain-text history). Remove all of it so an uninstall
; leaves no dictated text behind.
Type: filesandordirs; Name: "{userappdata}\flowtype"
