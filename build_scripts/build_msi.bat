@echo off
REM Build script for creating MSI installer on Windows using WiX Toolset v4
REM Requires: Python, PyInstaller, WiX Toolset v4

setlocal EnableDelayedExpansion

echo ==========================================
echo School Bell - MSI Package Builder
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

where dotnet >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] dotnet SDK is not installed (required for WiX v4)
    echo Download from: https://dotnet.microsoft.com/download
    exit /b 1
)

REM Get version from src/config.py
for /f "tokens=2 delims=\" %%i in ('findstr /R "^VERSION" "%PROJECT_ROOT%\src\config.py"') do set VERSION=%%i
set VERSION=!VERSION:"=!
set VERSION=!VERSION: =!
if "!VERSION!"=="" set VERSION=1.0.0

echo Version: !VERSION!

REM Configuration
set APP_NAME=SchoolBell
set BUILD_DIR=%PROJECT_ROOT%\build\msi
set DIST_DIR=%PROJECT_ROOT%\dist

REM Clean previous build
echo.
echo [1/6] Cleaning previous build...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%\%APP_NAME%" rmdir /s /q "%DIST_DIR%\%APP_NAME%"
mkdir "%BUILD_DIR%"

REM Run PyInstaller
echo.
echo [2/6] Running PyInstaller...
cd /d "%PROJECT_ROOT%"
pyinstaller --clean --noconfirm school_bell.spec
if %ERRORLEVEL% neq 0 (
    echo [ERROR] PyInstaller failed
    exit /b 1
)

REM Copy PyInstaller output to build directory
echo.
echo [3/6] Copying application files...
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

REM Create WiX project
echo.
echo [4/6] Creating WiX project...
cd /d "%BUILD_DIR%"

REM Create WiX project file
dotnet new wix -name SchoolBellInstaller -o WixProject
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Could not create WiX project, using manual wxs approach
    goto :manual_wxs
)

REM Copy our wxs file
copy /Y "%PROJECT_ROOT%\build_scripts\installer.wxs" "WixProject\Main.wxs"

REM Build MSI using WiX
echo.
echo [5/6] Building MSI package...
cd /d "%BUILD_DIR%\WixProject"
dotnet publish -c Release -r win-x64 --output "%BUILD_DIR%\output"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] WiX build failed
    exit /b 1
)

REM Copy MSI to dist folder
echo.
echo [6/6] Copying MSI to dist folder...
if exist "%BUILD_DIR%\output\*.msi" (
    copy /Y "%BUILD_DIR%\output\*.msi" "%DIST_DIR%\%APP_NAME%_v!VERSION!_x64.msi"
    echo.
    echo ==========================================
    echo SUCCESS! MSI created:
    echo %DIST_DIR%\%APP_NAME%_v!VERSION!_x64.msi
    echo ==========================================
    exit /b 0
)

:manual_wxs
echo [ERROR] WiX Toolset setup incomplete. Please install WiX v4 properly.
echo Download from: https://wixtoolset.org/
exit /b 1
