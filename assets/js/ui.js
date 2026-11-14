/* UI: auth, app shell, views, charts and render. */

/* ---------- Shared components ---------- */
const brandHTML=(cls='')=>`<div class="brand ${cls}"><span class="mark">${icon('leaf')}</span><span>AgriVision <span class="ai">AI</span></span></div>`;
const pageHead=(title,sub,extra='')=>`<div class="pagehead"><div><h1>${title}</h1>${sub?`<p class="sub">${sub}</p>`:''}</div>${extra}</div>`;
const sampleTag=()=>'<span class="tag info">Sample data</span>';
const kv=(l,v,meta='',cls='')=>`<div><div class="mut">${l}</div><span class="bigval ${cls}">${v}</span>${meta?`<div class="mut">${meta}</div>`:''}</div>`;
const statRow=arr=>`<div class="grid4">${arr.map(([l,v,n,c])=>`<div class="card">${kv(l,v,n||'',c||'')}</div>`).join('')}</div>`;
const statCards=arr=>statRow(arr.map(([l,v,n])=>[l,num(v),n]));
const emptyState=(title,text,cta='',ic='leaf')=>`<div class="empty"><span class="ico">${icon(ic)}</span><b>${title}</b><p class="mut" style="margin:0 auto;max-width:380px">${text}</p>${cta}</div>`;
function statusTag(s){
 const map={active:['ok','Active'],accepted:['ok','Accepted'],sold:['ok','Sold'],pending:['warn','Pending'],rejected:['bad','Rejected'],hidden:['bad','Hidden'],withdrawn:['','Withdrawn']};
 const [c,t]=map[s]||['warn','Pending'];
 return `<span class="tag ${c}">${t}</span>`;
}
function greeting(){const h=new Date().getHours();return h<12?'Good morning':h<17?'Good afternoon':'Good evening'}
function mediaInner(l){return l.img?`<img src="${l.img}" alt="${esc(l.crop)} photo">`:cropTile(l.crop,0)}
function currentBidListing(){
 const mine=myListings();if(!mine.length)return null;
 const L=mine.find(x=>x.id===PR.bl)||mine[0];PR.bl=L.id;return L;
}

/* ---------- Auth ---------- */
function renderAuth(mode='login'){
 const reg=mode==='register';
 $('#app').innerHTML=`<div class="auth">
  <aside class="hero">
   ${brandHTML()}
   <div>
    <h2>Sell at a fair price, with proof of quality.</h2>
    <p>Photo-based quality checks, mandi price context and bids from verified buyers, built for farmers and the traders who buy from them.</p>
    <ul>
     <li>${icon('scan')}<span>Check produce quality from a single photo, with a note on what was looked at.</span></li>
     <li>${icon('trend')}<span>See recent mandi prices and a suggested price before you list.</span></li>
     <li>${icon('check')}<span>Buyers are verified by the platform before they can place bids.</span></li>
    </ul>
   </div>
   <p class="fine">Prototype with sample data · Build Beyond '26</p>
  </aside>
  <div class="authwrap"><div class="authbox">
   ${brandHTML('dark')}
   <h1>${reg?'Create your account':'Welcome back'}</h1>
   <p class="sub">${reg?'Takes about a minute. Buyers are verified before they can bid.':'Sign in to open your workspace.'}</p>
   <div class="card" style="margin-top:20px;padding:24px">
    <div class="tabs" role="tablist">
     <button role="tab" aria-selected="${!reg}" class="${reg?'':'on'}" data-act="authmode" data-m="login">Sign in</button>
     <button role="tab" aria-selected="${reg}" class="${reg?'on':''}" data-act="authmode" data-m="register">Create account</button>
    </div>
    ${reg?registerForm():loginForm()}
   </div>
  </div></div>
 </div>`;
}
function loginForm(){
 return `<form data-form="login">
  <div class="form-field"><label for="em">Email</label><input id="em" name="email" type="email" required autocomplete="username" placeholder="you@example.com"></div>
  <div class="form-field" style="margin-top:14px"><label for="pw">Password</label>
   <div class="pw"><input id="pw" name="pass" type="password" required autocomplete="current-password" placeholder="Your password"><button type="button" data-act="togglepw" aria-label="Show password">Show</button></div></div>
  <button class="btn p w" type="submit">Sign in</button>
 </form>
 <div class="divider">Try a demo account</div>
 <div class="demos">
  <button class="demo" type="button" data-act="demo" data-e="ramesh@demo.in" data-p="farmer123"><span><b>Farmer</b> · Ramesh Kumar, Kolar</span><span class="tag ok">Farmer</span></button>
  <button class="demo" type="button" data-act="demo" data-e="buyer@demo.in" data-p="buyer123"><span><b>Buyer</b> · FreshMart Wholesale</span><span class="tag info">Buyer</span></button>
  <button class="demo" type="button" data-act="demo" data-e="admin@demo.in" data-p="admin123"><span><b>Administrator</b> · Platform Admin</span><span class="tag acc">Admin</span></button>
 </div>`;
}
function registerForm(){
 return `<form data-form="register">
  <div class="form-field"><label for="rn">Full name</label><input id="rn" name="name" required autocomplete="name" placeholder="As on your ID"></div>
  <div class="form-field" style="margin-top:14px"><label>I am a</label>
   <div class="roles">
    <label class="role"><input type="radio" name="role" value="farmer" checked><span><b>Farmer</b><br>I grow and sell produce</span></label>
    <label class="role"><input type="radio" name="role" value="buyer"><span><b>Buyer</b><br>Retailer, wholesaler or processor</span></label>
   </div></div>
  <div class="form-field" style="margin-top:14px"><label for="re">Email</label><input id="re" name="email" type="email" required autocomplete="email" placeholder="you@example.com"></div>
  <div class="form-field" style="margin-top:14px"><label for="rp">Mobile number <span class="mut" style="font-weight:400">(optional)</span></label><input id="rp" name="phone" inputmode="numeric" maxlength="10" pattern="[6-9][0-9]{9}" placeholder="10-digit mobile"></div>
  <div class="form-field" style="margin-top:14px"><label for="rd">District</label><select id="rd" name="district">${DISTRICTS.map(d=>`<option ${d==='Kolar'?'selected':''}>${d}</option>`).join('')}</select></div>
  <div class="form-field" style="margin-top:14px"><label for="rpw">Password</label><input id="rpw" name="pass" type="password" required minlength="6" autocomplete="new-password" placeholder="At least 6 characters"></div>
  <button class="btn p w" type="submit">Create account</button>
 </form>`;
}
function login(email,pass){
 const u=db.users.find(x=>x.email.toLowerCase()===email.trim().toLowerCase()&&x.pass===pass);
 if(!u){toast('Email or password is incorrect');return}
 db.session=u.id;db.nav='overview';log(u.name+' signed in');save();
 toast('Welcome, '+u.name.split(' ')[0],true);
 location.href=BASE+u.role+'/dashboard.html';
}

