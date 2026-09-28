#define MyAppName "In one line"
#define MyAppExeName "InOneLine.exe"
#define MyAppVersion "1.0.4"
#define MyAppPublisher "Local Streaming Tools"
#define MyAppId "{{D9AE3184-F16E-4B60-BDD9-D4B99541462E}"
#ifndef DistRoot
  #error DistRoot compile-time define is required
#endif

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion=1.0.4.0
DefaultDirName=C:\InOneLine
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=yes
AllowRootDirectory=no
AllowNetworkDrive=no
AllowUNCPath=no
PrivilegesRequired=admin
SetupArchitecture=x64
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern
SetupIconFile=..\assets\InOneLine.ico
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=output
OutputBaseFilename=InOneLine_Setup_{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
SetupLogging=yes
UsePreviousAppDir=yes
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no
ChangesAssociations=no
ChangesEnvironment=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"; Flags: unchecked

[InstallDelete]
; Clean only immutable runtime files on reinstall/update. User-owned data is deliberately preserved.
Type: files; Name: "{app}\{#MyAppExeName}"
Type: filesandordirs; Name: "{app}\_internal"

[UninstallDelete]
; R1.0.4 final uninstall policy: after the explicit destructive-data warning,
; remove all InOneLine-owned mutable data. External files referenced by the
; application are outside {app} and are never touched here.
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\backups"
Type: filesandordirs; Name: "{app}\logs"

[Registry]
; R1.0.4 FIX1: register private QSettings keys for declarative uninstall cleanup.
; dontcreatekey keeps installation side-effect free if the app has not created a key yet;
; uninsdeletekey removes the whole private key after a confirmed uninstall.
Root: HKCU; Subkey: "Software\Local Streaming Tools\Streaming Manager"; Flags: dontcreatekey uninsdeletekey
Root: HKCU; Subkey: "Software\Local Streaming Tools\InOneLine"; Flags: dontcreatekey uninsdeletekey

[Dirs]
; C:\InOneLine is created by an elevated installer. Grant normal users modify rights only
; to application-owned mutable directories, never to the EXE/_internal runtime tree.
Name: "{app}\data"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{app}\backups"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{app}\logs"; Permissions: users-modify; Flags: uninsneveruninstall

[Files]
Source: "{#DistRoot}\InOneLine.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DistRoot}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\data\import_template.csv"; DestDir: "{app}\data"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[Code]
const
  FullRemovalWarningMarker = 'ПОЛНОЕ УДАЛЕНИЕ ДАННЫХ IN ONE LINE';

function InitializeUninstall(): Boolean;
var
  Answer: Integer;
begin
  Answer := MsgBox(
    FullRemovalWarningMarker + #13#10 + #13#10 +
    'При удалении In one line будут безвозвратно удалены все данные программы в папке установки, включая:' + #13#10 +
    '• базу данных и историю;' + #13#10 +
    '• credentials и настройки интеграций;' + #13#10 +
    '• внутренние медиафайлы;' + #13#10 +
    '• локальные резервные копии;' + #13#10 +
    '• журналы программы.' + #13#10 + #13#10 +
    'Если эти данные могут понадобиться, нажмите «Нет», запустите In one line и откройте:' + #13#10 +
    'Настройки → Общие → Локальные данные →' + #13#10 +
    '«Создать полную резервную копию в случае полного удаления программы».' + #13#10 + #13#10 +
    'Сохраните файл .iolbackup ВНЕ папки InOneLine.' + #13#10 + #13#10 +
    'Продолжить полное удаление программы и всех её данных?',
    mbConfirmation, MB_YESNO or MB_DEFBUTTON2
  );
  Result := Answer = IDYES;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    { QSettings in 1.0.0 still uses the legacy application key for compatibility. }
    RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Local Streaming Tools\Streaming Manager');
    { Also remove the reserved final-name key if it exists. }
    RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Local Streaming Tools\InOneLine');
  end;
end;

function CandidateExePath(): String;
begin
  Result := AddBackslash(WizardDirValue) + '{#MyAppExeName}';
end;

function InstallPathIsSupported(): Boolean;
var
  ExePath: String;
begin
  ExePath := CandidateExePath();
  Result := Length(ExePath) < 260;
  if not Result then
    MsgBox(
      'Выбранный путь слишком длинный для In one line 1.0.4.' + #13#10 + #13#10 +
      'Полный путь к InOneLine.exe должен быть короче 260 символов.' + #13#10 +
      'Выберите более короткую папку установки.',
      mbError, MB_OK
    );
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then
    Result := InstallPathIsSupported();
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if Length(CandidateExePath()) >= 260 then
    Result :=
      'Полный путь к InOneLine.exe должен быть короче 260 символов. ' +
      'Выберите более короткую папку установки.';
end;
