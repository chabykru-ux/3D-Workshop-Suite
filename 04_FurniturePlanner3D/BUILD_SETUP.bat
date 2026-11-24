@echo off
setlocal
cd /d "%~dp0"
where npm >nul 2>&1
if errorlevel 1 (
  echo Node.js and npm are required. Install Node.js LTS and run again.
  goto fail
)
set CSC_IDENTITY_AUTO_DISCOVERY=false
call npm install --no-audit --no-fund
if errorlevel 1 goto fail
call npm run dist
if errorlevel 1 goto fail
echo.
echo Setup created in the dist folder.
start "" "%~dp0dist"
pause
exit /b 0
:fail
echo.
echo Build failed. Review the errors above.
pause
exit /b 1
