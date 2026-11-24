from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
import math
import numpy as np
import trimesh
from engine import analyze,load_drawing,make_mesh,export_3mf
B=Path(__file__).parent
p={'shape':'slope','L':100,'W':60,'H':45,'slope':20,'holes':[dict(d=14,x=27,y=30,depth=None),dict(d=10,x=79,y=30,depth=None)]}
def check(m,p):
 L,W,H,low=(p[k] for k in ('L','W','H','slope'));h=lambda x:H+(low-H)*x/L
 vol=L*W*(H+low)/2-sum(math.pi*(a['d']/2)**2*h(a['x']) for a in p['holes'])
 assert m.is_volume and len(m.split())==1 and np.allclose(m.extents,(L,W,H))
 assert math.isclose(m.volume,vol,rel_tol=.0001)
 assert all(np.isclose(z,0) or np.isclose(z,h(x+L/2)) for x,y,z in m.vertices)
with TemporaryDirectory() as t:
 for ext in ('png','pdf'):
  f=B/f'04_sloped_block_2_holes.{ext}';r=analyze(load_drawing(f));assert not r['errors'],r['errors'];assert r['params']==p,r['params'];m=make_mesh(r['params']);check(m,p)
  for fmt in ('stl','3mf'):
   out=Path(t)/f'test.{fmt}'
   if fmt=='stl':m.export(out)
   else:export_3mf(m,out)
   m2=trimesh.load(out,force='mesh');assert m2.is_volume and np.allclose(m2.extents,m.extents) and math.isclose(m2.volume,m.volume,rel_tol=1e-5)
  print(ext,'PASS: OCR, shape, coordinates, top plane, volume, STL and 3MF round-trip')
 for holes in [[],[dict(d=8,x=40,y=25,depth=None)],p['holes']+[dict(d=6,x=50,y=15,depth=None)]]:
  q=deepcopy(p);q['holes']=holes;check(make_mesh(q),q);print('Geometry PASS:',len(holes),'holes')
 for changes in [{'slope':0},{'slope':50},{'holes':[dict(d=10,x=99,y=30,depth=None)]},{'holes':[dict(d=10,x=20,y=30,depth=5)]},{'holes':[dict(d=10,x=20,y=30,depth=None),dict(d=10,x=21,y=30,depth=None)]}]:
  q=deepcopy(p);q.update(changes)
  try:make_mesh(q)
  except ValueError:print('Invalid geometry blocked:',changes)
  else:raise AssertionError(changes)
