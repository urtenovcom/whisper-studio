; Whisper Studio — онлайн-установщик (Inno Setup 6)
#define MyAppName "Whisper Studio"
#define MyAppVersion "1.0"
#define MyAppPublisher "Whisper Studio"
#define MyAppExeName "pythonw.exe"

[Setup]
AppId={{8B9F2D7E-A4B3-4F1C-9D2E-1234567890AB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppMutex=WhisperStudioInstaller
DefaultDirName={autopf}\Whisper Studio
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=..\dist-installer
OutputBaseFilename=WhisperStudio-Setup
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
SetupIconFile=app.ico
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\app.ico
; ~2.5 ГБ — реальный размер после установки всех pip-зависимостей
UninstallDisplaySize=2621440
AppPublisherURL=https://github.com/urtenovcom/whisper-studio
AppSupportURL=https://github.com/urtenovcom/whisper-studio/issues
AppUpdatesURL=https://github.com/urtenovcom/whisper-studio/releases
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Дополнительно:"

[Files]
; --- Python embeddable ---
Source: "python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs
; --- Bootstrap для pip ---
Source: "get-pip.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements-runtime.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup_deps.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
; --- Исходники приложения ---
Source: "..\app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dictation.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\overlay.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\mainwindow.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs
; --- Модели диаризации ---
Source: "..\data\models\diarize\segmentation.onnx"; DestDir: "{app}\data\models\diarize"; Flags: ignoreversion
Source: "..\data\models\diarize\embedding.onnx"; DestDir: "{app}\data\models\diarize"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app.py"""; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"
Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app.py"""; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app.py"""; Description: "Запустить {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[Code]
function GetTickCount: DWord;
  external 'GetTickCount@kernel32.dll stdcall';

var
  PipProgressPage: TOutputProgressWizardPage;
  CurDisplayedPct: Integer;
  TargetPct: Integer;
  CurDisplayedStatus: string;

procedure SmoothAnimateTo(NewPct: Integer; const NewStatus: string);
var
  i: Integer;
begin
  if NewStatus <> '' then begin
    CurDisplayedStatus := NewStatus;
    PipProgressPage.SetText('Установка Whisper Studio', NewStatus);
  end;
  if NewPct > CurDisplayedPct then begin
    while CurDisplayedPct < NewPct do begin
      Inc(CurDisplayedPct);
      PipProgressPage.SetProgress(CurDisplayedPct, 100);
      // короткий Sleep + Refresh окна — UI остаётся отзывчивым
      WizardForm.Refresh;
      Sleep(8);
    end;
  end;
end;

procedure ReadProgressFile(const Path: string);
var
  Lines: TArrayOfString;
  s, pctStr, statusStr: string;
  commaPos, newPct: Integer;
begin
  if not LoadStringsFromFile(Path, Lines) then Exit;
  if GetArrayLength(Lines) = 0 then Exit;
  s := Trim(Lines[0]);
  commaPos := Pos('|', s);
  if commaPos <= 1 then Exit;
  pctStr := Copy(s, 1, commaPos - 1);
  statusStr := Copy(s, commaPos + 1, Length(s));
  newPct := StrToIntDef(pctStr, -1);
  if newPct < 0 then Exit;
  if (newPct > TargetPct) or (statusStr <> CurDisplayedStatus) then begin
    if newPct > TargetPct then TargetPct := newPct;
    SmoothAnimateTo(TargetPct, statusStr);
  end;
end;

function RunPipInstall(): Boolean;
var
  AppDir, ProgressFile, DoneFlag, Cmd: string;
  ResultCode: Integer;
  StartTick, Elapsed, TimePct: Cardinal;
begin
  AppDir := ExpandConstant('{app}');
  ProgressFile := AppDir + '\setup.progress';
  DoneFlag := AppDir + '\setup.done';
  DeleteFile(ProgressFile);
  DeleteFile(DoneFlag);

  PipProgressPage := CreateOutputProgressPage('Установка Whisper Studio',
    'Загружаем библиотеки с PyPI. Это разовая операция, занимает 5–10 минут.');
  CurDisplayedPct := 0;
  TargetPct := 0;
  CurDisplayedStatus := '';
  PipProgressPage.SetText('Установка Whisper Studio', 'Подготовка...');
  PipProgressPage.SetProgress(0, 100);
  PipProgressPage.Show;

  Cmd := '/C ""' + AppDir + '\setup_deps.bat""';
  if not ShellExec('open', 'cmd.exe', Cmd, AppDir, SW_HIDE, ewNoWait, ResultCode) then begin
    PipProgressPage.Hide;
    Result := False;
    Exit;
  end;

  StartTick := GetTickCount;
  while not FileExists(DoneFlag) do begin
    ReadProgressFile(ProgressFile);
    // во время длинных этапов плавно ползём по времени между маркерами
    Elapsed := GetTickCount - StartTick;
    TimePct := (Elapsed * 90) div (7 * 60 * 1000);
    if TimePct > 90 then TimePct := 90;
    if (Integer(TimePct) > CurDisplayedPct) and (Integer(TimePct) < TargetPct + 2) then begin
      PipProgressPage.SetProgress(Integer(TimePct), 100);
      CurDisplayedPct := Integer(TimePct);
    end;
    WizardForm.Refresh;
    Sleep(50);
  end;

  SmoothAnimateTo(100, 'Готово!');
  Sleep(400);
  PipProgressPage.Hide;
  DeleteFile(DoneFlag);
  DeleteFile(ProgressFile);
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    RunPipInstall();
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\python\Lib\site-packages"
Type: filesandordirs; Name: "{app}\python\Scripts"
Type: filesandordirs; Name: "{app}\__pycache__"
