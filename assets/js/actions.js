/* Actions, forms, image analysis, event wiring and page boot. Every control here does something real in this prototype. */

/* ===== BACKEND BRIDGE =====
   These functions replace localStorage mutations with API calls.
   The existing act() switch cases call these instead of modifying db directly.
   On API success, they reload data into db and re-render. */

async function ensureAuthenticated() {
  if (API.Auth.isLoggedIn()) return true;
  const user = me();
  if (!user || !user.email) return false;
  const pass = user.pass || (user.role === 'farmer' ? 'farmer123' : user.role === 'buyer' ? 'buyer123' : 'admin123');
  try {
    const r = await API.login(user.email, pass);
    if (r && r.ok) {
      const d = await r.json();
      const access = d.access || d.tokens?.access;
      const refresh = d.refresh || d.tokens?.refresh;
      API.Auth.setTokens(access, refresh);
      API.Auth.setUser(d.user);
      return true;
    }
  } catch(e) {}
  return false;
}

async function apiLogin(email, pass) {
  try {
    const r = await API.login(email, pass);
    const d = await r.json();
    if (!r.ok) { toast(d.detail || d.non_field_errors?.[0] || 'Login failed'); return; }
    const access = d.access || d.tokens?.access;
    const refresh = d.refresh || d.tokens?.refresh;
    API.Auth.setTokens(access, refresh);
    API.Auth.setUser(d.user);
    // Also set db.session shim for compatibility
    db.session = d.user.id;
    db.nav = 'overview';
    const adapted = APIAdapter.user(d.user);
    // Upsert into db.users
    const idx = db.users.findIndex(u => u.id === adapted.id);
    if (idx >= 0) db.users[idx] = adapted; else db.users.push(adapted);
    save();
    toast('Welcome, ' + (d.user.full_name || '').split(' ')[0], true);
    location.href = BASE + d.user.role + '/dashboard.html';
  } catch (e) { toast('Connection error. Is the backend running?'); }
}

async function apiRegister(v) {
  const payload = {
    email: v.email.trim(),
    password: v.pass,
    full_name: (v.name || v.company || '').trim(),
    role: v.role,
    phone: v.phone || '',
  };
  if (v.role === 'farmer') {
    payload.farm_name = (v.farm || '').trim();
    payload.village = (v.village || '').trim();
    payload.district = v.district;
    payload.state = v.state || 'Karnataka';
    payload.farm_size = 0;
  } else {
    payload.company_name = (v.company || '').trim();
    payload.contact_person = (v.contactPerson || '').trim();
    payload.business_type = v.business || 'Wholesaler';
    payload.district = v.district;
    payload.state = v.state || 'Karnataka';
  }
  try {
    const r = await API.register(payload);
    const d = await r.json();
    if (!r.ok) {
      const msg = d.email?.[0] || d.non_field_errors?.[0] || d.detail || JSON.stringify(d);
      toast(msg); return;
    }
    const access = d.access || d.tokens?.access;
    const refresh = d.refresh || d.tokens?.refresh;
    API.Auth.setTokens(access, refresh);
    API.Auth.setUser(d.user);
    db.session = d.user.id;
    const adapted = APIAdapter.user(d.user);
    db.users.push(adapted);
    save();
    toast('Account created. Verification is pending.', true);
    location.href = BASE + d.user.role + '/dashboard.html';
  } catch (e) { toast('Connection error. Is the backend running?'); }
}

async function apiLoadMyListings() {
  await ensureAuthenticated();
  if (!API.Auth.isLoggedIn()) return;
  try {
    const r = await API.getProducts();
    if (!r || !r.ok) return;
    const d = await r.json();
    const items = Array.isArray(d) ? d : (d.results || []);
    items.forEach(l => {
      const adapted = APIAdapter.listing(l);
      const idx = db.listings.findIndex(x => x.id === adapted.id);
      if (idx >= 0) db.listings[idx] = adapted; else db.listings.push(adapted);
    });
    save();
    if (typeof render === 'function') render();
  } catch (e) { console.warn('apiLoadMyListings:', e); }
}

async function apiLoadBids() {
  await ensureAuthenticated();
  if (!API.Auth.isLoggedIn()) return;
  try {
    const r = await API.getBids();
    if (!r || !r.ok) return;
    const d = await r.json();
    const items = Array.isArray(d) ? d : (d.results || []);
    items.forEach(b => {
      const adapted = APIAdapter.bid(b);
      const idx = db.deals.findIndex(x => x.id === adapted.id);
      if (idx >= 0) db.deals[idx] = adapted; else db.deals.push(adapted);
    });
    save();
    if (typeof render === 'function') render();
  } catch (e) { console.warn('apiLoadBids:', e); }
}

async function apiPlaceBid(listingId, price, qty, message, delivery) {
  try {
    await ensureAuthenticated();
    const r = await API.createBid({ listing_id: listingId, offered_price: price, quantity: qty, message: message || '', delivery_preference: delivery || '' });
    const d = await r.json();
    if (!r.ok) {
      if (d.code === 'token_not_valid') {
        API.Auth.clear();
        await ensureAuthenticated();
        const retry = await API.createBid({ listing_id: listingId, offered_price: price, quantity: qty, message: message || '', delivery_preference: delivery || '' });
        if (retry.ok) {
          const rd = await retry.json();
          db.deals.push(APIAdapter.bid(rd));
          save();
          return true;
        }
      }
      const msg = d.detail || (d.listing_id && d.listing_id[0]) || (d.non_field_errors && d.non_field_errors[0]) || (typeof d === 'string' ? d : JSON.stringify(d));
      toast(msg);
      return false;
    }
    const adapted = APIAdapter.bid(d);
    db.deals.push(adapted);
    save();
    return true;
  } catch (e) { toast('Connection error'); return false; }
}

