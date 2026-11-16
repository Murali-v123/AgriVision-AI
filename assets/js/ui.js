/* UI core: app shell, components, Nearby Buyers panel, auth and landing pages, chart registry and render. */

/* ---------- Components ---------- */
const avatar=(u,cls='')=>`<span class="avatar ${cls} ${u.role==='buyer'?'acc':''}" aria-hidden="true">${esc((u.name||'?').split(' ').map(w=>w[0]).slice(0,2).join(''))}</span>`;
const locOf=(u,full=false)=>{
 const txt=full?`${u.city}, ${u.district}, ${u.state}`:`${u.city}, ${u.state}`;
 return `<span class="loc">${icon('map-pin')}<span title="${esc(txt)}">${esc(txt)}</span></span>`;
};
const verifiedOf=u=>u.verified?`<span class="badge-verified">${icon('badge-check')}Verified</span>`:`<span class="badge-pending">${icon('clock')}Verification pending</span>`;
function distLine(viewer,other){
 const d=distanceBetween(viewer,other);
 if(d!=null)return `<span class="dist">${icon('navigation')}${d} km away <span class="mut">(approx.)</span></span>`;
 if(viewer&&viewer.locShare===false)return `<span class="dist">${icon('eye-off')}Distance hidden: location sharing is off</span>`;
 return `<span class="dist">${icon('map')}Distance not available</span>`;
}
const chips=arr=>(arr||[]).map(x=>`<span class="chip outline">${esc(x)}</span>`).join(' ');
const statusChip=s=>{
 const m={active:['ok','Active'],paused:['warn','Paused'],sold:['info','Sold'],withdrawn:['outline','Withdrawn'],hidden:['bad','Hidden']};
 const [c,t]=m[s]||['outline',s];return `<span class="chip ${c}">${t}</span>`;
};
const dealChip=d=>{
 if(d.status==='accepted')return `<span class="chip ok">${icon('check')}Accepted</span>`;
 if(d.status==='rejected')return `<span class="chip bad">${icon('x')}Rejected</span>`;
 if(d.status==='counter')return `<span class="chip info">${icon('refresh')}Counter offer</span>`;
 return `<span class="chip warn">${icon('clock')}Pending</span>`;
};
const STAGES=['confirmed','dispatched','delivered'],STAGE_LABEL={confirmed:'Confirmed',dispatched:'Dispatched',delivered:'Delivered'};
function stageTrack(stage){
 const idx=STAGES.indexOf(stage);
 return `<div class="stepper">${STAGES.map((s,i)=>`<span class="s ${i<idx?'done':''} ${i===idx?'on':''}"><i>${i<idx?'✓':i+1}</i>${STAGE_LABEL[s]}</span>${i<STAGES.length-1?'<span class="sep"></span>':''}`).join('')}</div>`;
}
const pageHead=(title,sub,extra='')=>`<div class="pagehead"><div><h1>${title}</h1>${sub?`<p class="sub">${sub}</p>`:''}</div>${extra?`<div class="row" style="gap:8px">${extra}</div>`:''}</div>`;
const statCard=(label,value,ic,trend,cls='')=>`<div class="card stat"><div class="label">${label}${icon(ic)}</div><span class="bigval ${cls}">${value}</span>${trend?`<span class="trend ${trend.dir}">${icon(trend.dir==='up'?'trend-up':'trend-down')}${trend.text}</span>`:''}</div>`;
const kv=(l,v,meta='',cls='')=>`<div><div class="mut small">${l}</div><span class="bigval ${cls}">${v}</span>${meta?`<div class="mut small">${meta}</div>`:''}</div>`;
/* Row of compact stat cards. Each item: [label, value, note, tone]. */
const statRow=arr=>`<div class="grid4">${arr.map(([l,v,n,c])=>`<div class="card">${kv(l,v,n||'',c||'')}</div>`).join('')}</div>`;
const statCards=arr=>statRow(arr.map(([l,v,n])=>[l,typeof v==='number'?num(v):v,n]));
const emptyState=(title,text,cta='',ic='leaf')=>`<div class="empty"><span class="ico">${icon(ic)}</span><b>${title}</b><p class="mut" style="margin:0 auto;max-width:380px">${text}</p>${cta}</div>`;
/* Placeholder tints per crop, used until a real photo exists. */
const CROP_TINT={Tomato:['#F6E3DC','#A8432C'],Onion:['#EEE6F2','#6B4A86'],Potato:['#F3EBD8','#7A5E22']};
const tintOf=crop=>{const t=CROP_TINT[crop]||['var(--chip)','var(--brand)'];return `background:${t[0]};color:${t[1]}`};
const photoOf=(l,tall=false)=>`<div class="photo ${tall?'tall':''}">${l.img?`<img src="${l.img}" alt="${esc(l.name)} photo">`:`<span class="tile full" style="${tintOf(l.crop)}">${esc(l.crop[0])}</span>`}</div>`;
const gradeChip=(g,conf)=>`<span class="chip ${g==='A'?'ok':g==='B'?'info':'warn'}">Grade ${g}${conf?` · ${conf}%`:''}</span>`;

