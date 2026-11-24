# Furniture Planner 3D — 0.1.3

[Русский](README.ru.md) · [Suite overview](../README.md)

Arrange imported furniture modules in a rectangular room and print a numbered assembly layout from the current 3D viewing angle. Supports STL, 3MF, and FurnitureMaker JSON projects/libraries.

### Quick start
1. Set actual room width X, depth Y and height Z in millimeters.
2. Import the furniture models. For STL/3MF set the original scale denominator (e.g. 20 for 1:20); FurnitureMaker JSON restores the scale automatically.
3. Click `+` to place a module; clicking its library name only selects it.
4. Select a placed module. Bind it to wall A, B, C or D, or to a corner (A–B, B–C, C–D, D–A). Set height and position along the wall. Use free placement for islands or unusual geometry.
5. Set module numbers and save the `.planner.json` project.
6. Rotate the camera to a useful view and select **Print / PDF**. Choose A4/A3, color or black-and-white and optionally include the module list.

### Mouse controls
Left: select/drag; Shift + left: height; right: orbit camera; wheel: zoom; middle: pan.

Walls are fixed: A = rear (+Y), B = right (+X), C = front (Y=0), D = left (X=0). Auto-orientation assumes FurnitureMaker geometry. Snapping uses bounding boxes, and there is no automatic collision detection. The printed layout is supplementary to verified installation dimensions and working drawings.

### Windows installation and source build

Install `FurniturePlanner3D-Setup-0.1.3-x64.exe` from Releases once uploaded. No separate build tools are required for the installed application. To build: Node.js LTS with npm and internet for build dependencies. The script uses Electron and electron-builder. Run `BUILD_SETUP.bat`; the installer is expected in `dist/`. See the [original build guide (Russian)](README_WINDOWS_RU.txt). For ordinary paper/PDF printing in Furniture Planner, use the Windows print dialog.
