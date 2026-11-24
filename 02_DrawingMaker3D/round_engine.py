import math,re
import cv2,numpy as np,trimesh
from shapely.geometry import Polygon
from legacy_engine import value
SHAPES={'SPHERE':'sphere','HEMISPHERE':'hemisphere','CONE':'cone','FRUSTUM':'frustum'}
NAMES={'sphere':'Шар','hemisphere':'Полушарие','cone':'Конус','frustum':'Усечённый конус'}
def declared(text):return bool(re.search(r'\b(?:SPHERE|HEMISPHERE|CONE|FRUSTUM)\b',text,re.I))
def analyze_round(text,views,polys,bw,overlay,params,errors,notes):
    from engine import circle_poly,outline_score,inner_components
    found=re.findall(r'\bSHAPE\s*[:=]?\s*(SPHERE|HEMISPHERE|CONE|FRUSTUM)\b',text,re.I)
    if len(found)!=1 or len(re.findall(r'\bSHAPE\b',text,re.I))!=1:
        errors.append('Укажи одну строку SHAPE SPHERE / HEMISPHERE / CONE / FRUSTUM.');return
    shape=SHAPES[found[0].upper()]
    if re.search(r'\b(?:HOLE|DEPTH|THREAD|THREADED|CHAMFER|FILLET|COUNTERSINK|COUNTERBORE|SLOT|NOTCH|STEP|SLOPE|HOLLOW|BORE|INCH|INCHES|CM)\b',text,re.I):errors.append('Новые тела вращения пока сплошные, без отверстий и дополнительных элементов; размеры в MM.')
    ds=value(text,[r'BODY\s+DIA(?:METER)?']);hs=value(text,['HEIGHT']);ts=value(text,[r'TOP\s+DIA(?:METER)?'])
    if len(ds)!=1 or not .1<=ds[0]<=10000 or len(hs)!=1 or not .1<=hs[0]<=10000:
        errors.append('Нужны однозначные BODY DIA и HEIGHT (0.1–10000 мм).');return
    D,H=ds[0],hs[0];R=D/2;top=0
    if shape=='sphere' and not math.isclose(H,D,abs_tol=1e-7):errors.append('Шар: HEIGHT должен равняться BODY DIA.')
    if shape=='hemisphere' and not math.isclose(H,R,abs_tol=1e-7):errors.append('Полушарие: HEIGHT должен равняться половине BODY DIA.')
    if shape=='frustum':
        if len(ts)!=1 or not .1<=ts[0]<D:errors.append('Усечённый конус: нужен TOP DIA, меньше BODY DIA.');return
        top=ts[0]
    elif ts:errors.append('TOP DIA применяется только для FRUSTUM.')
    for key in ('LENGTH','WIDTH'):
        if any(not math.isclose(v,D,abs_tol=1e-7) for v in value(text,[key])):errors.append(f'{key} противоречит BODY DIA.')
    params.update(L=D,W=D,H=H,shape=shape,holes=[])
    if shape=='frustum':params['top_d']=top
    circle=circle_poly(.5,.5,.5)
    if shape=='sphere':side=circle
    elif shape=='hemisphere':side=Polygon([((1+math.cos(a))/2,math.sin(a)) for a in np.linspace(0,math.pi,193)])
    else:side=Polygon([(0,0),(1,0),(.5+top/(2*D),1),(.5-top/(2*D),1)])
    for k in ('TOP','FRONT','SIDE'):
        expected=circle if k=='TOP' else side;x,y,w,h=views[k];ratio=(w/h)/(1 if k=='TOP' else D/H)
        if not .80<=ratio<=1.25:errors.append(f'{k}: пропорции не согласуются с размерами тела вращения.')
        if outline_score(polys[k],views[k],expected)<.94:errors.append(f'{k}: внешний контур не соответствует форме {NAMES[shape]}.')
        circles,other=inner_components(bw,views[k],polys[k])
        if shape=='frustum' and k=='TOP':
            if len(circles)!=1 or other:errors.append('TOP: нужна одна концентрическая окружность TOP DIA.');continue
            a,b,u,v=circles[0]
            if abs(a/w-.5)>.04 or abs(b/h-.5)>.04 or not .78<=u/w/(top/D)<=1.22 or not .78<=v/h/(top/D)<=1.22:errors.append('TOP: верхняя окружность не соответствует TOP DIA или смещена.')
            cv2.ellipse(overlay,(round(x+a),round(y+b)),(round(u/2),round(v/2)),0,0,360,(0,145,155),2)
        elif circles or other:errors.append(f'{k}: лишние внутренние элементы; новые тела вращения сплошные.')
    if not errors:notes.append(f'Форма: {NAMES[shape]}; ось Z. Наружный диаметр {D:g} мм'+(f'; верхний диаметр {top:g} мм.' if shape=='frustum' else '.'))
    notes.append('Сверь форму и размеры перед экспортом. Сфера может требовать поддержек или разделения на половины в слайсере.')
def make_round(p):
    shape=p['shape'];D=float(p['L']);W=float(p['W']);H=float(p['H']);R=D/2
    if not all(math.isfinite(v) and .1<=v<=10000 for v in (D,W,H)) or not math.isclose(D,W,abs_tol=1e-7) or p.get('holes'):raise ValueError('Неверные размеры или отверстия в новом теле вращения.')
    if shape=='sphere':
        if not math.isclose(H,D,abs_tol=1e-7):raise ValueError('Шар: HEIGHT = BODY DIA.')
        a=np.linspace(-math.pi/2,math.pi/2,129);profile=np.column_stack((R*np.cos(a),R*(1+np.sin(a))));profile[0]=[0,0];profile[-1]=[0,D]
    elif shape=='hemisphere':
        if not math.isclose(H,R,abs_tol=1e-7):raise ValueError('Полушарие: HEIGHT = BODY DIA / 2.')
        a=np.linspace(0,math.pi/2,65);profile=np.vstack(([0,0],np.column_stack((R*np.cos(a),R*np.sin(a)))));profile[-1]=[0,H]
    elif shape=='cone':profile=np.array([[0,0],[R,0],[0,H]])
    elif shape=='frustum':
        top=float(p['top_d'])
        if not math.isfinite(top) or not .1<=top<D:raise ValueError('Неверный TOP DIA.')
        profile=np.array([[0,0],[R,0],[top/2,H],[0,H]])
    else:raise ValueError('Неизвестное тело вращения.')
    mesh=trimesh.creation.revolve(profile,sections=192);mesh.fix_normals()
    if not mesh.is_volume or len(mesh.split(only_watertight=False))!=1:raise ValueError('Тело вращения не является единым замкнутым объёмом.')
    return mesh
