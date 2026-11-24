from pathlib import Path
from tempfile import TemporaryDirectory
import math
import numpy as np
import trimesh
from PIL import ImageDraw,ImageFont
from engine import analyze,load_drawing,make_mesh,export_3mf
B=Path(__file__).parent
cases=[('05_sphere','sphere',40,40,0),('06_hemisphere','hemisphere',60,30,0),('07_cone','cone',50,55,0),('08_frustum','frustum',60,40,30)]
with TemporaryDirectory() as tmp:
 for name,shape,D,H,top in cases:
  R=D/2;rt=top/2
  volume={'sphere':4*math.pi*R**3/3,'hemisphere':2*math.pi*R**3/3,'cone':math.pi*R**2*H/3,'frustum':math.pi*H*(R**2+R*rt+rt**2)/3}[shape]
  for ext in ('png','pdf'):
   path=B/f'{name}.{ext}';r=analyze(load_drawing(path));assert not r['errors'],(path,r['errors'],r['text']);p=r['params'];assert p['shape']==shape and (p['L'],p['W'],p['H'])==(D,D,H)
   m=make_mesh(p);assert m.is_volume and len(m.split())==1 and np.allclose(m.extents,(D,D,H));assert math.isclose(m.volume,volume,rel_tol=.001)
   for fmt in ('stl','3mf'):
    dest=Path(tmp)/f'{name}.{fmt}'
    if fmt=='stl':m.export(dest)
    else:export_3mf(m,dest)
    n=trimesh.load(dest,force='mesh');assert n.is_volume and np.allclose(n.extents,m.extents,atol=1e-5) and math.isclose(n.volume,m.volume,rel_tol=1e-5)
   print(path.name,'PASS: OCR, geometry, volume, watertight, STL + 3MF round-trip',flush=True)
 for p in [dict(shape='sphere',L=40,W=40,H=35),dict(shape='hemisphere',L=60,W=60,H=31),dict(shape='frustum',L=60,W=60,H=40,top_d=70),dict(shape='cone',L=40,W=40,H=50,holes=[{'d':3}])]:
  try:make_mesh(p)
  except ValueError:print('Invalid geometry blocked:',p,flush=True)
  else:raise AssertionError(p)
 im=load_drawing(B/'05_sphere.png');d=ImageDraw.Draw(im);d.rectangle((1010,825,1500,895),fill='white');d.text((1010,825),'HEIGHT 30',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',38),fill='black');r=analyze(im);assert r['errors'],r;print('Contradictory drawing blocked',flush=True)
