/* Actions, form handlers, event wiring and page boot. */

function act(a,d,el){
 const u=me();
 switch(a){
  case 'authmode': location.href=BASE+(d.m==='register'?'register.html':'login.html');break;
  case 'demo': $('input[name=email]').value=d.e;$('input[name=pass]').value=d.p;break;
  case 'togglepw':{
   const i=el.parentElement.querySelector('input');const show=i.type==='password';
   i.type=show?'text':'password';el.textContent=show?'Hide':'Show';
   el.setAttribute('aria-label',show?'Hide password':'Show password');break;}
  case 'logout': db.session=null;save();location.href=BASE+'login.html';break;
  case 'nav': goTo(d.v,u.role);break;
  case 'pick': $('#up').click();break;
  case 'closem': closeM();break;
  case 'ask': confirmM(d);break;
  case 'yes': closeM();act(d.then,{id:d.id});break;

  case 'analyze':{
   const I=db.insp;
   if(!I.img){toast('Add a produce photo first');break}
   I.st='scan';save();render();
   setTimeout(()=>{I.st='done';save();render()},1600);
   break;}
  case 'manual': toast('Manual inspection requested (demo: queued).',true);break;
  case 'publish':{
   const I=db.insp;
   const L={id:'L'+Date.now().toString(36),farmer:u.id,crop:I.crop,qty:+I.qty||100,grade:'A',loc:I.loc.split(',')[0],ask:+I.ask||REF_PRICE,status:'active',verified:true,img:I.img||null};
   db.listings.push(L);
   log(u.name+' listed '+L.qty+' kg of '+L.crop);
   if(!save()){toast('Browser storage is full. Remove an older listing or use a smaller photo.');break}
   db.insp={crop:I.crop,qty:I.qty,loc:I.loc,st:'idle',img:null,ask:REF_PRICE};save();
   toast('Listing published. Buyers can now find it.',true);
   goTo('market','farmer');break;}
  case 'detail':{const l=listingOf(d.id);if(l)openM(detailHTML(l));break;}
  case 'placebid':{
   const l=listingOf(d.id);if(!l)break;
   const p=Math.round(+$('#bp').value),q=Math.round(+$('#bq').value),dl=$('#bl').value.trim();
   if(!(p>0)){toast('Enter a price per quintal greater than zero');break}
   if(!(q>0&&q<=l.qty)){toast('Quantity must be between 1 and '+num(l.qty)+' kg');break}
   if(!dl){toast('Enter a delivery location');break}
   db.bids.push({id:'B'+Date.now().toString(36),listing:l.id,buyerId:u.id,buyer:u.name,price:p,qty:q,deliver:dl,t:stamp(),status:'pending'});
   log(u.name+' bid '+fmt(p)+'/qtl on '+l.crop);save();closeM();
   toast('Bid submitted',true);render();break;}
  case 'raise':{
   const b=db.bids.find(x=>x.id===d.id);
   if(b&&b.status==='pending'){b.price+=20;log(u.name+' raised bid to '+fmt(b.price));save();render();toast('Bid raised to '+fmt(b.price),true)}
   break;}
  case 'doaccept':{
   const b=db.bids.find(x=>x.id===d.id);if(!b||b.status!=='pending')break;
   b.status='accepted';
   const L=listingOf(b.listing);if(L)L.status='sold';
   db.bids.filter(x=>x.listing===b.listing&&x.id!==b.id&&x.status==='pending').forEach(x=>x.status='rejected');
   log('Accepted '+b.buyer+' at '+fmt(b.price)+'/qtl');save();render();
   toast('Bid accepted. Sale recorded.',true);break;}
  case 'doreject':{
   const b=db.bids.find(x=>x.id===d.id);if(!b||b.status!=='pending')break;
   b.status='rejected';log('Rejected bid from '+b.buyer);save();render();toast('Bid rejected');break;}
  case 'save':{
   const i=db.saved.indexOf(d.id);i>=0?db.saved.splice(i,1):db.saved.push(d.id);
   save();render();break;}
  case 'mod':{
   const l=listingOf(d.id);if(!l)break;
   if(l.status==='hidden'&&u.role!=='admin')break;
   const hide=l.status==='active';
   l.status=hide?(u.role==='admin'?'hidden':'withdrawn'):'active';
   log('Listing '+l.crop+' '+(l.status==='active'?'restored':l.status));
   save();render();toast(l.status==='active'?'Listing restored':'Listing '+l.status,true);break;}
  case 'verify':{
   const x=userById(d.id);if(!x)break;
   x.verified=!x.verified;log('Buyer '+x.name+(x.verified?' verified':' verification revoked'));
   save();render();toast(x.name+(x.verified?' verified':' verification revoked'),true);break;}
 }
}