/* ---------- App shell ---------- */
function renderShell(){
 const u=me(),items=NAV[u.role];
 const label={farmer:'Farmer workspace',buyer:'Buyer workspace',admin:'Administration'}[u.role];
 $('#app').innerHTML=`<div class="app">
  <aside class="side" id="side" aria-label="Main navigation">
   ${brandHTML()}
   ${items.map(([id,l,ic,s])=>`<button class="nav" data-act="nav" data-v="${id}" aria-current="${db.nav===id?'page':'false'}"><span class="nic">${icon(ic)}</span><span class="long">${l}</span><span class="short">${s}</span></button>`).join('')}
   <div class="foot">Prototype · sample data<br>Saved in this browser only</div>
  </aside>
  <div class="main">
   <div class="top"><span class="crumb">${label}</span>
    <div class="who"><span class="nm">${esc(u.name)}</span><span class="av" aria-hidden="true">${esc(u.name[0])}</span><button class="btn o sm" data-act="logout">${icon('logout')}Log out</button></div>
   </div>
   <div id="view"></div>
  </div>
 </div>`;
}

/* ---------- Dialogs ---------- */
function confirmM(d){
 openM(`<h2>${d.title}</h2><p class="mut" style="margin:6px 0 22px;font-size:14px">${d.text}</p>
 <div class="row end"><button class="btn o" data-act="closem">Cancel</button><button class="btn ${d.danger?'dx':'p'}" data-act="yes" data-then="${d.then}" data-id="${d.id}">${d.label}</button></div>`);
}

