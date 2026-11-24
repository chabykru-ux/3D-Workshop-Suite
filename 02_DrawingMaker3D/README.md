# DrawingMaker 3D — 0.6.0 (FIXED3 build)

[Русский](README.ru.md) · [Suite overview](../README.md)

Convert supported, dimensioned technical drawings into printable 3D models without manually drawing the solid in CAD. The application uses OCR and supported shape templates, not unrestricted reconstruction. Inputs: PNG and single-page PDF.

Supported shapes include rectangular blocks, plates, cylinders, single-step and sloped blocks, a specific rounded 90° bracket, spheres, hemispheres, cones and frustums. Through/blind vertical holes are supported for applicable shapes; limits vary by template.

### Quick start
1. Open a supplied example or prepare a clear drawing with separate FRONT, SIDE and TOP views, dimension labels in English, and millimeter units.
2. Open the drawing and run **Analysis and 3D** (`Анализ и 3D`).
3. Compare recognized dimensions, holes and the 3D preview with the drawing.
4. Export STL or 3MF and inspect it in the slicer at actual size.

Use the included examples and original [drawing syntax guide](README_RU.txt). Do not use this application for safety-critical parts; unsupported geometry and OCR errors may produce incorrect results. Threads, arbitrary freeform shapes and general machining features are not supported.

### Windows installation and source build

Install `DrawingMaker3D-Setup-0.6.0-x64.exe` from Releases once uploaded. No separate build tools are required for the installed application. To build: Python 3.12 x64, Tesseract OCR with English language data, and Inno Setup 6; internet for dependencies. The build script packages Python and Tesseract and runs self-tests before producing the installer. Run `BUILD_SETUP.bat`; the installer is expected in `dist/`. See the [original build guide (Russian)](README_BUILD_RU.txt).
