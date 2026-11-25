# Third-party components / Сторонние компоненты

The MIT license in this repository covers the project's own code and documentation. It does not relicense third-party components, dependencies, fonts or assets.

## Declared dependencies and build tools

| Component | Upstream license information | Use |
| --- | --- | --- |
| Electron | [License](https://github.com/electron/electron/blob/main/LICENSE) | Runtime for three desktop applications |
| Chromium and bundled Electron dependencies | [Electron third-party notices](https://www.electronjs.org/docs/latest/tutorial/open-source) | Electron runtime |
| electron-builder | [License](https://github.com/electron-userland/electron-builder/blob/master/LICENSE) | Build tool |
| Python | [License](https://docs.python.org/3/license.html) | DrawingMaker runtime |
| Tesseract OCR | [License](https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE) | DrawingMaker offline OCR |
| Tesseract language data | [License](https://github.com/tesseract-ocr/tessdata/blob/main/LICENSE) | OCR data (verify actual distribution) |
| NumPy | [Upstream](https://github.com/numpy/numpy) | DrawingMaker |
| OpenCV / opencv-python-headless | [Upstream](https://github.com/opencv/opencv-python) | DrawingMaker |
| Pillow | [Upstream](https://github.com/python-pillow/Pillow) | DrawingMaker |
| pytesseract | [Upstream](https://github.com/madmaze/pytesseract) | DrawingMaker |
| pypdfium2 / PDFium | [Upstream](https://github.com/pypdfium2-team/pypdfium2) | DrawingMaker |
| trimesh | [Upstream](https://github.com/mikedh/trimesh) | DrawingMaker |
| Matplotlib | [Upstream](https://github.com/matplotlib/matplotlib) | DrawingMaker |
| SciPy | [Upstream](https://github.com/scipy/scipy) | DrawingMaker |
| Shapely / GEOS | [Upstream](https://github.com/shapely/shapely) | DrawingMaker |
| NetworkX | [Upstream](https://github.com/networkx/networkx) | DrawingMaker |
| lxml | [Upstream](https://github.com/lxml/lxml) | DrawingMaker |
| PyInstaller | [License](https://pyinstaller.org/en/stable/license.html) | Packaging tool and bootloader |
| Inno Setup | [License information](https://jrsoftware.org/isinfo.php) | Windows installer tool |
| NSIS | [License](https://nsis.sourceforge.io/License) | Electron Windows installer technology |

## Binary distribution verification

This list is based on the repository's dependency declarations and build scripts. It is not a complete software bill of materials or a substitute for the actual license texts, copyright notices, source-code offers or other obligations that may apply to distributed binaries. Exact versions and transitive components depend on the actual build. For DrawingMaker, consult the generated `build-dependencies.txt` and the installed runtime/OCR distribution. For Electron applications, retain the shipped Electron and Chromium license files.

Before publishing binaries, inspect the actual four Windows installers and their installed files, identify all bundled components, preserve applicable notices, and satisfy any source-distribution obligations. This verification has not been performed by reviewing the repository alone. Do not assume that a build tool's license applies unchanged to its generated output.

Windows system fonts are not bundled by design; users are responsible for permissions for any imported fonts.

## По-русски

Лицензия MIT распространяется на собственный код и документацию проекта, а не на сторонние библиотеки. Таблица выше составлена по файлам сборки и зависимостей; это не полный список компонентов установщиков и не замена обязательным текстам лицензий. Перед публикацией EXE необходимо проверить фактический состав каждого установщика и сохранить все требуемые уведомления и иные материалы. Полная проверка бинарных файлов пока не выполнена.
