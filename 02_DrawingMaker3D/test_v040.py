from pathlib import Path
from tempfile import TemporaryDirectory
import math
import numpy as np
import trimesh
from engine import analyze,load_drawing,make_mesh,export_3mf
B=Path(__file__).parent
cases={'example_drawing':(100,60,40),'example_multiple':(100,60,35),'example_cylinder':(60,60,30),'example_step':(100,60,40),'example_bracket':(20,15,20),'01_plate_5_holes':(100,70,24),'02_round_flange_5_holes':(80,80,18),'03_stepped_block_2_holes':(100,60,45)}
with TemporaryDirectory() as t:
 for name,dims in cases.items():
  for ext in ('png','pdf'):
   f=B/f'{name}.{ext}'
   if not f.exists():continue
   r=analyze(load_drawing(f));assert not r['errors'],(f,r['errors'])
   m=make_mesh(r['params']);assert m.is_volume and len(m.split())==1 and np.allclose(m.extents,dims),(f,m.extents)
   if name.startswith('03_'):
    expected=55*60*45+45*60*20-math.pi*(7**2*45+5**2*20)
    assert math.isclose(m.volume,expected,rel_tol=.0001)
   for fmt in ('stl','3mf'):
    out=Path(t)/f'{name}.{fmt}'
    if fmt=='stl':m.export(out)
    else:export_3mf(m,out)
    m2=trimesh.load(out,force='mesh');assert m2.is_volume and np.allclose(m2.extents,dims,atol=1e-4) and math.isclose(m2.volume,m.volume,rel_tol=.0001),(f,fmt)
   print(f.name,'PASS: closed solid, dimensions, STL and 3MF round-trip',flush=True)
 p={'shape':'step','L':100,'W':60,'H':45,'step':[55,20]}
 for holes in [[(10,20,20)],[(12,80,20)],[(10,20,20),(12,30,40),(8,75,15),(10,85,40)]]:
  p['holes']=[dict(d=d,x=x,y=y,depth=None) for d,x,y in holes];m=make_mesh(p)
  vol=55*60*45+45*60*20-sum(math.pi*(d/2)**2*(45 if x<55 else 20) for d,x,y in holes)
  assert m.is_volume and math.isclose(m.volume,vol,rel_tol=.0001)
  print('Additional geometry:',len(holes),'holes PASS',flush=True)
 for hole in [dict(d=10,x=55,y=30,depth=None),dict(d=10,x=20,y=30,depth=5),dict(d=10,x=98,y=30,depth=None)]:
  p['holes']=[hole]
  try:make_mesh(p)
  except ValueError:pass
  else:raise AssertionError(hole)
  print('Invalid geometry blocked:',hole,flush=True)