/* ---------- Profile and listing cards ---------- */
function buyerCard(b,viewer,compact=true){
 const crops=myCrops();
 const match=b.interests.filter(i=>crops.includes(i)).length;
 return `<article class="card" style="padding:14px" aria-label="${esc(b.name)}">
  <div class="row" style="align-items:flex-start;flex-wrap:nowrap">
   <div style="display:flex;gap:10px;min-width:0">${avatar(b,'sm')}<div style="min-width:0"><b style="display:block;font-size:14.5px;line-height:1.25">${esc(b.name)}</b><span class="mut">${esc(b.business)}</span></div></div>
   ${b.verified?`<span class="badge-verified">${icon('badge-check')}Verified</span>`:`<span class="badge-pending">${icon('clock')}Pending</span>`}
  </div>
  <div style="margin:10px 0 8px;display:flex;flex-wrap:wrap;gap:6px;align-items:center">${locOf(b)}</div>
  <div class="small mut" style="margin-bottom:6px">Interested in</div>
  <div style="display:flex;flex-wrap:wrap;gap:5px">${chips(b.interests)}</div>
  ${!compact?`<p class="mut small" style="margin-top:10px">${match?`Buys ${match} of the crops you grow.`:'No overlap with your crops yet.'} Contact: ${esc(b.contact)}</p>`:''}
  <div style="margin-top:10px">${distLine(viewer,b)}</div>
  <div class="row" style="margin-top:12px;gap:8px;flex-wrap:nowrap"><button class="btn o sm" style="flex:1" data-act="profile" data-id="${b.id}">${icon('eye')}View profile</button><button class="btn p sm" style="flex:1" data-act="offer-open" data-id="${b.id}">${icon('send')}Send offer</button></div>
 </article>`;
}
function farmerCard(f,viewer){
 const act=db.listings.filter(l=>l.farmer===f.id&&l.status==='active');
 const saved=db.savedFarmers.includes(f.id);
 return `<article class="card" style="display:flex;flex-direction:column;gap:12px">
  <div class="row" style="align-items:flex-start;flex-wrap:nowrap"><div style="display:flex;gap:10px;min-width:0">${avatar(f,'')}<div style="min-width:0"><b style="display:block;line-height:1.25">${esc(f.farm)}</b><span class="mut">${esc(f.name)}</span></div></div>${verifiedOf(f)}</div>
  ${locOf(f)}
  <div class="kv2"><div><span>Active listings</span><b>${act.length}</b></div><div><span>Land</span><b>${f.acres} acres</b></div><div><span>Crops</span><b>${esc([...new Set(act.map(l=>l.crop))].join(', ')||'—')}</b></div><div><span>Member since</span><b>${fmtDate(f.joined)}</b></div></div>
  ${distLine(viewer,f)}
  <div class="row" style="gap:8px;flex-wrap:nowrap"><button class="btn o sm" style="flex:1" data-act="profile" data-id="${f.id}">${icon('eye')}Profile</button><button class="btn ${saved?'on':'o'} sm" data-act="save-farmer" data-id="${f.id}" aria-pressed="${saved}">${icon('heart')}${saved?'Saved':'Save'}</button></div>
 </article>`;
}
function productCard(l,viewer){
 const f=userById(l.farmer)||{};
 const saved=db.saved.includes(l.id);
 return `<article class="card product" aria-label="${esc(l.name)}">
  <a href="${BASE}buyer/product.html?id=${l.id}" data-act="product" data-id="${l.id}" style="text-decoration:none;display:block;position:relative">${photoOf(l)}<span style="position:absolute;top:10px;left:10px">${gradeChip(l.grade,l.conf)}</span></a>
  <div style="min-width:0"><div class="name" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(l.name)}</div><span class="mut small">by ${esc(f.farm||f.name)}</span></div>
  <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">${locOf(f)}${verifiedOf(f)}</div>
  ${distLine(viewer,f)}
  <div class="kv2"><div><span>Available</span><b>${num(l.qty)} kg</b></div><div><span>Harvest</span><b>${fmtDate(l.harvest)}</b></div><div><span>Asking price</span><b>${fmtK(l.ask)}/kg</b></div><div><span>Recommended</span><b style="color:var(--brand)">${fmtK(recPrice(l.crop,l.district))}/kg</b></div></div>
  <div class="row" style="gap:8px;flex-wrap:nowrap;margin-top:auto"><button class="btn o sm" style="flex:1" data-act="product" data-id="${l.id}">View details</button><button class="btn p sm" style="flex:1" data-act="bid-open" data-id="${l.id}">Place bid</button><button class="btn o sm ${saved?'on':''}" data-act="save" data-id="${l.id}" aria-pressed="${saved}" aria-label="${saved?'Remove from saved':'Save product'}">${icon('heart')}</button></div>
 </article>`;
}
function myCrops(){
 const mine=db.listings.filter(l=>l.farmer===db.session).map(l=>l.crop);
 return mine.length?[...new Set(mine)]:['Tomato'];
}

