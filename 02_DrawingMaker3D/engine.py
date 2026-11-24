"""Constrained drawing reconstruction, v0.6. All model dimensions are in mm."""
import math,re
import cv2,numpy as np,trimesh,pytesseract
from PIL import Image
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from legacy_engine import load_drawing, ocr, associate_views, read_dimensions, value, export_3mf

NUM=r'(\d+(?:[.,]\d+)?)'
def num(s): return float(s.replace(',','.'))

def candidates(bw,allow_triangle=False):
    contours,_=cv2.findContours(bw,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    H,W=bw.shape; out=[]
    for c in contours:
        x,y,w,h=cv2.boundingRect(c); a=cv2.contourArea(c)
        if min(w,h)<max(27,min(H,W)*.025) or w*h<W*H*.002 or w*h>W*H*.75 or a/(w*h)<.35:continue
        poly=cv2.approxPolyDP(c,max(1,cv2.arcLength(c,True)*.003),True)[:,0,:]
        if len(poly)<(3 if allow_triangle else 4):continue
        p=Polygon(poly)
        if p.is_valid and p.area>0:out.append(((x,y,w,h),p))
    return out

def outline_score(poly,r,expected):
    x,y,w,h=r
    # Convert image coordinates into normalized drawing coordinates (Y up).
    p=Polygon([((a-x)/max(w-1,1),1-(b-y)/max(h-1,1)) for a,b in poly.exterior.coords])
    if not p.is_valid:return 0
    return p.intersection(expected).area/p.union(expected).area

def circle_poly(x,y,r):return Point(x,y).buffer(r,quad_segs=48)

def parse_holes(text,L,W,errors):
    holes=[]
    # one explicit HOLE record per line, no implicit center or depth
    records=[]
    for line in text.splitlines():
        m=re.search(r'\bHOLE\b(.*)',line,re.I)
        if m:records.append(m.group(1).strip().upper())
    if len(records)>24:errors.append('Максимум 24 отверстия.');return []
    for i,s in enumerate(records,1):
        s=s.replace('Ø','').replace('⌀','').strip()
        d=re.match(r'(?:DIAMETER\s+)?'+NUM+r'\b',s)
        x=re.search(r'\bX\s*[:=]?\s*'+NUM,s);y=re.search(r'\bY\s*[:=]?\s*'+NUM,s)
        center=bool(re.search(r'\b(?:CENTER|CENTRE|CENTERED)\b',s));thru=bool(re.search(r'\b(?:THRU|THROUGH)\b',s));depth=re.search(r'\bDEPTH\s*[:=]?\s*'+NUM,s)
        if not d or (center and (x or y)) or (not center and not (x and y)) or thru==bool(depth):
            errors.append(f'HOLE {i}: нужно HOLE 10 X 20 Y 15 THRU или HOLE 10 X 20 Y 15 DEPTH 5 (либо CENTER).');continue
        # Refuse unsupported modifiers instead of quietly treating them as a round hole.
        rest=s[d.end():]
        rest=re.sub(r'\b(?:X|Y|DEPTH)\s*[:=]?\s*'+NUM,'',rest)
        rest=re.sub(r'\b(?:CENTER|CENTRE|CENTERED|THRU|THROUGH|MM)\b','',rest).strip()
        if rest or len(re.findall(r'\b(?:X|Y|DEPTH)\b',s)) != sum(bool(v) for v in (x,y,depth)):
            errors.append(f'HOLE {i}: непонятные или повторные обозначения: {rest or s}.');continue
        holes.append(dict(d=num(d[1]),x=L/2 if center else num(x[1]),y=W/2 if center else num(y[1]),depth=None if thru else num(depth[1])))
    return holes

def inner_components(bw,r,poly):
    x,y,w,h=r; crop=bw[y:y+h,x:x+w].copy();mask=np.zeros_like(crop)
    pp=np.array([(a-x,b-y) for a,b in poly.exterior.coords],np.int32)
    cv2.fillPoly(mask,[pp],255);margin=max(4,round(min(w,h)*.055));mask=cv2.erode(mask,np.ones((2*margin+1,2*margin+1),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0);crop=cv2.bitwise_and(crop,mask)
    cs,_=cv2.findContours(crop,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    circles=[]; other=[]
    for c in cs:
        a,b,u,v=cv2.boundingRect(c);area=cv2.contourArea(c);peri=cv2.arcLength(c,True)
        if min(u,v)>=max(9,min(w,h)*.025) and .78<u/v<1.28 and peri>0 and 4*math.pi*area/(peri*peri)>.70 and area/(u*v)>.57:
            circles.append((a+u/2,b+v/2,u,v))
        elif max(u,v)>=max(8,min(w,h)*.04):other.append((a,b,u,v))
    return circles,other

def analyze(im):
    words,text=ocr(im);errors=[];notes=[];params={};overlay=np.array(im).copy()
    gray=cv2.cvtColor(overlay,cv2.COLOR_RGB2GRAY);_,bw=cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    if re.search(r'\b(?:BASE|UPRIGHT)\s+CENTER\s+THRU\b|\bEND[_ ]RADIUS\b',text,re.I):
        from bracket_engine import analyze_bracket
        return analyze_bracket(im,words,text,bw)
    from round_engine import declared,analyze_round
    is_new_round=declared(text)
    cs=candidates(bw,allow_triangle=is_new_round);rects=[r for r,p in cs]
    try:ids=associate_views(rects,words)
    except ValueError as e:ids={};errors.append(str(e))
    if len(cs)==3 and len(ids)<3:
        for i,(x,y,w,h) in enumerate(rects):
            if i in ids.values():continue
            crop=im.crop((max(0,int(x+w*.15)),min(im.height,y+h+3),min(im.width,int(x+w*.85)),min(im.height,y+h+int(h*.35))))
            if crop.width<10 or crop.height<10:continue
            raw=pytesseract.image_to_string(crop,lang='eng',config='--psm 8 -c tessedit_char_whitelist=TOPFRNSIDE',timeout=15).strip().upper()
            if raw in ('TOP','FRONT','SIDE') and raw not in ids:ids[raw]=i;notes.append(f'Повторный OCR: {raw}.')
    def result():return dict(errors=errors,notes=notes,text=text,params=params,overlay=Image.fromarray(overlay))
    if len(cs)!=3:errors.append(f'Найдено внешних контуров: {len(cs)}; ожидаются 3 раздельных замкнутых вида без рамки листа.')
    if set(ids)!= {'TOP','FRONT','SIDE'} or len(set(ids.values()))!=3:
        errors.append('Не удалось сопоставить TOP, FRONT, SIDE. Подпиши каждый вид под контуром.');return result()
    views={k:cs[i][0] for k,i in ids.items()};polys={k:cs[i][1] for k,i in ids.items()}
    for k,p in polys.items():
        cv2.polylines(overlay,[np.array(p.exterior.coords,np.int32)],True,(0,145,155),2)
        x,y,w,h=views[k];cv2.putText(overlay,k,(x,max(18,y-9)),cv2.FONT_HERSHEY_SIMPLEX,.65,(0,100,140),2)
    if is_new_round:
        analyze_round(text,views,polys,bw,overlay,params,errors,notes)
        return result()
    vals=read_dimensions(text,words,views)
    unit=box(0,0,1,1); top_circle=outline_score(polys['TOP'],views['TOP'],circle_poly(.5,.5,.5));top_rect=outline_score(polys['TOP'],views['TOP'],unit)
    declared_round=bool(re.search(r'\b(?:CYLINDER|BODY\s+DIA(?:METER)?)\b',text,re.I))
    round_body=declared_round or (top_circle>.94 and top_rect<.88)
    if round_body:
        ds=value(text,[r'BODY\s+DIA(?:METER)?',r'(?<!HOLE\s)DIAMETER'])
        if len(ds)!=1:errors.append('Цилиндр: укажи BODY DIA 60 (наружный диаметр).')
        else:
            for key in ('L','W'):
                if vals[key] and any(abs(v-ds[0])>1e-6 for v in vals[key]):errors.append(f'Диаметр корпуса противоречит размеру {key}.')
                vals[key]=ds
    for k in ('L','W','H'):
        if len(vals[k])!=1 or not .1<=vals[k][0]<=10000:errors.append(f'Размер {k}: не найден, вне диапазона или противоречив {vals[k]}. Добавь LENGTH, WIDTH, HEIGHT.')
        else:params[k]=vals[k][0]
    if re.search(r'\b(?:INCH|INCHES|CM)\b',text,re.I):errors.append('Нужны миллиметры (MM).')
    if re.search(r'\b(?:THREAD|THREADED|CHAMFER|FILLET|COUNTERSINK|COUNTERBORE|SLOT|NOTCH|TAPER)\b',text,re.I):errors.append('Чертёж содержит обозначение неподдерживаемой геометрии (резьба, фаска, паз и т. п.).')
    if len(params)!=3:return result()
    L,W,H=(params[k] for k in ('L','W','H'));params['shape']='cylinder' if round_body else 'block'
    step=re.findall(r'\bSTEP\s+X\s*'+NUM+r'\s+Z\s*'+NUM,text,re.I)
    if re.search(r'\bSTEP\b',text,re.I) and len(step)!=1:errors.append('Ступень: отдельная строка STEP X 60 Z 20 (слева высокая часть, справа низкая).')
    sx=sz=None
    if len(step)==1:
        sx,sz=map(num,step[0]);params['step']=[sx,sz]
        if round_body or not (0<sx<L and 0<sz<H):errors.append('Ступень допустима только на прямоугольной детали, внутри её размеров.')
        else:params['shape']='step'
    slope=re.findall(r'\bSLOPE\s+Z\s*'+NUM,text,re.I)
    if re.search(r'\bSLOPE\b',text,re.I):
        if len(slope)!=1 or len(re.findall(r'\bSLOPE\b',text,re.I))!=1:
            errors.append('Наклон: отдельная строка SLOPE Z 20 (высота справа).')
        elif round_body or step or not 0<num(slope[0])<H:
            errors.append('Наклон: прямоугольное основание, без ступени; 0 < SLOPE Z < HEIGHT.')
        else:
            params['shape']='slope';params['slope']=num(slope[0])
    exp={'TOP':circle_poly(.5,.5,.5) if round_body else unit,'FRONT':unit,'SIDE':unit}
    if params['shape']=='step':exp['FRONT']=Polygon([(0,0),(1,0),(1,sz/H),(sx/L,sz/H),(sx/L,1),(0,1)])
    if params['shape']=='slope':exp['FRONT']=Polygon([(0,0),(1,0),(1,params['slope']/H),(0,1)])
    for k,a,b in [('TOP',L,W),('FRONT',L,H),('SIDE',W,H)]:
        w,h=views[k][2:];ratio=(w/h)/(a/b)
        if not .70<=ratio<=1.43:errors.append(f'{k}: пропорции не согласуются с размерами.')
        if outline_score(polys[k],views[k],exp[k])<.94:errors.append(f'{k}: внешний контур не соответствует поддерживаемой форме / указанной ступени.')
    holes=parse_holes(text,L,W,errors);params['holes']=holes
    base=circle_poly(L/2,W/2,L/2) if round_body else box(0,0,L,W)
    holepolys=[]
    for i,hole in enumerate(holes,1):
        d,x,y,depth=(hole[k] for k in ('d','x','y','depth'));p=circle_poly(x,y,d/2) if d>0 else Point(x,y)
        if d<=0 or not base.contains(p) or base.boundary.distance(p)<.001:errors.append(f'HOLE {i}: отверстие выходит за пределы детали или касается края.')
        local_h=H
        if params['shape']=='step':
            if abs(x-sx)<=d/2+.001:errors.append(f'HOLE {i}: отверстие пересекает границу ступени или касается её. Перенеси его полностью на один уровень.')
            local_h=H if x<sx else sz
            if depth is not None:errors.append(f'HOLE {i}: глухие отверстия в ступенях пока не поддерживаются; только THRU.')
        if params['shape']=='slope' and depth is not None:errors.append(f'HOLE {i}: для наклона пока только вертикальные сквозные отверстия THRU.')
        if depth is not None and not 0<depth<local_h:errors.append(f'HOLE {i}: DEPTH должна быть больше нуля и меньше местной высоты; для сквозного используй THRU.')
        if any(p.distance(q)<.001 for q in holepolys):errors.append(f'HOLE {i}: отверстия пересекаются или касаются.')
        holepolys.append(p)
    detections={k:inner_components(bw,views[k],polys[k]) for k in views}
    circles,other=detections['TOP'];x,y,w,h=views['TOP']
    if len(circles)!=len(holes):errors.append(f'TOP: окружностей {len(circles)}, строк HOLE {len(holes)}. Укажи каждое отверстие отдельной строкой.')
    unused=list(circles)
    for i,hole in enumerate(holes,1):
        px,py=hole['x']/L,1-hole['y']/W
        if not unused:break
        j=min(range(len(unused)),key=lambda j:math.hypot(unused[j][0]/w-px,unused[j][1]/h-py));cx,cy,u,v=unused.pop(j)
        if abs(cx/w-px)>.045 or abs(cy/h-py)>.045 or not .68<=u/w/(hole['d']/L or 1)<=1.4 or not .68<=v/h/(hole['d']/W or 1)<=1.4:errors.append(f'HOLE {i}: окружность на TOP не совпадает с координатами или диаметром.')
        cv2.ellipse(overlay,(round(x+cx),round(y+cy)),(round(u/2),round(v/2)),0,0,360,(0,145,155),2)
    def step_line(items,axis,expected):
        if axis=='x':return bool(items) and all(u<=max(8,w*.045) and abs((a+u/2)/w-expected)<.05 for a,b,u,v in items) and sum(v for a,b,u,v in items)>.60*h
        return False
    if params['shape']=='step':
        if not step_line(other,'x',sx/L):errors.append('TOP: нужна видимая вертикальная линия ступени в позиции STEP X.')
    elif other:errors.append('TOP: дополнительные внутренние линии не поддерживаются (не рисуй осевые линии и размеры внутри вида).')
    for k,span in [('FRONT',L),('SIDE',W)]:
        cir,others=detections[k]; _,_,vw,vh=views[k]
        if cir:errors.append(f'{k}: обнаружены неизвестные окружности.')
        if params['shape']=='step' and k=='SIDE':
            # right-hand view: visible line at low platform height
            if not others or not all(v<=max(8,vh*.045) and abs((b+v/2)/vh-(1-sz/H))<.06 for a,b,u,v in others) or sum(u for a,b,u,v in others)<.6*vw:errors.append('SIDE: нужна горизонтальная линия на высоте STEP Z (вид справа).')
            continue
        edges=[]
        for hole in holes:
            pos=hole['x'] if k=='FRONT' else hole['y'];d=hole['d'];depth=hole['depth']
            edges.extend([(pos-d/2,pos+d/2,depth)])
        # Hidden lines optional; if drawn, they must agree with known hole boundaries/depth.
        for a,b,u,v in others:
            cx=(a+u/2)/vw;cy=(b+v/2)/vh
            vertical=u<=max(8,vw*.045) and any(min(abs(cx-lo/span),abs(cx-hi/span))<.055 and (dep is None or (b+v)/vh<=dep/H+.09) for lo,hi,dep in edges)
            horizontal=v<=max(8,vh*.045) and any(dep is not None and abs(cy-dep/H)<.065 and a/vw>=lo/span-.065 and (a+u)/vw<=hi/span+.065 for lo,hi,dep in edges)
            if params['shape']=='slope' and k=='SIDE' and v<=max(8,vh*.045) and abs(cy-(1-params['slope']/H))<.06 and u>.6*vw:continue
            if not (vertical or horizontal):errors.append(f'{k}: внутренняя линия не соответствует указанным отверстиям.');break
    if not errors:notes.append('Форма: '+{'block':'прямоугольный блок','cylinder':'цилиндр','step':'одна ступень','slope':'наклонная верхняя плоскость'}[params['shape']]+f'; отверстий: {len(holes)}.')
    notes.append('Ограниченное распознавание: обязательно сверь размеры, координаты и геометрию перед печатью.')
    return result()


def make_mesh(p):
    L,W,H=(p[k] for k in ('L','W','H'));shape=p.get('shape','block');holes=p.get('holes',[])
    if shape in ('sphere','hemisphere','cone','frustum'):
        from round_engine import make_round
        return make_round(p)
    if shape=='bracket':
        from bracket_engine import make_bracket
        return make_bracket(p)
    # Compatibility with original single-hole parameters.
    if 'D' in p and not holes:holes=[dict(d=p['D'],x=L/2,y=W/2,depth=None)]
    base=circle_poly(L/2,W/2,L/2) if shape=='cylinder' else box(0,0,L,W)
    if shape=='slope':
        mesh=sloped_holes_mesh(p,holes)
    elif shape=='step' and holes:
        mesh=stepped_holes_mesh(p,holes)
    elif shape=='step':
        sx,sz=p['step']; profile=Polygon([(0,0),(L,0),(L,sz),(sx,sz),(sx,H),(0,H)])
        mesh=extruded_profile(profile,W)
        # profile x,z extruded along y; mapping reverses orientation, corrected below
        mesh.vertices=mesh.vertices[:,[0,2,1]]
    else:
        hp=[(circle_poly(h['x'],h['y'],h['d']/2),0 if h['depth'] is None else H-h['depth']) for h in holes]
        levels=sorted({0,H,*[z for _,z in hp]});sections=[]
        for lo,hi in zip(levels,levels[1:]):
            active=[poly for poly,z in hp if z<=(lo+hi)/2];sections.append(base.difference(unary_union(active)) if active else base)
        vertices=[];faces=[]
        def triangle(coords,z):
            i=len(vertices);vertices.extend((x,y,z) for x,y in coords);faces.append((i,i+1,i+2))
        def caps(poly,z):
            if poly.is_empty:return
            if poly.geom_type!='Polygon':
                for sub in poly.geoms:caps(sub,z)
                return
            for t in constrained_delaunay_triangles(poly).geoms:triangle(list(t.exterior.coords)[:3],z)
        def walls(poly,lo,hi):
            for ring in [poly.exterior,*poly.interiors]:
                for a,b in zip(ring.coords,list(ring.coords)[1:]):
                    i=len(vertices);vertices.extend([(*a,lo),(*b,lo),(*b,hi),(*a,hi)]);faces.extend([(i,i+1,i+2),(i,i+2,i+3)])
        caps(sections[0],0);caps(sections[-1],H)
        for i,poly in enumerate(sections):
            if poly.geom_type!='Polygon' or not poly.is_valid:raise ValueError('Недопустимое поперечное сечение.')
            walls(poly,levels[i],levels[i+1])
            if i:caps(sections[i-1].symmetric_difference(poly),levels[i])
        mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
    mesh.apply_translation([-L/2,-W/2,0]);mesh.fix_normals()
    if not mesh.is_watertight or not mesh.is_winding_consistent or mesh.volume<=0 or len(mesh.split(only_watertight=False))!=1:raise ValueError('Модель не является единым замкнутым телом. Экспорт запрещён.')
    return mesh


def extruded_profile(poly,height):
    vertices=[];faces=[]
    for t in constrained_delaunay_triangles(poly).geoms:
        coords=list(t.exterior.coords)[:3]
        for z in (0,height):
            i=len(vertices);vertices.extend((*a,z) for a in coords);faces.append((i,i+1,i+2))
    for a,b in zip(poly.exterior.coords,list(poly.exterior.coords)[1:]):
        i=len(vertices);vertices.extend([(*a,0),(*b,0),(*b,height),(*a,height)]);faces.extend([(i,i+1,i+2),(i,i+2,i+3)])
    return trimesh.Trimesh(vertices=vertices,faces=faces,process=True)


def stepped_holes_mesh(p,holes):
    """Two disjoint height regions joined without internal faces. Through holes only."""
    L,W,H=(p[k] for k in ('L','W','H'));sx,sz=p['step']
    left=box(0,0,sx,W);right=box(sx,0,L,W)
    cuts=[]
    for h in holes:
        d,x,y=h['d'],h['x'],h['y']
        if d<=0 or h['depth'] is not None or abs(x-sx)<=d/2+.001:raise ValueError('Ступень: только сквозные отверстия внутри одного уровня.')
        poly=circle_poly(x,y,d/2);region=left if x<sx else right
        if not region.contains(poly) or region.boundary.distance(poly)<.001 or any(poly.distance(q)<.001 for q in cuts):raise ValueError('Отверстия пересекаются или выходят за край уровня.')
        cuts.append(poly)
    for poly in cuts:
        if poly.centroid.x<sx:left=left.difference(poly)
        else:right=right.difference(poly)
    # Build bottom and top as separate regional caps; common bottom edge
    # is shared by the two sets of triangles. Split the tall wall at z=sz
    # to match the shorter wall, skipping internal faces along x=sx.
    V=[];F=[]
    def face(pts):
        i=len(V);V.extend(pts);F.append((i,i+1,i+2))
    def cap(poly,z):
        for t in constrained_delaunay_triangles(poly).geoms:face([(*a,z) for a in list(t.exterior.coords)[:3]])
    def walls(poly,lo,hi,skip_interface):
        for ring in [poly.exterior,*poly.interiors]:
            c=list(ring.coords)
            for a,b in zip(c,c[1:]):
                if skip_interface and abs(a[0]-sx)<1e-8 and abs(b[0]-sx)<1e-8:continue
                face([(*a,lo),(*b,lo),(*b,hi)]);face([(*a,lo),(*b,hi),(*a,hi)])
    cap(left,0);cap(right,0);cap(left,H);cap(right,sz)
    walls(left,0,sz,True);walls(right,0,sz,True);walls(left,sz,H,False)
    return trimesh.Trimesh(vertices=V,faces=F,process=True)


def sloped_holes_mesh(p,holes):
    """One continuous planar top, horizontal bottom, vertical through bores.
    Triangulate the perforated XY footprint and lift the top onto z(x).
    No Boolean unions or internal faces; the top and bottom share ring vertices.
    """
    L,W,H=(float(p[k]) for k in ('L','W','H'));low=float(p['slope'])
    if not all(math.isfinite(v) for v in (L,W,H,low)) or min(L,W)<=0 or not 0<low<H:
        raise ValueError('Неверные размеры наклонной детали.')
    if len(holes)>24:raise ValueError('Максимум 24 отверстия.')
    base=box(0,0,L,W);cuts=[]
    for h in holes:
        d,x,y=(float(h[k]) for k in ('d','x','y'))
        if not all(math.isfinite(v) for v in (d,x,y)) or d<=0 or h['depth'] is not None:
            raise ValueError('Наклон: допустимы только вертикальные сквозные отверстия.')
        c=circle_poly(x,y,d/2)
        if not base.contains(c) or base.boundary.distance(c)<.001 or any(c.distance(q)<.001 for q in cuts):
            raise ValueError('Отверстия пересекаются или выходят за пределы детали.')
        cuts.append(c)
    poly=base.difference(unary_union(cuts)) if cuts else base
    if poly.geom_type!='Polygon' or not poly.is_valid:raise ValueError('Недопустимый контур.')
    V=[];F=[]
    def face(pts):
        i=len(V);V.extend(pts);F.append((i,i+1,i+2))
    def top(a):return (a[0],a[1],H+(low-H)*a[0]/L)
    for t in constrained_delaunay_triangles(poly).geoms:
        c=list(t.exterior.coords)[:3];face([(*a,0) for a in c]);face([top(a) for a in c])
    for ring in [poly.exterior,*poly.interiors]:
        c=list(ring.coords)
        for a,b in zip(c,c[1:]):
            face([(*a,0),(*b,0),top(b)]);face([(*a,0),top(b),top(a)])
    return trimesh.Trimesh(vertices=V,faces=F,process=True)
