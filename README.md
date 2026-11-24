# 3D Workshop Suite

[Русский](README.ru.md)

**Four independent Windows desktop tools for 3D printing, furniture scale models and assembly planning.**

Designed for small workshops, furniture makers and individual 3D-printing users who prefer focused tools to a large CAD suite. No account, ads or subscription required by the applications. Installed applications are designed to work offline.

## Applications

| Application | Version | Purpose |
| --- | --- | --- |
| [PlaqueMaker 3D](01_PlaqueMaker3D/README.md) | 1.3.1 | Nameplates, signs and custom labels for 3D printing |
| [DrawingMaker 3D](02_DrawingMaker3D/README.md) | 0.6.0 (FIXED3 build) | Convert supported technical drawings to printable 3D models |
| [FurnitureMaker 3D](03_FurnitureMaker3D/README.md) | 0.2.3 | Generate reusable scale-model furniture modules |
| [Furniture Planner 3D](04_FurniturePlanner3D/README.md) | 0.1.3 | Arrange furniture modules and print numbered assembly layouts |

## A practical workflow

1. Measure the room and sketch the initial arrangement.
2. Create cabinets and countertops in FurnitureMaker 3D. Save reusable modules in a library.
3. Export models to a slicer for physical scale-model printing, or import the models into Furniture Planner 3D for room layout and paper assembly schemes.
4. Use DrawingMaker 3D for supported simple technical parts and PlaqueMaker 3D for maker labels and signs as needed.

The applications are independent; install only the ones you need. They do not send jobs directly to a 3D printer. Use a compatible slicer, such as Creality Print, to prepare and send STL/3MF files. Furniture Planner prints through the Windows print system or a PDF printer.

## Windows installation

Download the desired Windows x64 Setup.exe from the repository's Releases section once the release assets have been uploaded. Run the installer and follow its prompts. An unsigned installer may trigger Windows SmartScreen; review the publisher and verify the download before running it.

| Installer filename | Version |
| --- | --- |
| `PlaqueMaker3D-Setup-1.3.1-x64.exe` | 1.3.1 |
| `DrawingMaker3D-Setup-0.6.0-x64.exe` | 0.6.0 |
| `FurnitureMaker3D-Setup-0.2.3-x64.exe` | 0.2.3 |
| `FurniturePlanner3D-Setup-0.1.3-x64.exe` | 0.1.3 |

## Build from source

Each application folder contains its own source and `BUILD_SETUP.bat`. Follow its individual build instructions. Internet access is needed to fetch build dependencies. PlaqueMaker, FurnitureMaker and Furniture Planner use Electron; DrawingMaker uses Python, Tesseract OCR, PyInstaller and Inno Setup.

## Scope and limitations

This is a lightweight collection, not a general-purpose CAD/CAM system or a CNC controller. Check all model dimensions and slicing settings before 3D printing. Furniture Planner layouts supplement, rather than replace, production drawings and installation measurements. Application versions retain their existing experimental numbering.

## License and dependencies

The source is included for review. A redistribution license for the project must be selected by its owner before granting open-source rights. Third-party dependencies retain their respective licenses. Windows system fonts are not bundled; use imported fonts only with appropriate rights.
