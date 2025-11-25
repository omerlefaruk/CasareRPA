; CasareRPA Developer Installer
; Inno Setup Script
;
; Build with: ISCC.exe /DAppVersion=1.0.0 /DSourceDir=..\..\dist /DOutputDir=..\output casarerpa-dev.iss

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

#ifndef SourceDir
  #define SourceDir "..\..\dist"
#endif

#ifndef OutputDir
  #define OutputDir "..\output"
#endif

#define AppName "CasareRPA"
#define AppPublisher "CasareRPA"
#define AppURL "https://github.com/casarerpa/casarerpa"
#define AppExeName "CasareRPA-Canvas.exe"

[Setup]
; App identification
AppId={{8E7B5A4F-3C2D-4E1A-9F8B-6D5E4C3A2B1F}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}/releases

; Installation directories
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Output
OutputDir={#OutputDir}
OutputBaseFilename=CasareRPA-Setup-{#AppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\Canvas\CasareRPA-Canvas\CasareRPA-Canvas.exe

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Wizard
WizardStyle=modern
WizardSizePercent=120
WizardImageFile=banner.bmp
WizardSmallImageFile=wizard.bmp

; Misc
AllowNoIcons=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "Full Installation (All Components)"
Name: "compact"; Description: "Canvas Only (Workflow Designer)"
Name: "robot_only"; Description: "Robot Only (For Client PCs)"
Name: "custom"; Description: "Custom Installation"; Flags: iscustom

[Components]
Name: "canvas"; Description: "CasareRPA Canvas (Workflow Designer)"; Types: full compact custom
Name: "orchestrator"; Description: "CasareRPA Orchestrator (Fleet Manager)"; Types: full custom
Name: "robot"; Description: "CasareRPA Robot (Workflow Executor)"; Types: full robot_only custom; Flags: checkablealone

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Components: canvas
Name: "desktopicon_orchestrator"; Description: "Create Orchestrator desktop icon"; GroupDescription: "{cm:AdditionalIcons}"; Components: orchestrator
Name: "desktopicon_robot"; Description: "Create Robot desktop icon"; GroupDescription: "{cm:AdditionalIcons}"; Components: robot
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Canvas files
Source: "{#SourceDir}\Canvas\CasareRPA-Canvas\*"; DestDir: "{app}\Canvas\CasareRPA-Canvas"; Components: canvas; Flags: ignoreversion recursesubdirs createallsubdirs

; Orchestrator files
Source: "{#SourceDir}\Orchestrator\CasareRPA-Orchestrator\*"; DestDir: "{app}\Orchestrator\CasareRPA-Orchestrator"; Components: orchestrator; Flags: ignoreversion recursesubdirs createallsubdirs

; Robot files
Source: "{#SourceDir}\Robot\CasareRPA-Robot\*"; DestDir: "{app}\Robot\CasareRPA-Robot"; Components: robot; Flags: ignoreversion recursesubdirs createallsubdirs

; Shared version info
Source: "{#SourceDir}\version.json"; DestDir: "{app}\Shared"; Flags: ignoreversion

[Icons]
; Canvas icons
Name: "{group}\CasareRPA Canvas"; Filename: "{app}\Canvas\CasareRPA-Canvas\CasareRPA-Canvas.exe"; Components: canvas
Name: "{autodesktop}\CasareRPA Canvas"; Filename: "{app}\Canvas\CasareRPA-Canvas\CasareRPA-Canvas.exe"; Tasks: desktopicon; Components: canvas

; Orchestrator icons
Name: "{group}\CasareRPA Orchestrator"; Filename: "{app}\Orchestrator\CasareRPA-Orchestrator\CasareRPA-Orchestrator.exe"; Components: orchestrator
Name: "{autodesktop}\CasareRPA Orchestrator"; Filename: "{app}\Orchestrator\CasareRPA-Orchestrator\CasareRPA-Orchestrator.exe"; Tasks: desktopicon_orchestrator; Components: orchestrator

; Robot icons
Name: "{group}\CasareRPA Robot"; Filename: "{app}\Robot\CasareRPA-Robot\CasareRPA-Robot.exe"; Components: robot
Name: "{autodesktop}\CasareRPA Robot"; Filename: "{app}\Robot\CasareRPA-Robot\CasareRPA-Robot.exe"; Tasks: desktopicon_robot; Components: robot

; Uninstall icon
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

[Registry]
; File associations for .crpa workflow files
Root: HKCR; Subkey: ".crpa"; ValueType: string; ValueName: ""; ValueData: "CasareRPA.Workflow"; Flags: uninsdeletevalue; Components: canvas
Root: HKCR; Subkey: "CasareRPA.Workflow"; ValueType: string; ValueName: ""; ValueData: "CasareRPA Workflow"; Flags: uninsdeletekey; Components: canvas
Root: HKCR; Subkey: "CasareRPA.Workflow\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\Canvas\CasareRPA-Canvas\CasareRPA-Canvas.exe,0"; Components: canvas
Root: HKCR; Subkey: "CasareRPA.Workflow\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Canvas\CasareRPA-Canvas\CasareRPA-Canvas.exe"" ""%1"""; Components: canvas

; App paths for easier command line access
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\casarerpa-canvas.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\Canvas\CasareRPA-Canvas\CasareRPA-Canvas.exe"; Flags: uninsdeletekey; Components: canvas
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\casarerpa-orchestrator.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\Orchestrator\CasareRPA-Orchestrator\CasareRPA-Orchestrator.exe"; Flags: uninsdeletekey; Components: orchestrator
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\casarerpa-robot.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\Robot\CasareRPA-Robot\CasareRPA-Robot.exe"; Flags: uninsdeletekey; Components: robot

; Store installation info
Root: HKLM; Subkey: "SOFTWARE\CasareRPA"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\CasareRPA"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"; Flags: uninsdeletekey

[Run]
; Install Playwright browsers (required for web automation)
; This runs the bundled playwright to install Chromium
Filename: "{app}\Canvas\CasareRPA-Canvas\_internal\playwright.exe"; Parameters: "install chromium"; Description: "Install Chromium browser for web automation"; Flags: postinstall runhidden waituntilterminated; Components: canvas; StatusMsg: "Installing Chromium browser..."
Filename: "{app}\Robot\CasareRPA-Robot\_internal\playwright.exe"; Parameters: "install chromium"; Description: "Install Chromium browser for web automation"; Flags: postinstall runhidden waituntilterminated; Components: robot not canvas; StatusMsg: "Installing Chromium browser..."

; Option to launch Canvas after install
Filename: "{app}\Canvas\CasareRPA-Canvas\CasareRPA-Canvas.exe"; Description: "{cm:LaunchProgram,CasareRPA Canvas}"; Flags: nowait postinstall skipifsilent; Components: canvas

[UninstallDelete]
; Clean up any generated files
Type: filesandordirs; Name: "{app}\Shared"
Type: filesandordirs; Name: "{userappdata}\CasareRPA"
Type: dirifempty; Name: "{app}"

[Code]
// Custom page for first-run configuration prompt
var
  ConfigPage: TWizardPage;
  SupabaseUrlEdit: TNewEdit;
  SupabaseKeyEdit: TNewEdit;

procedure InitializeWizard;
begin
  // Create configuration page (shown only for Orchestrator/Robot installs)
  ConfigPage := CreateCustomPage(wpSelectDir,
    'Backend Configuration',
    'Configure the Supabase backend connection (optional - can be configured later)');

  // Supabase URL
  with TNewStaticText.Create(ConfigPage) do
  begin
    Parent := ConfigPage.Surface;
    Caption := 'Supabase URL:';
    Left := 0;
    Top := 8;
  end;

  SupabaseUrlEdit := TNewEdit.Create(ConfigPage);
  with SupabaseUrlEdit do
  begin
    Parent := ConfigPage.Surface;
    Left := 0;
    Top := 28;
    Width := ConfigPage.SurfaceWidth;
    Text := '';
  end;

  // Supabase Key
  with TNewStaticText.Create(ConfigPage) do
  begin
    Parent := ConfigPage.Surface;
    Caption := 'Supabase Anon Key:';
    Left := 0;
    Top := 60;
  end;

  SupabaseKeyEdit := TNewEdit.Create(ConfigPage);
  with SupabaseKeyEdit do
  begin
    Parent := ConfigPage.Surface;
    Left := 0;
    Top := 80;
    Width := ConfigPage.SurfaceWidth;
    Text := '';
  end;

  with TNewStaticText.Create(ConfigPage) do
  begin
    Parent := ConfigPage.Surface;
    Caption := 'Leave empty to configure later via the application settings.';
    Left := 0;
    Top := 120;
    Font.Style := [fsItalic];
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;

  // Skip config page if only Canvas is selected
  if PageID = ConfigPage.ID then
  begin
    Result := not (IsComponentSelected('orchestrator') or IsComponentSelected('robot'));
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigPath: String;
  ConfigContent: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Save configuration if provided
    if (SupabaseUrlEdit.Text <> '') and (SupabaseKeyEdit.Text <> '') then
    begin
      ConfigPath := ExpandConstant('{app}\Shared\config.json');
      ConfigContent := '{' + #13#10 +
        '  "supabase_url": "' + SupabaseUrlEdit.Text + '",' + #13#10 +
        '  "supabase_key": "' + SupabaseKeyEdit.Text + '"' + #13#10 +
        '}';
      SaveStringToFile(ConfigPath, ConfigContent, False);
    end;
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
end;
