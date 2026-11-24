"""DrawingMaker 3D, experimental constrained drawing recognizer, dimensions in mm."""
import os, re, math, shutil, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import pytesseract
import pypdfium2 as pdfium
import trimesh


def setup_ocr():
    candidates=[os.environ.get('TESSERACT_EXE'), shutil.which('tesseract'),
        str(Path(__file__).parent/'tesseract'/'tesseract.exe'),
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        str(Path(os.environ.get('LOCALAPPDATA',''))/'Programs'/'Tesseract-OCR'/'tesseract.exe')]
    for p in candidates:
        if p and Path(p).is_file():
            pytesseract.pytesseract.tesseract_cmd=p
            return
    raise RuntimeError('Не найден Tesseract OCR. Запусти INSTALL_OCR.bat, затем открой программу заново.')


def load_drawing(path):
    if Path(path).suffix.lower()=='.pdf':
        doc=pdfium.PdfDocument(str(path))
        try:
            if len(doc)!=1: raise ValueError('Пока поддерживается PDF из одной страницы. Сохрани три вида на одном листе.')
            page=doc[0]
            try:
                w,h=page.get_size(); scale=min(3.5,2000/max(w,h))
                bitmap=page.render(scale=scale)
                try: im=bitmap.to_pil().convert('RGB').copy()
                finally: bitmap.close()
            finally: page.close()
        finally: doc.close()
    else:
        with Image.open(path) as img:
            rgba=img.convert('RGBA'); white=Image.new('RGBA',rgba.size,'white'); white.alpha_composite(rgba); im=white.convert('RGB')
    if max(im.size)>2400:
        im.thumbnail((2400,2400),Image.Resampling.LANCZOS)
    if max(im.size)<1600:
        factor=1600/max(im.size); im=im.resize(tuple(round(a*factor) for a in im.size),Image.Resampling.LANCZOS)
    return im


def ocr(im):
    setup_ocr()
    d=pytesseract.image_to_data(im,lang='eng',config='--psm 11',output_type=pytesseract.Output.DICT,timeout=45)
    words=[]
    for i,t in enumerate(d['text']):
        if t.strip() and float(d['conf'][i])>=25:
            words.append(dict(t=t.strip(),x=d['left'][i],y=d['top'][i],w=d['width'][i],h=d['height'][i],conf=float(d['conf'][i])))
    # Reassemble spatial lines; Tesseract may split a dimension across sparse-text blocks.
    lines=[]
    for a in sorted(words,key=lambda a:a['y']+a['h']/2):
        cy=a['y']+a['h']/2
        line=next((l for l in lines if abs(cy-l[0])<max(7,a['h']*.55)),None)
        if line is None: lines.append([cy,[a]])
        else: line[1].append(a)
    text='\n'.join(' '.join(a['t'] for a in sorted(l[1],key=lambda a:a['x'])) for l in lines)
    return words,text


