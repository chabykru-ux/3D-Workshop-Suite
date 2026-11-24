/* PlaqueMaker 3D v1.3 — no dependencies, no servers.
 * Geometry: millimetre-based sliced binary masks -> closed surface meshes.
 * 3MF: one compound parent object, independent materialized child meshes.
 */
(() => {
'use strict';
const $ = (q, root = document) => root.querySelector(q);
const $$ = (q, root = document) => [...root.querySelectorAll(q)];

/* Version 1.2.1: 12 offline Windows font choices, plus optional local font import.
 * Only names of OS-installed fonts are used: no font files are redistributed.
 * The same Canvas glyph rasterization drives both the preview and exports.
 */
const FONT_LIBRARY = [
 {id:'Arial', label:'Arial', kind:'Универсальный', langs:['ru','en','he'], stack:'Arial, "Segoe UI", sans-serif', sample:'Добро пожаловать'},
 {id:'Times New Roman',label:'Times New Roman',kind:'Классический',langs:['ru','en','he'],stack:'"Times New Roman", Georgia, serif',sample:'Добро пожаловать'},
 {id:'Georgia',label:'Georgia',kind:'Элегантный с засечками',langs:['ru','en'],stack:'Georgia, "Times New Roman", serif',sample:'Добро пожаловать'},
 {id:'Courier New',label:'Courier New',kind:'Ретро / машинописный',langs:['ru','en'],stack:'"Courier New", monospace',sample:'Добро пожаловать'},
 {id:'Trebuchet MS',label:'Trebuchet MS',kind:'Мягкий современный',langs:['ru','en'],stack:'"Trebuchet MS", Arial, sans-serif',sample:'Добро пожаловать'},
 {id:'Segoe Script',label:'Segoe Script',kind:'Каллиграфия',langs:['ru','en'],stack:'"Segoe Script", "Segoe Print", cursive',sample:'С любовью'},
 {id:'Segoe Print',label:'Segoe Print',kind:'Рукописный',langs:['ru','en'],stack:'"Segoe Print", "Comic Sans MS", cursive',sample:'С любовью'},
 {id:'Gabriola',label:'Gabriola',kind:'Старинная каллиграфия',langs:['ru','en'],stack:'Gabriola, "Segoe Script", cursive',sample:'С любовью'},
 {id:'Monotype Corsiva',label:'Monotype Corsiva',kind:'Винтажная каллиграфия',langs:['ru','en'],stack:'"Monotype Corsiva", "Segoe Script", cursive',sample:'С любовью'},
 {id:'Comic Sans MS',label:'Comic Sans MS',kind:'Неформальный рукописный',langs:['ru','en'],stack:'"Comic Sans MS", "Segoe Print", cursive',sample:'С любовью'},
 {id:'David',label:'David',kind:'Классический иврит',langs:['he','en'],stack:'David, "Times New Roman", Arial, serif',sample:'ברוכים הבאים'},
 {id:'Gisha',label:'Gisha',kind:'Современный иврит',langs:['he','en'],stack:'Gisha, "Segoe UI", Arial, sans-serif',sample:'ברוכים הבאים'}
];
const CUSTOM_FONT_ID='__custom__';
let customFontReady=false, customFontName='', customFontUrl=null, fontFilter='all';
const fontMeta=id=>FONT_LIBRARY.find(f=>f.id===id);
function selectedFontStack(id){
 if(id===CUSTOM_FONT_ID)return customFontReady?'"PlaqueImportedFont", Arial, sans-serif':'Arial, sans-serif';
 return fontMeta(id)?.stack || 'Arial, sans-serif';
}
function firstTextSamples(){
 const chosen=state.lines.find(l=>l.enabled&&l.value?.trim())?.value || 'PlaqueMaker 3D';
 return chosen.replace(/\s+/g,' ').slice(0,45);
}
function fontSample(meta){
 if(fontFilter==='he')return 'ברוכים הבאים';
 if(fontFilter==='ru')return 'С любовью';
 if(fontFilter==='en')return 'Welcome Home';
 return meta.sample;
}
function fillFontSelect(){
 const select=$('#fontFamilySelect');
 select.innerHTML='';
 for(const item of FONT_LIBRARY){
  const opt=document.createElement('option');opt.value=item.id;opt.textContent=item.label+' · '+item.kind;select.appendChild(opt);
 }
 const opt=document.createElement('option');opt.value=CUSTOM_FONT_ID;opt.textContent='Свой шрифт (импорт TTF/OTF)';select.appendChild(opt);
}
function refreshFontGallery(){
 const target=$('#fontGallery');target.innerHTML='';
 const visible=FONT_LIBRARY.filter(f=>fontFilter==='all'||f.langs.includes(fontFilter));
 for(const item of visible){
  const b=document.createElement('button');b.type='button';b.className='font-tile'+(state.fontFamily===item.id?' selected':'');
  b.setAttribute('aria-pressed',String(state.fontFamily===item.id));
  b.dataset.fontId=item.id;
  const row=document.createElement('div');row.className='font-tile-row';
  const name=document.createElement('strong');name.textContent=item.label;
  const lang=document.createElement('small');lang.textContent=item.langs.map(x=>({ru:'RU',en:'EN',he:'HE'})[x]).join(' · ');
  row.append(name,lang);
  const sample=document.createElement('div');sample.className='font-tile-sample';sample.textContent=fontSample(item);
  sample.style.fontFamily=item.stack;sample.dir=fontFilter==='he'||(!['ru','en'].some(x=>item.langs.includes(x)))?'rtl':'auto';
  const info=document.createElement('small');info.className='font-kind';info.textContent=item.kind;
  b.append(row,sample,info);b.addEventListener('click',()=>{state.fontFamily=item.id;$('#fontFamilySelect').value=item.id;refreshFontGallery();refreshChosenFont();requestBuild()});
  target.appendChild(b);
 }
 const custom=$('#fontCustomTile');
 custom.hidden=!customFontReady||(fontFilter!=='all');
 if(customFontReady){custom.classList.toggle('selected',state.fontFamily===CUSTOM_FONT_ID);custom.querySelector('.font-tile-sample').style.fontFamily='"PlaqueImportedFont", Arial, sans-serif';custom.querySelector('.font-tile-sample').textContent=firstTextSamples();custom.querySelector('strong').textContent=customFontName||'Мой шрифт'}
 $$('#fontFilters button').forEach(b=>b.classList.toggle('active',b.dataset.fontLang===fontFilter));
}
function refreshChosenFont(){
 const chosen=$('#chosenFontPreview');const meta=fontMeta(state.fontFamily);
 chosen.style.fontFamily=selectedFontStack(state.fontFamily);
 chosen.textContent=firstTextSamples();chosen.dir='auto';
 $('#selectedFontInfo').textContent=state.fontFamily===CUSTOM_FONT_ID?(customFontReady?'Свой шрифт: '+customFontName:'Свой шрифт не загружен — импортируй его повторно'):(meta?.label||'Arial');
 $('#fontAvailabilityNote').textContent=state.fontFamily===CUSTOM_FONT_ID?
    (customFontReady?'Шрифт импортирован в текущий сеанс и будет использован для настоящей 3D-геометрии.':'При открытии сохранённого проекта импортируй файл шрифта снова.'):
    'Используется шрифт, установленный в Windows. Если его нет, браузер покажет замену. Для гарантированного начертания можно импортировать свой TTF/OTF.';
}
async function importUserFont(file){
 if(!file)return;
 if(!/\.(ttf|otf|woff2?|TTF|OTF|WOFF2?)$/.test(file.name))throw Error('Нужен шрифт TTF, OTF, WOFF или WOFF2.');
 if(file.size>15*1024*1024)throw Error('Слишком большой файл шрифта (лимит 15 МБ).');
 const url=URL.createObjectURL(file);
 try{
  const face=new FontFace('PlaqueImportedFont',`url("${url}")`);
  await face.load();document.fonts.add(face);
  if(customFontUrl)URL.revokeObjectURL(customFontUrl);
  customFontUrl=url;customFontReady=true;customFontName=file.name;
  state.fontFamily=CUSTOM_FONT_ID;$('#fontFamilySelect').value=CUSTOM_FONT_ID;
  refreshFontGallery();refreshChosenFont();requestBuild();
 }catch(e){URL.revokeObjectURL(url);throw e}
}
function initFontGallery(){
 fillFontSelect();
 $$('#fontFilters button').forEach(b=>b.addEventListener('click',()=>{fontFilter=b.dataset.fontLang;refreshFontGallery()}));
 $('#fontCustomTile').addEventListener('click',()=>{if(customFontReady){state.fontFamily=CUSTOM_FONT_ID;$('#fontFamilySelect').value=CUSTOM_FONT_ID;refreshFontGallery();refreshChosenFont();requestBuild()}});
 $('#fontImportBtn').addEventListener('click',()=>$('#fontImportFile').click());
 $('#fontImportFile').addEventListener('change',async e=>{
  const file=e.target.files[0];if(!file)return;
  $('#fontImportBtn').disabled=true;$('#fontImportBtn').textContent='Загружаем шрифт...';
  try{await importUserFont(file)}catch(err){alert('Не удалось открыть шрифт: '+err.message)}finally{e.target.value='';$('#fontImportBtn').disabled=false;$('#fontImportBtn').textContent='＋ Импортировать свой TTF / OTF'}
 });
 refreshFontGallery();refreshChosenFont();
}

const lineDefs = [
  {id:'name', title:'Основная надпись', value:'CHABANY OLEG',size:10.5,y:24,bold:true,enabled:true},
  {id:'role', title:'Должность / описание', value:'PAINT SPECIALIST',size:5,y:43,bold:false,enabled:true},
  {id:'phone', title:'Номер телефона', value:'054-000-0000',size:8,y:63,bold:true,enabled:true},
  {id:'extra', title:'Дополнительный текст', value:'',size:5,y:76,bold:false,enabled:false}
];
const DEFAULTS = {
  plaqueType:'classic', sideWidth:36, sideText:'215', sideTextSize:17,
  sideTextY:40,sideTextBold:true,sideDividerWidth:1.0,sideTextColor:'#b34d8f',
  width:120,height:80,baseThickness:2.4,radius:5,
  rimEnabled:true,rimWidth:2.2,rimHeight:1.2,
  holesEnabled:false,holeDiameter:3.5,holeInset:7,
  fontFamily:'Arial',textMode:'raised',textDepth:1.1,textAlign:'center',
  dividerEnabled:true,dividerY:53,dividerWidth:0.8,dividerLength:70,dividerHeight:0.6,
  baseColor:'#f5f6f5',rimColor:'#3686bd',textColor:'#172f45',bottomTextColor:'#b34d8f',accentColor:'#3686bd',
  resolution:0.35,lines:lineDefs.map(x=>({...x}))
};
let state=JSON.parse(JSON.stringify(DEFAULTS));
let model=null, activeBuild=0, buildHandle=null, pendingBuild=null;
let renderer=null, isBusy=false;
const ROW_COLORS={base:'baseColor',rim:'rimColor',textTop:'textColor',textBottom:'bottomTextColor',accent:'accentColor',sideText:'sideTextColor'};
const clone=o=>JSON.parse(JSON.stringify(o));
const clamp=(v,min,max,fallback)=>{v=Number(v);return Number.isFinite(v)?Math.min(max,Math.max(min,v)):fallback};
const num=(v,d=2)=>Number(v).toFixed(d).replace(/\.0+$/,'').replace(/(\.\d*?)0+$/,'$1');
const scrub=(s)=>String(s||'').replace(/[<>"'&]/g,'');

function createLineControls(){
 const area=$('#textFields');
 area.innerHTML='';
 lineDefs.forEach((def,idx)=>{
   const el=document.createElement('div');el.className='text-line';el.dataset.row=String(idx);
   el.innerHTML=`<div class="text-line-head"><label class="switch-row"><input type="checkbox" data-line-check="${idx}"><span class="switch-ui"></span><span class="switch-copy"><strong>${def.title}</strong></span></label><span style="font-size:10px;color:#8198b3">${idx+1} / 4</span></div><div class="line-body"><input class="line-input" type="text" data-line-field="value" placeholder="Введите любой текст" maxlength="100"><div class="line-controls"><label class="field">Размер букв <span>мм</span><input type="number" min="2.5" max="28" step="0.5" data-line-field="size"></label><label class="field">Отступ сверху <span>мм</span><input type="number" min="4" max="175" step="1" data-line-field="y"></label></div><label class="switch-row" style="margin-top:11px"><input type="checkbox" data-line-field="bold"><span class="switch-ui"></span><span class="switch-copy"><strong>Жирный шрифт</strong></span></label></div>`;
   area.appendChild(el);
 });
 $$('#textFields [data-line-check]').forEach(input=>input.addEventListener('change',()=>{
   state.lines[+input.dataset.lineCheck].enabled=input.checked;
   updateVisibility();requestBuild();
 }));
 $$('#textFields [data-line-field]').forEach(input=>input.addEventListener(input.type==='checkbox'?'change':'input',()=>{
   const idx=+input.closest('[data-row]').dataset.row;
   const key=input.dataset.lineField;
   state.lines[idx][key] = input.type==='checkbox' ? input.checked : input.type==='number' ? Number(input.value) : input.value;
   refreshChosenFont();requestBuild();
 }));
}
function reflectState(){
 $$('[data-plaque-type]').forEach(input=>{input.checked=state.plaqueType===input.value});
 $$('[data-key]').forEach(input=>{
   const val=state[input.dataset.key];
   if(input.type==='checkbox')input.checked=!!val;
   else input.value=String(val);
 });
 $$('#textFields [data-row]').forEach(el=>{
   const l=state.lines[+el.dataset.row];
   $('[data-line-check]',el).checked=!!l.enabled;
   $$('[data-line-field]',el).forEach(inp=>{inp.type==='checkbox'?inp.checked=!!l[inp.dataset.lineField]:inp.value=String(l[inp.dataset.lineField]??'')});
 });
 updateVisibility();refreshFontGallery();refreshChosenFont();
}
function updateVisibility(){
 $$('[data-visible-template]').forEach(el=>el.hidden=state.plaqueType!==el.dataset.visibleTemplate);
 $$('[data-visible-if]').forEach(el=>el.hidden=!state[el.dataset.visibleIf]);
 $$('#textFields [data-row]').forEach(el=>{
   const enabled=!!state.lines[+el.dataset.row].enabled;
   $('.line-body',el).hidden=!enabled;
   el.style.opacity=enabled?'1':'.72';
 });
}
function connectControls(){
 $$('[data-plaque-type]').forEach(input=>input.addEventListener('change',()=>{if(!input.checked)return;state.plaqueType=input.value;updateVisibility();requestBuild()}));
 $$('[data-key]').forEach(input=>input.addEventListener((input.type==='checkbox'||input.tagName==='SELECT'||input.type==='color')?'change':'input',()=>{
    const k=input.dataset.key;
    if(input.type==='checkbox')state[k]=input.checked;
    else if(input.type==='number'||k==='resolution')state[k]=Number(input.value);
    else state[k]=input.value;
    if(k==='width'||k==='sideWidth'){
      state.sideWidth=clamp(state.sideWidth,16,Math.min(90,Number(state.width)*.48),Math.min(36,Number(state.width)*.35));
      $('[data-key="sideWidth"]').value=String(num(state.sideWidth,1));
    }
    if(k==='height'&&Number.isFinite(state.height)&&state.height>=30){
      state.sideTextY=Math.min(state.sideTextY,state.height-3);
      const maxY=state.height-2;
      for(const line of state.lines)line.y=Math.min(line.y,maxY);
      state.dividerY=Math.min(state.dividerY,state.height-3);
      reflectState();
    }
    if(input.type==='checkbox')updateVisibility();
    if(k==='fontFamily'){refreshFontGallery();refreshChosenFont();}
    requestBuild();
 }));
 $('#newBtn').addEventListener('click',()=>{if(!confirm('Сбросить текущие настройки таблички?'))return;state=clone(DEFAULTS);reflectState();requestBuild()});
 $('#saveBtn').addEventListener('click',()=>downloadFile('PlaqueMaker_project.json',new Blob([JSON.stringify({format:'PlaqueMaker3D',version:1,state},null,2)],{type:'application/json'})));
 $('#loadBtn').addEventListener('click',()=>$('#loadFile').click());
 $('#loadFile').addEventListener('change',async e=>{
   const file=e.target.files[0];if(!file)return;
   try{
    const payload=JSON.parse(await file.text());
    if(payload.format!=='PlaqueMaker3D'||!payload.state)throw Error('Неверный формат проекта');
    state=normalize({...clone(DEFAULTS),...payload.state});reflectState();requestBuild();
   }catch(err){alert('Не удалось открыть проект: '+err.message)}finally{e.target.value=''}
 });
 $('#exportStl').addEventListener('click',()=>exportModel('stl'));
 $('#export3mf').addEventListener('click',()=>exportModel('3mf'));
 $('#frontBtn').addEventListener('click',()=>renderer?.setView(0,Math.PI/2-0.02));
 $('#angleBtn').addEventListener('click',()=>renderer?.setView(-0.50,0.87));
 $('#zoomBtn').addEventListener('click',()=>renderer?.resetZoom());
}
function normalize(p){
 p.plaqueType=p.plaqueType==='room'?'room':'classic';
 p.sideText=String(p.sideText??DEFAULTS.sideText).slice(0,60);
 p.sideTextBold=!!p.sideTextBold;
 p.width=clamp(p.width,45,250,120);p.height=clamp(p.height,30,180,80);
 p.baseThickness=clamp(p.baseThickness,1.2,8,2.4);
 p.radius=clamp(p.radius,0,Math.min(20,p.width/2,p.height/2),5);
 p.sideWidth=clamp(p.sideWidth,16,Math.min(90,p.width*.48),Math.min(36,p.width*.35));
 p.sideTextSize=clamp(p.sideTextSize,3,32,17);
 p.sideTextY=clamp(p.sideTextY,4,p.height-4,p.height/2);
 p.sideDividerWidth=clamp(p.sideDividerWidth,.6,3,1);
 p.rimWidth=clamp(p.rimWidth,0.8,Math.min(12,p.width/4,p.height/4),2.2);
 p.rimHeight=clamp(p.rimHeight,0.4,4,1.2);
 p.holeDiameter=clamp(p.holeDiameter,2,10,3.5);
 p.holeInset=clamp(p.holeInset,3,Math.min(24,p.width/4,p.height/4),7);
 p.textDepth=clamp(p.textDepth,0.3,Math.min(2.5,p.baseThickness-0.35),1.1);
 p.dividerY=clamp(p.dividerY,3,p.height-3,p.height*0.65);
 p.dividerWidth=clamp(p.dividerWidth,.5,3,.8);
 p.dividerHeight=clamp(p.dividerHeight,.3,2,.6);
 p.dividerLength=clamp(p.dividerLength,15,95,70);
 p.resolution=[0.2,0.25,0.35,0.5].includes(+p.resolution)?+p.resolution:0.35;
 p.textMode=['raised','engraved'].includes(p.textMode)?p.textMode:'raised';
 p.textAlign=['left','center','right'].includes(p.textAlign)?p.textAlign:'center';
 p.fontFamily=(FONT_LIBRARY.some(f=>f.id===p.fontFamily)||p.fontFamily===CUSTOM_FONT_ID)?p.fontFamily:'Arial';
 for(const key of ['baseColor','rimColor','textColor','bottomTextColor','accentColor','sideTextColor'])if(!/^#[0-9a-fA-F]{6}$/.test(p[key]))p[key]=DEFAULTS[key];
 for(const key of ['rimEnabled','holesEnabled','dividerEnabled'])p[key]=!!p[key];
 p.lines=lineDefs.map((d,i)=>{
   const l=(Array.isArray(p.lines)?p.lines[i]:null)||d;
   return {...d,...l,value:String(l.value??d.value).slice(0,100),enabled:!!l.enabled,bold:!!l.bold,size:clamp(l.size,2.5,28,d.size),y:clamp(l.y,3,p.height-2,d.y)};
 });
 return p;
}
function requestBuild(){
 clearTimeout(buildHandle);
 $('#readyBadge').textContent='◌ Изменения...';
 buildHandle=setTimeout(()=>build(),170);
}
function makeMask(n){return new Uint8Array(n)}
function repairDiagonals(mask,nx,ny,allowed=null){
 // A 2x2 checkerboard creates a non-manifold vertical edge in a 3D extrusion.
 // Bridge diagonal cells by filling one missing grid cell (at most ~0.2–0.5 mm).
 for(let round=0;round<2;round++){
  let changes=0;
  for(let j=0;j<ny-1;j++)for(let i=0;i<nx-1;i++){
   const a=j*nx+i,b=a+1,c=a+nx,d=c+1;
   let candidates=null;
   if(mask[a]&&mask[d]&&!mask[b]&&!mask[c])candidates=[b,c];
   else if(mask[b]&&mask[c]&&!mask[a]&&!mask[d])candidates=[a,d];
   if(!candidates)continue;
   const pick=candidates.find(k=>!allowed||allowed[k]);
   if(pick!==undefined){mask[pick]=1;changes++}
  }
  if(!changes)break;
 }
}

function shapeContains(x,y,w,h,r){
  if(x<0||x>w||y<0||y>h)return false;
  r=Math.max(0,Math.min(r,w/2,h/2));
  if(!r)return true;
  const dx=Math.max(r-x,0,x-(w-r));
  const dy=Math.max(r-y,0,y-(h-r));
  return dx*dx+dy*dy<=r*r;
}
function getGeometry(p){
 if(p.fontFamily===CUSTOM_FONT_ID&&!customFontReady)throw Error('Для проекта со своим шрифтом импортируй файл TTF/OTF повторно.');
 const Nx=Math.ceil(p.width/p.resolution),Ny=Math.ceil(p.height/p.resolution);
 const cellCount=Nx*Ny;
 if(cellCount>1100000)throw Error('Слишком мелкая сетка для этого размера. Увеличь шаг сетки.');
 const sx=p.width/Nx,sy=p.height/Ny;
 const base=makeMask(cellCount),rim=makeMask(cellCount),textTopMask=makeMask(cellCount),textBottomMask=makeMask(cellCount),sideTextMask=makeMask(cellCount),lineMask=makeMask(cellCount);
 const split=p.plaqueType==='room';
 const splitX=p.width-p.sideWidth;
 const warning=[];
 const radius=p.radius;
 const holeR=p.holeDiameter/2;
 const inHole=(x,y)=>p.holesEnabled&&[
  [p.holeInset,p.holeInset],[p.width-p.holeInset,p.holeInset],
  [p.holeInset,p.height-p.holeInset],[p.width-p.holeInset,p.height-p.holeInset]
 ].some(([hx,hy])=>(x-hx)**2+(y-hy)**2<holeR**2);
 for(let j=0;j<Ny;j++)for(let i=0;i<Nx;i++){
  const x=(i+.5)*sx,y=(j+.5)*sy,k=j*Nx+i;
  if(!shapeContains(x,y,p.width,p.height,radius)||inHole(x,y))continue;
  base[k]=1;
  if(p.rimEnabled&&!shapeContains(x-p.rimWidth,y-p.rimWidth,p.width-2*p.rimWidth,p.height-2*p.rimWidth,Math.max(0,radius-p.rimWidth)))rim[k]=1;
 }
 // Render upper and lower rows to separate masks for two independently colored 3MF parts.
 const topCanvas=document.createElement('canvas'), bottomCanvas=document.createElement('canvas'), sideCanvas=document.createElement('canvas');
 for(const canvas of [topCanvas,bottomCanvas,sideCanvas]){canvas.width=Nx;canvas.height=Ny;}
 const topCtx=topCanvas.getContext('2d',{willReadFrequently:true});
 const bottomCtx=bottomCanvas.getContext('2d',{willReadFrequently:true});
 const sideCtx=sideCanvas.getContext('2d',{willReadFrequently:true});
 if(!topCtx||!bottomCtx||!sideCtx)throw Error('Недоступна функция рисования текста (Canvas).');
 for(const ctx of [topCtx,bottomCtx,sideCtx]){
   ctx.clearRect(0,0,Nx,Ny);ctx.save();ctx.scale(Nx/p.width,Ny/p.height);
   ctx.fillStyle='white';ctx.textBaseline='middle';
 }
 const mainW=split?splitX:p.width;
 const offset=(p.rimEnabled?p.rimWidth+3:4)+(p.holesEnabled?p.holeDiameter:0);
 const availableL=Math.max(6,mainW-2*offset-(split?2:0));
 let resized=0;
 p.lines.forEach((l,idx)=>{
  if(!l.enabled||!l.value.trim())return;
  const ctx=(p.dividerEnabled?(l.y<p.dividerY):(idx<2))?topCtx:bottomCtx;
  const parts=l.value.split(/\r?\n/).slice(0,4);
  const fontSize=l.size;
  ctx.direction=/[\u0590-\u05ff]/.test(l.value)?'rtl':'ltr';
  ctx.font=`${l.bold?'bold':'normal'} ${fontSize}px ${selectedFontStack(p.fontFamily)}`;
  const maxW=Math.max(12,availableL);
  const metrics=parts.map(s=>ctx.measureText(s).width);
  const natural=Math.max(1,...metrics);
  const fitted=Math.min(fontSize,fontSize*maxW/natural);
  if(fitted<fontSize*.99)resized++;
  ctx.font=`${l.bold?'bold':'normal'} ${fitted}px ${selectedFontStack(p.fontFamily)}`;
  ctx.textAlign=p.textAlign;
  const x=p.textAlign==='center'?mainW/2:p.textAlign==='left'?offset:mainW-offset;
  parts.forEach((s,i)=>ctx.fillText(s,x,l.y+(i-(parts.length-1)/2)*fitted*1.13));
 });
 if(split&&p.sideText.trim()){
   const parts=p.sideText.split(/\r?\n/).slice(0,3);
   const maxW=Math.max(4,p.sideWidth-2*Math.max(4,p.rimEnabled?p.rimWidth+2:4));
   const rtl=/[\u0590-\u05ff]/.test(p.sideText);
   sideCtx.direction=rtl?'rtl':'ltr';
   sideCtx.textAlign='center';
   const fontStr=size=>`${p.sideTextBold?'bold':'normal'} ${size}px ${selectedFontStack(p.fontFamily)}`;
   sideCtx.font=fontStr(p.sideTextSize);
   const natural=Math.max(1,...parts.map(part=>sideCtx.measureText(part).width));
   const fitted=Math.min(p.sideTextSize,p.sideTextSize*maxW/natural);
   if(fitted<p.sideTextSize*.99)warning.push('Надпись справа уменьшена, чтобы поместиться в зоне.');
   sideCtx.font=fontStr(fitted);
   parts.forEach((part,i)=>sideCtx.fillText(part,splitX+p.sideWidth/2,p.sideTextY+(i-(parts.length-1)/2)*fitted*1.13));
 }
 topCtx.restore();bottomCtx.restore();sideCtx.restore();
 if(resized)warning.push(`Автоматически уменьшено строк: ${resized}. Для читаемости проверь размер шрифта.`);
 const alphaTop=topCtx.getImageData(0,0,Nx,Ny).data;
 const alphaBottom=bottomCtx.getImageData(0,0,Nx,Ny).data;
 const alphaSide=sideCtx.getImageData(0,0,Nx,Ny).data;
 let count=0;
 for(let k=0;k<cellCount;k++){
   if(!base[k]||rim[k])continue;
   const x=((k%Nx)+.5)*sx;
   const isSide=split&&x>splitX+Math.max(2,p.sideDividerWidth/2+1);
   const isLeft=!split||x<splitX-Math.max(2,p.sideDividerWidth/2+1);
   const top=alphaTop[k*4+3]>92, bottom=alphaBottom[k*4+3]>92;
   if(isSide&&alphaSide[k*4+3]>92){sideTextMask[k]=1;count++}
   else if(isLeft&&bottom){textBottomMask[k]=1;count++}
   else if(isLeft&&top){textTopMask[k]=1;count++}
 }
 if(count===0&&(p.lines.some(l=>l.enabled&&l.value.trim())||(split&&p.sideText.trim())))warning.push('Не удалось уместить надпись. Проверь размеры и положение строк.');
 if(p.dividerEnabled){
  const half=mainW*p.dividerLength/200;
  for(let j=0;j<Ny;j++)for(let i=0;i<Nx;i++){
   const x=(i+.5)*sx,y=(j+.5)*sy,k=j*Nx+i;
   if(base[k]&&!rim[k]&&!textTopMask[k]&&!textBottomMask[k]&&Math.abs(y-p.dividerY)<=p.dividerWidth/2&&Math.abs(x-mainW/2)<=half&&(!split||x<splitX-2))lineMask[k]=1;
  }
 }
 if(split){
   for(let j=0;j<Ny;j++)for(let i=0;i<Nx;i++){
     const x=(i+.5)*sx,y=(j+.5)*sy,k=j*Nx+i;
     const pad=Math.max(p.rimEnabled?p.rimWidth+2:3,2.5);
     if(base[k]&&!rim[k]&&!textTopMask[k]&&!textBottomMask[k]&&!sideTextMask[k]&&
        Math.abs(x-splitX)<=p.sideDividerWidth/2&&y>pad&&y<p.height-pad)lineMask[k]=1;
   }
 }
 // Make every individual colored solid printable without diagonal-only contacts.
 repairDiagonals(base,Nx,Ny);
 if(p.rimEnabled)repairDiagonals(rim,Nx,Ny,base);
 const allowedText=makeMask(cellCount);
 for(let k=0;k<cellCount;k++)allowedText[k]=base[k]&&!rim[k]?1:0;
 const allowedLeft=makeMask(cellCount),allowedSide=makeMask(cellCount);
 for(let k=0;k<cellCount;k++){
    const x=((k%Nx)+.5)*sx;
    allowedLeft[k]=allowedText[k]&&(!split||x<splitX-1)?1:0;
    allowedSide[k]=allowedText[k]&&split&&x>splitX+1?1:0;
 }
 repairDiagonals(textTopMask,Nx,Ny,allowedLeft);
 // Keep top and bottom parts disjoint, including after diagonal repair.
 const allowedBottom=makeMask(cellCount);
 for(let k=0;k<cellCount;k++)allowedBottom[k]=allowedLeft[k]&&!textTopMask[k]?1:0;
 for(let k=0;k<cellCount;k++)if(textTopMask[k])textBottomMask[k]=0;
 repairDiagonals(textBottomMask,Nx,Ny,allowedBottom);
 if(split)repairDiagonals(sideTextMask,Nx,Ny,allowedSide);
 const allowedAccent=makeMask(cellCount);
 for(let k=0;k<cellCount;k++)allowedAccent[k]=allowedText[k]&&!textTopMask[k]&&!textBottomMask[k]&&!sideTextMask[k]?1:0;
 repairDiagonals(lineMask,Nx,Ny,allowedAccent);
 if(p.holesEnabled&&(p.holeInset-p.holeDiameter/2<2))warning.push('Крепёжные отверстия очень близко к краю.');
 if(p.textDepth>p.baseThickness-.35&&p.textMode==='engraved')warning.push('Гравировка слишком глубокая; оставь хотя бы 0,35 мм под надписью.');
 if(p.textMode==='engraved')warning.push('Гравировка является частью основания: два цвета текста доступны при выборе выпуклых букв.');
 if(p.lines.some(l=>l.enabled&&l.size<4))warning.push('Мелкий текст: некоторые линии букв могут оказаться тоньше возможностей сопла 0,4 мм.');
 if(p.resolution>=0.5&&p.lines.some(l=>l.enabled))warning.push('Для более гладких цифр и букв выбери сетку 0,25–0,35 мм.');
 const layersByPart={};
 if(p.textMode==='engraved'&&count){
  const clean=makeMask(cellCount);
  for(let i=0;i<cellCount;i++)clean[i]=base[i]&&!textTopMask[i]&&!textBottomMask[i]&&!sideTextMask[i]?1:0;
  layersByPart.base=[{z0:0,z1:p.baseThickness-p.textDepth,mask:base},{z0:p.baseThickness-p.textDepth,z1:p.baseThickness,mask:clean}];
 }else layersByPart.base=[{z0:0,z1:p.baseThickness,mask:base}];
 if(p.rimEnabled)layersByPart.rim=[{z0:p.baseThickness,z1:p.baseThickness+p.rimHeight,mask:rim}];
 if(p.textMode==='raised'&&count){
  if(textTopMask.some(x=>x))layersByPart.textTop=[{z0:p.baseThickness,z1:p.baseThickness+p.textDepth,mask:textTopMask}];
  if(textBottomMask.some(x=>x))layersByPart.textBottom=[{z0:p.baseThickness,z1:p.baseThickness+p.textDepth,mask:textBottomMask}];
  if(split&&sideTextMask.some(x=>x))layersByPart.sideText=[{z0:p.baseThickness,z1:p.baseThickness+p.textDepth,mask:sideTextMask}];
 }
 if(p.dividerEnabled||split)layersByPart.accent=[{z0:p.baseThickness,z1:p.baseThickness+p.dividerHeight,mask:lineMask}];
 const meshes={};
 for(const [key,layers] of Object.entries(layersByPart)){
   const triangles=meshLayers(layers,Nx,Ny,sx,sy,p.width,p.height);
   if(triangles.length)meshes[key]=triangles;
 }
 // STL uses geometric union of all parts (not overlapping shells).
 const levels=[...new Set(Object.values(layersByPart).flat().flatMap(l=>[l.z0,l.z1]).map(x=>Number(x.toFixed(5))))].sort((a,b)=>a-b);
 const unionLayers=[];
 for(let l=0;l<levels.length-1;l++){
   const z0=levels[l],z1=levels[l+1];if(z1-z0<0.00001)continue;
   const mask=makeMask(cellCount),mid=(z0+z1)/2;
   for(const layers of Object.values(layersByPart))for(const layer of layers){
     if(mid>layer.z0-1e-6&&mid<layer.z1+1e-6){for(let k=0;k<cellCount;k++)if(layer.mask[k])mask[k]=1;}
   }
   repairDiagonals(mask,Nx,Ny);
   unionLayers.push({z0,z1,mask});
 }
 const unified=meshLayers(unionLayers,Nx,Ny,sx,sy,p.width,p.height);
 return {meshes,unified,layersByPart,Nx,Ny,step:p.resolution, warnings:warning,maxZ:Math.max(...levels),dim:p,cellCount};
}
function meshLayers(layers,nx,ny,sx,sy,W,H){
 if(!layers.length)return new Float32Array(0);
 const quads=[]; // axis-aligned facets, later subdivided to eliminate T-junctions
 const eps=1e-5;
 const X=i=>-W/2+i*sx, Y=j=>H/2-j*sy;
 function quad(a,b,c,d){quads.push([a,b,c,d]);}
 function horizontal(mask,z,top){
  const remaining=mask.slice();
  for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){
   let idx=j*nx+i;if(!remaining[idx])continue;
   let ww=1;while(i+ww<nx&&remaining[idx+ww])ww++;
   let hh=1;
   extend:while(j+hh<ny){for(let a=i;a<i+ww;a++)if(!remaining[(j+hh)*nx+a])break extend;hh++}
   for(let y=j;y<j+hh;y++)for(let x=i;x<i+ww;x++)remaining[y*nx+x]=0;
   const left=X(i),right=X(i+ww),up=Y(j),down=Y(j+hh);
   if(top)quad([left,down,z],[right,down,z],[right,up,z],[left,up,z]);
   else quad([left,up,z],[right,up,z],[right,down,z],[left,down,z]);
  }
 }
 const N=nx*ny;
 const empty=new Uint8Array(N);
 for(let layerIndex=0;layerIndex<layers.length;layerIndex++){
  const layer=layers[layerIndex],mask=layer.mask,prev=layerIndex>0?layers[layerIndex-1].mask:empty,next=layerIndex+1<layers.length?layers[layerIndex+1].mask:empty;
  const prevTouches=layerIndex>0&&Math.abs(layers[layerIndex-1].z1-layer.z0)<eps;
  const nextTouches=layerIndex+1<layers.length&&Math.abs(layers[layerIndex+1].z0-layer.z1)<eps;
  const top=new Uint8Array(N),bottom=new Uint8Array(N);
  for(let n=0;n<N;n++)if(mask[n]){
    if(!(nextTouches&&next[n]))top[n]=1;
    if(!(prevTouches&&prev[n]))bottom[n]=1;
  }
  horizontal(top,layer.z1,true);horizontal(bottom,layer.z0,false);
  const z0=layer.z0,z1=layer.z1;
  // top and bottom Y boundaries: merge neighbouring X faces.
  for(let j=0;j<ny;j++)for(const front of [true,false]){
    const y=Y(j+(front?0:1));
    for(let i=0;i<nx;){
      const k=j*nx+i,valid=!!mask[k]&&(front?(j===0||!mask[k-nx]):(j===ny-1||!mask[k+nx]));
      if(!valid){i++;continue;}
      const start=i++;while(i<nx){const kk=j*nx+i;if(!mask[kk]||!(front?(j===0||!mask[kk-nx]):(j===ny-1||!mask[kk+nx])))break;i++;}
      const x0=X(start),x1=X(i);
      if(front)quad([x0,y,z0],[x0,y,z1],[x1,y,z1],[x1,y,z0]);
      else quad([x0,y,z0],[x1,y,z0],[x1,y,z1],[x0,y,z1]);
    }
  }
  // left/right X boundaries: merge neighbouring Y faces.
  for(let i=0;i<nx;i++)for(const right of [false,true]){
    const x=X(i+(right?1:0));
    for(let j=0;j<ny;){
      const k=j*nx+i,valid=!!mask[k]&&(right?(i===nx-1||!mask[k+1]):(i===0||!mask[k-1]));
      if(!valid){j++;continue;}
      const start=j++;while(j<ny){const kk=j*nx+i;if(!mask[kk]||!(right?(i===nx-1||!mask[kk+1]):(i===0||!mask[kk-1])))break;j++;}
      const yTop=Y(start),yBottom=Y(j);
      if(right)quad([x,yBottom,z0],[x,yTop,z0],[x,yTop,z1],[x,yBottom,z1]);
      else quad([x,yBottom,z0],[x,yBottom,z1],[x,yTop,z1],[x,yTop,z0]);
    }
  }
 }
 // Tessellate every quad along ALL collinear neighbour edge vertices.
 // This avoids T-junctions generated by greedy meshing, making each solid
 // topologically closed while keeping the exported mesh reasonably small.
 const edgeLines=new Map();
 function lineDef(a,b){
   let axis=0;
   if(Math.abs(a[1]-b[1])>eps)axis=1;
   if(Math.abs(a[2]-b[2])>eps)axis=2;
   const fixed=[0,1,2].filter(i=>i!==axis);
   const key=axis+'|'+a[fixed[0]].toFixed(5)+'|'+a[fixed[1]].toFixed(5);
   return {axis,key};
 }
 for(const q of quads)for(let i=0;i<4;i++){
    const a=q[i],b=q[(i+1)%4],{axis,key}=lineDef(a,b);
    let set=edgeLines.get(key);if(!set){set=new Set();edgeLines.set(key,set)}
    set.add(a[axis]);set.add(b[axis]);
 }
 const sorted=new Map();for(const [key,set] of edgeLines)sorted.set(key,[...set].sort((a,b)=>a-b));
 const triangles=[];
 for(const q of quads){
    const center=[0,0,0];for(const v of q)for(let k=0;k<3;k++)center[k]+=v[k]/4;
    const loop=[];
    for(let i=0;i<4;i++){
      const a=q[i],b=q[(i+1)%4],{axis,key}=lineDef(a,b);
      const from=a[axis],to=b[axis],low=Math.min(from,to),high=Math.max(from,to);
      const vals=sorted.get(key).filter(n=>n>=low-eps&&n<=high+eps);
      if(to<from)vals.reverse();
      for(const t of vals.slice(0,-1)){
        const vertex=[...a];vertex[axis]=t;
        if(!loop.length||loop[loop.length-1].some((v,k)=>Math.abs(v-vertex[k])>eps))loop.push(vertex);
      }
    }
    for(let i=0;i<loop.length;i++){
      const a=loop[i],b=loop[(i+1)%loop.length];
      if(Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2])<eps)continue;
      triangles.push(...center,...a,...b);
    }
 }
 return new Float32Array(triangles);
}

class Renderer{
 constructor(canvas){
  this.canvas=canvas;this.gl=canvas.getContext('webgl',{antialias:true,alpha:true,depth:true,preserveDrawingBuffer:false});
  if(!this.gl){
    this.ctx=canvas.getContext('2d');this.use2d=true;
    this.yaw=-.5;this.pitch=.87;this.zoom=1;this.dim={width:120,height:80,maxZ:3};
    this.rasterLayers=[];this.addInteractions();new ResizeObserver(()=>this.draw()).observe(this.canvas);return;
  }
  const gl=this.gl;
  const vs=`attribute vec3 aPos;attribute vec3 aNorm;uniform vec4 uCamera;uniform vec3 uDims;varying float vShade;void main(){float yaw=uCamera.x,pitch=uCamera.y,zoom=uCamera.z,aspect=uCamera.w;float c=cos(yaw),s=sin(yaw);float rx=c*aPos.x-s*aPos.y;float ry=s*aPos.x+c*aPos.y;float z=aPos.z-uDims.z*0.5;float yy=sin(pitch)*ry-cos(pitch)*z;float depth=cos(pitch)*ry+sin(pitch)*z;float scale=max(uDims.x,uDims.y)*0.52*zoom;gl_Position=vec4(rx/(scale*aspect),yy/scale,-depth/(scale*3.0),1.0);vec3 light=normalize(vec3(0.35,-0.25,0.9));vShade=0.72+0.28*max(0.0,dot(normalize(aNorm),light));}`;
  const fs=`precision mediump float;uniform vec3 uColor;varying float vShade;void main(){gl_FragColor=vec4(uColor*vShade,1.0);}`;
  const sh=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
  const program=gl.createProgram();gl.attachShader(program,sh(gl.VERTEX_SHADER,vs));gl.attachShader(program,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
  this.program=program;this.locations={pos:gl.getAttribLocation(program,'aPos'),norm:gl.getAttribLocation(program,'aNorm'),camera:gl.getUniformLocation(program,'uCamera'),dims:gl.getUniformLocation(program,'uDims'),color:gl.getUniformLocation(program,'uColor')};
  this.meshes=[];this.yaw=-.50;this.pitch=.87;this.zoom=1;this.dim={width:120,height:80,maxZ:3};
  gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.disable(gl.CULL_FACE);
  this.addInteractions();
  new ResizeObserver(()=>this.draw()).observe(this.canvas);
 }
 addInteractions(){
  let last=null;
  this.canvas.addEventListener('pointerdown',e=>{last=[e.clientX,e.clientY];this.canvas.setPointerCapture(e.pointerId)});
  this.canvas.addEventListener('pointermove',e=>{
   if(!last)return;
   this.yaw+=(e.clientX-last[0])*.012;this.pitch=clamp(this.pitch-(e.clientY-last[1])*.012,.1,Math.PI-.10,1);
   last=[e.clientX,e.clientY];this.draw();
  });
  const end=()=>last=null;
  this.canvas.addEventListener('pointerup',end);this.canvas.addEventListener('pointercancel',end);
  this.canvas.addEventListener('wheel',e=>{e.preventDefault();this.zoom=clamp(this.zoom*Math.exp(e.deltaY*.001),.53,2.6,1);this.draw()},{passive:false});
 }
 setView(yaw,pitch){this.yaw=yaw;this.pitch=pitch;this.draw()}
 resetZoom(){this.zoom=1;this.draw()}
 update(meshes,dim,built){
  if(this.use2d){this.dim=dim;this.update2d(built);this.draw();return;}
  if(!this.gl)return;
  const gl=this.gl;this.meshes.forEach(m=>{gl.deleteBuffer(m.p);gl.deleteBuffer(m.n)});this.meshes=[];
  for(const [key,triangles] of Object.entries(meshes)){
    if(!triangles.length)continue;
    const normals=new Float32Array(triangles.length);
    for(let i=0;i<triangles.length;i+=9){
      const ax=triangles[i],ay=triangles[i+1],az=triangles[i+2],bx=triangles[i+3],by=triangles[i+4],bz=triangles[i+5],cx=triangles[i+6],cy=triangles[i+7],cz=triangles[i+8];
      const ux=bx-ax,uy=by-ay,uz=bz-az,vx=cx-ax,vy=cy-ay,vz=cz-az;
      let nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
      const l=Math.hypot(nx,ny,nz)||1;nx/=l;ny/=l;nz/=l;
      for(let j=0;j<9;j+=3){normals[i+j]=nx;normals[i+j+1]=ny;normals[i+j+2]=nz}
    }
    const p=gl.createBuffer(),n=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,p);gl.bufferData(gl.ARRAY_BUFFER,triangles,gl.STATIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER,n);gl.bufferData(gl.ARRAY_BUFFER,normals,gl.STATIC_DRAW);
    this.meshes.push({key,p,n,length:triangles.length/3});
  }
  this.dim=dim;this.draw();
 }
 update2d(built){
  this.rasterLayers=[];
  if(!built)return;
  for(const [key,layers] of Object.entries(built.layersByPart)){
    const hex=state[ROW_COLORS[key]]||'#cccccc';
    const rgb=hex.substring(1).match(/../g).map(x=>parseInt(x,16));
    for(const layer of layers){
      const makeRaster=(shade)=>{
        const c=document.createElement('canvas');c.width=built.Nx;c.height=built.Ny;
        const cx=c.getContext('2d'),img=cx.createImageData(c.width,c.height);
        const r=Math.round(rgb[0]*shade),g=Math.round(rgb[1]*shade),b=Math.round(rgb[2]*shade);
        for(let i=0;i<layer.mask.length;i++)if(layer.mask[i]){
          const at=i*4;img.data[at]=r;img.data[at+1]=g;img.data[at+2]=b;img.data[at+3]=255;
        }
        cx.putImageData(img,0,0);return c;
      };
      this.rasterLayers.push({z0:layer.z0,z1:layer.z1,top:makeRaster(1),side:makeRaster(.70),Nx:built.Nx,Ny:built.Ny});
    }
  }
  this.rasterLayers.sort((a,b)=>a.z0-b.z0||a.z1-b.z1);
 }
 draw2d(){
  const ctx=this.ctx;if(!ctx)return;
  const cssW=Math.max(1,this.canvas.clientWidth),cssH=Math.max(1,this.canvas.clientHeight);
  const dpr=Math.min(window.devicePixelRatio||1,2);
  this.canvas.width=Math.round(cssW*dpr);this.canvas.height=Math.round(cssH*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,cssW,cssH);
  const w=this.dim.width,h=this.dim.height,zMax=this.dim.maxZ;
  const unit=Math.min(cssW/(w*1.55),cssH/(h*1.5))/this.zoom;
  const midX=cssW*.5,midY=cssH*.53;
  ctx.save();ctx.translate(midX,midY+20);
  ctx.scale(unit,unit*.40);ctx.fillStyle='#050d1c';ctx.globalAlpha=.46;
  ctx.beginPath();ctx.ellipse(0,0,w*.66,h*.60,0,0,Math.PI*2);ctx.fill();ctx.restore();ctx.globalAlpha=1;
  const ca=Math.cos(this.yaw),sa=Math.sin(this.yaw),sp=Math.sin(this.pitch),cp=Math.cos(this.pitch);
  const sx=w/(this.rasterLayers[0]?.Nx||1),sy=h/(this.rasterLayers[0]?.Ny||1);
  const drawRaster=(r,z,img)=>{
     // Canvas pixel-to-3D-plane affine projection, including controllable rotation.
     const x0=-w/2,y0=h/2,z0=z-zMax/2;
     const a=unit*ca*sx,b=-unit*sp*sa*sx,c=unit*sa*sy,d=unit*sp*ca*sy;
     const e=midX+unit*(ca*x0-sa*y0),f=midY-unit*(sp*(sa*x0+ca*y0)-cp*z0);
     ctx.setTransform(a,b,c,d,e,f);ctx.imageSmoothingEnabled=false;ctx.drawImage(img,0,0);
  };
  for(const r of this.rasterLayers){
    const parts=Math.max(1,Math.ceil((r.z1-r.z0)/.5));
    for(let n=0;n<parts;n++)drawRaster(r,r.z0+(r.z1-r.z0)*n/parts,r.side);
    drawRaster(r,r.z1,r.top);
  }
  ctx.setTransform(1,0,0,1,0,0);
 }
 draw(){
  if(this.use2d){this.draw2d();return;}
  const gl=this.gl;if(!gl)return;
  const w=Math.max(1,this.canvas.clientWidth),h=Math.max(1,this.canvas.clientHeight),dpr=Math.min(window.devicePixelRatio||1,2);
  const W=Math.floor(w*dpr),H=Math.floor(h*dpr);
  if(this.canvas.width!==W||this.canvas.height!==H){this.canvas.width=W;this.canvas.height=H;}
  gl.viewport(0,0,W,H);gl.clearColor(.055,.09,.15,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
  gl.useProgram(this.program);
  const u=this.locations;
  gl.uniform4f(u.camera,this.yaw,this.pitch,this.zoom,w/h);
  gl.uniform3f(u.dims,this.dim.width,this.dim.height,this.dim.maxZ);
  for(const m of this.meshes){
   const hex=state[ROW_COLORS[m.key]]||'#cccccc',rgb=hex.replace('#','').match(/../g).map(n=>parseInt(n,16)/255);
   gl.uniform3f(u.color,...rgb);
   gl.bindBuffer(gl.ARRAY_BUFFER,m.p);gl.enableVertexAttribArray(u.pos);gl.vertexAttribPointer(u.pos,3,gl.FLOAT,false,0,0);
   gl.bindBuffer(gl.ARRAY_BUFFER,m.n);gl.enableVertexAttribArray(u.norm);gl.vertexAttribPointer(u.norm,3,gl.FLOAT,false,0,0);
   gl.drawArrays(gl.TRIANGLES,0,m.length);
  }
 }
}
async function build(){
 if(isBusy){pendingBuild=true;return}
 isBusy=true;$('#readyBadge').textContent='◌ Построение...';
 try{
  // use validated view snapshot without mutating user inputs while typing.
  const p=normalize(clone(state));
  const built=getGeometry(p);
  model=built;
  renderer?.update(built.meshes,{width:p.width,height:p.height,maxZ:built.maxZ},built);
  $('#sizeMetric').textContent=`${num(p.width)} × ${num(p.height)} мм`;
  $('#thickMetric').textContent=`${num(built.maxZ)} мм`;
  $('#gridMetric').textContent=`${built.Nx} × ${built.Ny}`;
  $('#warnings').textContent=built.warnings.join(' ');
  $('#readyBadge').textContent='● Модель готова';
 }catch(err){model=null;$('#readyBadge').textContent='⚠ Ошибка';$('#warnings').textContent=err.message;console.error(err)}
 finally{isBusy=false;if(pendingBuild){pendingBuild=false;requestBuild()}}
}
function downloadFile(filename,blob){
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;
 document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);
}
function basename(){
 const raw=state.lines.find(l=>l.enabled&&l.value.trim())?.value||'plaque';
 return (raw.normalize('NFKD').replace(/[^a-zA-Z0-9а-яА-ЯёЁ\-_ ]/g,'').trim().replace(/\s+/g,'_').slice(0,44)||'plaque')+'_PlaqueMaker3D';
}
function createStl(triangles){
 const tris=triangles.length/9;
 const buffer=new ArrayBuffer(84+tris*50),view=new DataView(buffer);
 const head='PlaqueMaker 3D | units: mm | solid joined model';
 for(let i=0;i<Math.min(head.length,80);i++)view.setUint8(i,head.charCodeAt(i));
 view.setUint32(80,tris,true);
 let off=84;
 for(let n=0;n<triangles.length;n+=9){
  const ax=triangles[n],ay=triangles[n+1],az=triangles[n+2];
  const bx=triangles[n+3],by=triangles[n+4],bz=triangles[n+5];
  const cx=triangles[n+6],cy=triangles[n+7],cz=triangles[n+8];
  const ux=bx-ax,uy=by-ay,uz=bz-az,vx=cx-ax,vy=cy-ay,vz=cz-az;
  let nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
  let length=Math.hypot(nx,ny,nz)||1;nx/=length;ny/=length;nz/=length;
  for(const val of [nx,ny,nz,ax,ay,az,bx,by,bz,cx,cy,cz]){view.setFloat32(off,val,true);off+=4}
  view.setUint16(off,0,true);off+=2;
 }
 return new Blob([buffer],{type:'model/stl'});
}
function xmlEscape(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&apos;')}
function xmlMesh(triangles){
 // IMPORTANT: a shared physical vertex must have the SAME index across triangles.
 // The v1.0 exporter wrote three new vertices for every triangle, so Creality Print
 // counted every single triangle edge as open (13,396 * 3 = 40,188 open edges).
 // Indexed vertices are necessary for an explicitly watertight 3MF mesh.
 const vertices=[],faces=[],indices=new Map();
 function vertex(x,y,z){
   const key=[x,y,z].map(v=>num(v,5)).join(',');
   let index=indices.get(key);
   if(index===undefined){
     index=vertices.length;
     const [vx,vy,vz]=key.split(',');
     vertices.push(`<vertex x="${vx}" y="${vy}" z="${vz}"/>`);
     indices.set(key,index);
   }
   return index;
 }
 for(let t=0;t<triangles.length;t+=9){
  const v1=vertex(triangles[t],triangles[t+1],triangles[t+2]);
  const v2=vertex(triangles[t+3],triangles[t+4],triangles[t+5]);
  const v3=vertex(triangles[t+6],triangles[t+7],triangles[t+8]);
  if(v1===v2||v2===v3||v1===v3)continue;
  faces.push(`<triangle v1="${v1}" v2="${v2}" v3="${v3}"/>`);
 }
 return `<mesh><vertices>${vertices.join('')}</vertices><triangles>${faces.join('')}</triangles></mesh>`;
}
function create3mfXml(meshes,p){
 const colors=['baseColor','rimColor','textColor','bottomTextColor','accentColor','sideTextColor'].map(k=>p[k].toUpperCase()+'FF');
 const mats=['Основание','Бортик','Текст сверху','Текст снизу','Разделительные линии','Надпись справа'].map((name,i)=>`<base name="${xmlEscape(name)}" displaycolor="${colors[i]}"/>`).join('');
 const children=[],objects=[];
 let id=2;
 for(const [i,key] of ['base','rim','textTop','textBottom','accent','sideText'].entries()){
   const mesh=meshes[key];if(!mesh||!mesh.length)continue;
   objects.push(`<object id="${id}" name="${xmlEscape(key)}" type="model" pid="1" pindex="${i}">${xmlMesh(mesh)}</object>`);
   children.push(`<component objectid="${id}"/>`);id++;
 }
 const parent=id;
 objects.push(`<object id="${parent}" name="PlaqueMaker 3D • one composed plaque" type="model"><components>${children.join('')}</components></object>`);
 const xml=`<?xml version="1.0" encoding="UTF-8"?>`+
  `<model unit="millimeter" xml:lang="ru-RU" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">`+
  `<metadata name="Title">PlaqueMaker 3D custom plaque</metadata><metadata name="Application">PlaqueMaker3D v1.3</metadata>`+
  `<resources><basematerials id="1">${mats}</basematerials>${objects.join('')}</resources>`+
  `<build><item objectid="${parent}"/></build></model>`;
 return xml;
}
// ZIP format writer for 3MF with CRC32 and optional browser-native DEFLATE.
const enc=new TextEncoder();
const crcTable=(()=>{const t=new Uint32Array(256);for(let i=0;i<256;i++){let c=i;for(let j=0;j<8;j++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[i]=c>>>0;}return t})();
function crc32(bytes){let c=0xFFFFFFFF;for(let i=0;i<bytes.length;i++)c=crcTable[(c^bytes[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0}
function concat(arr){const n=arr.reduce((sum,a)=>sum+a.length,0),out=new Uint8Array(n);let off=0;for(const a of arr){out.set(a,off);off+=a.length}return out}
async function compress(bytes){
 if(!('CompressionStream' in window))return {method:0,bytes};
 try{
  const s=new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate-raw'));
  return {method:8,bytes:new Uint8Array(await new Response(s).arrayBuffer())};
 }catch{return {method:0,bytes}}
}
async function zip3mf(entries){
 const files=[],central=[],meta=[];let offset=0;
 for(const [name,string] of entries){
  const fn=enc.encode(name),raw=enc.encode(string),packed=await compress(raw),data=packed.bytes,checksum=crc32(raw);
  const header=new Uint8Array(30+fn.length),h=new DataView(header.buffer);
  h.setUint32(0,0x04034b50,true);h.setUint16(4,20,true);h.setUint16(6,0,true);h.setUint16(8,packed.method,true);
  h.setUint32(14,checksum,true);h.setUint32(18,data.length,true);h.setUint32(22,raw.length,true);h.setUint16(26,fn.length,true);header.set(fn,30);
  files.push(header,data);meta.push({fn,raw,data,checksum,method:packed.method,offset});offset+=header.length+data.length;
 }
 for(const m of meta){
  const hbuf=new Uint8Array(46+m.fn.length),h=new DataView(hbuf.buffer);
  h.setUint32(0,0x02014b50,true);h.setUint16(4,20,true);h.setUint16(6,20,true);
  h.setUint16(10,m.method,true);h.setUint32(16,m.checksum,true);
  h.setUint32(20,m.data.length,true);h.setUint32(24,m.raw.length,true);
  h.setUint16(28,m.fn.length,true);h.setUint32(42,m.offset,true);hbuf.set(m.fn,46);central.push(hbuf);
 }
 const centralSize=central.reduce((s,a)=>s+a.length,0),end=new Uint8Array(22),dv=new DataView(end.buffer);
 dv.setUint32(0,0x06054b50,true);dv.setUint16(8,meta.length,true);dv.setUint16(10,meta.length,true);
 dv.setUint32(12,centralSize,true);dv.setUint32(16,offset,true);
 return new Blob([...files,...central,end],{type:'model/3mf'});
}
async function exportModel(type){
 const btn=$('#export'+(type==='stl'?'Stl':'3mf'));
 // If user clicked before debounce elapsed, regenerate from the latest values.
 clearTimeout(buildHandle);
 if(isBusy){alert('Построение модели ещё не завершено. Повтори экспорт.');return}
 btn.disabled=true;
 const original=btn.innerHTML;
 btn.innerHTML=type==='stl'?'Готовим STL…':'Готовим 3MF…';
 try{
  const p=normalize(clone(state));
  // Always export from fresh state; never export a stale preview.
  const output=getGeometry(p);
  if(!output.unified.length)throw Error('Модель пуста. Проверь размеры и текст.');
  const blob=type==='stl'?createStl(output.unified):await zip3mf([
   ['[Content_Types].xml',`<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>`],
   ['_rels/.rels',`<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>`],
   ['3D/3dmodel.model',create3mfXml(output.meshes,p)]
  ]);
  downloadFile(basename()+'.'+type,blob);
  $('#readyBadge').textContent=`✓ ${type.toUpperCase()} создан`;
 }catch(err){console.error(err);alert('Не удалось создать модель: '+err.message);$('#readyBadge').textContent='⚠ Ошибка экспорта';}
 finally{btn.disabled=false;btn.innerHTML=original}
}

createLineControls();initFontGallery();connectControls();reflectState();
try{renderer=new Renderer($('#preview'))}catch(err){console.error('WebGL:',err);$('#previewFallback').hidden=false}
requestBuild();
// PWA support (useful once deployed on HTTPS; file:// still works without it).
if(location.protocol.startsWith('http')&&'serviceWorker' in navigator){navigator.serviceWorker.register('./service-worker.js').catch(()=>{})}
// Expose limited debugging introspection for offline smoke tests.
window.__plaqueTest={fontOptions:()=>FONT_LIBRARY.map(f=>({id:f.id,langs:f.langs})),getEffectiveFont:()=>normalize(clone(state)).fontFamily,getState:()=>clone(state),build:()=>getGeometry(normalize(clone(state))),setState:s=>{state=normalize({...clone(DEFAULTS),...s});reflectState();requestBuild()},create3mfXml};
})();