async function apiAcceptBid(bidId) {
  try {
    await ensureAuthenticated();
    const r = await API.acceptBid(bidId);
    const d = await r.json();
    if (!r.ok) {
      if (d.code === 'token_not_valid') {
        API.Auth.clear();
        await ensureAuthenticated();
        const retry = await API.acceptBid(bidId);
        if (retry.ok) {
          await apiLoadMyListings();
          await apiLoadBids();
          return true;
        }
      }
      toast(d.detail || 'Accept failed');
      return false;
    }
    await apiLoadMyListings();
    await apiLoadBids();
    return true;
  } catch (e) { toast('Connection error'); return false; }
}

async function apiRejectBid(bidId) {
  try {
    await ensureAuthenticated();
    const r = await API.rejectBid(bidId);
    if (!r || !r.ok) { toast('Reject failed'); return false; }
    await apiLoadBids();
    return true;
  } catch (e) { toast('Connection error'); return false; }
}

async function apiCounterBid(bidId, price, qty, note) {
  try {
    await ensureAuthenticated();
    const r = await API.counterBid(bidId, { offered_price: price, quantity: qty, message: note || '' });
    const d = await r.json();
    if (!r.ok) { toast(d.detail || 'Counter failed'); return false; }
    await apiLoadBids();
    return true;
  } catch (e) { toast('Connection error'); return false; }
}

// Called on page boot if logged in via API
async function syncFromBackend() {
  await ensureAuthenticated();
  const user = API.Auth.getUser();
  if (!user) return;
  db.session = user.id;
  const adapted = APIAdapter.user(user);
  const idx = db.users.findIndex(u => u.id === adapted.id);
  if (idx >= 0) db.users[idx] = adapted; else db.users.push(adapted);
  await Promise.all([apiLoadMyListings(), apiLoadBids()]);
}
/* ===== END BACKEND BRIDGE ===== */

/* ---------- Image analysis (demonstration rule on real pixels) ---------- */
function imageFeatures(src){
 return new Promise((res,rej)=>{
  const img=new Image();
  img.onload=()=>{
   const S=64,c=document.createElement('canvas');c.width=S;c.height=S;
   const g=c.getContext('2d');g.drawImage(img,0,0,S,S);
   const d=g.getImageData(0,0,S,S).data;
   let n=0,sL=0,sRG=0,sLL=0,sRGRG=0;const Ls=[];
   for(let i=0;i<d.length;i+=4){
    const r=d[i],gg=d[i+1],b=d[i+2];
    if(r+gg+b>560)continue;               // ignore light background (cream/white) so only produce is measured
    const L=0.3*r+0.59*gg+0.11*b,rg=r-gg;
    n++;sL+=L;sRG+=rg;sLL+=L*L;sRGRG+=rg*rg;Ls.push(L);
   }
   if(!n){rej(new Error('No produce detected'));return}
   const mL=sL/n,mRG=sRG/n;
   const sdL=Math.sqrt(Math.max(0,sLL/n-mL*mL)),sdRG=Math.sqrt(Math.max(0,sRGRG/n-mRG*mRG));
   const dark=Ls.filter(L=>L<0.6*mL).length;
   res({uniformity:Math.max(0,Math.min(100,Math.round(100-(sdL*0.8+sdRG*0.4)))),defects:Math.round(dark/n*100),brightness:Math.round(mL),rg:mRG});
  };
  img.onerror=()=>rej(new Error('Image could not be read'));
  img.src=src;
 });
}
function gradeFrom(f){
 const g=f.uniformity>=75&&f.defects<=8?'A':f.uniformity>=50&&f.defects<=12?'B':'C';
 const conf=Math.max(60,Math.min(96,Math.round(f.uniformity*0.9+8)));
 const ripe=f.rg>100?'Ripe (stage 4 of 6)':f.rg>40?'Turning (stage 3 of 6)':'Green (stage 2 of 6)';
 return {grade:g,conf,ripeness:ripe};
}
async function analyzeSrc(src,meta){
 const f=await imageFeatures(src);
 const r=gradeFrom(f);
 const a={id:'A'+Date.now().toString(36),farmer:db.session,crop:meta.crop,name:meta.name||meta.crop+' lot',grade:r.grade,conf:r.conf,uniformity:f.uniformity,defects:f.defects,brightness:f.brightness,ripeness:r.ripeness,img:src,saved:false,t:stamp()};
 db.assess.unshift(a);db.lastAssess=a.id;
 log(me().name+' ran a quality assessment: Grade '+a.grade);
 return a;
}