def rect_candidates(bw):
    contours,_=cv2.findContours(bw,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    out=[]; H,W=bw.shape
    for c in contours:
        x,y,w,h=cv2.boundingRect(c)
        if min(w,h)<max(35,min(H,W)*.035) or w*h<W*H*.003 or w*h>W*H*.8:continue
        area=abs(cv2.contourArea(c)); peri=cv2.arcLength(c,True)
        if area/(w*h)<.89:continue
        approx=cv2.approxPolyDP(c,.025*peri,True)
        if len(approx)!=4:continue
        if any(abs(float(np.dot(v-u,z-v)))/(np.linalg.norm(v-u)*np.linalg.norm(z-v)+1e-9)>.20 for u,v,z in zip(np.roll(approx[:,0,:],1,axis=0),approx[:,0,:],np.roll(approx[:,0,:],-1,axis=0))):continue
        out.append((x,y,w,h))
    chosen=[]
    for a in sorted(out,key=lambda r:r[2]*r[3],reverse=True):
        x,y,w,h=a
        if any(abs(x-X)<max(9,w*.06) and abs(y-Y)<max(9,h*.06) and abs(w-U)<max(14,w*.10) and abs(h-V)<max(14,h*.10) for X,Y,U,V in chosen):continue
        chosen.append(a)
    return chosen


def associate_views(rects,words):
    labels={}
    for word in words:
        t=re.sub('[^A-Z]','',word['t'].upper())
        if t not in ('TOP','FRONT','SIDE'):continue
        cx=word['x']+word['w']/2; cy=word['y']+word['h']/2
        distances=[]
        for i,(x,y,w,h) in enumerate(rects):
            dx=max(x-cx,0,cx-x-w); dy=max(y-cy,0,cy-y-h)
            dist=math.hypot(dx,dy)+.35*abs(cx-(x+w/2))
            distances.append((dist,i))
        if distances:
            dist,i=min(distances)
            if dist<max(rects[i][2:])*1.2:
                if t in labels and labels[t]!=i:raise ValueError(f'Несколько подписей {t}. Оставь одну подпись для каждого вида.')
                labels[t]=i
    return labels


def value(text,keys):
    matches=[]
    for k in keys:
        for m in re.finditer(r'(?<![A-Z0-9])'+k+r'\s*[:=]?\s*(\d+(?:[.,]\d+)?)\b',text,re.I):
            matches.append(float(m.group(1).replace(',','.')))
    return sorted(set(matches))


def read_dimensions(text,words,views):
    # Explicit named dimensions are preferred. No inference from absolute pixel scale.
    vals={ 'L':value(text,['LENGTH','L']), 'W':value(text,['WIDTH','W']), 'H':value(text,['HEIGHT','H']) }
    # Unlabelled conventional horizontal dimensions near view boundaries. Only accept exact agreement
    # across candidates; otherwise stop rather than select an arbitrary number.
    for name, mappings in {'L':[('TOP',0),('FRONT',0)],'W':[('TOP',1),('SIDE',0)],'H':[('FRONT',1),('SIDE',1)]}.items():
        candidates=[]
        for view,axis in mappings:
            x,y,w,h=views[view]
            for a in words:
                if not re.fullmatch(r'\d+(?:[.,]\d+)?',a['t']) or a['conf']<55:continue
                cx=a['x']+a['w']/2; cy=a['y']+a['h']/2
                if axis==0:
                    valid=abs(cx-x-w/2)<w*.15 and min(abs(cy-y),abs(cy-y-h))<h*.42 and (cy<y or cy>y+h)
                else:
                    valid=abs(cy-y-h/2)<h*.15 and min(abs(cx-x),abs(cx-x-w))<w*.32 and (cx<x or cx>x+w)
                if valid:candidates.append(float(a['t'].replace(',','.')))
        vals[name]=sorted(set(vals[name]+candidates))
    return vals


def detect_inner(bw,rect):
    x,y,w,h=rect; margin=max(6,round(min(w,h)*.035))
    crop=bw[y+margin:y+h-margin,x+margin:x+w-margin].copy()
    if crop.size==0:return [],0,[]
    contours,_=cv2.findContours(crop,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    circles=[]; other=[]
    for c in contours:
        X,Y,W,H=cv2.boundingRect(c); area=cv2.contourArea(c); peri=cv2.arcLength(c,True)
        if min(W,H)>max(13,min(w,h)*.07) and .87<W/H<1.15 and peri>0 and 4*math.pi*area/(peri*peri)>.77 and area/(W*H)>.65:
            circles.append((X+margin+W/2,Y+margin+H/2,(W+H)/4))
        elif max(W,H)>max(11,min(w,h)*.065):other.append((X,Y,W,H))
    return circles,int(np.count_nonzero(crop)),other


def analyze(im):
    words,text=ocr(im)
    errors=[]; notes=[]; params={}; overlay=np.array(im).copy()
    gray=cv2.cvtColor(np.array(im),cv2.COLOR_RGB2GRAY)
    _,bw=cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    # Remove recognized view labels and named dimensions only outside rectangles; geometry detection is independent of OCR.
    rects=rect_candidates(bw)
    try: ids=associate_views(rects,words)
    except ValueError as e: ids={};errors.append(str(e))
    if len(rects)==3 and len(ids)<3:
        for i,(x,y,w,h) in enumerate(rects):
            if i in ids.values():continue
            # A tightly cropped label below a view is more reliable than full-page sparse OCR.
            crop=im.crop((max(0,int(x+w*.15)),min(im.height,y+h+3),min(im.width,int(x+w*.85)),min(im.height,y+h+int(h*.35))))
            if crop.width<10 or crop.height<10:continue
            raw=pytesseract.image_to_string(crop,lang='eng',config='--psm 8 -c tessedit_char_whitelist=TOPFRNSIDE',timeout=15).strip().upper()
            if raw in ('TOP','FRONT','SIDE') and raw not in ids:
                ids[raw]=i;notes.append(f'Подпись {raw} распознана повторным OCR.')
    if len(rects)!=3:errors.append(f'Найдено прямоугольных контуров: {len(rects)}; ожидаются ровно три простых замкнутых вида без сложных вырезов. Проверь линии.')
    if set(ids)!=set(('TOP','FRONT','SIDE')) or len(set(ids.values()))!=3:
        errors.append('Не удалось однозначно сопоставить три вида. Подпиши каждый отдельно: TOP, FRONT, SIDE (латиницей), рядом с контуром.')
        return dict(errors=errors,notes=notes,text=text,params=params,overlay=Image.fromarray(overlay))
    views={k:rects[i] for k,i in ids.items()}
    for k,(x,y,w,h) in views.items():
        cv2.rectangle(overlay,(x,y),(x+w,y+h),(0,145,155),max(2,round(max(im.size)/700)))
        cv2.putText(overlay,k,(x,max(18,y-9)),cv2.FONT_HERSHEY_SIMPLEX,max(.55,max(im.size)/2000),(0,100,140),2)
    vals=read_dimensions(text,words,views)
    for k,name in [('L','длина LENGTH'),('W','ширина WIDTH'),('H','высота HEIGHT')]:
        v=vals[k]
        if len(v)!=1: errors.append(f'Размер {name}: '+('не найден' if not v else f'противоречие {v}')+'. Добавь отдельную подпись, например '+{'L':'LENGTH 100','W':'WIDTH 60','H':'HEIGHT 40'}[k]+'.')
        elif not .1<=v[0]<=10000:errors.append(f'Размер {name} вне диапазона 0.1–10000 мм.')
        else:params[k]=v[0]
    if re.search(r'\b(?:INCH|INCHES|CM)\b',text,re.I):errors.append('Обнаружены другие единицы. Для этой версии нужны миллиметры (MM).')
    if len(params)==3:
        # Check ratios within each projection; drawings need only be approximately proportional.
        for k,a,b in [('TOP','L','W'),('FRONT','L','H'),('SIDE','W','H')]:
            w,h=views[k][2:]; ratio=(w/h)/(params[a]/params[b]);
            if not .70<=ratio<=1.43:errors.append(f'{k}: пропорции контура сильно отличаются от указанных размеров. Проверь размеры и форму.')
    detected={k:detect_inner(bw,r) for k,r in views.items()}
    topcir,_,topother=detected['TOP']
    diam=value(text,['HOLE(?:\\s+DIAMETER)?','DIAMETER','DIA','D','[Ø⌀Φ]'])
    if len(topcir)>1:errors.append('На TOP найдено несколько окружностей. В v0.1 поддерживается одно центральное отверстие.')
    if topother:errors.append('TOP: внутри контура есть дополнительные линии/элементы. v0.1 не поддерживает вырезы, осевые линии и дополнительные элементы внутри TOP; размеры размещай снаружи.')
    if len(topcir)==1:
        cx,cy,r=topcir[0]; x,y,w,h=views['TOP']; cv2.circle(overlay,(round(x+cx),round(y+cy)),round(r),(0,145,155),3)
        if abs(cx-w/2)>w*.055 or abs(cy-h/2)>h*.055:errors.append('Отверстие не выглядит центральным. Смещённые отверстия пока не поддерживаются.')
        if not re.search(r'\b(?:THRU|THROUGH)\b',text,re.I):errors.append('Не указан тип отверстия. Добавь THRU (сквозное) или убери отверстие для первого теста.')
        if not re.search(r'\b(?:CENTER|CENTRE|CENTERED)\b',text,re.I):errors.append('Не подтверждено положение отверстия. Добавь CENTER (если оно действительно в центре).')
        if len(diam)!=1:errors.append('Диаметр отверстия не найден или противоречив. Напиши, например, HOLE 20 THRU CENTER.')
        else:
            d=diam[0]; params['D']=d
            if 'L' in params and 'W' in params:
                if not 0<d<min(params['L'],params['W']):errors.append('Диаметр должен быть меньше длины и ширины.')
                elif not .65<=(2*r/w)/(d/params['L'])<=1.50 or not .65<=(2*r/h)/(d/params['W'])<=1.50:errors.append('Диаметр на рисунке сильно отличается от надписи.')
    elif diam or re.search(r'\b(?:HOLE|THRU|THROUGH)\b',text,re.I):errors.append('Есть обозначение отверстия, но окружность на TOP не распознана.')
    # For simple blocks FRONT/SIDE may contain only symmetric vertical hidden lines for the through hole.
    for k in ('FRONT','SIDE'):
        circles,_,other=detected[k]; x,y,w,h=views[k]
        if circles:errors.append(f'{k}: обнаружены окружности; v0.1 поддерживает отверстие только сверху.')
        if other:
            hidden=bool(len(topcir)==1 and 'D' in params and all(W<=max(10,w*.05) for X,Y,W,H in other))
            if hidden:
                # Each dash must lie on one of the two expected hidden edges, allowing sketch imprecision.
                axis='L' if k=='FRONT' else 'W'; margin=max(6,round(min(w,h)*.035))
                if axis in params:
                    expected=[w/2-w*params['D']/params[axis]/2,w/2+w*params['D']/params[axis]/2]
                    hidden=all(min(abs(X+margin+W/2-e) for e in expected)<w*.075 for X,Y,W,H in other)
                else:hidden=False
            if not hidden:errors.append(f'{k}: обнаружена дополнительная внутренняя геометрия, которую эта версия не понимает.')
    if not errors:notes.append('Распознана прямоугольная деталь'+(' с центральным сквозным отверстием.' if 'D' in params else ' без отверстия.'))
    notes.append('Это ограниченное распознавание; размерные надписи и модель необходимо проверить перед печатью.')
    return dict(errors=errors,notes=notes,text=text,params=params,overlay=Image.fromarray(overlay))


def make_mesh(p):
    L,W,H=p['L'],p['W'],p['H']
    if 'D' not in p:
        mesh=trimesh.creation.box(extents=[L,W,H]);mesh.apply_translation([0,0,H/2]);return mesh
    r=p['D']/2
    angles=sorted(set([i*2*math.pi/128 for i in range(128)]+[math.atan2(y,x)%(2*math.pi) for x in (-L/2,L/2) for y in (-W/2,W/2)]))
    n=len(angles);outer=[];inner=[]
    for a in angles:
        c,s=math.cos(a),math.sin(a);t=min(L/2/max(abs(c),1e-12),W/2/max(abs(s),1e-12));outer.append((t*c,t*s));inner.append((r*c,r*s))
    vertices=[(x,y,z) for z in (0,H) for ring in (outer,inner) for x,y in ring];faces=[]
    for i in range(n):
        j=(i+1)%n; a,b,c,d=i,j,n+i,n+j; A,B,C,D=2*n+i,2*n+j,3*n+i,3*n+j
        faces.extend([(a,c,b),(b,c,d),(A,B,C),(B,D,C),(a,b,A),(b,B,A),(c,C,d),(d,C,D)])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True);mesh.fix_normals()
    if not mesh.is_watertight or not mesh.is_winding_consistent or mesh.volume<=0:raise ValueError('Ошибка построения замкнутой модели.')
    return mesh


def export_3mf(mesh,path):
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
    def tag(x):return '{'+ns+'}'+x
    root=ET.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'});resources=ET.SubElement(root,tag('resources'));obj=ET.SubElement(resources,tag('object'),{'id':'1','type':'model'});m=ET.SubElement(obj,tag('mesh'));v=ET.SubElement(m,tag('vertices'));t=ET.SubElement(m,tag('triangles'))
    for x,y,z in mesh.vertices:ET.SubElement(v,tag('vertex'),dict(x=f'{x:.8f}',y=f'{y:.8f}',z=f'{z:.8f}'))
    for a,b,c in mesh.faces:ET.SubElement(t,tag('triangle'),dict(v1=str(a),v2=str(b),v3=str(c)))
    build=ET.SubElement(root,tag('build'));ET.SubElement(build,tag('item'),{'objectid':'1'})
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