/* ---------- Nearby Buyers panel (farmer right-hand column) ---------- */
function nearbyPanel(){
 const v=me();
 const crops=myCrops();
 let list=db.users.filter(u=>u.role==='buyer'&&u.status==='active');
 list=list.map(b=>({b,d:distanceBetween(v,b),m:b.interests.filter(i=>crops.includes(i)).length}));
 const tabs={nearby:'Nearby',all:'All',retailers:'Retailers',wholesalers:'Wholesalers',processors:'Food processors'};
 const typeOf={retailers:'Retailer',wholesalers:'Wholesaler',processors:'Food Processor'};
 if(NB.tab==='nearby')list=list.filter(x=>x.d!=null&&x.d<=200);
 if(typeOf[NB.tab])list=list.filter(x=>x.b.business===typeOf[NB.tab]);
 if(NB.sort==='distance')list.sort((a,b)=>(a.d==null)-(b.d==null)||(a.d||0)-(b.d||0));
 else list.sort((a,b)=>b.m-a.m||((a.d==null)-(b.d==null))||(a.d||0)-(b.d||0));
 const hidden=v.locShare===false;
 return `<section class="card" aria-labelledby="nb-title">
  <div class="row" style="margin-bottom:10px"><div><h2 id="nb-title" style="margin:0">Nearby buyers</h2><p class="mut small">Verified buyers near ${esc(v.district)}</p></div>${icon('map-pin')}</div>
  <div class="tabs" role="tablist" style="margin:8px 0 10px;width:100%">${Object.entries(tabs).map(([k,t])=>`<button role="tab" aria-selected="${NB.tab===k}" data-act="nb-tab" data-t="${k}">${t}</button>`).join('')}</div>
  <div class="row" style="margin-bottom:12px"><label class="sr" for="nb-sort">Sort buyers</label><select id="nb-sort" data-nb="sort" style="width:auto;min-width:0;font-size:13px;padding:6px 10px;min-height:34px">
    <option value="distance" ${NB.sort==='distance'?'selected':''}>Sort by distance</option><option value="interest" ${NB.sort==='interest'?'selected':''}>Sort by product interest</option></select>
    <span class="mut small">${list.length} buyer${list.length===1?'':'s'}</span></div>
  ${hidden?`<div class="note info small" style="margin-bottom:12px">Location sharing is off, so distances are hidden. Turn it on in Settings.</div>`:''}
  <div class="stack" style="gap:10px">${list.slice(0,5).map(x=>buyerCard(x.b,v)).join('')||(hidden&&NB.tab==='nearby'?emptyState('Nearby needs your location','Distances are hidden because location sharing is off. Turn it on in Settings, or choose All.','<button class="btn o sm" data-act="tab-all">Show all buyers</button>','map'):emptyState('No buyers in this view','Try a different tab.','','map'))}</div>
  <button class="btn o w" style="margin-top:12px" data-act="nav" data-v="buyers">View all buyers</button>
  <p class="hint">Distances are approximate, measured between district centres. Exact addresses are never shown.</p>
 </section>`;
}

/* ---------- Charts ---------- */
function chartBox(id,make,cls='',aria='Chart'){
 CHARTS.push({id,make});
 return `<div class="chart ${cls}"><canvas id="${id}" role="img" aria-label="${esc(aria)}"></canvas></div>`;
}
function cssVar(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim()}
function mountCharts(){
 if(typeof Chart==='undefined'){
  document.querySelectorAll('canvas').forEach(c=>{const p=c.parentElement;if(p&&!p.querySelector('.chart-fallback'))p.insertAdjacentHTML('beforeend','<div class="chart-fallback mut small" style="position:absolute;inset:0;display:grid;place-items:center">Chart library unavailable offline.</div>')});
  return;
 }
 const C={brand:cssVar('--brand'),brand2:cssVar('--brand-2'),accent:cssVar('--accent'),grid:cssVar('--line-2'),mut:cssVar('--mut-ink'),ink:cssVar('--ink'),ok:cssVar('--ok'),bad:cssVar('--bad'),warn:cssVar('--warn'),info:cssVar('--info'),elev:cssVar('--elev')};
 Chart.defaults.font.family='Inter, system-ui, sans-serif';
 Chart.defaults.color=C.mut;
 Chart.defaults.borderColor=C.grid;
 CHARTS.forEach(({id,make})=>{
  const el=document.getElementById(id);if(!el)return;
  try {
    const existing = (typeof Chart!=='undefined' && Chart.getChart) ? Chart.getChart(el) : null;
    if(existing) existing.destroy();
  } catch(e){}
  try{new Chart(el,make(C))}catch(e){}
 });
}

