from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import os
B=Path(__file__).parent
FONT=os.environ.get('DRAWING_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
for name,shape,D,H,top in [('05_sphere','SPHERE',40,40,0),('06_hemisphere','HEMISPHERE',60,30,0),('07_cone','CONE',50,55,0),('08_frustum','FRUSTUM',60,40,30)]:
    im=Image.new('RGB',(1900,1300),'white');d=ImageDraw.Draw(im);font=ImageFont.truetype(FONT,38);title=ImageFont.truetype(FONT,44);s=7
    d.text((100,45),'TEST '+name[:2]+' / ALL DIMENSIONS MM',font=title,fill='black')
    for x,label in [(180,'FRONT'),(1150,'SIDE')]:
        y=150;w=D*s;h=H*s
        if shape=='SPHERE':d.ellipse((x,y,x+w,y+h),outline='black',width=5)
        elif shape=='HEMISPHERE':
            d.arc((x,y,x+w,y+2*h),180,360,fill='black',width=5);d.line((x,y+h,x+w,y+h),fill='black',width=5)
        else:d.line([(x,y+h),(x+w/2-top*s/2,y),(x+w/2+top*s/2,y),(x+w,y+h),(x,y+h)],fill='black',width=5,joint='curve')
        d.text((x+w/2,y+h+27),label,font=font,fill='black',anchor='mt')
    x=180;y=675;w=D*s
    d.ellipse((x,y,x+w,y+w),outline='black',width=5)
    if top:
        a=(D-top)*s/2;d.ellipse((x+a,y+a,x+w-a,y+w-a),outline='black',width=5)
    d.text((x+w/2,y+w+25),'TOP',font=font,fill='black',anchor='mt')
    rows=[f'SHAPE {shape}',f'BODY DIA {D}',f'HEIGHT {H}']+([f'TOP DIA {top}'] if top else [])
    for i,row in enumerate(rows):d.text((1010,695+i*65),row,font=font,fill='black')
    im.save(B/(name+'.png'));im.save(B/(name+'.pdf'),'PDF',resolution=150,quality=98)
