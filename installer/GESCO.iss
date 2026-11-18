#define MyAppName "GESCO"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "GESCO"

[Setup]
AppId={{A9E9B4D2-7F6B-4B35-9C12-6A7C1E0D9F31}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\GESCO
DefaultGroupName=GESCO
OutputDir=..\dist
OutputBaseFilename=Setup-GESCO
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
PrivilegesRequired=admin
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\GESCO.exe

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis supplémentaires :"; Flags: unchecked

[Files]
Source: "..\dist\GESCO\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "prerequisites\VC_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\GESCO"; Filename: "{app}\GESCO.exe"
Name: "{autodesktop}\GESCO"; Filename: "{app}\GESCO.exe"; Tasks: desktopicon

[Run]
Filename: "{tmp}\VC_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installation des composants Microsoft Visual C++..."; Flags: waituntilterminated; Check: not IsVCRedistInstalled
Filename: "{app}\GESCO.exe"; Description: "Lancer GESCO"; Flags: postinstall nowait skipifsilent

[Code]
function IsVCRedistInstalled: Boolean;
var
  Installed: Cardinal;
begin
  Result := RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) and (Installed = 1);
end;