/* ---------- Listing pieces ---------- */
function listingTable(arr,actions,admin){
 if(!arr.length)return emptyState('No listings yet','Run a quality check on a produce photo, then publish it to reach buyers.','<button class="btn p" data-act="nav" data-v="inspect">New listing</button>');
 return `<div class="tablewrap"><table><thead><tr><th>Crop</th><th class="num">Quantity</th><th>Grade</th><th>Location</th><th class="num">Asking / qtl</th><th>Status</th>${actions?'<th></th>':''}</tr></thead><tbody>
 ${arr.map(l=>`<tr><td><div class="crop">${cropTile(l.crop,34)}${esc(l.crop)}</div></td><td class="num">${num(l.qty)} kg</td><td>${esc(l.grade)}</td><td>${esc(l.loc)}</td><td class="num">${fmt(l.ask)}</td><td>${statusTag(l.status)}</td>${actions?`<td class="act">${rowAction(l,admin)}</td>`:''}</tr>`).join('')}
 </tbody></table></div>`;
}
function rowAction(l,admin){
 if(l.status==='active'){
  return admin
   ?`<button class="btn o sm" data-act="ask" data-title="Hide this listing?" data-text="Buyers will stop seeing it until you restore it." data-label="Hide listing" data-then="mod" data-id="${l.id}" data-danger="1">Hide</button>`
   :`<button class="btn o sm" data-act="ask" data-title="Withdraw this listing?" data-text="Buyers will no longer see it. You can relist it later." data-label="Withdraw" data-then="mod" data-id="${l.id}">Withdraw</button>`;
 }
 if(l.status==='hidden'&&!admin)return '<span class="mut">Hidden by admin</span>';
 if(l.status==='withdrawn'||l.status==='hidden')return `<button class="btn o sm" data-act="mod" data-id="${l.id}">Restore</button>`;
 return '';
}
function salesTable(arr,buyerView){
 return `<div class="tablewrap"><table><thead><tr><th>Crop</th><th>${buyerView?'Seller':'Buyer'}</th><th class="num">Quantity</th><th class="num">Price / qtl</th><th class="num">Total</th><th>Delivery</th><th>Date</th></tr></thead><tbody>
 ${arr.map(b=>{
   const L=listingOf(b.listing);
   const seller=L&&userById(L.farmer)?userById(L.farmer).name:'—';
   return `<tr><td>${L?esc(L.crop):'—'}</td><td>${esc(buyerView?seller:b.buyer)}</td><td class="num">${num(b.qty)} kg</td><td class="num">${fmt(b.price)}</td><td class="num"><b>${fmt(b.price*b.qty/100)}</b></td><td>${esc(b.deliver)}</td><td class="mut">${esc(b.t)}</td></tr>`;
  }).join('')}
 </tbody></table></div>`;
}
function reportHTML(I){
 const conf=MODEL_CONF,low=conf<75;
 const ind=[['Colour uniformity',92],['Surface defects (fewer is better)',97],['Size uniformity',88],['Freshness signals',90]];
 return `<div class="row"><h2>Quality report</h2>${sampleTag()}</div>
 ${low?`<div class="note warn">Low model confidence. Request a manual inspection before listing.<br><button class="btn o sm" data-act="manual" style="margin-top:8px">Request manual inspection</button></div>`:''}
 <div class="kvs" style="margin:16px 0 20px">
  ${kv('Detected crop',esc(I.crop))}
  ${kv('Quality grade','A','Illustrative','ok')}
  ${kv('Model confidence',conf+'%','Illustrative')}
  ${kv('Visual condition','Good')}
 </div>
 <div class="mut" style="margin-bottom:2px">Quality indicators</div>
 ${ind.map(([l,v])=>`<div class="row" style="margin-top:10px;font-size:14px"><span>${l}</span><b>${v}</b></div><div class="bar"><i style="width:${v}%"></i></div>`).join('')}
 <div class="rec"><b>Suggested use:</b> suitable for a standard listing of ${num(I.qty)} kg from ${esc(I.loc)}. Price guidance is on the Price intelligence page.</div>
 <div class="form" style="margin-top:18px;grid-template-columns:1fr">
  <div class="form-field"><label for="ask">Asking price per quintal (₹)</label><input id="ask" type="number" min="1" inputmode="numeric" data-i="ask" value="${I.ask||REF_PRICE}"><p class="hint">Mandi reference today: ${fmt(REF_PRICE)} per quintal (sample).</p></div>
 </div>
 <button class="btn g w" data-act="publish">${icon('upload')}Publish listing</button>
 <div class="note">Scores are illustrative until the trained model is connected.</div>`;
}
function card(l){
 const saved=db.saved.includes(l.id),buyer=db.session&&me().role==='buyer';
 return `<article class="card hov listing"><div class="pimg">${mediaInner(l)}</div>
  <div class="row"><b style="font-size:16px">${esc(l.crop)}</b><span class="tag ok">Grade ${esc(l.grade)}</span></div>
  <div class="mut meta">${icon('pin')}${esc(l.loc)} · ${num(l.qty)} kg available</div>
  <div class="row" style="margin-top:14px"><span><b class="price">${fmt(l.ask)}</b> <span class="mut">per quintal</span></span>${l.verified?'<span class="tag info">AI checked</span>':''}</div>
  <div class="row" style="margin-top:14px;gap:8px;flex-wrap:nowrap"><button class="btn p sm" style="flex:1" data-act="detail" data-id="${l.id}">View details</button>${buyer?`<button class="btn o sm ${saved?'on':''}" data-act="save" data-id="${l.id}" aria-pressed="${saved}" aria-label="${saved?'Remove from saved':'Save listing'}">${icon('heart')}</button>`:''}</div>
 </article>`;
}
function gridHTML(){
 const q=F.q.trim().toLowerCase();
 const L=db.listings.filter(l=>l.status==='active'&&l.crop.toLowerCase().includes(q)&&(!F.loc||l.loc===F.loc)&&(!F.grade||l.grade===F.grade)&&l.qty>=(+F.minQ||0));
 L.sort((a,b)=>F.sort==='asc'?a.ask-b.ask:b.ask-a.ask);
 return L.map(card).join('')||`<div class="card" style="grid-column:1/-1">${emptyState('No listings match these filters','Try a wider location, a lower minimum quantity or a different crop.','','store')}</div>`;
}
function marketView(){
 const locs=[...new Set(db.listings.map(l=>l.loc))].sort();
 const buyer=me().role==='buyer';
 return `${pageHead(buyer?'Explore produce':'Marketplace',buyer?'Verified listings from farmers. Open one to read its quality summary and place a bid.':'All active listings on the platform.')}
 <div class="card" style="margin-bottom:16px"><div class="form">
  <div class="form-field span2"><label for="fq">Search crop</label><input id="fq" data-f="q" placeholder="Tomato, onion…" value="${esc(F.q)}"></div>
  <div class="form-field"><label for="fl">Location</label><select id="fl" data-f="loc"><option value="">All locations</option>${locs.map(l=>`<option ${F.loc===l?'selected':''}>${esc(l)}</option>`).join('')}</select></div>
  <div class="form-field"><label for="fg">Grade</label><select id="fg" data-f="grade"><option value="">All grades</option>${['A','B','C'].map(g=>`<option value="${g}" ${F.grade===g?'selected':''}>Grade ${g}</option>`).join('')}</select></div>
  <div class="form-field"><label for="fm">Minimum quantity (kg)</label><input id="fm" type="number" min="0" inputmode="numeric" data-f="minQ" value="${F.minQ||''}" placeholder="0"></div>
  <div class="form-field"><label for="fs">Price</label><select id="fs" data-f="sort"><option value="asc" ${F.sort==='asc'?'selected':''}>Lowest first</option><option value="desc" ${F.sort==='desc'?'selected':''}>Highest first</option></select></div>
 </div></div>
 <div class="grid3" id="grid">${gridHTML()}</div>`;
}
function detailHTML(l){
 const f=userById(l.farmer)||{name:'Farmer'};
 const buyer=me().role==='buyer',bids=bidsOn(l.id);
 return `<div class="row"><div><h2 style="margin:0 0 4px">${esc(l.crop)} · Grade ${esc(l.grade)}</h2><p class="mut" style="margin:0">${esc(f.name)} · ${esc(l.loc)}</p></div>${l.verified?'<span class="tag info">AI checked</span>':''}</div>
 <div class="pimg" style="height:180px;margin:16px 0 18px">${mediaInner(l)}</div>
 <div class="kvs" style="margin-bottom:20px">${kv('Asking price',fmt(l.ask),'per quintal')}${kv('Available',num(l.qty)+' kg','')}${kv('Quality','Grade '+esc(l.grade),'Illustrative summary')}</div>
 <h2>Current bids (${bids.length})</h2>
 ${bids.length?bids.map(b=>`<div class="lrow"><span><b>${esc(b.buyer)}</b><span class="mut"> · ${esc(b.deliver)}</span></span><span>${fmt(b.price)}/qtl · ${num(b.qty)} kg ${statusTag(b.status)}</span></div>`).join(''):'<p class="mut">No bids yet.</p>'}
 ${buyer&&l.status==='active'?`<h2 style="margin-top:22px">Place a bid</h2>
  <div class="form">
   <div class="form-field"><label for="bp">Price per quintal (₹)</label><input id="bp" type="number" min="1" inputmode="numeric" value="${l.ask}"></div>
   <div class="form-field"><label for="bq">Quantity (kg)</label><input id="bq" type="number" min="1" max="${l.qty}" inputmode="numeric" value="${l.qty}"></div>
   <div class="form-field"><label for="bl">Delivery location</label><input id="bl" value="Bengaluru APMC"></div>
  </div>
  <p class="hint">Prices are per quintal (100 kg). Total = price × kg ÷ 100.</p>
  <button class="btn p w" data-act="placebid" data-id="${l.id}">Submit bid</button>`:''}`;
}