/* Generated demonstration produce images (drawn on a canvas, so they are real raster images). */
function makeSample(kind){
 const c=document.createElement('canvas');c.width=c.height=320;const g=c.getContext('2d');
 g.fillStyle='#EFE6D2';g.fillRect(0,0,320,320);
 let seed=kind.length*131+7;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647};
 g.beginPath();g.arc(160,172,118,0,Math.PI*2);g.fillStyle='#C2402C';g.fill();
 if(kind==='mixed'){
  for(let i=0;i<7;i++){const x=110+rnd()*100,y=110+rnd()*120,r=18+rnd()*22;g.beginPath();g.arc(x,y,r,0,Math.PI*2);g.fillStyle=rnd()>.5?'#D8B04A':'#86A24E';g.fill()}
 }
 const spots=kind==="damaged"?70:kind==="mixed"?6:0;
 for(let i=0;i<spots;i++){const a=rnd()*Math.PI*2,rr=Math.sqrt(rnd())*104,r=kind==='damaged'?5+rnd()*8:3+rnd()*3;g.beginPath();g.arc(160+Math.cos(a)*rr,172+Math.sin(a)*rr,r,0,Math.PI*2);g.fillStyle='#4A2A1A';g.fill()}
 g.beginPath();g.ellipse(160,58,26,11,0,0,Math.PI*2);g.fillStyle='#4F7A34';g.fill();
 return c.toDataURL('image/png');
}

