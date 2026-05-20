@echo off
REM Build All Script for School Bell (Windows)
REM Automatically runs all available build scripts

setlocal EnableDelayedExpansion

echo ==========================================
echo School Bell - Build All Script (Windows)
echo ==========================================

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo.
echo Available build targets:
echo   1. MSI package (build_msi.bat) - Requires WiX Toolset v4
echo   2. EXE installer (build_exe.bat) - Requires Inno Setup
echo.

set /p BUILD_TYPE="Enter build type (msi/exe/all) [all]: "
if "!BUILD_TYPE!"=="" set BUILD_TYPE=all

if /i "!BUILD_TYPE!"=="msi" (
    if exist "%SCRIPT_DIR%build_msi.bat" (
        echo Running MSI build...
        call "%SCRIPT_DIR%build_msi.bat"
        if !ERRORLEVEL! neq 0 (
            echo [ERROR] MSI build failed
            exit /b 1
        )
        echo.
        echo MSI build completed!
    ) else (
        echo [ERROR] build_msi.bat not found
        exit /b 1
    )
) else if /i "!BUILD_TYPE!"=="exe" (
    if exist "%SCRIPT_DIR%build_exe.bat" (
        echo Running EXE installer build...
        call "%SCRIPT_DIR%build_exe.bat"
        if !ERRORLEVEL! neq 0 (
            echo [ERROR] EXE build failed
            exit /b 1
        )
        echo.
        echo EXE build completed!
    ) else (
        echo [ERROR] build_exe.bat not found
        exit /b 1
    )
) else if /i "!BUILD_TYPE!"=="all" (
    echo Running all builds...
    echo.
    
    REM Try MSI build
    if exist "%SCRIPT_DIR%build_msi.bat" (
        echo [1/2] Building MSI package...
        call "%SCRIPT_DIR%build_msi.bat"
        if !ERRORLEVEL! equ 0 (
            echo MSI build completed successfully
        ) else (
            echo [WARNING] MSI build failed or was skipped
        )
        echo.
    ) else (
        echo [WARNING] build_msi.bat not found, skipping MSI build
        echo.
    )
    
    REM Try EXE build
    if exist "%SCRIPT_DIR%build_exe.bat" (
        echo [2/2] Building EXE installer...
        call "%SCRIPT_DIR%build_exe.bat"
        if !ERRORLEVEL! equ 0 (
            echo EXE build completed successfully
        ) else (
            echo [WARNING] EXE build failed or was skipped
        )
        echo.
    ) else (
        echo [WARNING] build_exe.bat not found, skipping EXE build
        echo.
    )
    
    echo ==========================================
    echo All builds completed!
    echo ==========================================
) else (
    echo Unknown build type: !BUILD_TYPE!
    echo Valid options: msi, exe, all
    exit /b 1
)

exit /b 0