/* Click, keyboard and form wiring */
document.addEventListener('click',e=>{
 const el=e.target.closest('[data-act]');
 if(!el)return;
 if(el.id==='modal'&&e.target!==el)return;
 act(el.dataset.act,el.dataset,el);
});
document.addEventListener('keydown',e=>{
 if(e.key==='Escape')closeM();
 if((e.key==='Enter'||e.key===' ')&&e.target.matches&&e.target.matches('[role="button"][data-act]')){
  e.preventDefault();e.target.click();
 }
});
document.addEventListener('submit',e=>{
 const f=e.target.dataset.form;if(!f)return;e.preventDefault();
 const v=Object.fromEntries(new FormData(e.target));
 if(f==='login')login(v.email,v.pass);
 if(f==='register')register(v);
});
function register(v){
 if(db.users.some(x=>x.email.toLowerCase()===v.email.toLowerCase())){toast('An account with this email already exists');return}
 if(v.phone&&!/^[6-9]\d{9}$/.test(v.phone)){toast('Enter a valid 10-digit mobile number');return}
 const id='u'+Date.now().toString(36);
 db.users.push({id,role:v.role,name:v.name.trim(),email:v.email.trim(),pass:v.pass,phone:v.phone||'',loc:v.district?v.district+', Karnataka':'',verified:false});
 db.session=id;db.nav='overview';log(v.name+' registered as '+v.role);save();
 toast('Account created',true);
 location.href=BASE+v.role+'/dashboard.html';
}
function setPhoto(file){
 readImage(file).then(url=>{
  db.insp.img=url;db.insp.st='idle';
  if(!save())toast('This photo is too large to keep in the browser. Try a smaller image.');
  render();
 }).catch(()=>toast('That file could not be read as an image'));
}
function onIn(e){
 const t=e.target;
 if(e.type==='input'&&t.tagName==='SELECT')return;
 if(t.dataset.u){const f=t.files&&t.files[0];if(f)setPhoto(f);return}
 if(t.dataset.i){db.insp[t.dataset.i]=t.value;save();return}
 if(t.dataset.p){PR[t.dataset.p]=t.dataset.p==='range'?+t.value:t.value;render();return}
 if(t.dataset.f){F[t.dataset.f]=t.value;const g=$('#grid');if(g)g.innerHTML=gridHTML();}
}
document.addEventListener('input',onIn);
document.addEventListener('change',onIn);
document.addEventListener('dragover',e=>{if(e.target.closest&&e.target.closest('#drop'))e.preventDefault()});
document.addEventListener('drop',e=>{
 const dz=e.target.closest&&e.target.closest('#drop');if(!dz)return;e.preventDefault();
 const f=e.dataTransfer.files[0];
 if(f&&f.type.startsWith('image/'))setPhoto(f);else toast('Drop a JPG or PNG image');
});

/* ---------- Page boot (multi-page entry) ---------- */
const P=window.AV_PAGE||{};
if(P.kind==='index'){
 location.href=BASE+(db.session&&me()?me().role+'/dashboard.html':'login.html');
}else if(P.kind==='auth'){
 if(db.session&&me()){location.href=BASE+me().role+'/dashboard.html'}
 else renderAuth(P.mode||'login');
}else if(!db.session||!me()){
 location.href=BASE+'login.html';
}else if(me().role!==P.role){
 location.href=BASE+me().role+'/dashboard.html';
}else{
 db.nav=P.view||'overview';save();render();
}
