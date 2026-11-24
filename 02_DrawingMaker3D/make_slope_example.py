from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
B=Path(__file__).parent
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
L,W,H,low=100,60,45,20
holes=[(14,27,30),(10,79,30)]
im=Image.new('RGB',(1900,1250),'white');d=ImageDraw.Draw(im);font=ImageFont.truetype(F,36);title=ImageFont.truetype(F,42)
d.text((100,45),'TEST 04 / ALL DIMENSIONS MM',font=title,fill='black');s=6;x,y=140,145;X=1120;Y=660
# Front (X/Z) and right side (Y/Z).
d.line([(x,y),(x+L*s,y+(H-low)*s),(x+L*s,y+H*s),(x,y+H*s),(x,y)],fill='black',width=5)
d.rectangle((X,y,X+W*s,y+H*s),outline='black',width=5)
d.line((X,y+(H-low)*s,X+W*s,y+(H-low)*s),fill='black',width=4)
d.rectangle((x,Y,x+L*s,Y+W*s),outline='black',width=5)
for dia,hx,hy in holes:
    cx=x+hx*s;cy=Y+(W-hy)*s;r=dia*s/2;d.ellipse((cx-r,cy-r,cx+r,cy+r),outline='black',width=5)
    for pos in (hx-dia/2,hx+dia/2):
        start=round(y+(H-low)*pos*s/L)+9
        for yy in range(start,y+H*s-8,24):d.line((x+pos*s,yy,x+pos*s,min(yy+12,y+H*s-8)),fill='black',width=3)
for a,b,t in [(x+L*s/2,y+H*s+25,'FRONT'),(X+W*s/2,y+H*s+25,'SIDE'),(x+L*s/2,Y+W*s+25,'TOP')]:d.text((a,b),t,font=font,fill='black',anchor='mt')
for i,t in enumerate(['LENGTH 100','WIDTH 60','HEIGHT 45','SLOPE Z 20','HOLE 14 X 27 Y 30 THRU','HOLE 10 X 79 Y 30 THRU']):d.text((920,660+i*58),t,font=font,fill='black')
im.save(B/'04_sloped_block_2_holes.png');im.save(B/'04_sloped_block_2_holes.pdf','PDF',resolution=150,quality=95)