/* ---------- Dialogs and notifications ---------- */
function toast(msg,ok){
 const t=document.createElement('div');
 t.className='toast'+(ok?' ok':'');t.setAttribute('role','status');t.textContent=msg;
 $('#toasts').appendChild(t);
 setTimeout(()=>t.remove(),2800);
}
function openM(html){const m=$('#modal');m.innerHTML=`<div class="mbox" role="dialog" aria-modal="true"><button class="x" data-act="closem" aria-label="Close">${icon('x')}</button>${html}</div>`;m.classList.add('open')}
function closeM(){$('#modal').classList.remove('open')}
function confirmM(d){
 openM(`<h2>${d.title}</h2><p class="mut" style="margin:6px 0 22px;font-size:14px">${d.text}</p>
 <div class="row end"><button class="btn o" data-act="closem">Cancel</button><button class="btn ${d.danger?'dx':'p'}" data-act="yes" data-then="${d.then}" data-id="${d.id}">${d.label}</button></div>`);
}
function profileModal(u){
 const isFarmer=u.role==='farmer';
 const listings=db.listings.filter(l=>l.farmer===u.id&&l.status==='active');
 const phone=u.phone?u.phone.slice(0,5)+' •••••':'Not shared';
 return `<div class="row" style="align-items:flex-start;flex-wrap:nowrap;padding-right:30px">
  <div style="display:flex;gap:12px;min-width:0">${avatar(u,'lg')}<div><h2 style="margin:0 0 4px">${esc(isFarmer?u.farm:u.name)}</h2><p class="mut">${esc(isFarmer?u.name+' · Farmer':u.business+' · Contact: '+u.contact)}</p></div></div>
  ${verifiedOf(u)}</div>
  <div class="kv2" style="margin:18px 0"><div><span>Location</span><b>${esc(u.city)}, ${esc(u.district)}, ${esc(u.state)}</b></div><div><span>Member since</span><b>${fmtDate(u.joined)}</b></div><div><span>${isFarmer?'Land':'Business type'}</span><b>${isFarmer?u.acres+' acres':esc(u.business)}</b></div><div><span>Phone</span><b>${phone}</b></div></div>
  <h3>${isFarmer?'Active listings':'Interested in'}</h3>
  ${isFarmer?(listings.length?listings.map(l=>`<div class="lrow"><span><b>${esc(l.name)}</b><span class="mut"> · ${num(l.qty)} kg</span></span><span>${gradeChip(l.grade)} ${fmtK(l.ask)}/kg</span></div>`).join(''):'<p class="mut">No active listings.</p>'):`<div style="display:flex;gap:6px;flex-wrap:wrap">${chips(u.interests)}</div>`}
  <p class="hint" style="margin-top:14px">Contact details are shared only after a bid or offer is accepted. Locations are shown at city and district level.</p>`;
}

