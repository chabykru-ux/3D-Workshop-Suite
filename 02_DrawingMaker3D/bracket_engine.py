"""Explicit rounded L bracket profile; conservative matching of labelled views."""
import math,re
import cv2,numpy as np,trimesh
from PIL import Image
from shapely.geometry import Polygon,Point,box
from shapely import constrained_delaunay_triangles
from legacy_engine import value

NUM=r'(\d+(?:[.,]\d+)?)'
def rounded_profile(L,W,R):
    # circular cap tangent only for semicircular end; R=W/2 by contract
    a=np.linspace(-math.pi/2,math.pi/2,97)
    return Polygon([(0,0),*[(L-R+R*math.cos(t),W/2+R*math.sin(t)) for t in a],(0,W)])

def analyze_bracket(im,words,text,bw):
    errors=[];notes=[];p={};overlay=np.array(im).copy()
    def result():return dict(errors=errors,notes=notes,text=text,params=p,overlay=Image.fromarray(overlay))
    for k,label in [('L','LENGTH'),('W','WIDTH'),('H','HEIGHT'),('T','THICKNESS'),('R','END[_ ]RADIUS')]:
        vals=value(text,[label]);
        if len(vals)!=1 or not .1<=vals[0]<=10000:errors.append(f'{label}: нужен один точный размер в мм.')
        else:p[k]=vals[0]
    if errors:return result()
    L,W,H,T,R=(p[k] for k in ('L','W','H','T','R'));p['shape']='bracket'
    if abs(R-W/2)>1e-6 or not (T<min(L,H)-R and R>0):errors.append('Уголок v0.3: оба конца полукруглые, END_RADIUS = WIDTH/2; толщина меньше прямой части.')
    if re.search(r'\b(?:THREAD|CHAMFER|FILLET|COUNTERSINK|COUNTERBORE|SLOT|NOTCH|TAPER|DEPTH|INCH|CM)\b',text,re.I):errors.append('Уголок v0.3: только цилиндрические сквозные отверстия, без дополнительных элементов; единицы мм.')
    holes=[]
    for line in text.splitlines():
        if not re.search(r'\bHOLE\b',line,re.I):continue
        s=re.split(r'\bHOLE\b',line,flags=re.I)[1].strip().upper()
        m=re.fullmatch(NUM+r'\s+(BASE|UPRIGHT)\s+CENTER\s+THRU',s)
        if not m:errors.append('Уголок: HOLE 5 BASE CENTER THRU или HOLE 5 UPRIGHT CENTER THRU.');continue
        d=float(m[1].replace(',','.'));face=m[2];u=(L if face=='BASE' else H)/2
        if not (0<d and u-d/2>T and d<W):errors.append(f'{face}: отверстие пересекает край или сгиб.')
        holes.append(dict(d=d,face=face,u=u,x=u,y=W/2,depth=None))
    if sorted(h['face'] for h in holes)!=['BASE','UPRIGHT']:errors.append('Для этого шаблона нужно ровно по одному отверстию BASE и UPRIGHT.')
    p['holes']=holes
    if errors:return result()
    labels={}
    for w in words:
        k=re.sub('[^A-Z]','',w['t'].upper())
        if k in ('TOP','FRONT','SIDE'):
            if k in labels:errors.append(f'Повторная подпись {k}.')
            labels[k]=(w['x']+w['w']/2,w['y']+w['h']/2)
    if set(labels)!= {'TOP','FRONT','SIDE'}:errors.append('Нужны три подписи TOP, FRONT, SIDE под видами.');return result()
    # Match actual outlines to three different normalized templates, with gentle gap repair.
    # L-profile has intentionally low fill ratio. Do not discard it by area ratio.
    expected={'TOP':rounded_profile(L,W,R),'FRONT':Polygon([(0,0),(W,0),*[(W/2+R*math.cos(a),H-R+R*math.sin(a)) for a in np.linspace(0,math.pi,97)],(0,0)]),'SIDE':Polygon([(0,0),(L,0),(L,T),(T,T),(T,H),(0,H)])}
    spans={'TOP':(L,W),'FRONT':(W,H),'SIDE':(L,H)}
    Hpx,Wpx=bw.shape; scale=max(1,round(min(Hpx,Wpx)/1086)); candidates=[]
    for o,c in [(1,1),(3,7),(3,13),(4,19),(5,25)]:
        k1=max(1,o*scale); k2=max(1,c*scale)
        mask=cv2.morphologyEx(bw,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k1,k1)))
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k2,k2)))
        cs,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for co in cs:
            x,y,w,h=cv2.boundingRect(co)
            if min(w,h)<min(Hpx,Wpx)*.09 or w*h>Wpx*Hpx*.65:continue
            poly=cv2.approxPolyDP(co,max(1,cv2.arcLength(co,True)*.002),True)[:,0,:]
            if len(poly)<4:continue
            q=Polygon([((a-x)/max(w-1,1),1-(b-y)/max(h-1,1)) for a,b in poly]).buffer(0)
            if not q.is_empty:candidates.append(((x,y,w,h),poly,q))
    from shapely.affinity import scale as sc
    chosen={}
    for k,(cx,cy) in labels.items():
        a,b=spans[k];target=sc(expected[k],xfact=1/a,yfact=1/b,origin=(0,0)); options=[]
        for r,poly,q in candidates:
            x,y,w,h=r
            if not (abs(cx-x-w/2)<w*.38 and -.025*h<cy-y-h<h*.65 and .70<(w/h)/(a/b)<1.40):continue
            score=q.intersection(target).area/q.union(target).area
            options.append((score,r,poly))
        if not options:errors.append(f'{k}: подходящий контур не найден.');continue
        score,r,poly=max(options,key=lambda a:a[0]); limit=.65 if k=='SIDE' else .88
        if score<limit:errors.append(f'{k}: контур не похож на заданный профиль (совпадение {score:.0%}).');continue
        chosen[k]=r;cv2.polylines(overlay,[poly.astype(np.int32)],True,(0,145,155),2);notes.append(f'{k}: контур сопоставлен ({score:.0%}).')
    if len(chosen)!=3:return result()
    # OCR may merge graphic annotations with the record lines, but the declared diameters
    # must agree approximately with actual circular contours (drawing need not be exact scale).
    cs,_=cv2.findContours(bw,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    for hole in holes:
        k='TOP' if hole['face']=='BASE' else 'FRONT';x,y,w,h=chosen[k];a,b=spans[k]
        target=(hole['u']/L,.5) if k=='TOP' else (.5,1-hole['u']/H)
        found=[]
        for co in cs:
            xx,yy,ww,hh=cv2.boundingRect(co);ar=cv2.contourArea(co);per=cv2.arcLength(co,True)
            if min(ww,hh)<8 or not .75<ww/hh<1.33 or not per or 4*math.pi*ar/(per*per)<.65:continue
            px=(xx+ww/2-x)/w;py=(yy+hh/2-y)/h
            if .08<px<.92 and .08<py<.92 and .60<ww/w/(hole['d']/a)<1.45 and .60<hh/h/(hole['d']/b)<1.45:found.append((px,py,xx,yy,ww,hh))
        matches=[v for v in found if abs(v[0]-target[0])<.12 and abs(v[1]-target[1])<.12]
        if not matches:errors.append(f'{k}: отверстие не подтверждено по рисунку.');continue
        if any(abs(v[0]-target[0])>=.12 or abs(v[1]-target[1])>=.12 for v in found):errors.append(f'{k}: дополнительная окружность не описана.');continue
        _,_,xx,yy,ww,hh=matches[0];cv2.ellipse(overlay,(xx+ww//2,yy+hh//2),(ww//2,hh//2),0,0,360,(0,145,155),2)
    notes.append('Шаблон: уголок 90°, полукруглые концы, два центральных сквозных отверстия. CENTER означает центр полного габарита полки. Без зенковок и радиуса сгиба. Сверь с исходным чертежом.')
    return result()

def make_bracket(p):
    L,W,H,T,R=(p[k] for k in ('L','W','H','T','R'))
    holes={h['face']:h for h in p['holes']}
    def circle(u,v,d):return Point(u,v).buffer(d/2,quad_segs=48)
    # Split the solid at the shared rectangular interface z=T. Create only external faces.
    base=rounded_profile(L,W,R); h=holes['BASE'];base=base.difference(circle(h['u'],h['y'],h['d']))
    exposed=base.difference(box(0,0,T,W))
    # Add vertices at x=T on the base perimeter to ensure matching triangulation.
    outer=list(base.exterior.coords)[:-1];out=[]
    for a,b in zip(outer,outer[1:]+outer[:1]):
        out.append(a)
        if min(a[0],b[0])<T<max(a[0],b[0]):out.append((T,a[1]+(b[1]-a[1])*(T-a[0])/(b[0]-a[0])))
    base=Polygon(out,[list(r.coords) for r in base.interiors]);h=holes['UPRIGHT']
    upright=Polygon([(0,T),(W,T),*[(W/2+R*math.cos(a),H-R+R*math.sin(a)) for a in np.linspace(0,math.pi,97)],(0,T)]).difference(circle(h['y'],h['u'],h['d']))
    V=[];F=[]
    def face(points):
        j=len(V);V.extend(points);F.append((j,j+1,j+2))
    def cap(poly,z,mapfn):
        for tr in constrained_delaunay_triangles(poly).geoms:face([mapfn(a,b,z) for a,b in list(tr.exterior.coords)[:3]])
    def walls(poly,lo,hi,mapfn,skip=None):
        for ring in [poly.exterior,*poly.interiors]:
            coords=list(ring.coords)
            for a,b in zip(coords,coords[1:]):
                if skip and skip(a,b):continue
                aa=mapfn(*a,lo);bb=mapfn(*b,lo);cc=mapfn(*b,hi);dd=mapfn(*a,hi);face([aa,bb,cc]);face([aa,cc,dd])
    bmap=lambda x,y,z:(x,y,z);umap=lambda y,z,x:(x,y,z)
    cap(base,0,bmap);cap(exposed,T,bmap);walls(base,0,T,bmap)
    cap(upright,0,umap);cap(upright,T,umap);walls(upright,0,T,umap,lambda a,b:abs(a[1]-T)<1e-8 and abs(b[1]-T)<1e-8)
    m=trimesh.Trimesh(vertices=V,faces=F,process=True);m.apply_translation([-L/2,-W/2,0]);m.fix_normals()
    if not m.is_volume or len(m.split(only_watertight=False))!=1:raise ValueError('Уголок: сетка не является единым замкнутым телом.')
    return m
