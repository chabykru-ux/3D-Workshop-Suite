[Setup]
AppId={{A725AB03-AD1C-45BB-9D1C-96ED43DFFB23}
AppName=DrawingMaker 3D
AppVersion=0.6.0
AppVerName=DrawingMaker 3D 0.6.0
DefaultDirName={localappdata}\Programs\DrawingMaker3D
DefaultGroupName=DrawingMaker 3D
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=dist
OutputBaseFilename=DrawingMaker3D-Setup-0.6.0-x64
SetupIconFile=DrawingMaker3D.ico
UninstallDisplayIcon={app}\DrawingMaker3D.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
VersionInfoVersion=0.6.0.0
CloseApplications=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\DrawingMaker3D\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DrawingMaker 3D"; Filename: "{app}\DrawingMaker3D.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\DrawingMaker 3D"; Filename: "{app}\DrawingMaker3D.exe"; WorkingDir: "{app}"

[Run]
Filename: "{app}\DrawingMaker3D.exe"; Description: "DrawingMaker 3D"; Flags: nowait postinstall skipifsilent