/* ---------- Views ---------- */
const VIEWS={
 'farmer.overview'(){
  const mine=myListings(),ids=mine.map(l=>l.id),mv=movement();
  const offers=db.bids.filter(b=>ids.includes(b.listing)&&b.status==='pending').length;
  const sold=db.bids.filter(b=>ids.includes(b.listing)&&b.status==='accepted').length;
  const qty=mine.filter(l=>l.status==='active').reduce((a,l)=>a+l.qty,0);
  const recent=db.bids.filter(b=>ids.includes(b.listing)).slice(0,4);
  return `${pageHead(`${greeting()}, ${esc(me().name.split(' ')[0])}`,'Your listings, bids and price context at a glance.',`<button class="btn p" data-act="nav" data-v="inspect">${icon('scan')}New listing</button>`)}
  ${statCards([['Active listings',mine.filter(l=>l.status==='active').length],['Quantity listed (kg)',qty],['Open bids',offers],['Completed sales',sold]])}
  <div class="grid2">
   <div class="card"><div class="row"><h2>Price snapshot</h2>${sampleTag()}</div>
    <div class="kvs" style="margin-bottom:18px">
     ${kv('Mandi reference',fmt(REF_PRICE),'per quintal')}
     ${kv('Suggested price',fmt(REC_PRICE),'per quintal','brand')}
     ${kv('Expected range',fmt(PRED_RANGE[0])+'–'+num(PRED_RANGE[1]),'next period')}
     ${kv('Price movement',mv.text,'vs previous month',mv.up?'ok':'bad')}
    </div>
    <button class="btn o w" data-act="nav" data-v="price">Open price intelligence</button></div>
   <div class="card"><h2>Regional demand</h2>
    ${DEMAND.map(([r,v])=>`<div class="dem"><div class="row"><span>${r}</span><b>${v}</b></div><div class="bar"><i style="width:${v}%"></i></div></div>`).join('')}
    <p class="mut" style="margin-top:8px">Demand index · sample data</p></div>
  </div>
  <div class="grid2">
   <div class="card"><div class="row"><h2>Price trend, ₹ per quintal</h2>${sampleTag()}</div><div class="chart"><canvas id="cTrend" role="img" aria-label="Historical mandi price trend"></canvas></div></div>
   <div class="card"><h2>Latest bids</h2>
    ${recent.length?recent.map(b=>`<div class="lrow"><div><b>${esc(b.buyer)}</b><div class="mut">${fmt(b.price)}/qtl · ${num(b.qty)} kg</div></div>${statusTag(b.status)}</div>`).join(''):emptyState('No bids yet','Bids on your listings will appear here.','','tag')}
    <button class="btn o w" data-act="nav" data-v="bids">Review bids</button></div>
  </div>
  <div class="card"><div class="row"><h2>Your listings</h2></div>${listingTable(mine)}</div>`;
 },
 'farmer.produce'(){
  return `${pageHead('My produce','Listings you have published. Withdraw a listing to pause it, and restore it when you are ready.','<button class="btn p" data-act="nav" data-v="inspect">New listing</button>')}
  <div class="card">${listingTable(myListings(),true)}</div>`;
 },
 'farmer.inspect'(){
  const I=db.insp||(db.insp={crop:'Tomato',qty:100,loc:'Kolar, Karnataka',st:'idle',img:null,ask:REF_PRICE});
  const step=!I.img?0:I.st==='done'?2:1;
  const steps=['Add photo','Assess quality','List'].map((s,i)=>`<div class="step ${i<step?'done':''} ${i===step?'on':''}"><span>${i<step?icon('check'):i+1}</span>${s}</div>`).join('');
  const photo=I.img
   ?`<div class="photo"><img src="${I.img}" alt="Uploaded produce photo">${I.st==='done'?'<svg class="overlay" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><ellipse cx="34" cy="42" rx="11" ry="9"/><ellipse cx="66" cy="60" rx="8" ry="7"/></svg>':''}</div>
     <div class="row" style="margin-top:12px"><span class="mut">${I.st==='done'?'Dashed areas are illustrative highlights, not model output.':'Photo ready for analysis.'}</span><button class="btn o sm" data-act="pick">Replace photo</button></div>`
   :`<div class="drop" id="drop" data-act="pick" role="button" tabindex="0" aria-label="Choose a produce photo"><div class="dz-ico">${icon('upload')}</div><b>Add a produce photo</b><span class="mut">Drag it here, or tap to use your camera or gallery. JPG or PNG.</span></div>`;
  let res;
  if(I.st==='scan')res=`<div class="scan">${I.img?`<img src="${I.img}" alt="">`:''}</div><p class="mut" style="text-align:center;margin:14px 0 4px">Checking colour, texture and visible defects…</p><div class="skel"></div><div class="skel" style="width:70%"></div>`;
  else if(I.st==='done')res=reportHTML(I);
  else res=`<div class="row"><h2>What the check looks at</h2></div>
   <ul class="checks">${[['Colour uniformity','Even ripeness and colour across the lot'],['Surface defects','Cuts, bruises, spots and cracks'],['Size uniformity','Variation that affects grading'],['Freshness signals','Firmness and visible wilting']].map(([t,s])=>`<li>${icon('check')}<span><b>${t}</b><br><span class="mut">${s}</span></span></li>`).join('')}</ul>
   <div class="note">For best results: shoot in daylight on a plain background, keep the item in focus, and include a representative sample of the lot.</div>`;
  return `${pageHead('AI quality check','Assess produce from a photo and get a grade you can use when listing.')}
  <div class="stepper" aria-label="Progress">${steps}</div>
  <div class="grid2">
   <div class="card">${photo}<input type="file" id="up" accept="image/*" data-u="1" hidden>
    <div class="form" style="margin-top:16px">
     <div class="form-field"><label for="ic">Crop</label><select id="ic" data-i="crop">${CROPS.map(c=>`<option ${I.crop===c?'selected':''}>${c}</option>`).join('')}</select></div>
     <div class="form-field"><label for="iq">Quantity (kg)</label><input id="iq" type="number" min="1" inputmode="numeric" data-i="qty" value="${I.qty}"></div>
     <div class="form-field"><label for="il">Location</label><select id="il" data-i="loc">${FARM_LOCS.map(c=>`<option ${I.loc===c?'selected':''}>${c}</option>`).join('')}</select></div>
    </div>
    <button class="btn g w" data-act="analyze" ${!I.img||I.st==='scan'?'disabled':''}>${I.st==='scan'?'Analyzing…':'Analyze produce'}</button>
    ${I.img?'':'<p class="hint" style="text-align:center">Add a photo to run the analysis.</p>'}
   </div>
   <div class="card">${res}</div>
  </div>`;
 },
 'farmer.price'(){
  const sel=(list,val,key)=>`<select id="p-${key}" data-p="${key}">${list.map(x=>`<option ${x===val?'selected':''}>${x}</option>`).join('')}</select>`;
  const mv=movement();
  const factors=[['Historical price movement',70,'+6%'],['Produce quality (Grade A)',62,'+4%'],['Regional demand',66,'+5%'],['Seasonality',30,'−2%'],['Transport cost',34,'−3%']];
  const pos=Math.round((REC_PRICE-PRED_RANGE[0])/(PRED_RANGE[1]-PRED_RANGE[0])*100);
  return `${pageHead('Price intelligence','Mandi price history, a short-term forecast and the reasons behind the suggested price.',sampleTag())}
  <div class="card" style="margin-bottom:16px"><div class="form">
   <div class="form-field"><label for="p-crop">Crop</label>${sel(CROPS,PR.crop,'crop')}</div>
   <div class="form-field"><label for="p-mkt">Market</label>${sel(MARKETS,PR.mkt,'mkt')}</div>
   <div class="form-field"><label for="p-range">Period</label><select id="p-range" data-p="range"><option value="6" ${PR.range==6?'selected':''}>Last 6 months</option><option value="12" ${PR.range==12?'selected':''}>Last 12 months</option></select></div>
  </div><p class="hint">This prototype shows the same sample series for every crop and market.</p></div>
  ${statRow([
    ['Mandi reference',fmt(REF_PRICE),'per quintal'],
    ['Suggested selling price',fmt(REC_PRICE),'per quintal','brand'],
    ['Expected range',fmt(PRED_RANGE[0])+'–'+num(PRED_RANGE[1]),'next period'],
    ['Transport cost',fmt(Math.round(TRANS_RATE*70)),'per quintal, 70 km']
  ])}
  <div class="grid2">
   <div class="card"><div class="row"><h2>Historical and forecast price, ₹ per quintal</h2>${sampleTag()}</div><div class="chart"><canvas id="cTrend" role="img" aria-label="Historical and forecast mandi price"></canvas></div></div>
   <div class="card xai"><h2>What drives the suggestion</h2>
    <p class="mut" style="margin:-6px 0 14px">Bar length shows relative influence. The figure is the estimated effect on price.</p>
    <ul>${factors.map(([l,w,d])=>`<li><div class="row"><span style="font-size:14px">${l}</span><b class="${d.startsWith('−')?'neg':'pos'}">${d}</b></div><div class="bar ${d.startsWith('−')?'neg':''}"><i style="width:${w}%"></i></div></li>`).join('')}</ul>
    <div style="margin-top:14px"><div class="row"><span class="mut">Expected range</span><span class="tag warn">Confidence ${PRED_CONF}% · sample</span></div>
     <div class="range"><i></i><b style="left:${pos}%"></b></div>
     <div class="scale"><span>${fmt(PRED_RANGE[0])}</span><span>Suggested ${fmt(REC_PRICE)}</span><span>${fmt(PRED_RANGE[1])}</span></div></div>
   </div>
  </div>
  <div class="card"><div class="row"><h2>Regional demand forecast</h2>${sampleTag()}</div><div class="chart" style="height:220px"><canvas id="cDemand" role="img" aria-label="Regional demand index"></canvas></div></div>`;
 },
 'farmer.market'(){return marketView()},
 'buyer.explore'(){return marketView()},
 'farmer.bids'(){
  const mine=myListings();
  if(!mine.length)return `${pageHead('Bids','Compare bids on each listing, then accept one.')}<div class="card">${emptyState('No listings yet','Publish a produce listing to start receiving bids.','<button class="btn p" data-act="nav" data-v="inspect">New listing</button>','tag')}</div>`;
  const L=currentBidListing();
  const list=bidsOn(L.id).slice().sort((a,b)=>b.price-a.price);
  const best=list.find(b=>b.status==='pending');
  const open=list.filter(b=>b.status==='pending').length;
  const top=best?best.price:null;
  return `${pageHead('Bids','Accepting a bid closes the listing and declines the other open bids.',`<div style="min-width:260px"><label for="bl-sel">Listing</label><select id="bl-sel" data-p="bl">${mine.map(x=>`<option value="${x.id}" ${x.id===L.id?'selected':''}>${esc(x.crop)} · ${num(x.qty)} kg · ${esc(x.loc)}</option>`).join('')}</select></div>`)}
  ${statRow([
    ['Asking price',fmt(L.ask),'per quintal'],
    ['Highest bid',top?fmt(top):'—',top?((top-L.ask)>=0?'+':'−')+fmt(Math.abs(top-L.ask))+' vs asking':'No open bids','ok'],
    ['Open bids',open,'awaiting a decision'],
    ['Listing status',statusTag(L.status),'']
  ])}
  <div class="card" style="margin-bottom:16px">${list.length?`<div class="tablewrap"><table><thead><tr><th>Buyer</th><th class="num">Bid / qtl</th><th class="num">vs asking</th><th class="num">Quantity</th><th>Delivery</th><th>Received</th><th>Status</th><th></th></tr></thead><tbody>
   ${list.map(b=>{const d=b.price-L.ask;return `<tr><td><b>${esc(b.buyer)}</b>${best&&b.id===best.id?' <span class="tag ok">Highest</span>':''}</td><td class="num">${fmt(b.price)}</td><td class="num ${d>=0?'pos':'neg'}">${d>=0?'+':'−'}${fmt(Math.abs(d))}</td><td class="num">${num(b.qty)} kg</td><td>${esc(b.deliver)}</td><td class="mut">${esc(b.t)}</td><td>${statusTag(b.status)}</td><td class="act">${b.status==='pending'?`<button class="btn g sm" data-act="ask" data-title="Accept this bid?" data-text="The listing will be marked sold and other open bids will be declined." data-label="Accept bid" data-then="doaccept" data-id="${b.id}">Accept</button> <button class="btn d sm" data-act="ask" data-title="Reject this bid?" data-text="The buyer will be told the bid was not accepted." data-label="Reject bid" data-then="doreject" data-id="${b.id}" data-danger="1">Reject</button>`:''}</td></tr>`}).join('')}
  </tbody></table></div>`:emptyState('No bids yet','Buyers can see this listing in Explore produce. Bids will appear here.','','tag')}</div>
  <div class="card"><h2>Bid against asking price</h2><p class="mut" style="margin:-4px 0 12px">How far each bid is above or below your asking price, in ₹ per quintal.</p><div class="chart" style="height:${Math.max(150,list.length*52+40)}px"><canvas id="cBid" role="img" aria-label="Bids compared with the asking price"></canvas></div></div>`;
 },
 'farmer.sales'(){
  const ids=myListings().map(l=>l.id);
  const done=db.bids.filter(b=>ids.includes(b.listing)&&b.status==='accepted');
  return `${pageHead('Sales history','Completed sales from accepted bids.')}<div class="card">${done.length?salesTable(done):emptyState('No completed sales yet','Accepted bids appear here as sales.','','receipt')}</div>`;
 },
 'buyer.overview'(){
  const mine=db.bids.filter(b=>b.buyerId===db.session);
  const avail=db.listings.filter(l=>l.status==='active').reduce((a,l)=>a+l.qty,0);
  const live=db.listings.filter(l=>l.status==='active').slice(0,5);
  return `${pageHead(`${greeting()}, ${esc(me().name.split(' ')[0])}`,'Find verified produce, compare bids and place your own.',`<button class="btn p" data-act="nav" data-v="explore">${icon('store')}Explore produce</button>`)}
  ${statCards([['Open bids',mine.filter(b=>b.status==='pending').length],['Accepted bids',mine.filter(b=>b.status==='accepted').length],['Available produce (kg)',avail],['Saved listings',db.saved.length]])}
  <div class="grid2">
   <div class="card"><h2>Recent activity</h2><div class="feed">${db.log.slice(0,6).map(x=>`<div>${esc(x)}</div>`).join('')}</div></div>
   <div class="card"><h2>Available produce</h2>
    ${live.length?live.map(l=>`<div class="lrow"><div class="crop">${cropTile(l.crop,34)}<div><b>${esc(l.crop)}</b><div class="mut">${num(l.qty)} kg · Grade ${esc(l.grade)} · ${esc(l.loc)}</div></div></div><button class="btn o sm" data-act="detail" data-id="${l.id}">View</button></div>`).join(''):emptyState('Nothing listed right now','Check back soon.','','store')}
    <button class="btn p w" data-act="nav" data-v="explore">Explore all produce</button></div>
  </div>`;
 },
 'buyer.mybids'(){
  const mine=db.bids.filter(b=>b.buyerId===db.session);
  return `${pageHead('My bids','Track each bid. You can raise a pending bid by ₹20 per quintal.')}<div class="card">${mine.length?`<div class="tablewrap"><table><thead><tr><th>Produce</th><th class="num">My bid / qtl</th><th class="num">Quantity</th><th>Delivery</th><th>Status</th><th></th></tr></thead><tbody>
  ${mine.map(b=>{const L=listingOf(b.listing);return `<tr><td>${L?`<div class="crop">${cropTile(L.crop,30)}${esc(L.crop)}</div>`:'—'}</td><td class="num">${fmt(b.price)}</td><td class="num">${num(b.qty)} kg</td><td>${esc(b.deliver)}</td><td>${statusTag(b.status)}</td><td class="act">${b.status==='pending'?`<button class="btn o sm" data-act="raise" data-id="${b.id}">Raise +₹20</button>`:''}</td></tr>`}).join('')}
  </tbody></table></div>`:emptyState('No bids placed yet','Explore produce to find a listing and place your first bid.','<button class="btn p" data-act="nav" data-v="explore">Explore produce</button>','tag')}</div>`;
 },
 'buyer.saved'(){
  const L=db.listings.filter(l=>db.saved.includes(l.id));
  return `${pageHead('Saved listings','Listings you bookmarked to compare later.')}${L.length?`<div class="grid3">${L.map(card).join('')}</div>`:`<div class="card">${emptyState('Nothing saved yet','Tap the heart on a listing in Explore produce to save it here.','<button class="btn p" data-act="nav" data-v="explore">Explore produce</button>','heart')}</div>`}`;
 },
 'buyer.purchases'(){
  const mine=db.bids.filter(b=>b.buyerId===db.session&&b.status==='accepted');
  return `${pageHead('Purchase history','Bids that were accepted.')}<div class="card">${mine.length?salesTable(mine,true):emptyState('No purchases yet','Accepted bids will show here.','','receipt')}</div>`;
 },
 'admin.overview'(){
  const farmers=db.users.filter(u=>u.role==='farmer').length,buyers=db.users.filter(u=>u.role==='buyer').length;
  const tx=db.bids.filter(b=>b.status==='accepted').length;
  return `${pageHead('Overview','Marketplace health at a glance. Sample data.')}
  ${statCards([['Registered farmers',farmers],['Registered buyers',buyers],['Active listings',db.listings.filter(l=>l.status==='active').length],['Completed transactions',tx]])}
  <div class="card"><h2>Recent activity</h2><div class="feed">${db.log.slice(0,10).map(x=>`<div>${esc(x)}</div>`).join('')}</div></div>`;
 },
 'admin.users'(){
  const rows=db.users.filter(u=>u.role!=='admin');
  return `${pageHead('Users','Verify buyers before they can place bids on live listings.')}<div class="card"><div class="tablewrap"><table><thead><tr><th>Name</th><th>Role</th><th>Location</th><th>Verification</th><th></th></tr></thead><tbody>
  ${rows.map(u=>`<tr><td><b>${esc(u.name)}</b><div class="mut">${esc(u.email)}</div></td><td style="text-transform:capitalize">${u.role}</td><td>${esc(u.loc||'—')}</td><td>${u.role==='buyer'?(u.verified?'<span class="tag ok">Verified</span>':'<span class="tag warn">Pending review</span>'):'<span class="tag">Farmer</span>'}</td><td class="act">${u.role!=='buyer'?'':u.verified?`<button class="btn o sm" data-act="ask" data-title="Revoke verification?" data-text="${esc(u.name)} will not be able to place bids until verified again." data-label="Revoke" data-then="verify" data-id="${u.id}" data-danger="1">Revoke</button>`:`<button class="btn p sm" data-act="verify" data-id="${u.id}">Verify buyer</button>`}</td></tr>`).join('')}
  </tbody></table></div></div>`;
 },
 'admin.moderation'(){
  return `${pageHead('Listing moderation','Review listings and hide any that break marketplace policy.')}<div class="card">${listingTable(db.listings,true,true)}</div>`;
 },
 'admin.activity'(){
  return `${pageHead('Activity','Every marketplace event recorded in this session.')}<div class="card"><div class="feed">${db.log.map(x=>`<div>${esc(x)}</div>`).join('')}</div></div>`;
 }
};

