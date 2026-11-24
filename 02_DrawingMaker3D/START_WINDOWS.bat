@echo off
cd /d "%~dp0"
setlocal
if exist ".venv\Scripts\python.exe" goto run
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 -m venv .venv
  if not errorlevel 1 goto install
  py -3 -m venv .venv
  if not errorlevel 1 goto install
)
where python >nul 2>nul
if not errorlevel 1 (
  python -m venv .venv
  if not errorlevel 1 goto install
)
echo Python 3.12 is recommended. Run INSTALL_PYTHON.bat first.
pause
exit /b 1
:install
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
:run
.venv\Scripts\python.exe -c "import cv2,pypdfium2,pytesseract,trimesh,matplotlib,scipy,networkx; from shapely import constrained_delaunay_triangles" >nul 2>nul
if errorlevel 1 (
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe app.py
if errorlevel 1 goto fail
exit /b 0
:fail
echo Setup or launch failed. Please send a screenshot of this window.
pause
exit /b 1
