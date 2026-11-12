import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { SVGRenderer } from 'three/addons/renderers/SVGRenderer.js';
const $=id=>document.getElementById(id), data=JSON.parse($('assembly-data').textContent);
const brakeOnly=document.body.dataset.mode==='brake';const focus=new THREE.Vector3(brakeOnly?85:0,brakeOnly?-8:0,brakeOnly?28:0);
const stage=$('stage');let canvas=$('canvas'),renderer,software=false;
if(canvas.getContext('webgl2')){renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));}
else {software=true;renderer=new SVGRenderer();canvas.replaceWith(renderer.domElement);canvas=renderer.domElement;canvas.id='canvas';canvas.setAttribute('aria-label','Drag to rotate CAD, software rendering');canvas.style.cssText='display:block;width:100%;height:100%;touch-action:none';$('saveImage').textContent='Save SVG ↓';}
renderer.setClearColor(0xf5f6f5);
renderer.outputColorSpace=THREE.SRGBColorSpace;
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(35,1,.1,4000);
camera.position.copy(focus).add(brakeOnly?new THREE.Vector3(150,100,230):new THREE.Vector3(320,190,480));
const controls=new OrbitControls(camera,canvas);controls.target.copy(focus);controls.enableDamping=true;controls.minDistance=160;controls.maxDistance=1500;
scene.add(new THREE.AmbientLight(0xffffff,.65));
for(const [p,v] of [[[250,350,400],.85],[[-300,50,-100],.35]]){const l=new THREE.DirectionalLight(0xffffff,v);l.position.set(...p);scene.add(l);}
const group=new THREE.Group();scene.add(group);
const meshes=new Map(), buttons=new Map();let selected=null,isolated=false,explosion=0;
for(const d of data){
 let geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(d.vertices.flat(),3));geometry.setIndex(d.faces.flat());geometry=geometry.toNonIndexed();geometry.computeVertexNormals();
 const material=new THREE.MeshPhongMaterial({color:d.color,shininess:d.kind==='printed'?15:60,side:THREE.FrontSide});
 const mesh=new THREE.Mesh(geometry,material);mesh.userData=d;group.add(mesh);meshes.set(d.id,mesh);
 if(['lid'].includes(d.id)){const edges=new THREE.LineSegments(new THREE.EdgesGeometry(geometry,25),new THREE.LineBasicMaterial({color:0x6f9991,transparent:true,opacity:.25}));mesh.userData.edges=edges;group.add(edges);}
 if(d.kind!=='fastener'&&d.id!=='shaft'&&d.id!=='pads'){
  const button=document.createElement('button');button.className='part';button.innerHTML=`<i class="swatch" style="background:${d.color}"></i><span>${d.label}</span>`;button.onclick=()=>select(d.id);$('parts').appendChild(button);buttons.set(d.id,button);
 }
}
function select(id){selected=id;for(const [key,m]of meshes)m.material.emissive.set(key===id?'#173e37':'#000000');for(const[k,b]of buttons)b.classList.toggle('active',k===id);const d=meshes.get(id).userData;$('detail').innerHTML=`<strong>${d.label}</strong><br>${d.note}${d.file?`<br><a href="${d.file}" download>Download ${d.reference?"reference":"fit"} STL ↓</a>`:''}`;$('selectionCaption').textContent=d.label;if(isolated)refresh();draw();}
function refresh(){
 const transparent=$('transparent').checked;
 for(const [id,m]of meshes){const d=m.userData;m.position.set(...d.explode.map(v=>v*explosion));const visible=(!isolated||id===selected)&&($('fasteners').checked||d.kind!=='fastener')&&($('motorVisible').checked||!['motor','shaft'].includes(id));const ghost=transparent&&['lid'].includes(id)&&!isolated;m.visible=visible&&!ghost;if(d.edges){d.edges.visible=visible&&ghost;d.edges.position.copy(m.position);}}
 $('explodedValue').value=Math.round(explosion*100)+'%';$('viewState').textContent=(explosion===0?'Assembled':`Exploded · ${Math.round(explosion*100)}%`)+(transparent?' · casing transparent':'');
 $('assembled').classList.toggle('active',explosion===0);$('exploded').classList.toggle('active',explosion===1);
 draw();
}
function setExplosion(value){explosion=value;$('explode').value=100*value;refresh();controls.target.copy(focus);controls.target.z+=85*explosion;}
$('explode').oninput=e=>setExplosion(Number(e.target.value)/100);
$('assembled').onclick=()=>setExplosion(0);$('exploded').onclick=()=>{setExplosion(1);camera.position.set(460,240,520);};
for(const id of ['transparent','fasteners','motorVisible'])$(id).onchange=refresh;
$('isolate').onclick=()=>{if(!selected)select(brakeOnly?'caliper':'housing');isolated=true;refresh();};
$('showAll').onclick=()=>{isolated=false;$('fasteners').checked=true;$('motorVisible').checked=true;refresh();};
function view(type){const t=controls.target.clone(),d=explosion?650:(brakeOnly?250:540);camera.up.set(0,1,0);camera.position.copy(t).add(type==='front'?new THREE.Vector3(0,0,d):type==='side'?new THREE.Vector3(d,0,0):new THREE.Vector3(d*.63,d*.4,d*.98));controls.update();}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));
$('reset').onclick=()=>{isolated=false;$('transparent').checked=false;$('fasteners').checked=true;$('motorVisible').checked=true;setExplosion(0);view('iso');};
$('saveImage').onclick=()=>{renderer.render(scene,camera);const a=document.createElement('a');a.href=software?URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(canvas)],{type:'image/svg+xml'})):canvas.toDataURL('image/png');a.download='motor-mounted-brake-'+(explosion?'exploded':'assembled')+'-FIT-ONLY.'+(software?'svg':'png');a.click();if(software)setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
let start;canvas.addEventListener('pointerdown',e=>start=[e.clientX,e.clientY]);canvas.addEventListener('pointerup',e=>{if(!start||Math.hypot(e.clientX-start[0],e.clientY-start[1])>5)return;const r=canvas.getBoundingClientRect(),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hits=ray.intersectObjects([...meshes.values()].filter(m=>m.visible&&(!m.material.transparent||m.material.opacity>.5)));if(hits.length)select(hits[0].object.userData.id);});
new ResizeObserver(()=>{const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();draw();}).observe(stage);
let queued=false;function draw(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;controls.update();renderer.render(scene,camera);});}
controls.enableDamping=!software;controls.addEventListener('change',draw);refresh();draw();
window.cadViewer={meshes,select,setExplosion,scene,camera,getState:()=>({parts:meshes.size,software,explosion,selected,isolated,visible:[...meshes].filter(([id,m])=>m.visible).map(([id])=>id),triangles:renderer.info.render.triangles??renderer.info.render.faces})};
document.body.dataset.viewerReady='true';
