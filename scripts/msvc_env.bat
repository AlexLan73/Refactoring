@echo off
REM Активация MSVC из VS 18 (2026) и запуск переданной команды
REM Использование: msvc_env.bat <команда и аргументы>
REM ⚠️ Путь захардкожен на VS 18 Community — изменить при другой установке
set "VCVARS=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat"
if not exist "%VCVARS%" (
    echo ERROR: vcvarsall.bat not found at %VCVARS% >&2
    exit /b 1
)
call "%VCVARS%" x64 >nul
%*
