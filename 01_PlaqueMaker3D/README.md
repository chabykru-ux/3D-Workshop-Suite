# PlaqueMaker 3D — 1.3.1

[Русский](README.ru.md) · [Suite overview](../README.md)

Create personalized 3D-printable signs, door plates, business cards and maker labels. Choose the standard layout or a layout with a separate right-hand field. Set dimensions, rounded corners, borders, text, fonts, decorative lines and colors. The live 3D preview updates as settings change. Russian, English and Hebrew text are supported when suitable fonts are available.

### Quick start
1. Choose a plaque type and enter its dimensions in millimeters.
2. Enter text, select fonts, and adjust layout and colors. The right-hand field can contain a room number, text or a symbol.
3. Save the editable JSON project if needed.
4. Export 3MF for separate colored parts or STL for single-material geometry.
5. Open in a slicer, assign filament slots, and check fine text and layers before printing.

System fonts depend on Windows. Custom TTF/OTF files can be imported for the current session; they must be imported again when reopening a project that uses them. Thin strokes may not print at small sizes. Recessed text is not a separate colored part.

### Windows installation and source build

Install `PlaqueMaker3D-Setup-1.3.1-x64.exe` from Releases once uploaded. No separate build tools are required for the installed application. To build: Node.js LTS with npm and internet for build dependencies. The script uses Electron and electron-builder. Run `BUILD_SETUP.bat`; the installer is expected in `dist/`. See the [original build guide (Russian)](README_WINDOWS_RU.txt).
