from pathlib import Path
from tempfile import TemporaryDirectory
import math
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont
from engine import analyze,load_drawing,make_mesh,export_3mf
BASE=Path(__file__).parent
cases={'example_drawing':([100,60,40],100*60*40-math.pi*10**2*40), 'example_multiple':([100,60,35],100*60*35-math.pi*(6**2*35+9**2*12+5**2*35)), 'example_cylinder':([60,60,30],math.pi*(30**2*30-8**2*30-5**2*8)), 'example_step':([100,60,40],60*60*40+40*60*20)}
with TemporaryDirectory() as temp:
    for name,(dims,volume) in cases.items():
        for ext in ('png','pdf'):
            r=analyze(load_drawing(BASE/f'{name}.{ext}'));assert not r['errors'],(name,ext,r['errors'])
            m=make_mesh(r['params']);assert m.is_watertight and m.is_winding_consistent and m.is_volume
            assert np.allclose(m.extents,dims) and math.isclose(m.volume,volume,rel_tol=.001)
            for fmt in ('stl','3mf'):
                p=Path(temp)/f'{name}.{fmt}'
                if fmt=='stl':m.export(p)
                else:export_3mf(m,p)
                imported=trimesh.load(p,force='mesh');assert imported.is_watertight and np.allclose(imported.extents,dims,atol=1e-4) and math.isclose(imported.volume,m.volume,rel_tol=.0001)
            print(name,ext,'PASS',flush=True)
    # Missing or changed hole declaration should fail on original geometry.
    import engine
    real=engine.ocr
    for old,new in [('HOLE 20 THRU CENTER',''),('HOLE 20 THRU CENTER','HOLE 20 X 10 Y 10 THRU'),('HOLE 20 THRU CENTER','HOLE 20 THRU CENTER THREAD'),('LENGTH 100','LENGTH 120'),('HOLE 20 THRU CENTER','HOLE 20 CENTER DEPTH 45')]:
        def mock(im):
            words,text=real(im);return words,text.replace(old,new)
        engine.ocr=mock
        r=analyze(load_drawing(BASE/'example_drawing.png'));assert r['errors'],(old,new,r)
        print('Reject',new or 'missing hole','PASS',flush=True)
    engine.ocr=real
    r=analyze(Image.new('RGB',(1600,1200),'white'));assert r['errors'];print('Blank drawing PASS',flush=True)
