import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from engine import load_drawing, analyze, make_mesh, export_3mf

def hole_position(h):
    if h.get('face')=='UPRIGHT':return f'Стенка: Y={h["y"]:g}, Z={h["u"]:g}'
    if h.get('face')=='BASE':return f'Основание: X={h["x"]:g}, Y={h["y"]:g}'
    return f'X={h["x"]:g}, Y={h["y"]:g}'

class App:
    def __init__(self,root):
        self.root=root;root.title('DrawingMaker 3D • v0.6.0 EXPERIMENTAL');root.geometry('1220x780');root.minsize(820,550)
        self.path=None;self.result=None;self.mesh=None;self.im=None;self.photo=None;self.pool=ThreadPoolExecutor(max_workers=1);self.busy=False
        style=ttk.Style();style.theme_use('clam');style.configure('TButton',padding=7);style.configure('Title.TLabel',font=('Segoe UI',16,'bold'))
        head=ttk.Frame(root,padding=10);head.pack(fill='x');ttk.Label(head,text='DrawingMaker 3D',style='Title.TLabel').pack(side='left');ttk.Label(head,text='  v0.6.0  /  Experimental').pack(side='left')
        bar=ttk.Frame(root,padding=(10,0,10,8));bar.pack(fill='x')
        self.openbtn=ttk.Button(bar,text='1. Открыть чертёж',command=self.open);self.openbtn.pack(side='left',padx=3)
        self.anbtn=ttk.Button(bar,text='2. Анализ и 3D',command=self.run,state='disabled');self.anbtn.pack(side='left',padx=3)
        self.stl=ttk.Button(bar,text='Экспорт STL',command=lambda:self.save('stl'),state='disabled');self.stl.pack(side='left',padx=3)
        self.mf=ttk.Button(bar,text='Экспорт 3MF',command=lambda:self.save('3mf'),state='disabled');self.mf.pack(side='left',padx=3)
        examples=ttk.Menubutton(bar,text='Примеры'); menu=tk.Menu(examples,tearoff=False); examples['menu']=menu; examples.pack(side='left',padx=3)
        for label,filename in [('Исходный блок','example_drawing.pdf'),('Три отверстия','example_multiple.pdf'),('Цилиндр','example_cylinder.pdf'),('Шар','05_sphere.pdf'),('Полушарие','06_hemisphere.pdf'),('Конус','07_cone.pdf'),('Усечённый конус','08_frustum.pdf'),('Ступень','example_step.pdf'),('Ступень с двумя отверстиями','03_stepped_block_2_holes.pdf'),('Наклон с двумя отверстиями','04_sloped_block_2_holes.pdf'),('Уголок','example_bracket.png'),('Пластина: пять отверстий','01_plate_5_holes.pdf'),('Фланец: пять отверстий','02_round_flange_5_holes.pdf')]:
            menu.add_command(label=label,command=lambda f=filename:self.example(f))
        self.status=tk.StringVar(value='Открой PDF (1 страница), PNG или JPG.');ttk.Label(root,textvariable=self.status,padding=(12,4)).pack(fill='x',side='bottom')
        panes=ttk.Panedwindow(root,orient='horizontal');panes.pack(fill='both',expand=True,padx=10,pady=(0,5))
        left=ttk.Frame(panes);right=ttk.Frame(panes);panes.add(left,weight=1);panes.add(right,weight=1)
        ttk.Label(left,text='Исходный чертёж / распознанные контуры').pack(anchor='w',pady=5)
        self.canvas=tk.Canvas(left,bg='#ffffff',highlightthickness=1,highlightbackground='#b9c4ca',height=320);self.canvas.pack(fill='both',expand=True);self.canvas.bind('<Configure>',lambda e:self.refresh_image())
        ttk.Label(left,text='Диагностика и извлечённые параметры').pack(anchor='w',pady=5)
        tf=ttk.Frame(left);tf.pack(fill='both');self.log=tk.Text(tf,height=13,wrap='word',font=('Segoe UI',10),state='disabled');scroll=ttk.Scrollbar(tf,command=self.log.yview);self.log.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.log.pack(fill='both',expand=True)
        ttk.Label(right,text='3D Preview — вращение мышью, масштаб с помощью панели').pack(anchor='w',pady=5)
        self.fig=Figure(figsize=(5,5),dpi=100,facecolor='#f1f5f6');self.ax=self.fig.add_subplot(111,projection='3d');self.plot=FigureCanvasTkAgg(self.fig,master=right);self.plot.get_tk_widget().pack(fill='both',expand=True);NavigationToolbar2Tk(self.plot,right).update();self.preview()
        self.write('Поддержка v0.6: шар, полушарие, конус и усечённый конус без отверстий; наклонная плоскость с вертикальными сквозными отверстиями; уголок с полукруглыми концами и двумя отверстиями; блоки, цилиндры, одна ступень со сквозными отверстиями, несколько сквозных и глухих отверстий в блоках/цилиндрах. Три подписанных вида TOP / FRONT / SIDE. Размеры в миллиметрах. Программа не редактирует чертёж.')
    def write(self,s):
        self.log.configure(state='normal');self.log.delete('1.0','end');self.log.insert('end',s);self.log.configure(state='disabled')
    def refresh_image(self):
        if self.im is None:return
        im=self.im.copy();im.thumbnail((max(1,self.canvas.winfo_width()-8),max(1,self.canvas.winfo_height()-8)));self.photo=ImageTk.PhotoImage(im);self.canvas.delete('all');self.canvas.create_image(self.canvas.winfo_width()/2,self.canvas.winfo_height()/2,image=self.photo,anchor='center')
    def preview(self):
        self.ax.clear();self.ax.set_facecolor('#f1f5f6');self.ax.set_xlabel('X / mm');self.ax.set_ylabel('Y / mm');self.ax.set_zlabel('Z / mm');self.ax.view_init(elev=26,azim=-55)
        if self.mesh is None:self.ax.text2D(.18,.5,'No validated 3D model',transform=self.ax.transAxes,color='#617781')
        else:
            m=self.mesh;tri=m.vertices[m.faces];norm=m.face_normals;light=np.clip(norm@np.array([.35,-.45,.82]),-.4,1);colors=np.array([.20,.65,.69])[None,:]*(.7+.3*light[:,None]);self.ax.add_collection3d(Poly3DCollection(tri,facecolors=np.clip(colors,0,1),edgecolors='none'))
            bounds=m.bounds;center=bounds.mean(axis=0);ext=m.extents;span=max(ext)*.58
            self.ax.set_xlim(center[0]-span,center[0]+span);self.ax.set_ylim(center[1]-span,center[1]+span);self.ax.set_zlim(center[2]-span,center[2]+span);self.ax.set_box_aspect([1,1,1]);self.ax.set_title(' × '.join(f'{a:g}' for a in ext)+' mm')
        self.fig.tight_layout();self.plot.draw_idle()
    def open(self):
        if self.busy:return
        p=filedialog.askopenfilename(filetypes=[('Drawings','*.pdf *.png *.jpg *.jpeg *.bmp'),('All files','*.*')]);
        if p:self.load(p)
    def example(self,filename='example_drawing.pdf'):
        if not self.busy:self.load(Path(__file__).parent/filename)
    def load(self,p):
        self.mesh=None;self.result=None;self.im=None;self.path=None;self.canvas.delete('all');self.preview();self.stl['state']=self.mf['state']=self.anbtn['state']='disabled'
        try:self.im=load_drawing(p);self.path=Path(p);self.refresh_image();self.anbtn['state']='normal';self.write('Файл открыт. Нажми «Анализ и 3D».');self.status.set(self.path.name)
        except Exception as e:self.write(str(e));self.status.set('Ошибка открытия');messagebox.showerror('Ошибка',str(e))
    def run(self):
        if self.busy or self.path is None:return
        self.busy=True;self.mesh=None;self.preview();self.stl['state']=self.mf['state']=self.openbtn['state']=self.anbtn['state']='disabled';self.status.set('Распознавание…');self.write('Идёт локальное распознавание геометрии и текста…')
        fut=self.pool.submit(self.process,self.path);self.root.after(120,lambda:self.poll(fut))
    @staticmethod
    def process(path):
        result=analyze(load_drawing(path));mesh=make_mesh(result['params']) if not result['errors'] else None;return result,mesh
    def poll(self,fut):
        if not fut.done():self.root.after(120,lambda:self.poll(fut));return
        self.busy=False;self.openbtn['state']=self.anbtn['state']='normal'
        try:
            self.result,self.mesh=fut.result();r=self.result;self.im=r['overlay'];self.refresh_image();names={'L':'Длина','W':'Ширина','H':'Высота','D':'Диаметр','T':'Толщина','R':'Радиус конца'};s='\n'.join(f'{names[k]}: {v:g} мм' for k,v in r['params'].items() if k in names);s+='\n'+'\n'.join(f'Отверстие {i}: Ø{h["d"]:g}, {hole_position(h)}; '+('сквозное' if h['depth'] is None else f'глубина {h["depth"]:g} мм') for i,h in enumerate(r['params'].get('holes',[]),1));s+=('\nСтупень X/Z: '+str(r['params']['step']) if 'step' in r['params'] else '');s+=(f'\nВысота справа: {r["params"]["slope"]:g} мм' if 'slope' in r['params'] else '');s+=(f'\nВерхний диаметр: {r["params"]["top_d"]:g} мм' if 'top_d' in r['params'] else '');s+='\n\n'+ ('ПРОВЕРЬ И ИСПРАВЬ ЧЕРТЁЖ:\n'+'\n'.join('• '+e for e in r['errors']) if r['errors'] else 'Модель построена. Сверь её с чертежом перед экспортом.');s+='\n\n'+'\n'.join(r['notes'])+'\n\nOCR (исходный распознанный текст):\n'+r['text'];self.write(s);self.preview();self.status.set('Модель готова к проверке' if self.mesh is not None else 'Экспорт заблокирован: исправь исходный чертёж')
            if self.mesh is not None:self.stl['state']=self.mf['state']='normal'
        except Exception as e:self.write('Ошибка анализа:\n'+str(e));self.status.set('Анализ не выполнен')
    def save(self,ext):
        if self.mesh is None:return
        p=filedialog.asksaveasfilename(defaultextension='.'+ext,initialfile=self.path.stem+'.'+ext,filetypes=[(ext.upper(),'*.'+ext)])
        if p:
            try:
                if ext=='stl':self.mesh.export(p)
                else:export_3mf(self.mesh,p)
                self.status.set('Сохранено: '+p)
            except Exception as e:messagebox.showerror('Ошибка экспорта',str(e))

if __name__=='__main__':
    root=tk.Tk();app=App(root);root.mainloop()
