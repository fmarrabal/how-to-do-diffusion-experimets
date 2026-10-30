/* Genuine Three.js 3D ensemble; trajectories and statistics are separate. */
(function(){
 'use strict';
 let renderer,scene,camera,particles,cube,matrix,temp,trajectories;
 const N=96,STEPS=450,blue=0x53d4ff,orange=0xffba68;
 let lastSize='';
 function random(seed){let x=seed|0;return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return((x>>>0)+1)/4294967297;};}
 function init(){
  if(!window.THREE)return false;
  try {
   renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setClearColor(0x07131f,0);renderer.outputColorSpace=THREE.SRGBColorSpace;
   scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(36,1,.1,500);camera.position.set(56,38,58);camera.lookAt(0,0,0);
   scene.add(new THREE.AmbientLight(0xa4d5ef,2.3));const light=new THREE.DirectionalLight(0xffffff,3.4);light.position.set(20,30,25);scene.add(light);
   cube=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(44,44,44)),new THREE.LineBasicMaterial({color:0x37667a,transparent:true,opacity:.65}));scene.add(cube);
   const grid=new THREE.GridHelper(44,8,0x426878,0x173b4d);grid.position.y=-22;scene.add(grid);
   particles=new THREE.InstancedMesh(new THREE.SphereGeometry(.72,12,10),new THREE.MeshStandardMaterial({roughness:.3,metalness:.15}),N);particles.instanceMatrix.setUsage(THREE.DynamicDrawUsage);for(let i=0;i<N;i++)particles.setColorAt(i,new THREE.Color(i<N/2?blue:orange));particles.instanceColor.needsUpdate=true;scene.add(particles);matrix=new THREE.Matrix4();temp=new THREE.Object3D();
   const axis=new THREE.ArrowHelper(new THREE.Vector3(0,1,0),new THREE.Vector3(25,-22,-22),47,0xba9aff,2,1);scene.add(axis);
   const rng=random(208147),normal=()=>Math.sqrt(-2*Math.log(rng()))*Math.cos(2*Math.PI*rng());trajectories=[];
   for(let i=0;i<N;i++){const coords=new Float32Array((STEPS+1)*3);for(let k=1;k<=STEPS;k++)for(let j=0;j<3;j++)coords[k*3+j]=coords[(k-1)*3+j]+normal()*Math.sqrt(2*.7);trajectories.push({origin:[(rng()-.5)*18,(rng()-.5)*18,(rng()-.5)*18],coords});}
   return true;
  }catch(e){window.DiffusionThreeFallback=String(e);renderer=null;return false;}
 }
 function label(c,s,x,y,size=15,col='#c6dfed'){c.fillStyle=col;c.font=`${size}px "Segoe UI",sans-serif`;c.fillText(s,x,y);}
 function graph(c,x,y,w,h,D1,D2,tm,lang,totalTime){
  const ymax=6*Math.max(D1,D2)*totalTime;c.strokeStyle='#2a4d63';c.lineWidth=1;c.beginPath();c.moveTo(x,y);c.lineTo(x,y+h);c.lineTo(x+w,y+h);c.stroke();
  for(let k=0;k<=3;k++){const yy=y+h-h*k/3;c.strokeStyle='#1e3b50';c.beginPath();c.moveTo(x,yy);c.lineTo(x+w,yy);c.stroke();label(c,String(Math.round(ymax*k/3)),x-37,yy+4,11,'#7698ad');label(c,String(Math.round(k*totalTime/3)),x+w*k/3-9,y+h+21,11,'#7698ad');}
  for(const [D,color] of [[D1,'#53d4ff'],[D2,'#ffba68']]){c.strokeStyle=color;c.lineWidth=3;c.beginPath();c.moveTo(x,y+h);c.lineTo(x+w*tm/totalTime,y+h-h*6*D*tm/ymax);c.stroke();c.fillStyle=color;c.beginPath();c.arc(x+w*tm/totalTime,y+h-h*6*D*tm/ymax,4,0,Math.PI*2);c.fill();}
  label(c,'⟨r²⟩ / µm²',x,y-20,13);label(c,lang==='es'?'Tiempo / ms':'Time / ms',x+w/2-30,y+h+43,12,'#7698ad');
 }
 window.ThreeScenes={render(c,id,t,p,lang,w,h){
  if(id!=='brownian')return false;if(!renderer&&!init())return false;
  const D1=Number(p.D1??p.Dslow??p.dSlow??p.slowD??.3),D2=Number(p.D2??p.Dfast??p.dFast??p.fastD??1.2);
  const totalTime=Number(p.Delta??100),tm=Math.max(0,Math.min(totalTime,t/18*totalTime)),u=tm/.7,index=Math.min(STEPS-1,Math.floor(u)),fraction=u-index;
  const small=w<750,pw=small?w-20:w*.64,ph=small?h*.47:h*.83,px=small?10:10,py=35;
  const renderScale=window.DiffusionRenderScale||1;const size=Math.round(pw)+'x'+Math.round(ph)+'@'+renderScale;if(size!==lastSize){renderer.setPixelRatio(renderScale);renderer.setSize(Math.round(pw),Math.round(ph),false);camera.aspect=pw/ph;camera.updateProjectionMatrix();lastSize=size;}
  for(let i=0;i<N;i++){const data=trajectories[i],scale=Math.sqrt(i<N/2?D1:D2);for(let j=0;j<3;j++){const raw=data.origin[j]+scale*((1-fraction)*data.coords[index*3+j]+fraction*data.coords[(index+1)*3+j]);const wrapped=((raw+22)%44+44)%44-22;temp.position.setComponent(j,wrapped);}temp.rotation.set(0,0,0);temp.scale.setScalar(i<N/2?1.25:.82);temp.updateMatrix();particles.setMatrixAt(i,temp.matrix);}particles.instanceMatrix.needsUpdate=true;
  const angle=.7+t*.023+Number(p._yaw||0);camera.position.set(80*Math.sin(angle),34,80*Math.cos(angle));camera.lookAt(0,0,0);renderer.render(scene,camera);c.drawImage(renderer.domElement,px,py,pw,ph);
  const gx=small?52:w*.7,gy=small?h*.57:85,gw=small?w-93:w*.24,gh=small?h*.26:h*.46;
  label(c,lang==='es'?'Ensamble browniano · Three.js 3D':'Brownian ensemble · Three.js 3D',25,18,Math.max(12,w/105),'#a6ead6');
  graph(c,gx,gy,gw,gh,D1,D2,tm,lang,totalTime);
  label(c,`D₁ = ${D1.toFixed(2)} × 10⁻⁹ m²/s`,gx,gy+gh+75,Math.max(12,w/110),'#53d4ff');label(c,`D₂ = ${D2.toFixed(2)} × 10⁻⁹ m²/s`,gx,gy+gh+101,Math.max(12,w/110),'#ffba68');
  label(c,'⟨r²⟩ = 6 D t',gx,gy+gh+138,Math.max(18,w/70),'#e5f3ff');
  label(c,lang==='es'?'Ventana 44 µm · envoltura sólo visual':'44 µm view · visual wrapping only',25,Math.min(h-20,py+ph+16),12,'#8fafc4');
  label(c,lang==='es'?'No hay pared física ni deriva media':'No physical wall or mean drift',25,Math.min(h-3,py+ph+35),12,'#8fafc4');return true;
 },available:()=>Boolean(renderer),version:'three@0.180.0'};
})();
