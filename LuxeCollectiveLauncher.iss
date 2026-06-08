; Luxe Collective Platform – Inno Setup Script
; Creates a Windows installer that sets up the Docker environment helper.
; WARNING: This does NOT install the platform as a native Windows app.
;          It only copies the Docker helper files and creates shortcuts.

#define MyAppName "Luxe Collective Platform"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Luxe Collective"
#define MyAppURL "https://github.com/dmang69/LUXE"
#define MyAppExeName "start-luxe.bat"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputBaseFilename=LuxeCollective-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ChangesEnvironment=no
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
InfoBeforeFile=info.txt
DisableDirPage=no
DisableProgramGroupPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "docker-compose.yml";      DestDir: "{app}"; Flags: ignoreversion
Source: ".env.template";           DestDir: "{app}"; Flags: ignoreversion
Source: "start-luxe.bat";          DestDir: "{app}"; Flags: ignoreversion
Source: "stop-luxe.bat";           DestDir: "{app}"; Flags: ignoreversion
Source: "info.txt";                DestDir: "{app}"; Flags: ignoreversion
Source: "dashboard.py";            DestDir: "{app}"; Flags: ignoreversion
Source: "requirements-dashboard.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "Dockerfile.api";          DestDir: "{app}"; Flags: ignoreversion
Source: "Dockerfile.dashboard";    DestDir: "{app}"; Flags: ignoreversion
Source: "api\*";                   DestDir: "{app}\api"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Start Luxe Collective"; Filename: "{app}\start-luxe.bat"
Name: "{group}\Stop Luxe Collective";  Filename: "{app}\stop-luxe.bat"
Name: "{group}\Open Dashboard";        Filename: "http://localhost:8501"
Name: "{group}\Open API Docs";         Filename: "http://localhost:8000/docs"
Name: "{commondesktop}\Luxe Collective"; Filename: "{app}\start-luxe.bat"; Tasks: desktopicon

[Run]
Filename: "{app}\start-luxe.bat"; Description: "Launch Luxe Collective now (requires Docker Desktop)"; Flags: nowait postinstall skipifsilent shellexec

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not MsgBox(
    'LUXE COLLECTIVE PLATFORM – DOCKER ENVIRONMENT SETUP' + #13#10 + #13#10 +
    'WARNING: This does NOT install the platform as a Windows application.' + #13#10 +
    'It ONLY copies Docker helper files to run Luxe Collective locally.' + #13#10 +
    #13#10 +
    'You MUST:' + #13#10 +
    '  1. Have Docker Desktop installed and running' + #13#10 +
    '  2. Have ~3 GB free disk space' + #13#10 +
    '  3. Understand this is for LOCAL DEMO/DEVELOPMENT ONLY' + #13#10 +
    #13#10 +
    'For real AI generation, a free Google Gemini API key is optional.' + #13#10 +
    'Without it, the platform runs in mock mode with instant results.' + #13#10 +
    #13#10 +
    'Do you want to continue?',
    mbConfirmation, MB_YESNO) = IDYES then
  begin
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  DockerFound: Boolean;
begin
  if CurStep = ssPostInstall then
  begin
    // Check for Docker Desktop registry key
    DockerFound := RegKeyExists(HKLM, 'SOFTWARE\Docker Desktop') or
                   RegKeyExists(HKLM, 'SOFTWARE\WOW6432Node\Docker Desktop');
    if not DockerFound then
    begin
      if MsgBox(
        'Docker Desktop was not detected on your system.' + #13#10 +
        'The platform cannot run without it.' + #13#10 +
        #13#10 +
        'Would you like to open the Docker Desktop download page now?',
        mbConfirmation, MB_YESNO) = IDYES then
      begin
        ShellExec('open', 'https://www.docker.com/products/docker-desktop/', '', '', SW_SHOWNORMAL, ewNoWait, 0);
      end;
    end;
  end;
end;
