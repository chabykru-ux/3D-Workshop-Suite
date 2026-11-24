from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def draw_example(name,L,W,H,holes=(),shape='block',step=None):
    im=Image.new('RGB',(1900,1250),'white');d=ImageDraw.Draw(im);font=ImageFont.truetype(F,32);title=ImageFont.truetype(F,40)
    d.text((90,30),'TECHNICAL DRAWING - MM',font=title,fill='black');s=5; x,y=130,150; X=1000; Y=650
    def rect(a,b,c,e):d.rectangle((a,b,c,e),outline='black',width=4)
    def label(a,b,t):d.text((a,b),t,font=font,fill='black',anchor='mt')
    if shape=='step':
        sx,sz=step;pts=[(x,y+H*s),(x+L*s,y+H*s),(x+L*s,y+(H-sz)*s),(x+sx*s,y+(H-sz)*s),(x+sx*s,y),(x,y),(x,y+H*s)];d.line(pts,fill='black',width=4)
    else:rect(x,y,x+L*s,y+H*s)
    rect(X,y,X+W*s,y+H*s)
    label(x+L*s/2,y+H*s+20,'FRONT');label(X+W*s/2,y+H*s+20,'SIDE')
    if shape=='cylinder':d.ellipse((x,Y,x+L*s,Y+W*s),outline='black',width=4)
    else:rect(x,Y,x+L*s,Y+W*s)
    if step:
        d.line((x+sx*s,Y,x+sx*s,Y+W*s),fill='black',width=4);d.line((X,y+(H-sz)*s,X+W*s,y+(H-sz)*s),fill='black',width=4)
    for dia,hx,hy,depth in holes:
        cx=x+hx*s;cy=Y+(W-hy)*s;r=dia*s/2;d.ellipse((cx-r,cy-r,cx+r,cy+r),outline='black',width=4)
        # Hidden edges intentionally shown in both projections.
        for xx,loc in [(x,hx),(X,hy)]:
            end=y+(H if depth is None else depth)*s
            for pos in [loc-dia/2,loc+dia/2]:
                for yy in range(y+8,int(end)-3,24):d.line((xx+pos*s,yy,xx+pos*s,min(yy+12,end-2)),fill='black',width=3)
    label(x+L*s/2,Y+W*s+20,'TOP')
    rows=[f'LENGTH {L}',f'WIDTH {W}',f'HEIGHT {H}'] if shape!='cylinder' else [f'BODY DIA {L}',f'HEIGHT {H}']
    if step:rows.append(f'STEP X {sx} Z {sz}')
    for dia,hx,hy,depth in holes:rows.append(f'HOLE {dia} X {hx} Y {hy} '+('THRU' if depth is None else f'DEPTH {depth}'))
    for i,t in enumerate(rows):d.text((850,625+i*55),t,font=font,fill='black')
    im.save(name+'.png');im.save(name+'.pdf','PDF',resolution=150)
if __name__=='__main__':
    draw_example('example_multiple',100,60,35,[(12,20,15,None),(18,70,40,12),(10,85,15,None)])
    draw_example('example_cylinder',60,60,30,[(16,30,30,None),(10,43,42,8)],'cylinder')
    draw_example('example_step',100,60,40,shape='step',step=(60,20))