/* ---------- App shell ---------- */
function renderShell(){
 const u=me();
 $('#app').innerHTML=`<div class="app">
  <aside class="side" id="side" aria-label="Main navigation">
   <a class="brand" href="${BASE}${u.role}/dashboard.html"><span class="mark">${icon('leaf')}</span><span>AgriVision <span class="ai">AI</span></span></a>
   <nav id="nav" aria-label="${u.role} navigation"></nav>
   <div class="foot">Prototype · demonstration data<br>Saved in this browser only</div>
  </aside>
  <div class="scrim" id="scrim" data-act="menu"></div>
  <div class="main">
   <header class="topbar">
    <button class="iconbtn menu-btn" data-act="menu" aria-label="Open navigation" aria-controls="side">${icon('menu')}</button>
    <div class="greet" id="greet" style="font-weight:600;white-space:nowrap" aria-live="polite"></div>
    <form class="search" data-form="search" role="search"><label class="sr" for="gs">Search</label>${icon('search')}<input id="gs" name="q" type="search" placeholder="" autocomplete="off"></form>
    <div class="top-right">
     <div class="seg" role="group" aria-label="Theme">
      <button data-act="theme" data-t="light" aria-pressed="false">${icon('sun')}Light</button>
      <button data-act="theme" data-t="dark" aria-pressed="false">${icon('moon')}Dark</button>
      <button data-act="theme" data-t="system" aria-pressed="false">${icon('monitor')}System</button>
     </div>
     <div class="pop-wrap">
      <button class="icon-btn" data-act="pop" data-p="notif" aria-label="Notifications" aria-expanded="false" id="bell">${icon('bell')}<span class="dot" id="dot"></span></button>
      <div class="pop" data-pop="notif" hidden><div class="head row"><b>Notifications</b><button class="btn g sm" data-act="mark-read">Mark all read</button></div><div id="notif-list"></div></div>
     </div>
     <div class="pop-wrap">
      <button class="user-btn" data-act="pop" data-p="user" aria-label="Account menu" aria-expanded="false" id="userbtn"></button>
      <div class="pop" data-pop="user" hidden id="usermenu"></div>
     </div>
    </div>
   </header>
   <div class="content" id="content"><div class="main-col" id="view"></div><aside class="aside" id="aside" aria-label="Side panel"></aside></div>
  </div>
 </div>`;
}
function updateChrome(){
 const u=me();
 const hour=new Date().getHours();
 $('#greet').textContent=`${hour<12?'Good morning':hour<17?'Good afternoon':'Good evening'}, ${u.name.split(' ')[0]}`;
 const ph={farmer:'Search buyers, produce, farms…',buyer:'Search produce, farmers, orders…',admin:'Search users, listings, deals…'};
 $('#gs').placeholder=ph[u.role];
 $('#gs').value=SEARCH;
 const choice=document.documentElement.dataset.themeChoice||getTheme();
 document.querySelectorAll('[data-act="theme"]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.t===choice)));
 $('#userbtn').innerHTML=`${avatar(u,'sm')}<span class="nm" style="font-size:14px;font-weight:600">${esc(u.name.split(' ')[0])}</span>${icon('chevron')}`;
 const demo={farmer:['buyer@demo.in','Switch to buyer demo'],buyer:['ramesh@demo.in','Switch to farmer demo']}[u.role];
 $('#usermenu').innerHTML=`<div class="head"><b>${esc(u.name)}</b><div class="mut small">${u.role[0].toUpperCase()+u.role.slice(1)} · ${esc(u.email)}</div></div>
  <button class="item" data-act="nav" data-v="profile">${icon('user')}Profile</button>
  <button class="item" data-act="nav" data-v="settings">${icon('settings')}Settings</button>
  ${demo?`<button class="item" data-act="switch" data-e="${demo[0]}">${icon('refresh')}${demo[1]}</button>`:''}
  <button class="item" data-act="logout" style="color:var(--bad)">${icon('logout')}Log out</button>`;
 const notes=db.log.slice(0,6);
 $('#notif-list').innerHTML=notes.map(n=>`<div class="note-item">${esc(n)}</div>`).join('')||'<div class="note-item mut">No notifications.</div>';
 $('#dot').style.display=db.notesSeen===db.log[0]?'none':'block';
}
function renderNav(){
 const u=me(),items=NAV[u.role];
 $('#nav').innerHTML=items.map(([id,l,ic])=>`<button class="nav" data-act="nav" data-v="${id}" aria-current="${db.nav===id?'page':'false'}" class="">${icon(ic)}<span>${l}</span></button>`).join('');
 $('#nav').querySelectorAll('.nav').forEach((b,i)=>{b.classList.toggle('on',items[i][0]===db.nav)});
}

/* ---------- Render ---------- */
/* The Nearby Buyers panel sits beside the dashboard and price pages. Table-heavy pages use the full width. */
const FARMER_ASIDE=['overview','prices','quality'];
function render(){
 if(!db.session||!me()){renderAuth();return}
 if(!$('.app'))renderShell();
 const u=me(),extra=EXTRA_VIEWS[u.role]||[];
 if(!NAV[u.role].some(i=>i[0]===db.nav)&&!extra.includes(db.nav))db.nav='overview';
 renderNav();
 CHARTS=[];
 const key=u.role+'.'+db.nav;
 let html=(VIEWS[key]||VIEWS[u.role+'.overview'])();
 let aside=(u.role==='farmer'&&FARMER_ASIDE.includes(db.nav))?nearbyPanel():'';
 /* On narrow screens the Nearby Buyers panel moves up, directly below the statistics. */
 const narrow=window.matchMedia&&matchMedia('(max-width:1180px)').matches;
 if(aside&&narrow&&html.includes('<!--ASIDE-->')){html=html.replace('<!--ASIDE-->',`<div class="aside-inline">${aside}</div>`);aside=''}
 html=html.replace('<!--ASIDE-->','');
 $('#view').innerHTML=html;
 $('#aside').innerHTML=aside;
 $('#content').classList.toggle('has-aside',!!aside);
 updateChrome();
 setPop(POP);
 mountCharts();
}
function setPop(p){
 POP=p;
 document.querySelectorAll('[data-pop]').forEach(x=>x.hidden=x.dataset.pop!==p);
 document.querySelectorAll('[data-act="pop"]').forEach(b=>b.setAttribute('aria-expanded',String(b.dataset.p===p)));
}

/* ---------- Public: landing page ---------- */
function publicNav(active){
 return `<header class="public-nav"><div class="in">
  <a class="brand" href="${BASE}index.html" style="padding:0;min-width:0"><span class="mark">${icon('leaf')}</span><span>AgriVision <span class="ai">AI</span></span></a>
  <nav class="links hide-s" aria-label="Page sections"><a href="#about">About</a><a href="#how">How it works</a><a href="#roles">Who it's for</a><a href="#contact">Contact</a></nav>
  <div class="seg hide-s" role="group" aria-label="Theme">
   <button data-act="theme" data-t="light" aria-pressed="false">${icon('sun')}<span class="hide-s">Light</span></button>
   <button data-act="theme" data-t="dark" aria-pressed="false">${icon('moon')}<span class="hide-s">Dark</span></button>
   <button data-act="theme" data-t="system" aria-pressed="false">${icon('monitor')}<span class="hide-s">System</span></button>
  </div>
  <div class="nav-actions">
   <a class="btn o sm" href="${BASE}login.html">Log in</a>
   <a class="btn p sm" href="${BASE}register.html">Get started</a>
  </div>
 </div></header>`;
}
function renderLanding(){
 $('#app').innerHTML=`${publicNav()}
 <main>
  <section class="wrap hero">
   <div>
    <p class="eyebrow">Farm-to-market trade for Karnataka</p>
    <h1>Sell your produce at a fair price, backed by a quality check.</h1>
    <p class="lead">AgriVision AI connects farmers directly with retailers, wholesalers and food processors. Photo-based quality grading, mandi price context and transparent bids in one place.</p>
    <div class="row hero-actions" style="justify-content:flex-start;margin-top:26px;gap:12px">
     <a class="btn p lg" href="${BASE}register.html">Create a farmer or buyer account${icon('arrow-right')}</a>
     <a class="btn o lg" href="#how">How it works</a>
    </div>
    <p class="hint" style="margin-top:14px">Prototype with demonstration data. Prices, distances and quality scores are simulated.</p>
   </div>
   <div class="card" style="padding:22px;box-shadow:0 18px 40px rgba(41,49,41,.08)">
    <div class="row"><b>Sample quality report</b><span class="chip outline">Demonstration</span></div>
    <div class="kvs" style="margin:16px 0;grid-template-columns:1fr 1fr">
     <div><div class="mut small">Crop</div><b>Tomato</b></div>
     <div><div class="mut small">Grade</div><span class="bigval ok" style="font-size:22px">A</span></div>
     <div><div class="mut small">Colour uniformity</div><b>88 / 100</b></div>
     <div><div class="mut small">Visible defects</div><b>Low</b></div>
    </div>
    <div class="bar" style="margin-bottom:16px"><i style="width:88%"></i></div>
    <div class="note info small">This is a model prediction for demonstration. It is not an official agricultural certification.</div>
    <div class="row" style="margin-top:16px"><span class="mut small">Suggested price</span><b style="color:var(--brand)">₹30.0/kg</b></div>
   </div>
  </section>

  <section class="section" id="about"><div class="wrap">
   <p class="eyebrow">About AgriVision AI</p>
   <h2 class="big">Trust, transparency and fair prices for every crop</h2>
   <p class="sub" style="max-width:720px">Farmers often sell without knowing what their produce is worth, and buyers struggle to verify quality before they commit. AgriVision AI gives both sides the same information: a quality summary for each lot, recent market prices, and a bidding process where every offer and counter-offer is recorded.</p>
   <div class="grid4" style="margin-top:26px">
    <div class="card">${icon('scan')}<h3 style="margin-top:12px">Quality from a photo</h3><p class="mut">A quick grade for each lot, with the visual checks it is based on.</p></div>
    <div class="card">${icon('chart')}<h3 style="margin-top:12px">Market context</h3><p class="mut">Mandi price history and a suggested price for the crop and district.</p></div>
    <div class="card">${icon('handshake')}<h3 style="margin-top:12px">Transparent bids</h3><p class="mut">Accept, reject or counter. Every step is shown to both parties.</p></div>
    <div class="card">${icon('shield')}<h3 style="margin-top:12px">Verified participants</h3><p class="mut">Buyers are checked before they can bid. Location is shown only at district level.</p></div>
   </div>
  </div></section>

  <section class="section" id="how"><div class="wrap">
   <p class="eyebrow">How it works</p>
   <h2 class="big">From harvest to delivery in four steps</h2>
   <div class="steps4">
    <div class="card"><div class="stepno">1</div><h3>Upload a photo</h3><p class="mut">Add the crop, quantity, harvest date and farm location.</p></div>
    <div class="card"><div class="stepno">2</div><h3>Get a quality grade</h3><p class="mut">Review the grade, confidence and visual checks. Save the assessment.</p></div>
    <div class="card"><div class="stepno">3</div><h3>Receive bids</h3><p class="mut">Verified buyers nearby send bids or offers. Accept, reject or counter.</p></div>
    <div class="card"><div class="stepno">4</div><h3>Deliver and get paid</h3><p class="mut">Track dispatch and delivery, and record payment in one place.</p></div>
   </div>
  </div></section>

  <section class="section" id="roles"><div class="wrap">
   <p class="eyebrow">Who it's for</p>
   <h2 class="big">One platform, three workspaces</h2>
   <div class="grid3" style="margin-top:24px">
    <div class="card"><span class="chip ok">Farmers</span><h3 style="margin-top:12px">List produce and find buyers</h3><p class="mut">Assess quality, see price guidance, browse nearby buyers and manage bids and orders.</p></div>
    <div class="card"><span class="chip info">Buyers</span><h3 style="margin-top:12px">Discover verified produce</h3><p class="mut">Filter by district, grade and price. Place bids, track orders and keep a transaction history.</p></div>
    <div class="card"><span class="chip acc">Platform team</span><h3 style="margin-top:12px">Oversee the marketplace</h3><p class="mut">Verify users, monitor listings and AI performance, and review activity. Accounts are provisioned by staff.</p></div>
   </div>
  </div></section>

  <section class="section" id="contact"><div class="wrap contact-grid">
   <div><p class="eyebrow">Contact</p><h2 class="big">Questions about the platform?</h2><p class="sub">Send a message to the AgriVision team. This prototype stores messages in your browser so the admin view can show them.</p>
    <p class="mut small" style="margin-top:16px">Email: hello@agrivision.example · Phone: 080-0000-0000 (demo)</p></div>
   <form class="card stack contact-form-card" data-form="contact" novalidate>
    <div class="form contact-fields"><div class="field"><label for="cn">Name</label><input id="cn" name="name" required autocomplete="name"></div><div class="field"><label for="ce">Email</label><input id="ce" name="email" type="email" required autocomplete="email"></div></div>
    <div class="field"><label for="cm">Message</label><textarea id="cm" name="message" required placeholder="How can we help?"></textarea></div>
    <div class="row end contact-actions"><button class="btn p contact-submit" type="submit">${icon('send')}Send message</button></div>
   </form>
  </div></section>
 </main>
 <footer class="wrap foot-public row"><span>© 2026 AgriVision AI · Build Beyond '26 prototype</span><span class="row" style="gap:14px"><a href="${BASE}login.html">Log in</a><a href="${BASE}register.html">Register</a></span></footer>`;
}

/* ---------- Auth pages ---------- */
function authSide(title,lead){
 return `<aside class="auth-side">
  <a class="brand" href="${BASE}index.html" style="padding:0"><span class="mark">${icon('leaf')}</span><span>AgriVision <span class="ai">AI</span></span></a>
  <div><h2>${title}</h2><p class="sub">${lead}</p>
   <ul><li>${icon('scan')}<span>Quality grades from a single photo, with the checks behind them.</span></li><li>${icon('chart')}<span>Mandi price history and a suggested price.</span></li><li>${icon('shield')}<span>Verified buyers, and transparent bids and orders.</span></li></ul></div>
  <p class="mut small">Prototype · demonstration data</p>
 </aside>`;
}
function renderAuth(mode='login'){
 const reg=mode==='register';
 $('#app').innerHTML=`<div class="auth-shell">
  ${authSide(reg?'Join the marketplace':'Welcome back',reg?'Create a farmer or buyer account. Administrator accounts are set up by the platform team.':'Sign in to your workspace.')}
  <main class="auth-form"><div class="authbox">
   <a class="brand" href="${BASE}index.html" style="display:none"></a>
   <h1>${reg?'Create your account':'Sign in'}</h1>
   <p class="sub">${reg?'Choose a role. The fields change to match it.':'Use your registered email and password.'}</p>
   <div class="tabs-block" role="tablist"><button role="tab" aria-selected="${!reg}" data-act="authmode" data-m="login">Sign in</button><button role="tab" aria-selected="${reg}" data-act="authmode" data-m="register">Register</button></div>
   ${reg?registerForm():loginForm()}
  </div></main>
 </div>`;
}
function loginForm(){
 return `<form data-form="login" class="stack" style="gap:0">
  <div class="field"><label for="em">Email</label><input id="em" name="email" type="email" required autocomplete="username" placeholder="you@example.com"></div>
  <div class="field" style="margin-top:14px"><label for="pw">Password</label><div class="pw"><input id="pw" name="pass" type="password" required autocomplete="current-password" placeholder="Your password"><button type="button" data-act="togglepw" aria-label="Show password">Show</button></div></div>
  <div class="row" style="margin:12px 0 4px"><span></span><a class="small" href="${BASE}forgot.html">Forgot password?</a></div>
  <button class="btn p w lg" type="submit" style="margin-top:10px">Sign in</button>
 </form>
 <div class="divider">Demonstration accounts</div>
 <div class="demos">
  <button class="demo" type="button" data-act="demo" data-e="ramesh@demo.in" data-p="farmer123"><span><b>Farmer</b> · Ramesh Kumar, Kolar</span><span class="chip ok">Farmer</span></button>
  <button class="demo" type="button" data-act="demo" data-e="buyer@demo.in" data-p="buyer123"><span><b>Buyer</b> · FreshMart Wholesale</span><span class="chip info">Buyer</span></button>
  <button class="demo" type="button" data-act="demo" data-e="admin@demo.in" data-p="admin123"><span><b>Administrator</b> · restricted access</span><span class="chip acc">Admin</span></button>
 </div>
 <p class="hint" style="margin-top:12px">Demonstration accounts only. Filling in a demo account does not sign you in until you press Sign in.</p>`;
}
function registerForm(){
 const farmer=REG_ROLE==='farmer';
 const dl=`<datalist id="kadist">${KA_DISTRICTS.map(d=>`<option value="${d}">`).join('')}</datalist>`;
 return `<form data-form="register" class="stack" style="gap:14px">
  <div class="roles" role="radiogroup" aria-label="Account type">
   <label class="role"><input type="radio" name="role" value="farmer" ${farmer?'checked':''} data-act="regrole" data-r="farmer"><span><b>Farmer</b><br>I grow and sell produce</span></label>
   <label class="role"><input type="radio" name="role" value="buyer" ${!farmer?'checked':''} data-act="regrole" data-r="buyer"><span><b>Buyer</b><br>Retailer, wholesaler or processor</span></label>
  </div>
  <div class="form">
   ${farmer?`
    <div class="field span2"><label for="r1">Full name</label><input id="r1" name="name" required autocomplete="name"></div>
    <div class="field"><label for="r2">Mobile number</label><input id="r2" name="phone" required inputmode="numeric" maxlength="10" pattern="[6-9][0-9]{9}" placeholder="10 digits"></div>
    <div class="field"><label for="r3">Email</label><input id="r3" name="email" type="email" required autocomplete="email"></div>
    <div class="field"><label for="r4">Farm name</label><input id="r4" name="farm" required></div>
    <div class="field"><label for="r5">Village</label><input id="r5" name="village" required></div>
    <div class="field"><label for="r6">State</label><select id="r6" name="state" data-act="" >${STATES.map(s=>`<option ${s==='Karnataka'?'selected':''}>${s}</option>`).join('')}</select></div>
    <div class="field"><label for="r7">District</label><input id="r7" name="district" list="kadist" required placeholder="Start typing"></div>
    <div class="field span2"><label for="r8">Farm location</label><input id="r8" name="location" required placeholder="Nearest landmark or road (not shared publicly)"><p class="hint">Only the district is shown to buyers. Your exact location is never published.</p></div>
    <div class="field span2"><label for="r9">Password</label><input id="r9" name="pass" type="password" required minlength="6" autocomplete="new-password" placeholder="At least 6 characters"></div>
   `:`
    <div class="field span2"><label for="r1">Company name</label><input id="r1" name="company" required></div>
    <div class="field"><label for="r2">Contact person</label><input id="r2" name="contactPerson" required autocomplete="name"></div>
    <div class="field"><label for="r3">Email</label><input id="r3" name="email" type="email" required autocomplete="email"></div>
    <div class="field"><label for="r4">Mobile number</label><input id="r4" name="phone" required inputmode="numeric" maxlength="10" pattern="[6-9][0-9]{9}" placeholder="10 digits"></div>
    <div class="field"><label for="r5">Business type</label><select id="r5" name="business">${['Retailer','Wholesaler','Food Processor'].map(s=>`<option>${s}</option>`).join('')}</select></div>
    <div class="field span2"><label for="r6">Business address</label><input id="r6" name="address" required placeholder="Street, area (not shared publicly)"></div>
    <div class="field"><label for="r7">State</label><select id="r7" name="state">${STATES.map(s=>`<option ${s==='Karnataka'?'selected':''}>${s}</option>`).join('')}</select></div>
    <div class="field"><label for="r8">District</label><input id="r8" name="district" list="kadist" required placeholder="Start typing"></div>
    <div class="field span2"><label for="r9">Password</label><input id="r9" name="pass" type="password" required minlength="6" autocomplete="new-password" placeholder="At least 6 characters"></div>
   `}
  </div>
  ${dl}
  <label class="check" style="font-weight:400"><input type="checkbox" name="terms" required> I agree to the terms and understand this is a prototype with demonstration data.</label>
  <button class="btn p w lg" type="submit">Create account</button>
  <p class="hint">Administrator accounts cannot be registered here. Platform staff provision them.</p>
 </form>`;
}
function renderForgot(){
 $('#app').innerHTML=`<div class="auth-shell">
  ${authSide('Reset your password','We will send a reset link to your registered email.')}
  <main class="auth-form"><div class="authbox">
   <h1>Forgot password</h1>
   <p class="sub">Enter the email you registered with.</p>
   <form data-form="forgot" class="stack" style="margin-top:20px;gap:14px">
    <div class="field"><label for="fe">Email</label><input id="fe" name="email" type="email" required autocomplete="username"></div>
    <button class="btn p w lg" type="submit">Send reset link</button>
   </form>
   <p class="hint" style="margin-top:14px">Demonstration only: no email is sent. The confirmation message is shown on screen.</p>
   <p style="margin-top:18px"><a href="${BASE}login.html">Back to sign in</a></p>
  </div></main>
 </div>`;
}