/* Reads an image file and returns a downsized JPEG data URL. Defined in data.js as readImage. */
function setDraftImage(src){
 db.draft.img=src;
 if(!save())toast('This photo is too large to keep in this browser. Try a smaller image.');
 render();
}
function downloadCSV(name,rows){
 const esc2=v=>'"'+String(v).replace(/"/g,'""')+'"';
 const csv=rows.map(r=>r.map(esc2).join(',')).join('\n');
 const a=document.createElement('a');
 a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download=name;document.body.appendChild(a);a.click();a.remove();
}

/* ---------- Dialog builders ---------- */
function offerModal(buyer){
 const mine=myListings().filter(l=>l.status==='active');
 if(!mine.length)return emptyState('No active listings','Upload produce first, then you can send an offer to a buyer.','<button class="btn p" data-act="nav" data-v="upload">Upload produce</button>','package');
 const l=mine[0];
 return `<h2>Send an offer to ${esc(buyer.name)}</h2>
 <p class="mut small" style="margin:-6px 0 14px">${locOf(buyer)} · Buyer interests: ${esc(buyer.interests.join(', ')||'—')}</p>
 <form data-form="offer" data-id="${buyer.id}" class="stack" style="gap:14px">
  <div class="field"><label for="of-l">Product</label><select id="of-l" name="listing">${mine.map(x=>`<option value="${x.id}">${esc(x.name)} · ${num(x.qty)} kg available</option>`).join('')}</select></div>
  <div class="form">
   <div class="field"><label for="of-p">Price / kg (₹)</label><input id="of-p" name="price" type="number" min="1" step="any" value="${recPrice(l.crop,l.district)}" required></div>
   <div class="field"><label for="of-q">Quantity (kg)</label><input id="of-q" name="qty" type="number" min="1" value="${Math.min(l.qty,100)}" required></div>
  </div>
  <div class="field"><label for="of-m">Message</label><textarea id="of-m" name="message" placeholder="Harvest date, grading, delivery timing"></textarea></div>
  ${buyer.verified?'':'<div class="note warn small">This buyer is not verified yet. Their response may take longer.</div>'}
  <div class="row end"><button type="button" class="btn o" data-act="closem">Cancel</button><button class="btn p" type="submit">${icon('send')}Send offer</button></div>
 </form>`;
}
function counterModal(d){
 return `<h2>Counter offer</h2><p class="mut small" style="margin:-6px 0 14px">Current proposal: ${fmtK(d.price)}/kg for ${num(d.qty)} kg (total ${fmt(d.price*d.qty)}).</p>
 <form data-form="counter" data-id="${d.id}" class="stack" style="gap:14px">
  <div class="form"><div class="field"><label for="ct-p">Your price / kg (₹)</label><input id="ct-p" name="price" type="number" min="1" step="any" value="${d.price}" required></div>
  <div class="field"><label for="ct-q">Quantity (kg)</label><input id="ct-q" name="qty" type="number" min="1" value="${d.qty}" required></div></div>
  <div class="field"><label for="ct-m">Note (optional)</label><textarea id="ct-m" name="note" placeholder="Why this price?"></textarea></div>
  <div class="row end"><button type="button" class="btn o" data-act="closem">Cancel</button><button class="btn s" type="submit">${icon('refresh')}Send counter offer</button></div>
 </form>`;
}
function editModal(l){
 return `<h2>Edit product</h2>
 <form data-form="edit" data-id="${l.id}" class="stack" style="gap:14px;margin-top:14px">
  <div class="field"><label for="ed-n">Product name</label><input id="ed-n" name="name" value="${esc(l.name)}" required></div>
  <div class="form">
   <div class="field"><label for="ed-q">Quantity (kg)</label><input id="ed-q" name="qty" type="number" min="1" value="${l.qty}" required></div>
   <div class="field"><label for="ed-a">Asking price / kg (₹)</label><input id="ed-a" name="ask" type="number" min="1" step="any" value="${l.ask}" required></div>
  </div>
  <p class="hint">Recommended price for ${esc(l.crop)} in ${esc(l.district)}: ${fmtK(recPrice(l.crop,l.district))}/kg (demonstration rule).</p>
  <div class="row end"><button type="button" class="btn o" data-act="closem">Cancel</button><button class="btn p" type="submit">${icon('check')}Save changes</button></div>
 </form>`;
}
function listingDetailModal(l){
 return `<h2>${esc(l.name)}</h2><p class="mut" style="margin:-4px 0 14px">${esc(l.crop)} · ${esc(l.district)} · listed ${fmtDate(l.listedAt)}</p>
 <div class="grid2 even" style="gap:14px"><div class="photo">${l.img?`<img src="${l.img}" alt="">`:`<span class="tile full" style="background:var(--chip);color:var(--brand)">${esc(l.crop[0])}</span>`}</div>
 <div class="kv2"><div><span>Grade</span>${gradeChip(l.grade,l.conf)}</div><div><span>Status</span>${statusChip(l.status)}</div><div><span>Quantity</span><b>${num(l.qty)} kg</b></div><div><span>Harvest</span><b>${fmtDate(l.harvest)}</b></div><div><span>Asking / kg</span><b>${fmtK(l.ask)}</b></div><div><span>Recommended / kg</span><b>${fmtK(recPrice(l.crop,l.district))}</b></div></div></div>
 <div class="note" style="margin-top:14px">Grade and confidence are model predictions for demonstration, not certification.</div>`;
}

/* ---------- Actions ---------- */
async function act(a,d,el){
 const u=me();
 switch(a){
  /* public */
  case 'authmode': location.href=BASE+(d.m==='register'?'register.html':'login.html');break;
  case 'demo': $('input[name=email]').value=d.e;$('input[name=pass]').value=d.p;break;
  case 'togglepw':{const i=el.parentElement.querySelector('input');const show=i.type==='password';i.type=show?'text':'password';el.textContent=show?'Hide':'Show';el.setAttribute('aria-label',show?'Hide password':'Show password');break;}
  case 'regrole': REG_ROLE=d.r;renderAuth('register');break;
  case 'theme': setTheme(d.t);render();break;
  case 'logout': if(window.API){API.Auth.clear();} db.session=null;save();location.href=BASE+'login.html';break;
  case 'switch':{
   const x=db.users.find(y=>y.email===d.e);if(!x)break;
   const pass = x.pass || (x.role === 'farmer' ? 'farmer123' : x.role === 'buyer' ? 'buyer123' : 'admin123');
   if(window.API){
    try {
     const r = await API.login(x.email, pass);
     if(r && r.ok){
      const resp = await r.json();
      API.Auth.setTokens(resp.access || resp.tokens?.access, resp.refresh || resp.tokens?.refresh);
      API.Auth.setUser(resp.user);
     }
    } catch(e){}
   }
   db.session=x.id;db.nav='overview';log('Switched to demonstration account '+x.name);save();
   location.href=BASE+x.role+'/dashboard.html';break;}
  case 'nav': if(u)goTo(d.v,u.role);break;
  case 'pop': setPop(POP===d.p?null:d.p);break;
  case 'mark-read': db.notesSeen=db.log[0];save();updateChrome();break;
  case 'menu':{$('#side').classList.toggle('open');$('#scrim').classList.toggle('open');break;}
  case 'closem': closeM();break;
  case 'ask': confirmM(d);break;
  case 'yes': closeM();act(d.then,{id:d.id});break;
  case 'tab': TAB[d.k]=d.t;render();break;
  case 'nb-tab': NB.tab=d.t;render();break;
  case 'tab-all': NB.tab='all';render();break;
  case 'clear-filters': F={q:'',grade:'',crop:'',sort:'distance',tab:'all',minP:'',maxP:'',district:'',minQ:'',maxKm:'any',verifiedOnly:false};render();break;
  case 'pick': {const up=$('#up');if(up)up.click();break;}
  case 'sample':{setDraftImage(makeSample(d.s));toast('Sample photo loaded. It is a generated demonstration image.',true);break;}

  /* profile and offers */
  case 'profile':{const x=userById(d.id);if(x)openM(profileModal(x));break;}
  case 'offer-open':{const x=userById(d.id);if(x)openM(offerModal(x));break;}
  case 'product': location.href=BASE+'buyer/product.html?id='+encodeURIComponent(d.id);break;
  case 'bid-open': location.href=BASE+'buyer/product.html?id='+encodeURIComponent(d.id)+'#bidpanel';break;
  case 'save':{const i=db.saved.indexOf(d.id);i>=0?db.saved.splice(i,1):db.saved.push(d.id);save();render();break;}
  case 'save-farmer':{const i=db.savedFarmers.indexOf(d.id);i>=0?db.savedFarmers.splice(i,1):db.savedFarmers.push(d.id);save();render();toast(i>=0?'Farm removed from saved':'Farm saved',true);break;}

  /* produce upload and quality */
  case 'analyze':{
   const D=db.draft;
   if(!D.img){toast('Add a produce photo first');break}
   if(!D.qty&&D.qty!==0){/* quantity optional for analysis */}
   analyzeSrc(D.img,{crop:D.crop,name:D.name}).then(()=>{save();goTo('quality','farmer')}).catch(e=>toast(e.message||'Analysis failed'));
   break;}
  case 'analyze-again':{
   const a=db.assess.find(x=>x.id===db.lastAssess);if(!a||!a.img){toast('No photo to analyse again');break}
   analyzeSrc(a.img,{crop:a.crop,name:a.name}).then(()=>{save();render();toast('New assessment added to history',true)}).catch(e=>toast(e.message));
   break;}
  case 'save-assess':{const a=db.assess.find(x=>x.id===db.lastAssess);if(a){a.saved=true;log('Saved assessment for '+a.name);save();render();toast('Assessment saved',true)}break;}
  case 'list-open':{
   const a=db.assess.find(x=>x.id===d.id);if(!a)break;
   openM(`<h2>List this product</h2><p class="mut small" style="margin:-6px 0 14px">Grade ${a.grade} · ${a.conf}% confidence. Buyers see the grade as a model prediction.</p>
   <form data-form="list" data-id="${a.id}" class="stack" style="gap:14px">
    <div class="field"><label for="ls-n">Product name</label><input id="ls-n" name="name" value="${esc(a.name)}" required></div>
    <div class="form">
     <div class="field"><label for="ls-q">Quantity</label><input id="ls-q" name="qty" type="number" min="1" value="${esc(db.draft.qty||100)}" required></div>
     <div class="field"><label for="ls-u">Unit</label><select id="ls-u" name="unit">${selectOpts(['kg','quintal'],db.draft.unit)}</select></div>
     <div class="field"><label for="ls-a">Asking price / kg (₹)</label><input id="ls-a" name="ask" type="number" min="1" step="any" value="${recPrice(a.crop,db.draft.district)}" required></div>
     <div class="field"><label for="ls-h">Harvest date</label><input id="ls-h" name="harvest" type="date" value="${esc(db.draft.harvest)}" max="${daysAgo(0)}" required></div>
    </div>
    <div class="field"><label for="ls-d">Farm district</label><select id="ls-d" name="district">${selectOpts(KA_DISTRICTS,db.draft.district)}</select></div>
    <div class="row end"><button type="button" class="btn o" data-act="closem">Cancel</button><button class="btn p" type="submit">${icon('package')}List product</button></div>
   </form>`);break;}
  case 'view-product':{const l=listingOf(d.id);if(l)openM(listingDetailModal(l));break;}
  case 'edit-product':{const l=listingOf(d.id);if(l)openM(editModal(l));break;}
  case 'pause':{
   const l=listingOf(d.id);if(!l||l.farmer!==u.id)break;
   l.status=l.status==='active'?'paused':'active';log(l.name+' '+(l.status==='paused'?'paused':'resumed'));save();render();toast(l.status==='paused'?'Listing paused. Buyers cannot see it.':'Listing is live again',true);break;}
  case 'delete-product':{
   const l=listingOf(d.id);if(!l||l.farmer!==u.id)break;
   if(db.deals.some(x=>x.listing===l.id&&x.status==='accepted')){toast('This product has accepted orders. Withdraw it instead.');break}
   db.deals.forEach(x=>{if(x.listing===l.id&&isOpen(x))x.status='rejected'});
   db.listings=db.listings.filter(x=>x.id!==l.id);db.saved=db.saved.filter(x=>x!==l.id);
   log('Deleted listing '+l.name);save();render();toast('Product deleted',true);break;}
  case 'dismiss':{break}

  /* bids and orders */
  case 'accept':{
   const x=db.deals.find(y=>y.id===d.id);if(!x||!isOpen(x)||x.by===u.role)break;
   if(window.API){
    const ok=await apiAcceptBid(d.id);
    if(ok){toast('Accepted. Order created.',true);render();}
    break;
   }
   const L=listingOf(x.listing);
   if(L&&x.qty>L.qty){toast('Only '+num(L.qty)+' kg of this listing is still available. Counter with a smaller quantity.');break}
   x.status='accepted';x.stage='confirmed';
   let left=0,dropped=0;
   if(L){
    L.soldQty=(L.soldQty||0)+x.qty;L.qty-=x.qty;left=L.qty;
    if(L.qty<=0){L.qty=0;L.status='sold'}
    /* Other open bids stay open if the remaining stock still covers them; the rest are closed. */
    db.deals.filter(y=>y.listing===x.listing&&y.id!==x.id&&isOpen(y)&&y.qty>L.qty).forEach(y=>{y.status='rejected';dropped++});
   }
   log('Accepted '+userById(x.buyerId).name+' at '+fmtK(x.price)+'/kg for '+num(x.qty)+' kg');save();render();
   toast('Accepted. An order has been created.'+(left>0?' '+num(left)+' kg remains listed.':' Listing sold out.')+(dropped?' '+dropped+' bid'+(dropped>1?'s':'')+' above the remaining stock closed.':''),true);break;}
  case 'reject':{
   const x=db.deals.find(y=>y.id===d.id);if(!x||!isOpen(x))break;
   if(window.API){
    const ok=await apiRejectBid(d.id);
    if(ok){toast('Rejected');render();}
    break;
   }
   x.status='rejected';x.by=u.role;log('Rejected a deal on '+listingOf(x.listing).name);save();render();toast('Rejected');break;}
  case 'counter-open':{const x=db.deals.find(y=>y.id===d.id);if(x)openM(counterModal(x));break;}
  case 'dispatch':{const x=db.deals.find(y=>y.id===d.id);if(x&&x.stage==='confirmed'){x.stage='dispatched';log('Dispatched order '+x.id.toUpperCase());save();render();toast('Marked as dispatched',true)}break;}
  case 'deliver':{const x=db.deals.find(y=>y.id===d.id);if(x&&x.stage==='dispatched'){x.stage='delivered';log('Delivery confirmed for '+x.id.toUpperCase());save();render();toast('Delivery confirmed',true)}break;}
  case 'pay':{const x=db.deals.find(y=>y.id===d.id);if(x&&!x.paid){x.paid=true;log((u.role==='farmer'?'Payment received for ':'Payment sent for ')+x.id.toUpperCase());save();render();toast((u.role==='farmer'?'Payment marked as received':'Payment recorded')+' (demonstration, no money moves)',true)}break;}
  case 'place-bid':{
   const L=listingOf(d.id);if(!L)break;
   if(db.platform.requireVerifiedBuyers&&!u.verified){toast('Your business must be verified before you can bid');break}
   const p=+$('#bp').value,q=Math.round(+$('#bq').value),del=$('#bd').value,msg=$('#bm').value.trim();
   if(!(p>0)){toast('Enter a price per kg greater than zero');break}
   if(!(q>0&&q<=L.qty)){toast('Quantity must be between 1 and '+num(L.qty)+' kg');break}
   if(window.API){
    const ok=await apiPlaceBid(L.id,p,q,msg,del);
    if(ok){log(u.name+' bid '+fmtK(p)+'/kg on '+L.name);toast('Bid sent to the farm',true);goTo('bids','buyer');}
    break;
   }
   db.deals.push({id:'d'+Date.now().toString(36),listing:L.id,farmerId:L.farmer,buyerId:u.id,initiator:'buyer',price:p,qty:q,status:'pending',by:'buyer',stage:null,paid:false,t:stamp(),message:[del,msg].filter(Boolean).join(' · '),rounds:1});
   log(u.name+' bid '+fmtK(p)+'/kg on '+L.name);save();toast('Bid sent to the farm',true);goTo('bids','buyer');break;}

  /* admin */
  case 'mod':{
   const l=listingOf(d.id);if(!l)break;
   if(l.status==='hidden'){if(u.role!=='admin'){toast('Only an administrator can restore a hidden listing');break}l.status='active'}
   else if(u.role==='admin'){l.status='hidden'}
   else{break}
   log('Listing '+l.name+' set to '+l.status);save();render();toast('Listing '+(l.status==='active'?'restored':'hidden'),true);break;}
  case 'verify':{const x=userById(d.id);if(!x)break;x.verified=!x.verified;log(x.name+(x.verified?' verified':' verification revoked'));save();render();toast(x.name+(x.verified?' verified':' verification revoked'),true);break;}
  case 'suspend':{const x=userById(d.id);if(!x)break;x.status='suspended';log('Suspended '+x.name);save();render();toast(x.name+' suspended');break;}
  case 'reactivate':{const x=userById(d.id);if(!x)break;x.status='active';log('Reactivated '+x.name);save();render();toast(x.name+' reactivated',true);break;}
  case 'export':{
   const rows=[['id','listing','farmer','buyer','initiator','price_per_kg','qty_kg','total','status','stage','paid','time']];
   db.deals.forEach(d=>{const l=listingOf(d.listing);rows.push([d.id,l?l.name:'',userById(d.farmerId).farm,userById(d.buyerId).name,d.initiator,d.price,d.qty,d.price*d.qty,d.status,d.stage||'',d.paid?'yes':'no',d.t])});
   downloadCSV('agrivision-transactions.csv',rows);break;}
  case 'reset':{db=seed();save();toast('Demonstration data reset',true);location.href=BASE+'login.html';break;}
  default: break;
 }
}

/* ---------- Form submissions ---------- */
function login(email,pass){
 if(window.API){apiLogin(email,pass);return;}
 const x=db.users.find(y=>y.email.toLowerCase()===email.trim().toLowerCase()&&y.pass===pass);
 if(!x){toast('Email or password is incorrect');return}
 if(x.status==='suspended'){toast('This account is suspended. Contact the platform team.');return}
 db.session=x.id;db.nav='overview';log(x.name+' signed in');save();
 toast('Welcome, '+x.name.split(' ')[0],true);
 location.href=BASE+x.role+'/dashboard.html';
}
function register(v){
 if(window.API){apiRegister(v);return;}
 if(db.users.some(x=>x.email.toLowerCase()===v.email.toLowerCase())){toast('An account with this email already exists');return}
 if(v.phone&&!/^[6-9]\d{9}$/.test(v.phone)){toast('Enter a valid 10-digit mobile number');return}
 if(!KA_DISTRICTS.includes(v.district)&&!PLACES[v.district]){toast('Choose a district from the list');return}
 const id='u'+Date.now().toString(36);
 const base={id,role:v.role,email:v.email.trim(),pass:v.pass,phone:v.phone||'',state:v.state||'Karnataka',district:v.district,status:'active',verified:false,locShare:true,joined:daysAgo(0),prefs:{notifyBids:true,notifyPrices:false}};
 const u=v.role==='farmer'
  ?Object.assign(base,{name:v.name.trim(),farm:v.farm.trim(),village:v.village.trim(),city:v.village.trim(),acres:0,address:v.location.trim()})
  :Object.assign(base,{name:v.company.trim(),contact:v.contactPerson.trim(),business:v.business,city:v.district,address:v.address.trim(),interests:[]});
 db.users.push(u);db.session=id;db.nav='overview';log(u.name+' registered as '+v.role);save();
 toast('Account created. Verification is pending.',true);
 location.href=BASE+v.role+'/dashboard.html';
}
function saveProfile(v){
 const u=me();
 if(v.phone&&!/^[6-9]\d{9}\d*$/.test(v.phone)){toast('Enter a valid mobile number');return}
 if(!KA_DISTRICTS.includes(v.district)&&!PLACES[v.district]){toast('Choose a district from the list');return}
 Object.assign(u,{phone:v.phone||u.phone,state:v.state,district:v.district,city:v.city.trim()});
 if(u.role==='farmer')Object.assign(u,{name:v.name.trim(),farm:v.farm.trim(),village:v.village.trim(),acres:+v.acres||0});
 else Object.assign(u,{name:v.name.trim(),business:v.business});
 log(u.name+' updated profile');save();render();toast('Profile saved',true);
}
function changePassword(v){
 const u=me();
 if(v.current!==u.pass){toast('Current password is incorrect');return}
 u.pass=v.next;save();toast('Password updated',true);
}

/* ---------- Wiring ---------- */
document.addEventListener('click',e=>{
 const el=e.target.closest('[data-act]');
 if(!el){if(POP&&!e.target.closest('.pop-wrap'))setPop(null);return}
 if(el.id==='modal'&&e.target!==el)return;
 if(el.dataset.act!=='pop'&&POP&&!el.closest('.pop'))setPop(null);
 if(el.tagName==='A')return;            // links navigate on their own
 act(el.dataset.act,el.dataset,el);
});
document.addEventListener('keydown',e=>{
 if(e.key==='Escape'){closeM();if(POP)setPop(null);$('#side')&&$('#side').classList.remove('open');$('#scrim')&&$('#scrim').classList.remove('open')}
 if((e.key==='Enter'||e.key===' ')&&e.target.matches&&e.target.matches('[role="button"][data-act]')){e.preventDefault();e.target.click()}
});
document.addEventListener('submit',e=>{
 const form=e.target,f=form.dataset.form;if(!f)return;e.preventDefault();
 const v=Object.fromEntries(new FormData(form));
 if(f==='login')return login(v.email,v.pass);
 if(f==='register')return register(v);
 if(f==='forgot'){toast('If an account exists for '+v.email+', a reset link would be sent. (Demonstration: no email is sent.)',true);form.reset();return}
 if(f==='contact'){
  if(!v.name||!v.email||!v.message){toast('Please fill in all fields');return}
  db.messages.unshift({id:'m'+Date.now().toString(36),name:v.name,email:v.email,message:v.message,t:stamp()});
  log('New contact message from '+v.name);save();form.reset();toast('Thanks. Your message has been recorded.',true);return;
 }
 if(f==='search'){
  SEARCH=(v.q||'').trim();
  const r=me()?me().role:null;
  if(!r){toast('Sign in to search');return}
  goTo({farmer:'buyers',buyer:'browse',admin:'users'}[r],r);return;
 }
 if(f==='profile'){saveProfile(v);return}
 if(f==='password'){changePassword(v);form.reset();return}
 if(f==='offer'){
  const L=listingOf(v.listing),u=me(),buyer=userById(form.dataset.id);
  const p=+v.price,q=Math.round(+v.qty);
  if(!L||L.farmer!==u.id){toast('Choose one of your listings');return}
  if(!(p>0)){toast('Enter a valid price');return}
  if(!(q>0&&q<=L.qty)){toast('Quantity must be between 1 and '+num(L.qty)+' kg');return}
  db.deals.push({id:'d'+Date.now().toString(36),listing:L.id,farmerId:u.id,buyerId:buyer.id,initiator:'farmer',price:p,qty:q,status:'pending',by:'farmer',stage:null,paid:false,t:stamp(),message:v.message||'',rounds:1});
  log(u.name+' sent an offer to '+buyer.name);save();closeM();toast('Offer sent to '+buyer.name,true);render();return;
 }
 if(f==='counter'){
  const x=db.deals.find(y=>y.id===form.dataset.id);if(!x)return;
  const p=+v.price,q=Math.round(+v.qty);
  if(!(p>0)||!(q>0)){toast('Enter a valid price and quantity');return}
  if(window.API){
   apiCounterBid(x.id,p,q,v.note).then(ok=>{if(ok){closeM();toast('Counter offer sent',true);render();}});
   return;
  }
  x.price=p;x.qty=q;x.by=me().role;x.status='counter';x.rounds=(x.rounds||1)+1;if(v.note)x.message=v.note;
  log(me().name+' countered at '+fmtK(p)+'/kg');save();closeM();toast('Counter offer sent',true);render();return;
 }
 if(f==='edit'){
  const l=listingOf(form.dataset.id);if(!l)return;
  const q=Math.round(+v.qty),a=+v.ask;
  if(!(q>0)||!(a>0)){toast('Enter a valid quantity and price');return}
  Object.assign(l,{name:v.name.trim(),qty:q,ask:a});log('Updated '+l.name);save();closeM();render();toast('Product updated',true);return;
 }
 if(f==='list'){
  const a=db.assess.find(x=>x.id===form.dataset.id);if(!a)return;
  const q=Math.round(+v.qty),kg=v.unit==='quintal'?q*100:q,ask=+v.ask;
  if(!(kg>0)||!(ask>0)){toast('Enter a valid quantity and price');return}
  const L={id:'l'+Date.now().toString(36),farmer:me().id,name:v.name.trim(),crop:a.crop,qty:kg,unit:'kg',ask,grade:a.grade,conf:a.conf,status:'active',district:v.district,harvest:v.harvest,listedAt:daysAgo(0),verified:true,img:a.img||null};
  db.listings.push(L);db.draft.district=v.district;db.draft.harvest=v.harvest;db.draft.unit=v.unit;
  log(me().name+' listed '+num(kg)+' kg of '+L.crop);save();closeM();toast('Listing published. Buyers can now find it.',true);goTo('produce','farmer');return;
 }
 if(f==='password'){return}
});
document.addEventListener('input',e=>{
 const t=e.target;
 if(t.dataset.dr){db.draft[t.dataset.dr]=t.value;save();return}
 if(t.dataset.bid==='price'||t.dataset.bid==='qty'){const p=+$('#bp').value,q=+$('#bq').value;const el=$('#bidtotal');if(el)el.textContent=fmt(p*q);return}
});
document.addEventListener('change',e=>{
 const t=e.target;
 if(t.dataset.dr){db.draft[t.dataset.dr]=t.value;save();if(t.dataset.dr==='crop'||t.dataset.dr==='district')render();return}
 if(t.dataset.f){
  if(t.dataset.f==='sort'&&t.tagName==='SELECT'){F.sort=t.value;render();return}
  F[t.dataset.f]=t.type==='checkbox'?t.checked:t.value;render();return;
 }
 if(t.dataset.nb==='sort'){NB.sort=t.value;render();return}
 if(t.dataset.p){
  const k=t.dataset.p;
  if(k==='range')PR.range=+t.value;
  else if(k==='state'){PR.district=Object.keys(PLACES).find(d=>PLACES[d][0]===t.value)||PR.district}
  else if(k==='district')PR.district=t.value;
  else if(k==='crop')PR.crop=t.value;
  else if(k==='mkt')PR.mkt=t.value;
  render();return;
 }
 if(t.dataset.set){
  const u=me();if(t.dataset.set==='locShare')u.locShare=t.checked;else u.prefs[t.dataset.set]=t.checked;
  save();render();toast('Setting saved',true);return;
 }
 if(t.dataset.plat){db.platform[t.dataset.plat]=t.checked;log('Platform rule changed: '+t.dataset.plat+' '+(t.checked?'on':'off'));save();render();toast('Platform rule updated',true);return}
 if(t.dataset.interest){const u=me(),i=u.interests.indexOf(t.dataset.interest);if(t.checked&&i<0)u.interests.push(t.dataset.interest);if(!t.checked&&i>=0)u.interests.splice(i,1);save();return}
 if(t.dataset.file!==undefined||t.dataset.u){const f=t.files&&t.files[0];if(f){readImage(f).then(src=>setDraftImage(src)).catch(()=>toast('That file could not be read as an image'))}return}
});
document.addEventListener('dragover',e=>{if(e.target.closest&&e.target.closest('#drop'))e.preventDefault()});
document.addEventListener('drop',e=>{
 const dz=e.target.closest&&e.target.closest('#drop');if(!dz)return;e.preventDefault();
 const f=e.dataTransfer.files[0];
 if(f&&f.type.startsWith('image/'))readImage(f).then(src=>setDraftImage(src)).catch(()=>toast('Could not read that image'));
 else toast('Drop a JPG or PNG image');
});

/* Theme: apply immediately and follow the system setting while "System" is selected. */
applyTheme(getTheme());
if(window.matchMedia)matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if(getTheme()==='system'){applyTheme('system');render()}});
if(window.matchMedia)matchMedia('(max-width:1180px)').addEventListener('change',()=>render());

