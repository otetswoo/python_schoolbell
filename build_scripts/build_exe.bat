@echo off
REM Build script for creating EXE installer on Windows using Inno Setup
REM Requires: Python, PyInstaller, Inno Setup Compiler (ISCC)

setlocal EnableDelayedExpansion

echo ==========================================
echo School Bell - EXE Installer Builder
echo ==========================================

REM Get project root directory (parent of build_scripts)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM Check for required tools
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] python is not installed or not in PATH
    exit /b 1
)

where pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pyinstaller is not installed. Install with: pip install pyinstaller
    exit /b 1
)

REM Check for Inno Setup
set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
    if not exist "%ISCC_PATH%" (
        echo [ERROR] Inno Setup Compiler not found at expected locations
        echo Please install Inno Setup from https://jrsoftware.org/isdl.php
        exit /b 1
    )
)

REM Get version from src/config.py
for /f "tokens=2 delims=\" %%i in ('findstr /R "^VERSION" "%PROJECT_ROOT%\src\config.py"') do set VERSION=%%i
set VERSION=!VERSION:"=!
set VERSION=!VERSION: =!
if "!VERSION!"=="" set VERSION=1.0.0

echo Version: !VERSION!

REM Configuration
set APP_NAME=SchoolBell
set BUILD_DIR=%PROJECT_ROOT%\build\exe_installer
set DIST_DIR=%PROJECT_ROOT%\dist

REM Clean previous build
echo.
echo [1/5] Cleaning previous build...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%\%APP_NAME%" rmdir /s /q "%DIST_DIR%\%APP_NAME%"
mkdir "%BUILD_DIR%"

REM Run PyInstaller with proper options for PySide6
echo.
echo [2/5] Running PyInstaller...
cd /d "%PROJECT_ROOT%"
pyinstaller --clean --noconfirm school_bell.spec
if %ERRORLEVEL% neq 0 (
    echo [ERROR] PyInstaller failed
    exit /b 1
)

REM Copy PyInstaller output to build directory
echo.
echo [3/5] Copying application files...
if exist "%DIST_DIR%\school-bell" (
    xcopy /E /I /Y "%DIST_DIR%\school-bell" "%BUILD_DIR%\%APP_NAME%"
) else if exist "%DIST_DIR%\SchoolBell" (
    xcopy /E /I /Y "%DIST_DIR%\SchoolBell" "%BUILD_DIR%\%APP_NAME%"
) else (
    echo [ERROR] PyInstaller output not found
    exit /b 1
)

REM Copy sounds directory
if exist "%PROJECT_ROOT%\sounds" (
    xcopy /E /I /Y "%PROJECT_ROOT%\sounds" "%BUILD_DIR%\%APP_NAME%\sounds"
)

REM Copy config files
if exist "%PROJECT_ROOT%\schedule.yml" (
    copy /Y "%PROJECT_ROOT%\schedule.yml" "%BUILD_DIR%\%APP_NAME%\"
)
if exist "%PROJECT_ROOT%\preferences.yml" (
    copy /Y "%PROJECT_ROOT%\preferences.yml" "%BUILD_DIR%\%APP_NAME%\"
)

REM Copy icon file
if exist "%PROJECT_ROOT%\src\school_bell.png" (
    copy /Y "%PROJECT_ROOT%\src\school_bell.png" "%BUILD_DIR%\icon.png"
)

REM Generate Inno Setup script from template
echo.
echo [4/5] Generating Inno Setup script...
(
    echo #define MyAppName "School Bell"
    echo #define MyAppVersion "!VERSION!"
    echo #define MyAppPublisher "otetswoo"
    echo #define MyAppExeName "SchoolBell.exe"
    echo.
    echo [Setup]
    echo AppId={{B1C2D3E4-F5A6-7890-BCDE-F12345678901}
    echo AppName={#MyAppName}
    echo AppVersion={#MyAppVersion}
    echo AppPublisher={#MyAppPublisher}
    echo DefaultDirName={autopf}\SchoolBell
    echo DefaultGroupName=School Bell
    echo AllowNoIcons=yes
    echo LicenseFile=..\..\LICENSE
    echo OutputDir=..\..\dist
    echo OutputBaseFilename=SchoolBell_Setup_v{#MyAppVersion}
    echo SetupIconFile=icon.ico
    echo UninstallDisplayIcon={app}\{#MyAppExeName}
    echo Compression=lzma
    echo SolidCompression=yes
    echo WizardStyle=modern
    echo PrivilegesRequired=admin
    echo ArchitecturesAllowed=x64
    echo ArchitecturesInstallIn64BitMode=x64
    echo.
    echo [Languages]
    echo Name: "english"; MessagesFile: "compiler:Default.isl"
    echo Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
    echo.
    echo [Tasks]
    echo Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
    echo.
    echo [Files]
    echo Source: "..\..\build\exe_installer\SchoolBell\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
    echo NOTE: Don^'t use "Flags: ignoreversion" on any shared system files
    echo.
    echo [Icons]
    echo Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
    echo Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
    echo Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
    echo.
    echo [Run]
    echo Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '^&', '^&^&')}}"; Flags: nowait postinstall skipifsilent
    echo.
    echo [Code]
    echo function InitializeSetup(): Boolean;
    echo var
    echo   ResultCode: Integer;
    echo begin
    echo   Result := True;
    echo end;
) > "%BUILD_DIR%\installer.iss"

REM Create a simple icon if none exists (convert PNG to ICO)
if not exist "%BUILD_DIR%\icon.ico" (
    echo [INFO] Creating placeholder icon...
    REM For now, just copy the PNG as a placeholder - Inno Setup can use PNG
    copy /Y "%BUILD_DIR%\icon.png" "%BUILD_DIR%\icon.ico" 2>nul || echo [WARNING] Could not create icon file
)

REM Run Inno Setup Compiler
echo.
echo [5/5] Building EXE installer...
cd /d "%BUILD_DIR%"
"%ISCC_PATH%" installer.iss
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Inno Setup compilation failed
    exit /b 1
)

REM Verify output
if exist "%DIST_DIR%\SchoolBell_Setup_v!VERSION!.exe" (
    echo.
    echo ==========================================
    echo SUCCESS! EXE installer created:
    echo %DIST_DIR%\SchoolBell_Setup_v!VERSION!.exe
    echo ==========================================
    echo.
    echo Silent installation options:
    echo   /SILENT     - Silent mode, no progress window
    echo   /VERYSILENT - Very silent mode, no interaction
    echo   /SUPPRESSMSGBOXES - Suppress message boxes
    echo   /NORESTART  - Do not restart after installation
    echo   /SP-        - Skip "This will install..." message
    exit /b 0
) else (
    echo [ERROR] Output file not found
    dir "%DIST_DIR%" 2>nul
    exit /b 1
)
