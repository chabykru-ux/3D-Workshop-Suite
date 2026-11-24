# FurnitureMaker 3D — 0.2.3

[Русский](README.ru.md) · [Suite overview](../README.md)

Generate parametrically sized furniture miniatures for reusable physical mock-ups and digital layout planning. Create base cabinets, wall cabinets, tall units, drawers, doors, niches, 45° and 90° corner cabinets and four countertop shapes (including a diagonal inner corner).

### Quick start
1. Choose a template and enter real furniture dimensions in millimeters and the model scale (default 1:20).
2. Configure sections, doors, drawers, handles, feet or plinth, and colors. Section heights must add up to the body height.
3. Save the module or export the reusable JSON library. Back up your library regularly.
4. Export STL or multicolor 3MF for the slicer, or import a furniture JSON project/library into Furniture Planner 3D for automatic scale recovery.

The application produces scale models, not furniture production cut lists. Door and drawer shapes are fixed, not moving parts. Open niches are not supported for corner cabinets. Check model printability, supports and dimensions; the displayed volume is geometric volume, not filament consumption.

### Windows installation and source build

Install `FurnitureMaker3D-Setup-0.2.3-x64.exe` from Releases once uploaded. No separate build tools are required for the installed application. To build: Node.js LTS with npm and internet for build dependencies. The script uses Electron and electron-builder. Run `BUILD_SETUP.bat`; the installer is expected in `dist/`. See the [original build guide (Russian)](README_WINDOWS_RU.txt).
