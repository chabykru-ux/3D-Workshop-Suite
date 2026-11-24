(()=>{
const num=(v,n)=>Number(v).toFixed(n);
function createStl(triangles){
 const tris=triangles.length/9;
 const buffer=new ArrayBuffer(84+tris*50),view=new DataView(buffer);
 const head='FurnitureMaker 3D | units: mm | solid joined model';
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

function xml(meshes){let keys=Object.keys(meshes),mats=keys.map((k,i)=>`<base name="Color ${i+1}" displaycolor="${k.toUpperCase()}FF"/>`).join(''),objects=keys.map((k,i)=>`<object id="${i+2}" name="${'COLOR_'+(i+1)+'_'+k.slice(1)}" type="model" pid="1" pindex="${i}">${xmlMesh(meshes[k])}</object>`).join(''),id=keys.length+2,children=keys.map((k,i)=>`<component objectid="${i+2}"/>`).join('');return `<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Application">FurnitureMaker 3D v0.2.2</metadata><resources><basematerials id="1">${mats}</basematerials>${objects}<object id="${id}" name="FurnitureMaker 3D" type="model"><components>${children}</components></object></resources><build><item objectid="${id}"/></build></model>`;}
const mf=async meshes=>zip3mf([['[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'],['_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'],['3D/3dmodel.model',xml(meshes)]]);
window.FurnitureExport={stl:createStl,mf,xml};})();