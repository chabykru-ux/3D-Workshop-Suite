@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0BUILD_SETUP.ps1"
if errorlevel 1 (
  echo.
  echo BUILD FAILED. See build-log.txt and self-test.txt if present.
  pause
  exit /b 1
)
echo.
echo DONE. The installer is in dist.
start "" "%~dp0dist"
pause
