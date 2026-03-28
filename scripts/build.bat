@echo off
REM build.bat -- Сборка проекта Refactoring на Windows (MSVC)
REM Использование: scripts\build.bat

set REPO_ROOT=%~dp0..
set BUILD_DIR=%REPO_ROOT%\build

echo === Refactoring: Build (Windows) ===

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
cd /d "%BUILD_DIR%"

cmake "%REPO_ROOT%" -G "Visual Studio 17 2022"
cmake --build . --config Release

echo === Build complete ===