/* ---------- Charts ---------- */
function mountCharts(){
 Object.values(CH).forEach(c=>c&&c.destroy());CH={};
 if(typeof Chart==='undefined')return;
 const C={brand:'#1F4A3A',brand2:'#2E6B53',accent:'#C9962E',grid:'#EEEDE7',mut:'#5C6861',light:'#A9C4B5',bad:'#D9776B'};
 Chart.defaults.font.family='Inter, system-ui, sans-serif';
 Chart.defaults.color=C.mut;
 const money=v=>'₹'+Number(v).toLocaleString('en-IN');
 const legend={position:'bottom',labels:{boxWidth:8,boxHeight:8,usePointStyle:true}};
 const trend=document.getElementById('cTrend');
 if(trend){
  const n=PR.range,hist=[...HP.slice(-n),...Array(3).fill(null)];
  const pred=[...Array(n-1).fill(null),HP[HP.length-1],...PP];
  CH.t=new Chart(trend,{type:'line',data:{labels:[...HM.slice(-n),...PM],datasets:[
   {label:'Historical mandi price',data:hist,borderColor:C.brand,backgroundColor:'rgba(31,74,58,.08)',fill:true,tension:.3,pointRadius:2,borderWidth:2},
   {label:'Forecast (sample)',data:pred,borderColor:C.accent,borderDash:[6,5],tension:.3,pointRadius:2,borderWidth:2}]},
   options:{responsive:true,maintainAspectRatio:false,animation:{duration:500},plugins:{legend},scales:{y:{ticks:{callback:money},grid:{color:C.grid}},x:{grid:{display:false}}}}});
 }
 const dem=document.getElementById('cDemand');
 if(dem)CH.d=new Chart(dem,{type:'bar',data:{labels:DEMAND.map(d=>d[0]),datasets:[{label:'Demand index (sample)',data:DEMAND.map(d=>d[1]),backgroundColor:DEMAND.map((d,i)=>i<2?C.brand:C.light),borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,animation:{duration:500},plugins:{legend:{display:false}},scales:{y:{grid:{color:C.grid}},x:{grid:{display:false}}}}});
 const bid=document.getElementById('cBid');
 const L=currentBidListing();
 if(bid&&L){
  const b=bidsOn(L.id);
  CH.b=new Chart(bid,{type:'bar',data:{labels:b.map(x=>x.buyer),datasets:[{label:'Bid vs asking price (₹/qtl)',data:b.map(x=>x.price-L.ask),backgroundColor:b.map(x=>x.price>=L.ask?C.brand2:C.bad),borderRadius:6}]},
   options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:{duration:500},plugins:{legend:{display:false}},scales:{x:{ticks:{callback:v=>(v>0?'+':'')+money(v)},grid:{color:C.grid}},y:{grid:{display:false}}}}});
 }
}

/* ---------- Render ---------- */
function render(){
 if(!db.session||!me()){renderAuth();return}
 if(!$('.app'))renderShell();
 const u=me(),items=NAV[u.role];
 if(!items.some(i=>i[0]===db.nav))db.nav='overview';
 document.querySelectorAll('.nav').forEach(b=>{const on=b.dataset.v===db.nav;b.classList.toggle('on',on);b.setAttribute('aria-current',on?'page':'false')});
 const key=u.role+'.'+db.nav;
 $('#view').innerHTML=(VIEWS[key]||VIEWS[u.role+'.overview'])();
 mountCharts();
}
