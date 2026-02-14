#define AppName "ABoroOffice"
#define AppVersion "1.0.0"
#define AppPublisher "ABoroOffice"
#if GetEnv("ABORO_PKG_DIR") == ""
  #define SourceDir ".\package"
#else
  #define SourceDir GetEnv("ABORO_PKG_DIR")
#endif
#define DockerUrl "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe?utm_campaign=docs-driven-download-win-amd64&utm_medium=webreferral&utm_source=docker"

[Setup]
AppId={{7F1A0C3B-5C8F-4E61-9E6C-6F0B6E3F7B12}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={pf}\ABoroOffice
DefaultGroupName=ABoroOffice
OutputBaseFilename=ABoroOfficeSetup
Compression=none
SolidCompression=no
PrivilegesRequired=admin

[Tasks]
Name: "installDocker"; Description: "Download and install Docker Desktop"; GroupDescription: "Optional components:"; Check: not IsDockerInstalled
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\logs"

[Code]
function IsDockerInstalled(): Boolean;
begin
  Result := FileExists(ExpandConstant('{pf}\Docker\Docker\Docker Desktop.exe'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvPath: String;
  ExamplePath: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Ensure logs folder is empty
    DelTree(ExpandConstant('{app}\logs'), True, True, True);
    ForceDirectories(ExpandConstant('{app}\logs'));

    // If .env is missing but .env.example exists, copy it
    EnvPath := ExpandConstant('{app}\.env');
    ExamplePath := ExpandConstant('{app}\.env.example');
    if (not FileExists(EnvPath)) and FileExists(ExamplePath) then
    begin
      FileCopy(ExamplePath, EnvPath, False);
    end;
  end;
end;

[Icons]
Name: "{group}\ABoroOffice Docker Launcher"; Filename: "{app}\bin\ABoroOfficeDockerLauncher.exe"
Name: "{commondesktop}\ABoroOffice Docker Launcher"; Filename: "{app}\bin\ABoroOfficeDockerLauncher.exe"; Tasks: desktopicon

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; \
    Parameters: "-ExecutionPolicy Bypass -Command ""$u='{#DockerUrl}'; $p=Join-Path $env:TEMP 'Docker Desktop Installer.exe'; Invoke-WebRequest -Uri $u -OutFile $p; Start-Process -FilePath $p -ArgumentList 'install','--accept-license' -Wait"""; \
    StatusMsg: "Downloading and installing Docker Desktop..."; Tasks: installDocker
