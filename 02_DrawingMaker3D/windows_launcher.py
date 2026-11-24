import os, sys, traceback
from pathlib import Path
from tempfile import TemporaryDirectory

BASE = Path(__file__).resolve().parent

def configure_ocr():
    if getattr(sys, 'frozen', False):
        ocr = BASE / 'tesseract'
        if not (ocr / 'tesseract.exe').is_file() or not (ocr / 'tessdata' / 'eng.traineddata').is_file():
            raise RuntimeError('Bundled OCR is missing. Reinstall DrawingMaker 3D.')
        os.environ['TESSERACT_EXE'] = str(ocr / 'tesseract.exe')
        os.environ['TESSDATA_PREFIX'] = str(ocr / 'tessdata')

def smoke_test(report):
    lines = []
    try:
        configure_ocr()
        import tkinter as tk
        import trimesh, numpy as np
        from app import App
        from engine import load_drawing, analyze, make_mesh, export_3mf
        root = tk.Tk(); root.withdraw(); app = App(root); root.update_idletasks(); root.destroy(); app.pool.shutdown()
        files = sorted(BASE.glob('*.png')) + sorted(BASE.glob('*.pdf'))
        files = [p for p in files if p.name != 'icon.png']
        if len(files) != 25:
            raise RuntimeError(f'Expected 25 sample drawings, found {len(files)}')
        with TemporaryDirectory() as tmp:
            for path in files:
                result = analyze(load_drawing(path))
                if result['errors']:
                    raise RuntimeError(f'{path.name}: {result["errors"]}')
                mesh = make_mesh(result['params'])
                if not mesh.is_volume or len(mesh.split()) != 1:
                    raise RuntimeError(f'{path.name}: invalid mesh')
                for fmt in ('stl', '3mf'):
                    target = Path(tmp) / (path.stem + '.' + fmt)
                    if fmt == 'stl': mesh.export(target)
                    else: export_3mf(mesh, target)
                    restored = trimesh.load(target, force='mesh')
                    if not restored.is_volume or not np.allclose(restored.extents, mesh.extents, atol=1e-5) or not np.isclose(restored.volume, mesh.volume, rtol=1e-5):
                        raise RuntimeError(f'{path.name}: {fmt} round-trip failed')
                lines.append(f'PASS {path.name} (OCR, geometry, STL, 3MF)')
                report.write_text('\n'.join(lines), encoding='utf-8')
        report.write_text('\n'.join(lines + ['ALL TESTS PASSED']), encoding='utf-8')
        return 0
    except Exception:
        report.write_text('\n'.join(lines + [traceback.format_exc()]), encoding='utf-8')
        return 1

def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        return smoke_test(Path(sys.argv[2]))
    try:
        configure_ocr()
        import tkinter as tk
        from app import App
        root = tk.Tk()
        if (BASE / 'DrawingMaker3D.ico').exists(): root.iconbitmap(str(BASE / 'DrawingMaker3D.ico'))
        App(root)
        root.mainloop()
        return 0
    except Exception:
        import tkinter.messagebox as mb
        mb.showerror('DrawingMaker 3D', traceback.format_exc())
        return 1

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    sys.exit(main())
