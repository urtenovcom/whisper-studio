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

function PrettyStatus(const Line: string): string;
var
  s, name: string;
  p: Integer;
begin
  s := Trim(Line);
  Result := '';
  if Pos('Collecting ', s) = 1 then begin
    name := Copy(s, 12, Length(s));
    p := Pos(' ', name);
    if p > 0 then name := Copy(name, 1, p - 1);
    Result := 'Загрузка ' + name + '...';
  end else if Pos('Downloading ', s) = 1 then begin
    name := Copy(s, 13, Length(s));
    p := Pos(' ', name);
    if p > 0 then name := Copy(name, 1, p - 1);
    Result := 'Загрузка ' + name + '...';
  end else if Pos('Installing collected packages', s) = 1 then begin
    Result := 'Установка пакетов...';
  end else if Pos('Successfully installed', s) = 1 then begin
    Result := 'Завершение установки...';
  end;
end;

procedure ReadStatusLine(const Path: string; var LastShown: string);
var
  Lines: TArrayOfString;
  i: Integer;
  candidate: string;
begin
  if not LoadStringsFromFile(Path, Lines) then Exit;
  // ищем сверху вниз последнюю строку, из которой можно сделать красивый статус
  for i := Length(Lines) - 1 downto 0 do begin
    candidate := PrettyStatus(Lines[i]);
    if candidate <> '' then begin
      if candidate <> LastShown then begin
        LastShown := candidate;
        PipProgressPage.SetText('Установка Whisper Studio', candidate);
      end;
      Exit;
    end;
  end;
end;

function RunPipInstall(): Boolean;
var
  AppDir, StatusLog, DoneFlag, Cmd: string;
  ResultCode: Integer;
  StartTick, Elapsed, EstimatedMs, Pct: Cardinal;
  LastStatus: string;
begin
  AppDir := ExpandConstant('{app}');
  StatusLog := AppDir + '\setup.log';
  DoneFlag := AppDir + '\setup.done';
  DeleteFile(StatusLog);
  DeleteFile(DoneFlag);

  PipProgressPage := CreateOutputProgressPage('Установка Whisper Studio',
    'Загружаем библиотеки с PyPI. Это разовая операция, занимает 5–10 минут.');
  PipProgressPage.SetText('Подготовка...', '');
  PipProgressPage.SetProgress(0, 100);
  PipProgressPage.Show;

  // Запускаем bat скрыто и асинхронно, перенаправляем вывод в файл
  Cmd := '/C ""' + AppDir + '\setup_deps.bat" > "' + StatusLog + '" 2>&1 & echo done > "' + DoneFlag + '""';
  if not ShellExec('open', 'cmd.exe', Cmd, AppDir, SW_HIDE, ewNoWait, ResultCode) then begin
    PipProgressPage.Hide;
    Result := False;
    Exit;
  end;

  StartTick := GetTickCount;
  EstimatedMs := 7 * 60 * 1000; // ~7 минут на типичной скорости
  LastStatus := '';

  while not FileExists(DoneFlag) do begin
    Elapsed := GetTickCount - StartTick;
    Pct := (Elapsed * 95) div EstimatedMs;
    if Pct > 95 then Pct := 95;
    PipProgressPage.SetProgress(Pct, 100);
    ReadStatusLine(StatusLog, LastStatus);
    Sleep(400);
  end;

  PipProgressPage.SetProgress(100, 100);
  PipProgressPage.SetText('Готово', 'Whisper Studio установлен.');
  Sleep(600);
  PipProgressPage.Hide;
  DeleteFile(DoneFlag);
  DeleteFile(StatusLog);
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