/* ---------- Page boot ---------- */
const P=window.AV_PAGE||{};
if(P.kind==='landing'){
 renderLanding();
}else if(P.kind==='index'){
 location.href=BASE+(db.session&&me()?me().role+'/dashboard.html':'index.html');
}else if(P.kind==='auth'){
 if(db.session&&me()){location.href=BASE+me().role+'/dashboard.html'}
 else if(window.API&&API.Auth.isLoggedIn()){
  const u=API.Auth.getUser();
  if(u){location.href=BASE+u.role+'/dashboard.html';}
  else renderAuth(P.mode||'login');
 }
 else renderAuth(P.mode||'login');
}else if(P.kind==='forgot'){
 renderForgot();
}else if(P.kind==='app'){
 if(!db.session||!me()){
  if(window.API&&API.Auth.isLoggedIn()){
   const u=API.Auth.getUser();
   if(u){db.session=u.id;db.nav=P.view||'overview';save();}
   else{location.href=BASE+'login.html';}
  }else{
   location.href=BASE+'login.html';
  }
 }
 if(db.session&&me()){
  if(me().role!==P.role){location.href=BASE+me().role+'/dashboard.html'}
  else{db.nav=P.view||'overview';save();render();
   if(window.API&&API.Auth.isLoggedIn()){
    syncFromBackend().catch(console.warn);
   }
  }
 }
}
