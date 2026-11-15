/* Views for every page in the three role workspaces. */

let TAB={};
const tab=(k,def)=>TAB[k]||def;
const TH=(cols)=>`<thead><tr>${cols.map(c=>{const [l,n]=Array.isArray(c)?c:[c,false];return `<th class="${n?'num':''}">${l}</th>`}).join('')}</tr></thead>`;
const tbl=(cols,rows,empty='')=>rows.length?`<div class="tablewrap"><table>${TH(cols)}<tbody>${rows.join('')}</tbody></table></div>`:empty;
const tdN=(x)=>`<td class="num">${x}</td>`;
const tabBar=(k,def,items)=>`<div class="tabs" role="tablist">${items.map(([v,l])=>`<button role="tab" aria-selected="${tab(k,def)===v}" data-act="tab" data-k="${k}" data-t="${v}">${l}</button>`).join('')}</div>`;
const selectOpts=(arr,val,all='')=>(all?`<option value="">${all}</option>`:'')+arr.map(x=>`<option value="${esc(x)}" ${String(val)===String(x)?'selected':''}>${esc(x)}</option>`).join('');
const field=(id,label,inner,cls='')=>`<div class="field ${cls}"><label for="${id}">${label}</label>${inner}</div>`;
const dealsForFarmer=()=>{
  const u=me(),uid=u?u.id:db.session;
  return (db.deals||[]).filter(d=>d.farmerId===uid||d.farmerId===db.session||(u&&(d.farmerId==='f1'||d.farmerId===u.id))||(!d.farmerId&&u&&u.role==='farmer'));
};
const dealsForBuyer=()=>{
  const u=me(),uid=u?u.id:db.session;
  return (db.deals||[]).filter(d=>d.buyerId===uid||d.buyerId===db.session||(u&&(d.buyerId==='b1'||d.buyerId===u.id))||(!d.buyerId&&u&&u.role==='buyer'));
};
const isOpen=d=>d.status==='pending'||d.status==='counter';
const totalOf=d=>d.price*d.qty;
const monthsSince=(iso)=>iso?new Date(iso).getMonth():null;
function trend(now,prev){const p=((now-prev)/prev)*100;return {dir:p>=0?'up':'down',text:(p>=0?'+':'')+p.toFixed(1)+'% vs last month'}}
function dealRowActions(d,viewerRole){
 const canAct=isOpen(d)&&d.by!==viewerRole;
 const profile=`<button class="btn o sm" data-act="profile" data-id="${viewerRole==='farmer'?d.buyerId:d.farmerId}">${icon('eye')}Profile</button>`;
 if(canAct)return `<div class="row end" style="gap:6px;flex-wrap:nowrap;justify-content:flex-end">${profile}<button class="btn s sm" data-act="accept" data-id="${d.id}">${icon('check')}Accept</button><button class="btn o sm" data-act="counter-open" data-id="${d.id}">${icon('refresh')}Counter</button><button class="btn d sm" data-act="ask" data-title="Reject this ${viewerRole==='farmer'?'bid':'offer'}?" data-text="The other party will be told it was not accepted." data-label="Reject" data-then="reject" data-id="${d.id}" data-danger="1">${icon('x')}Reject</button></div>`;
 if(isOpen(d))return `<div class="row end" style="gap:6px;justify-content:flex-end">${profile}<span class="mut small">Waiting for the other party</span></div>`;
 return `<div class="row end" style="gap:6px;justify-content:flex-end">${profile}</div>`;
}
const priceChartCfg=(crop,district,months)=>{
 const s=series(crop,district,months);
 return C=>({type:'line',data:{labels:s.map(p=>p.label),datasets:[{label:`${crop} – ${district} (demo, ₹/kg)`,data:s.map(p=>p.v),borderColor:C.brand,backgroundColor:'rgba(120,131,75,.12)',fill:true,tension:.3,pointRadius:2,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,usePointStyle:true}}},scales:{y:{ticks:{callback:v=>'₹'+v},grid:{color:C.grid}},x:{grid:{display:false}}}}});
};
const kpi=(l,v,ic,t,cls)=>statCard(l,v,ic,t,cls);
const DEMO_TREND=(s)=>({dir:'up',text:s});

/* ================= FARMER ================= */
const FARMER={};
FARMER.overview=()=>{
 const mine=myListings(),ds=dealsForFarmer();
 const open=ds.filter(isOpen).length,orders=ds.filter(d=>d.status==='accepted').length;
 const earned=ds.filter(d=>d.status==='accepted'&&d.paid).reduce((a,d)=>a+totalOf(d),0);
 const week=mine.filter(l=>l.listedAt>=daysAgo(7)).length;
 const crop=myCrops()[0];
 const cur=currentPrice(crop,me().district),rec=recPrice(crop,me().district);
 const s=series(crop,me().district,12),prev=s[s.length-2].v,now=s[s.length-1].v;
 return `${pageHead('Overview','Your listings, bids and sales at a glance.',`<button class="btn p" data-act="nav" data-v="upload">${icon('upload')}Upload produce</button>`)}
 <div class="grid4">
  ${kpi('Products listed',num(mine.filter(l=>l.status!=='withdrawn').length),'package',{dir:'up',text:`+${week} added this week`})}
  ${kpi('Active bids & offers',num(open),'handshake',DEMO_TREND('+3 since yesterday (demo)'))}
  ${kpi('Orders received',num(orders),'truck',DEMO_TREND('+1 this month (demo)'))}
  ${kpi('Total earnings',fmt(earned),'wallet',DEMO_TREND('+8.4% vs last month (demo)'),'brand')}
 </div>
 <!--ASIDE-->
 <div class="grid2">
  <div class="card"><div class="row"><div><h2 style="margin:0">Price snapshot · ${esc(crop)}</h2><p class="mut small">${esc(me().district)} · demonstration data</p></div><span class="chip outline">Demo data</span></div>
   <div class="kvs" style="margin:14px 0 10px">
    <div><div class="mut small">Current market</div><span class="bigval" style="font-size:20px">${fmtK(cur)}/kg</span></div>
    <div><div class="mut small">Recommended</div><span class="bigval brand" style="font-size:20px">${fmtK(rec)}/kg</span></div>
    <div><div class="mut small">Last month</div><span class="bigval" style="font-size:20px">${(((now-prev)/prev)*100>=0?'▲ ':'▼ ')+Math.abs(((now-prev)/prev)*100).toFixed(1)}%</span></div>
   </div>
   ${chartBox('cOverviewPrice',priceChartCfg(crop,me().district,12),'short','Price trend for '+crop)}
  </div>
  <div class="card"><div class="row"><h2 style="margin:0">Latest bids & offers</h2><button class="btn g sm" data-act="nav" data-v="bids">View all</button></div>
   <div style="margin-top:8px">${ds.slice(0,5).map(d=>{const b=userById(d.buyerId),l=listingOf(d.listing);return `<div class="lrow"><div style="min-width:0"><b>${esc(b.name)}</b><div class="mut small">${esc(l.name)} · ${num(d.qty)} kg · ${fmtK(d.price)}/kg</div></div>${dealChip(d)}</div>`}).join('')||emptyState('No bids yet','Buyers nearby will send bids on your listings.','','handshake')}</div>
  </div>
 </div>
 <div class="card pad0"><div class="table-head"><h2 style="margin:0">My products</h2><button class="btn o sm" data-act="nav" data-v="produce">Manage products</button></div>
  ${tbl(['Product',['Quantity',1],['Grade',0],['Asking / kg',1],['Status',0]],mine.slice(0,5).map(l=>`<tr><td><div class="cropcell">${l.img?`<span class="tile" style="width:34px;height:34px;overflow:hidden;padding:0"><img src="${l.img}" alt="" style="width:100%;height:100%;object-fit:cover"></span>`:`<span class="tile" style="width:34px;height:34px;${tintOf(l.crop)}">${esc(l.crop[0])}</span>`}<div><div>${esc(l.name)}</div><div class="mut small">${esc(l.crop)}</div></div></div></td>${tdN(num(l.qty)+' kg')}<td>${gradeChip(l.grade)}</td>${tdN(fmtK(l.ask))}<td>${statusChip(l.status)}</td></tr>`),emptyState('No products yet','Upload a photo to create your first listing.','<button class="btn p" data-act="nav" data-v="upload">Upload produce</button>','package'))}
 </div>`;
};

FARMER.produce=()=>{
 const q=SEARCH.toLowerCase(),st=tab('produce','all');
 let L=myListings().filter(l=>(st==='all'||l.status===st)&&(!q||l.name.toLowerCase().includes(q)||l.crop.toLowerCase().includes(q)));
 const counts=(s)=>myListings().filter(l=>s==='all'||l.status===s).length;
 return `${pageHead('My Products','List, price and manage your produce. Withdrawn listings are kept for your records.',`<button class="btn p" data-act="nav" data-v="upload">${icon('plus')}Add product</button>`)}
 <div class="card pad0">
  <div class="table-head">${tabBar('produce','all',[['all',`All (${counts('all')})`],['active',`Active (${counts('active')})`],['paused',`Paused (${counts('paused')})`],['sold',`Sold (${counts('sold')})`],['withdrawn',`Withdrawn (${counts('withdrawn')})`]])}</div>
  ${tbl(['Product image','Crop',['Quantity',1],['AI grade',0],['Asking / kg',1],['Recommended / kg',1],['Status',0],['Date listed',0],['Actions',0]],
   L.map(l=>`<tr><td>${l.img?`<span class="tile" style="width:44px;height:44px;overflow:hidden;padding:0"><img src="${l.img}" alt="" style="width:100%;height:100%;object-fit:cover"></span>`:`<span class="tile" style="width:44px;height:44px;${tintOf(l.crop)}">${esc(l.crop[0])}</span>`}</td>
    <td><b>${esc(l.name)}</b><div class="mut small">${esc(l.crop)} · ${esc(l.district)}</div></td>
    ${tdN(num(l.qty)+' kg')}<td>${gradeChip(l.grade,l.conf)}</td>${tdN(fmtK(l.ask))}${tdN(fmtK(recPrice(l.crop,l.district)))}
    <td>${statusChip(l.status)}</td><td>${fmtDate(l.listedAt)}</td>
    <td class="act"><div class="row" style="gap:4px;justify-content:flex-end;flex-wrap:nowrap">
     <button class="iconbtn" data-act="view-product" data-id="${l.id}" aria-label="View details" title="View details">${icon('eye')}</button>
     <button class="iconbtn" data-act="edit-product" data-id="${l.id}" aria-label="Edit" title="Edit">${icon('pencil')}</button>
     ${l.status==='active'?`<button class="iconbtn" data-act="pause" data-id="${l.id}" aria-label="Pause listing" title="Pause listing">${icon('pause')}</button>`:l.status==='paused'?`<button class="iconbtn" data-act="pause" data-id="${l.id}" aria-label="Resume listing" title="Resume listing">${icon('play')}</button>`:''}
     <button class="iconbtn" data-act="ask" data-title="Delete this product?" data-text="This removes ${esc(l.name)} from your listings and from buyer views." data-label="Delete" data-then="delete-product" data-id="${l.id}" data-danger="1" aria-label="Delete" title="Delete" style="color:var(--bad)">${icon('trash')}</button>
    </div></td></tr>`),
   emptyState('No products here','Change the filter, or upload a photo to list new produce.','<button class="btn p" data-act="nav" data-v="upload">Upload produce</button>','package'))}
  <div class="table-foot">${L.length} of ${myListings().length} products shown</div>
 </div>`;
};

FARMER.upload=()=>{
 const D=db.draft;
 return `${pageHead('Upload Produce','Add a clear photo and the lot details. Then run the quality check.')}
 <div class="grid2 even">
  <div class="card stack">
   <div class="row"><h2 style="margin:0">Produce photo</h2><span class="chip outline">JPG or PNG</span></div>
   ${D.img?`<div class="photo tall"><img src="${D.img}" alt="Selected produce photo"></div><div class="row"><span class="mut small">Photo ready for analysis.</span><button class="btn o sm" data-act="pick">${icon('upload')}Replace image</button></div>`
    :`<div class="dropzone" id="drop" data-act="pick" role="button" tabindex="0" aria-label="Choose a produce photo">
      <div class="dz-ico">${icon('image')}</div><b>Drag an image here</b><span class="mut">or click to choose from your camera or gallery</span>
      <span class="btn o sm" style="margin-top:10px">${icon('upload')}Upload image</span></div>`}
   <input type="file" id="up" accept="image/*" data-u="1" hidden>
   <div><div class="mut small" style="margin-bottom:6px">No photo to hand? Try a demonstration sample:</div>
    <div class="sample-row"><button class="btn o sm" data-act="sample" data-s="uniform">Uniform red lot</button><button class="btn o sm" data-act="sample" data-s="mixed">Mixed ripeness</button><button class="btn o sm" data-act="sample" data-s="damaged">Damaged lot</button></div>
    <p class="hint">Samples are generated illustrations for demonstration, not real produce.</p></div>
  </div>
  <div class="card stack">
   <h2 style="margin:0">Lot details</h2>
   <div class="form" style="grid-template-columns:minmax(0,1fr) minmax(0,1fr)">
    ${field('d-name','Product name',`<input id="d-name" data-dr="name" value="${esc(D.name)}" placeholder="e.g. Hybrid Tomato, grade 1">`,'span2')}
    ${field('d-crop','Crop',`<select id="d-crop" data-dr="crop">${selectOpts(CROPS,D.crop)}</select>`)}
    ${field('d-qty','Quantity',`<input id="d-qty" type="number" min="1" inputmode="numeric" data-dr="qty" value="${esc(D.qty)}" placeholder="e.g. 500">`)}
    ${field('d-unit','Unit',`<select id="d-unit" data-dr="unit">${selectOpts(['kg','quintal'],D.unit)}</select>`)}
    ${field('d-harv','Harvest date',`<input id="d-harv" type="date" data-dr="harvest" value="${esc(D.harvest)}" max="${daysAgo(0)}">`)}
    ${field('d-loc','Farm location (district)',`<select id="d-loc" data-dr="district">${selectOpts(KA_DISTRICTS,D.district)}</select>`,'span2')}
   </div>
   <div class="note info small">Quantity is stored in kilograms. One quintal is 100 kg.</div>
   <div class="row" style="gap:10px;margin-top:4px">
    <button class="btn o" data-act="pick">${icon('upload')}Upload image</button>
    <button class="btn p" data-act="analyze" ${D.img?'':'disabled'}>${icon('scan')}Analyze quality</button>
   </div>
   ${D.img?'':'<p class="hint">Add a photo to enable quality analysis.</p>'}
  </div>
 </div>`;
};

FARMER.quality=()=>{
 const a=db.assess.find(x=>x.id===db.lastAssess)||db.assess[0];
 const hist=db.assess.slice().reverse();
 if(!a)return `${pageHead('AI Quality Assessment','Grade a lot from a photo.')}<div class="card">${emptyState('No assessment yet','Upload a produce photo and run the quality check to see its grade here.','<button class="btn p" data-act="nav" data-v="upload">Upload produce</button>','scan')}</div>`;
 const cat={A:'High quality',B:'Medium quality',C:'Low quality'}[a.grade];
 const surface=a.defects<=4?'Low':a.defects<=10?'Moderate':'High';
 const colour=a.uniformity>=75?'Consistent':a.uniformity>=55?'Some variation':'Uneven';
 return `${pageHead('AI Quality Assessment','Model prediction for this lot. Read the notes before listing.',`<button class="btn o" data-act="analyze-again">${icon('refresh')}Analyze again</button><button class="btn o" data-act="save-assess" ${a.saved?'disabled':''}>${icon('check')}${a.saved?'Assessment saved':'Save assessment'}</button><button class="btn p" data-act="list-open" data-id="${a.id}">${icon('package')}List product</button>`)}
 <div class="grid2 even">
  <div class="card stack">
   <div class="row"><h2 style="margin:0">Analysed photo</h2><span class="chip outline">${esc(a.t)}</span></div>
   <div class="photo tall">${a.img?`<img src="${a.img}" alt="Analysed produce photo">`:`<span class="tile full" style="${tintOf(a.crop)}">${esc(a.crop[0])}</span>`}</div>
   <p class="mut small">Colour uniformity and defect levels were calculated from the pixels in this photo. The grade uses a simple demonstration rule, not a trained classifier.</p>
  </div>
  <div class="card stack">
   <div class="row"><div><div class="mut small">Predicted quality grade</div><span class="bigval ${a.grade==='A'?'ok':a.grade==='B'?'':'bad'}" style="font-size:40px">Grade ${a.grade}</span></div><span class="chip ${a.grade==='A'?'ok':a.grade==='B'?'info':'warn'}">${cat}</span></div>
   <div><div class="row"><span class="small">Model confidence</span><b>${a.conf}%</b></div><div class="bar"><i style="width:${a.conf}%"></i></div></div>
   <div><h3>Visual assessment</h3>
    <div class="lrow"><span>Colour consistency</span><b>${colour} (${a.uniformity}/100)</b></div>
    <div class="lrow"><span>Visible defects</span><b>${a.defects}% of photo</b></div>
    <div class="lrow"><span>Surface damage</span><b>${surface}</b></div>
    <div class="lrow"><span>Ripeness indicator</span><b>${esc(a.ripeness)}</b></div>
   </div>
   <div class="note"><b>Model prediction, not certification.</b> This result comes from a demonstration classifier. It is not an official agricultural or food-safety certificate, and it should be confirmed by inspection before a sale.</div>
  </div>
 </div>
 <div class="card pad0"><div class="table-head"><h2 style="margin:0">Assessment history</h2></div>
  ${tbl(['Date',['Crop',0],['Grade',0],['Confidence',1],['Saved',0]],hist.map(x=>`<tr><td>${esc(x.t)}</td><td>${esc(x.crop)}</td><td>${gradeChip(x.grade)}</td>${tdN(x.conf+'%')}<td>${x.saved?'<span class="chip ok">Saved</span>':'<span class="chip outline">Not saved</span>'}</td></tr>`),emptyState('No assessments yet','Run an analysis to build your history.'))}
 </div>`;
};

FARMER.prices=()=>{
 const crop=PR.crop,dist=PR.district,months=PR.range,mkt=PR.mkt||'Kolar';

 // Trigger live ML fetch in background if ML client is available
 const cacheKey = `${crop}-${mkt}-${dist}`;
 if(typeof fetchMLIntelligence === 'function' && (!window.ML_CACHE || (!window.ML_CACHE.loading && window.ML_CACHE.lastQuery !== cacheKey))){
   fetchMLIntelligence(crop, mkt, dist).then(()=>{ if(typeof render==='function') render(); });
 }

 const cur=currentPrice(crop,dist);
 const hasML = window.ML_CACHE && window.ML_CACHE.priceData && window.ML_CACHE.lastQuery === cacheKey;

 // In ML model, price is in INR/Quintal (1 Quintal = 100 kg)
 const mlPriceKg = hasML ? (window.ML_CACHE.priceData.predicted_modal_price / 100) : recPrice(crop,dist);
 const mlLowKg = hasML ? (window.ML_CACHE.priceData.prediction_interval.lower_bound / 100) : (mlPriceKg * 0.9);
 const mlHighKg = hasML ? (window.ML_CACHE.priceData.prediction_interval.upper_bound / 100) : (mlPriceKg * 1.1);

 const dem = hasML && window.ML_CACHE.demandData 
   ? { label: window.ML_CACHE.demandData.demand_trend, v: window.ML_CACHE.demandData.confidence_percentage, note: window.ML_CACHE.demandData.economic_interpretation }
   : DEMAND_IDX[crop] || { label: 'Medium', v: 60 };

 const mlExplain = hasML && window.ML_CACHE.explainData 
   ? window.ML_CACHE.explainData.natural_language_explanation 
   : `Calculated as 1.04 × the average of the last three months (demonstration rule). Current market: ${fmtK(cur)}/kg.`;

 const s=series(crop,dist,months);
 const last=s[s.length-1].v,prev=s[s.length-2].v,chg=((last-prev)/prev)*100;
 const regions=Object.keys(PLACES).filter(d=>PLACES[d][0]===PLACES[dist][0]).slice(0,7);
 const regCfg=C=>({type:'bar',data:{labels:regions,datasets:[{label:'Current price (₹/kg)',data:regions.map(r=>currentPrice(crop,r)),backgroundColor:regions.map(r=>r===dist?C.brand:C.brand2),borderRadius:6}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{callback:v=>'₹'+v},grid:{color:C.grid}},y:{grid:{display:false}}}}});
 const fluct=s.slice(1).map((p,i)=>({label:p.label,v:Math.round(((p.v-s[i].v)/s[i].v)*1000)/10}));
 const flCfg=C=>({type:'bar',data:{labels:fluct.map(p=>p.label),datasets:[{label:'Month-on-month change (%)',data:fluct.map(p=>p.v),backgroundColor:fluct.map(p=>p.v>=0?C.ok:C.bad),borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:v=>v+'%'},grid:{color:C.grid}},x:{grid:{display:false}}}}});
 const seasonal=series(crop,dist,12);

 const modelBadge = hasML 
   ? `<span class="chip ok">Live ML Engine · ${esc(window.ML_CACHE.priceData.model_type || 'GradientBoosting')}</span>`
   : `<span class="chip outline">Connecting to ML Microservice...</span>`;

 return `${pageHead('Market Price Intelligence','Mandi price history, ML price predictions and demand forecasting.',modelBadge)}
 <div class="card"><div class="toolbar">
  ${field('p-crop','Crop',`<select id="p-crop" data-p="crop">${selectOpts(CROPS,crop)}</select>`)}
  ${field('p-state','State',`<select id="p-state" data-p="state">${selectOpts(STATES.filter(x=>['Karnataka','Tamil Nadu'].includes(x)),PLACES[dist][0])}</select>`)}
  ${field('p-dist','District',`<select id="p-dist" data-p="district">${selectOpts(Object.keys(PLACES).filter(d=>PLACES[d][0]===PLACES[dist][0]),dist)}</select>`)}
  ${field('p-mkt','Market',`<select id="p-mkt" data-p="mkt">${selectOpts(MARKETS,PR.mkt)}</select>`)}
  ${field('p-range','Date range',`<select id="p-range" data-p="range">${[[3,'Last 3 months'],[6,'Last 6 months'],[12,'Last 12 months']].map(([v,l])=>`<option value="${v}" ${months==v?'selected':''}>${l}</option>`).join('')}</select>`)}
 </div></div>
 ${statRow([
  ['Current market price',fmtK(cur)+'/kg',`${esc(PR.mkt)}`],
  ['AI Recommended price','₹'+mlPriceKg.toFixed(2)+'/kg',hasML ? 'GradientBoosting (MAE ₹88/qtl)' : 'Demonstration rule','brand'],
  ['Market Demand Index (Proxy)',dem.label,hasML ? `Model confidence ${dem.v}` : `Absorption proxy ${dem.v}`,dem.label==='Increasing'||dem.label==='High'?'ok':'warn'],
  ['80% Prediction Band',hasML ? `₹${mlLowKg.toFixed(1)} – ₹${mlHighKg.toFixed(1)}/kg` : '±10% range','Model uncertainty band',hasML ? 'ok' : '']
 ])}
 <div class="grid2">
  <div class="card"><div class="row"><h2 style="margin:0">Historical price · ${esc(crop)}</h2><span class="chip outline">Mandi Series</span></div>${chartBox('cPriceHist',priceChartCfg(crop,dist,months),'','Historical price line chart')}</div>
  <div class="card stack" style="gap:12px"><h2 style="margin:0">Explainable AI Recommendation</h2>
   <p class="sub">AI Suggested selling price: <b style="color:var(--brand)">₹${mlPriceKg.toFixed(2)}/kg</b> (₹${(mlPriceKg*100).toFixed(0)}/quintal)</p>
   <p class="small">${esc(mlExplain)}</p>
   <div class="note ${dem.label==='Increasing'||dem.label==='High'?'ok':'info'} small"><b>Market Demand Index (Proxy):</b> ${dem.label} for ${esc(crop)} in ${esc(dist)}. ${dem.note ? esc(dem.note) : ''}</div>
   <h3 style="margin-top:6px">Seasonal pattern (12 months)</h3>
   <p class="mut small">Lowest: ${fmtK(Math.min(...seasonal.map(p=>p.v)))}/kg · Highest: ${fmtK(Math.max(...seasonal.map(p=>p.v)))}/kg</p>
  </div>
 </div>
 <div class="grid2 even">
  <div class="card"><h2>Regional price comparison</h2><p class="mut small" style="margin:-6px 0 8px">Districts in ${esc(PLACES[dist][0])}</p>${chartBox('cRegion',regCfg,'tall','Regional price comparison bar chart')}</div>
  <div class="card"><h2>Price fluctuation</h2><p class="mut small" style="margin:-6px 0 8px">Month-on-month change</p>${chartBox('cFluct',flCfg,'tall','Price fluctuation bar chart')}</div>
 </div>`;
};

FARMER.buyers=()=>{
 const v=me(),q=SEARCH.toLowerCase();
 const tabs=tab('buyers','all');
 const typeOf={retailers:'Retailer',wholesalers:'Wholesaler',processors:'Food Processor'};
 let L=db.users.filter(u=>u.role==='buyer'&&u.status==='active'&&(!q||u.name.toLowerCase().includes(q)||u.interests.join(' ').toLowerCase().includes(q)));
 if(tabs==='nearby')L=L.filter(b=>{const d=distanceBetween(v,b);return d!=null&&d<=200});
 if(typeOf[tabs])L=L.filter(b=>b.business===typeOf[tabs]);
 const crops=myCrops();
 L=L.map(b=>({b,d:distanceBetween(v,b),m:b.interests.filter(i=>crops.includes(i)).length}));
 if(F.sort==='interest')L.sort((a,b)=>b.m-a.m);else L.sort((a,b)=>(a.d==null)-(b.d==null)||(a.d||0)-(b.d||0));
 return `${pageHead('Buyer Marketplace','Verified retailers, wholesalers and food processors. Send an offer, or view a profile first.')}
 <div class="card"><div class="toolbar">
  ${tabBar('buyers','all',[['all','All'],['nearby','Nearby'],['retailers','Retailers'],['wholesalers','Wholesalers'],['processors','Food processors']])}
  <div class="field" style="margin-left:auto;min-width:200px"><label for="bsort">Sort</label><select id="bsort" data-f="sort"><option value="distance" ${F.sort==='distance'?'selected':''}>Distance</option><option value="interest" ${F.sort==='interest'?'selected':''}>Product interest</option></select></div>
 </div></div>
 <p class="mut small" style="margin:6px 2px">${L.length} buyer${L.length===1?'':'s'} · distances are approximate, measured between district centres</p>
 <div class="grid3">${L.map(x=>buyerCard(x.b,v,false)).join('')||`<div class="card" style="grid-column:1/-1">${emptyState('No buyers match','Try All, or clear the search.','','users')}</div>`}</div>`;
};

FARMER.bids=()=>{
 const st=tab('bids','all');
 let ds=dealsForFarmer();
 const counts={all:ds.length,needs:ds.filter(d=>isOpen(d)&&d.by!=='farmer').length,sent:ds.filter(d=>isOpen(d)&&d.by==='farmer').length,accepted:ds.filter(d=>d.status==='accepted').length,rejected:ds.filter(d=>d.status==='rejected').length};
 if(st==='needs')ds=ds.filter(d=>isOpen(d)&&d.by!=='farmer');
 if(st==='sent')ds=ds.filter(d=>isOpen(d)&&d.by==='farmer');
 if(st==='accepted')ds=ds.filter(d=>d.status==='accepted');
 if(st==='rejected')ds=ds.filter(d=>d.status==='rejected');
 return `${pageHead('Bids & Offers','Respond to bids on your produce, or review offers you have sent. Counter offers appear here too.')}
 <div class="card pad0"><div class="table-head">${tabBar('bids','all',[['all',`All (${counts.all})`],['needs',`Needs response (${counts.needs})`],['sent',`Sent by you (${counts.sent})`],['accepted',`Accepted (${counts.accepted})`],['rejected',`Rejected (${counts.rejected})`]])}</div>
 ${tbl(['Buyer',['Product',0],['Qty (kg)',1],['Price / kg',1],['Total',1],['Date',0],['Status',0],['Actions',0]],ds.map(d=>{const b=userById(d.buyerId),l=listingOf(d.listing);return `<tr>
  <td><b>${esc(b.name)}</b><div>${locOf(b)}</div></td>
  <td>${esc(l.name)}<div class="mut small">${d.initiator==='farmer'?'You sent an offer':'Bid from buyer'}</div></td>
  ${tdN(num(d.qty))}${tdN(fmtK(d.price))}${tdN('<b>'+fmt(totalOf(d))+'</b>')}
  <td>${esc(d.t)}</td><td>${dealChip(d)}${d.rounds>1?`<div class="mut small">Round ${d.rounds}</div>`:''}</td>
  <td class="act">${dealRowActions(d,'farmer')}</td></tr>`}),emptyState('Nothing here yet','Bids from buyers appear here. You can also send offers from the Buyer Marketplace.','<button class="btn p" data-act="nav" data-v="buyers">Open buyer marketplace</button>','handshake'))}
 </div>`;
};

FARMER.orders=()=>{
 const ds=dealsForFarmer().filter(d=>d.status==='accepted');
 const active=ds.filter(d=>d.stage!=='delivered'),done=ds.filter(d=>d.stage==='delivered');
 const unpaid=ds.filter(d=>!d.paid).reduce((a,d)=>a+totalOf(d),0);
 return `${pageHead('Orders','Track dispatch and delivery for accepted bids.')}
 ${statRow([['Active orders',active.length,'Awaiting dispatch or delivery'],['Completed',done.length,'Delivered orders'],['Pending payments',fmt(unpaid),'Not yet paid'],['Order value',fmt(ds.reduce((a,d)=>a+totalOf(d),0)),'All accepted bids']])}
 <div class="card pad0"><div class="table-head"><h2 style="margin:0">Order tracking</h2></div>
 ${tbl(['Order',['Buyer',0],['Product',0],['Value',1],['Payment',0],['Progress',0],['Action',0]],ds.map(d=>{const b=userById(d.buyerId),l=listingOf(d.listing);return `<tr>
  <td><b>#${d.id.toUpperCase()}</b><div class="mut small">${esc(d.t)}</div></td>
  <td>${esc(b.name)}<div>${locOf(b)}</div></td>
  <td>${esc(l.name)}<div class="mut small">${num(d.qty)} kg @ ${fmtK(d.price)}/kg</div></td>
  ${tdN('<b>'+fmt(totalOf(d))+'</b>')}
  <td>${d.paid?'<span class="chip ok">Paid</span>':'<span class="chip warn">Pending</span>'}</td>
  <td style="min-width:260px">${stageTrack(d.stage)}</td>
  <td class="act">${d.stage==='confirmed'?`<button class="btn s sm" data-act="dispatch" data-id="${d.id}">${icon('truck')}Mark dispatched</button>`:d.stage==='dispatched'?'<span class="mut small">Waiting for buyer to confirm</span>':'<span class="chip ok">Completed</span>'}${d.paid?'':`<div style="margin-top:6px"><button class="btn o sm" data-act="pay" data-id="${d.id}">${icon('wallet')}Mark payment received</button></div>`}</td></tr>`}),emptyState('No orders yet','Accept a bid to create an order.','','truck'))}
 </div>`;
};

FARMER.earnings=()=>{
 const ds=dealsForFarmer().filter(d=>d.status==='accepted');
 const paid=ds.filter(d=>d.paid),pend=ds.filter(d=>!d.paid);
 const byCrop={};ds.forEach(d=>{const c=listingOf(d.listing).crop;byCrop[c]=(byCrop[c]||0)+totalOf(d)});
 const cfg=C=>({type:'bar',data:{labels:Object.keys(byCrop),datasets:[{label:'Order value (₹)',data:Object.values(byCrop),backgroundColor:C.brand,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{ticks:{callback:v=>'₹'+num(v)},grid:{color:C.grid}},x:{grid:{display:false}}}}});
 const avg=ds.length?ds.reduce((a,d)=>a+d.price,0)/ds.length:0;
 return `${pageHead('Earnings','Payments received, pending amounts and transaction history.')}
 ${statRow([['Total earnings (paid)',fmt(paid.reduce((a,d)=>a+totalOf(d),0)),'Received',"brand"],['Pending payments',fmt(pend.reduce((a,d)=>a+totalOf(d),0)),'Awaiting buyer payment','bad'],['Completed orders',num(ds.filter(d=>d.stage==='delivered').length),'Delivered'],['Average price / kg',fmtK(avg),'Across accepted bids']])}
 <div class="grid2">
  <div class="card"><h2>Order value by crop</h2>${chartBox('cEarn',cfg,'','Order value by crop bar chart')}</div>
  <div class="card"><h2>Pending payments</h2>${pend.map(d=>{const b=userById(d.buyerId);return `<div class="lrow"><div><b>${esc(b.name)}</b><div class="mut small">${esc(listingOf(d.listing).name)}</div></div><b>${fmt(totalOf(d))}</b></div>`}).join('')||'<p class="mut">No pending payments.</p>'}</div>
 </div>
 <div class="card pad0"><div class="table-head"><h2 style="margin:0">Transaction history</h2></div>
 ${tbl(['Date',['Buyer',0],['Product',0],['Quantity',1],['Amount',1],['Payment',0]],ds.map(d=>{const b=userById(d.buyerId),l=listingOf(d.listing);return `<tr><td>${esc(d.t)}</td><td>${esc(b.name)}</td><td>${esc(l.name)}</td>${tdN(num(d.qty)+' kg')}${tdN('<b>'+fmt(totalOf(d))+'</b>')}<td>${d.paid?'<span class="chip ok">Paid</span>':'<span class="chip warn">Pending</span>'}</td></tr>`}),emptyState('No transactions yet','Accepted bids and payments will show here.','','receipt'))}
 </div>`;
};

function profileForm(u,role){
 const farmer=role==='farmer';
 return `<form data-form="profile" class="card stack" style="gap:14px">
  <div class="form">
   ${farmer?`<div class="field"><label for="pf-name">Full name</label><input id="pf-name" name="name" value="${esc(u.name)}" required></div>
   <div class="field"><label for="pf-farm">Farm name</label><input id="pf-farm" name="farm" value="${esc(u.farm)}" required></div>
   <div class="field"><label for="pf-vil">Village</label><input id="pf-vil" name="village" value="${esc(u.village)}" required></div>
   <div class="field"><label for="pf-acr">Land (acres)</label><input id="pf-acr" name="acres" type="number" min="0" step="any" value="${u.acres}"></div>`
   :`<div class="field"><label for="pf-name">Company name</label><input id="pf-name" name="name" value="${esc(u.name)}" required></div>
   <div class="field"><label for="pf-con">Contact person</label><input id="pf-con" name="contact" value="${esc(u.contact)}" required></div>
   <div class="field"><label for="pf-biz">Business type</label><select id="pf-biz" name="business">${selectOpts(['Retailer','Wholesaler','Food Processor'],u.business)}</select></div>`}
   <div class="field"><label for="pf-phone">Mobile number</label><input id="pf-phone" name="phone" inputmode="numeric" maxlength="10" value="${esc(u.phone)}"></div>
   <div class="field"><label for="pf-state">State</label><select id="pf-state" name="state">${selectOpts(STATES,u.state)}</select></div>
   <div class="field"><label for="pf-dist">District</label><input id="pf-dist" name="district" list="kadist" value="${esc(u.district)}" required></div>
   <div class="field"><label for="pf-city">City or town</label><input id="pf-city" name="city" value="${esc(u.city)}" required></div>
  </div>
  <div class="row"><span class="mut small">Email: ${esc(u.email)} (contact support to change)</span><button class="btn p" type="submit">${icon('check')}Save changes</button></div>
 </form>`;
}
FARMER.profile=()=>{const u=me();return `${pageHead('Profile','This is how buyers see your farm. Exact addresses are never shown.')}
 <div class="grid2"><div class="stack">${profileForm(u,'farmer')}</div>
 <div class="card stack"><div class="row" style="justify-content:flex-start;gap:12px">${avatar(u,'lg')}<div><b style="font-size:16px">${esc(u.farm)}</b><div class="mut">${esc(u.name)}</div></div></div>
  <div>${verifiedOf(u)}</div>
  <div class="kv2"><div><span>Location shown</span><b>${esc(u.district)}, ${esc(u.state)}</b></div><div><span>Member since</span><b>${fmtDate(u.joined)}</b></div><div><span>Phone</span><b>${esc(u.phone.slice(0,5))} •••••</b></div><div><span>Land</span><b>${u.acres} acres</b></div></div>
  <p class="hint">Verification is completed by a platform administrator. Pending accounts can list produce, but buyers see a pending badge.</p>
 </div></div>`};

function settingsBlock(u){
 u = u || me() || {};
 const prefs = (u && u.prefs) || { notifyBids: true, notifyPrices: false };
 if (!u.prefs) u.prefs = prefs;
 return `<div class="grid2 even">
  <div class="card"><h2>Appearance</h2><p class="mut small" style="margin:-6px 0 10px">Choose light, dark or the system setting. Your choice is saved in this browser.</p>
   <div class="seg" role="group" aria-label="Theme" style="display:inline-flex">
    <button data-act="theme" data-t="light" aria-pressed="false">${icon('sun')}Light</button><button data-act="theme" data-t="dark" aria-pressed="false">${icon('moon')}Dark</button><button data-act="theme" data-t="system" aria-pressed="false">${icon('monitor')}System</button></div></div>
  <div class="card"><h2>Notifications</h2>
   <div class="switch"><span>Bid and offer updates</span><input type="checkbox" data-set="notifyBids" ${prefs.notifyBids?'checked':''} aria-label="Bid and offer updates"></div>
   <div class="switch"><span>Price alerts for my crops</span><input type="checkbox" data-set="notifyPrices" ${prefs.notifyPrices?'checked':''} aria-label="Price alerts"></div>
  </div>
 </div>
 <div class="grid2 even" style="margin-top:14px">
  <div class="card"><h2>Location sharing</h2>
   <div class="switch" style="border:0"><span>Share my district so buyers see distances<br><span class="mut small">Only approximate distances between district centres are shown.</span></span><input type="checkbox" data-set="locShare" ${u.locShare!==false?'checked':''} aria-label="Share location"></div>
   ${u.locShare===false?'<div class="note info small" style="margin-top:8px">Location sharing is off. Distances are hidden from buyers and from your Nearby Buyers list.</div>':''}
  </div>
  <div class="card"><h2>Change password</h2>
   <form data-form="password" class="stack" style="gap:12px">
    <div class="field"><label for="pw0">Current password</label><input id="pw0" name="current" type="password" required autocomplete="current-password"></div>
    <div class="field"><label for="pw1">New password</label><input id="pw1" name="next" type="password" required minlength="6" autocomplete="new-password"></div>
    <div class="row end"><button class="btn p" type="submit">Update password</button></div>
   </form>
  </div>
 </div>`;
}
FARMER.settings=()=>`${pageHead('Settings','Preferences for this account.')}${settingsBlock(me())}`;

/* ================= BUYER ================= */
const BUYER={};
BUYER.overview=()=>{
 const ds=dealsForBuyer(),acc=ds.filter(d=>d.status==='accepted');
 const spend=acc.reduce((a,d)=>a+totalOf(d),0);
 const active=acc.filter(d=>d.stage!=='delivered').length;
 const open=ds.filter(isOpen);
 const recs=db.listings.filter(l=>l.status==='active'&&l.grade==='A').slice(0,3);
 const viewed=db.viewed.map(id=>listingOf(id)).filter(Boolean).slice(0,4);
 return `${pageHead(`Welcome, ${esc(me().contact||me().name)}`,'Find verified produce, compare bids and track your orders.',`<button class="btn p" data-act="nav" data-v="browse">${icon('basket')}Browse produce</button>`)}
 <div class="grid4">
  ${kpi('Active orders',num(active),'truck',DEMO_TREND('Awaiting delivery'))}
  ${kpi('Total purchases',fmt(spend),'receipt',DEMO_TREND('Accepted bids only'),'brand')}
  ${kpi('Pending bids',num(open.length),'handshake',DEMO_TREND('Awaiting response'))}
  ${kpi('Saved farmers',num(db.savedFarmers.length),'users',DEMO_TREND('Saved from Search Farmers'))}
 </div>
 <div class="grid2">
  <div class="card"><div class="row"><h2 style="margin:0">Market price · Tomato</h2><span class="chip outline">Demo</span></div>${chartBox('cBuyerPrice',priceChartCfg('Tomato',me().district,12),'short','Tomato price trend')}</div>
  <div class="card"><h2>Active bids</h2>${open.slice(0,4).map(d=>{const l=listingOf(d.listing);return `<div class="lrow"><div><b>${esc(l.name)}</b><div class="mut small">${num(d.qty)} kg @ ${fmtK(d.price)}/kg</div></div>${dealChip(d)}</div>`}).join('')||'<p class="mut">No open bids.</p>'}<button class="btn o w" style="margin-top:12px" data-act="nav" data-v="bids">Manage bids</button></div>
 </div>
 <div class="grid2 even">
  <div class="card"><h2>Recommended produce</h2><p class="mut small" style="margin:-6px 0 8px">Grade A lots from verified farms</p>
   ${recs.map(l=>`<div class="lrow"><div class="cropcell"><span class="tile" style="width:44px;height:44px;${tintOf(l.crop)}">${esc(l.crop[0])}</span><div><b>${esc(l.name)}</b><div class="mut small">${esc(l.district)} · ${num(l.qty)} kg</div></div></div><button class="btn o sm" data-act="product" data-id="${l.id}">View</button></div>`).join('')}
  </div>
  <div class="card"><h2>Recently viewed</h2>${viewed.map(l=>`<div class="lrow"><span><b>${esc(l.name)}</b><div class="mut small">${esc(l.district)}</div></span><button class="btn g sm" data-act="product" data-id="${l.id}">Open</button></div>`).join('')||'<p class="mut">Products you open will appear here.</p>'}</div>
 </div>
 <div class="card pad0"><div class="table-head"><h2 style="margin:0">Recent purchases</h2><button class="btn g sm" data-act="nav" data-v="purchases">All purchases</button></div>
  ${tbl(['Product',['Seller',0],['Quantity',1],['Total',1],['Status',0]],acc.slice(0,4).map(d=>{const l=listingOf(d.listing),f=userById(l.farmer);return `<tr><td>${esc(l.name)}</td><td>${esc(f.farm)}</td>${tdN(num(d.qty)+' kg')}${tdN(fmt(totalOf(d)))}<td>${stageChipOf(d)}</td></tr>`}),emptyState('No purchases yet','Accepted bids will appear here.','','receipt'))}
 </div>`;
};
function stageChipOf(d){return d.stage==='delivered'?'<span class="chip ok">Delivered</span>':d.stage==='dispatched'?'<span class="chip info">In transit</span>':'<span class="chip warn">Confirmed</span>'}

BUYER.browse=()=>{
 const q=(SEARCH||F.q||'').toLowerCase(),v=me();
 let L=db.listings.filter(l=>l.status==='active'&&(!q||l.name.toLowerCase().includes(q)||l.crop.toLowerCase().includes(q)||(userById(l.farmer).farm||'').toLowerCase().includes(q)));
 if(F.crop)L=L.filter(l=>l.crop===F.crop);
 if(F.grade)L=L.filter(l=>l.grade===F.grade);
 if(F.district)L=L.filter(l=>l.district===F.district);
 if(F.minP!=='')L=L.filter(l=>l.ask>=+F.minP);
 if(F.maxP!=='')L=L.filter(l=>l.ask<=+F.maxP);
 if(F.minQ!=='')L=L.filter(l=>l.qty>=+F.minQ);
 if(F.maxKm&&F.maxKm!=='any'){L=L.filter(l=>{const d=distanceBetween(v,userById(l.farmer));return d!=null&&d<=+F.maxKm})}
 if(F.sort==='price-asc')L.sort((a,b)=>a.ask-b.ask);
 else if(F.sort==='price-desc')L.sort((a,b)=>b.ask-a.ask);
 else L.sort((a,b)=>{const da=distanceBetween(v,userById(a.farmer)),dbb=distanceBetween(v,userById(b.farmer));return (da==null)-(dbb==null)||(da||0)-(dbb||0)});
 const sel=(id,label,opts,val)=>field(id,label,`<select id="${id}" data-f="${id.replace('f-','')}">${opts.map(([x,l])=>`<option value="${x}" ${String(val)===String(x)?'selected':''}>${l}</option>`).join('')}</select>`);
 return `${pageHead('Browse Products','Verified produce from farms across Karnataka. Distances are approximate.')}
 <div class="card"><div class="toolbar">
  ${sel('f-crop','Crop',[['','All crops'],...CROPS.map(c=>[c,c])],F.crop)}
  ${sel('f-grade','Quality grade',[['','All grades'],['A','Grade A'],['B','Grade B'],['C','Grade C']],F.grade)}
  ${sel('f-district','Location',[['','All districts'],...['Kolar','Chikkaballapur','Tumakuru','Mandya','Mysuru','Hassan','Ramanagara','Bengaluru Urban'].map(d=>[d,d])],F.district)}
  ${sel('f-maxKm','Distance',[['any','Any distance'],['50','Within 50 km'],['100','Within 100 km'],['200','Within 200 km']],F.maxKm||'any')}
  ${sel('f-sort','Sort by',[['distance','Distance'],['price-asc','Price: low to high'],['price-desc','Price: high to low']],F.sort)}
 </div>
 <div class="toolbar" style="margin-top:10px">
  ${field('f-minP','Min price / kg (₹)',`<input id="f-minP" data-f="minP" type="number" min="0" value="${F.minP}" inputmode="numeric">`)}
  ${field('f-maxP','Max price / kg (₹)',`<input id="f-maxP" data-f="maxP" type="number" min="0" value="${F.maxP}" inputmode="numeric">`)}
  ${field('f-minQ','Min quantity (kg)',`<input id="f-minQ" data-f="minQ" type="number" min="0" value="${F.minQ}" inputmode="numeric">`)}
  <button class="btn o" data-act="clear-filters" style="align-self:flex-end">Clear filters</button>
 </div></div>
 <p class="mut small" style="margin:6px 2px">${L.length} listing${L.length===1?'':'s'} found</p>
 <div class="grid3">${L.map(l=>productCard(l,v)).join('')||`<div class="card" style="grid-column:1/-1">${emptyState('No produce matches these filters','Try a wider distance or a different grade.','<button class="btn o" data-act="clear-filters">Clear filters</button>','basket')}</div>`}</div>`;
};

BUYER.farmers=()=>{
 const v=me(),q=SEARCH.toLowerCase();
 let L=db.users.filter(u=>u.role==='farmer'&&u.status==='active'&&(!q||u.farm.toLowerCase().includes(q)||u.name.toLowerCase().includes(q)||u.district.toLowerCase().includes(q)));
 if(F.verifiedOnly)L=L.filter(f=>f.verified);
 if(F.district)L=L.filter(f=>f.district===F.district);
 L.sort((a,b)=>(distanceBetween(v,a)==null)-(distanceBetween(v,b)==null)||(distanceBetween(v,a)||0)-(distanceBetween(v,b)||0));
 return `${pageHead('Search Farmers','Find farms by name, district or crop. Save farms to return to them later.')}
 <div class="card"><div class="toolbar">
  ${field('ff-d','District',`<select id="ff-d" data-f="district">${selectOpts(KA_DISTRICTS.filter(d=>db.users.some(f=>f.district===d)),F.district,'All districts')}</select>`)}
  <label class="check" style="margin-bottom:8px"><input type="checkbox" data-f="verifiedOnly" ${F.verifiedOnly?'checked':''}> Verified farms only</label>
 </div></div>
 <p class="mut small" style="margin:6px 2px">${L.length} farm${L.length===1?'':'s'}</p>
 <div class="grid3">${L.map(f=>farmerCard(f,v)).join('')||`<div class="card" style="grid-column:1/-1">${emptyState('No farms match','Clear the district or search text.','','sprout')}</div>`}</div>`;
};

BUYER.verified=()=>{
 const v=me();
 const L=db.listings.filter(l=>l.status==='active'&&userById(l.farmer).verified).sort((a,b)=>b.conf-a.conf);
 return `${pageHead('AI Verified Produce','Lots from verified farms, with the quality grade and confidence from the photo check.')}
 <div class="grid2"><div class="card stack" style="gap:10px"><h2 style="margin:0">How to read a grade</h2>
  <div class="lrow"><span>${gradeChip('A')}</span><span class="mut small">High quality. Consistent colour and few visible defects.</span></div>
  <div class="lrow"><span>${gradeChip('B')}</span><span class="mut small">Medium quality. Some variation; suitable for processing or bulk.</span></div>
  <div class="lrow"><span>${gradeChip('C')}</span><span class="mut small">Low quality. Check the photo and request a manual inspection before bidding.</span></div>
  <div class="note info small" style="margin-top:6px"><b>Model predictions, not certification.</b> Grades come from a demonstration classifier. Confirm on delivery.</div>
 </div>
 <div class="card"><h2>Summary</h2><div class="kvs"><div><div class="mut small">Verified lots</div><span class="bigval">${L.length}</span></div><div><div class="mut small">Grade A</div><span class="bigval ok">${L.filter(l=>l.grade==='A').length}</span></div><div><div class="mut small">Average confidence</div><span class="bigval">${L.length?Math.round(L.reduce((a,l)=>a+l.conf,0)/L.length):0}%</span></div></div></div></div>
 <div class="grid3" style="margin-top:4px">${L.map(l=>productCard(l,v)).join('')||`<div class="card" style="grid-column:1/-1">${emptyState('No verified lots right now','Check back soon.','','badge')}</div>`}</div>`;
};

BUYER.bids=()=>{
 const st=tab('bidsb','all');
 let ds=dealsForBuyer();
 const v=me();
 if(st==='open')ds=ds.filter(isOpen);
 if(st==='accepted')ds=ds.filter(d=>d.status==='accepted');
 if(st==='rejected')ds=ds.filter(d=>d.status==='rejected');
 const notice=(db.platform.requireVerifiedBuyers&&!v.verified)?`<div class="note warn" style="margin-bottom:14px"><b>Your account is awaiting verification.</b> You can browse, but bids are disabled until a platform administrator verifies your business.</div>`:'';
 return `${pageHead('Place Bids','Track every bid and offer. Accept a counter, make a new counter, or reject.')}
 ${notice}
 <div class="card pad0"><div class="table-head">${tabBar('bidsb','all',[['all','All'],['open','Open'],['accepted','Accepted'],['rejected','Rejected']])}<a class="btn o sm" href="${BASE}buyer/browse.html">${icon('basket')}Find produce</a></div>
 ${tbl(['Product',['Farmer',0],['Qty (kg)',1],['My price / kg',1],['Total',1],['Date',0],['Status',0],['Actions',0]],ds.map(d=>{const l=listingOf(d.listing),f=userById(d.farmerId);return `<tr>
  <td><b>${esc(l.name)}</b><div class="mut small">${d.initiator==='farmer'?'Offer from farm':'Your bid'}</div></td>
  <td>${esc(f.farm)}<div>${locOf(f)}</div></td>
  ${tdN(num(d.qty))}${tdN(fmtK(d.price))}${tdN('<b>'+fmt(totalOf(d))+'</b>')}
  <td>${esc(d.t)}</td><td>${dealChip(d)}${d.rounds>1?`<div class="mut small">Round ${d.rounds}</div>`:''}</td>
  <td class="act">${dealRowActions(d,'buyer')}</td></tr>`}),emptyState('No bids here','Open a product and place a bid to start negotiating.','<a class="btn p" href="'+BASE+'buyer/browse.html">Browse produce</a>','handshake'))}
 </div>`;
};

BUYER.purchases=()=>{
 const ds=dealsForBuyer().filter(d=>d.status==='accepted');
 const unpaid=ds.filter(d=>!d.paid).reduce((a,d)=>a+totalOf(d),0);
 return `${pageHead('My Purchases','Accepted bids, with payment status.')}
 ${statRow([['Purchases',num(ds.length),'Accepted bids'],['Total spent',fmt(ds.filter(d=>d.paid).reduce((a,d)=>a+totalOf(d),0)),'Paid','brand'],['Awaiting payment',fmt(unpaid),'Due','bad'],['Quantity bought',num(ds.reduce((a,d)=>a+d.qty,0))+' kg','All orders']])}
 <div class="card pad0"><div class="table-head"><h2 style="margin:0">Purchase list</h2></div>
 ${tbl(['Product',['Seller',0],['Quantity',1],['Price / kg',1],['Total',1],['Payment',0],['Action',0]],ds.map(d=>{const l=listingOf(d.listing),f=userById(d.farmerId);return `<tr><td><b>${esc(l.name)}</b><div class="mut small">${esc(d.t)}</div></td><td>${esc(f.farm)}</td>${tdN(num(d.qty)+' kg')}${tdN(fmtK(d.price))}${tdN('<b>'+fmt(totalOf(d))+'</b>')}<td>${d.paid?'<span class="chip ok">Paid</span>':'<span class="chip warn">Pending</span>'}</td><td class="act">${d.paid?'':`<button class="btn p sm" data-act="pay" data-id="${d.id}">${icon('wallet')}Pay now</button>`}</td></tr>`}),emptyState('No purchases yet','Accepted bids appear here.','','receipt'))}
 </div>`;
};

BUYER.orders=()=>{
 const ds=dealsForBuyer().filter(d=>d.status==='accepted');
 return `${pageHead('Orders & Delivery','Track each order from confirmation to delivery.')}
 <div class="stack">${ds.map(d=>{const l=listingOf(d.listing),f=userById(d.farmerId);return `<article class="card" style="display:grid;grid-template-columns:minmax(0,1fr) auto;gap:14px;align-items:center">
  <div class="stack" style="gap:10px"><div class="row" style="justify-content:flex-start;gap:10px"><b style="font-size:15px">${esc(l.name)}</b><span class="mut">from ${esc(f.farm)}</span>${locOf(f)}</div>
  ${stageTrack(d.stage)}
  <div class="mut small">${num(d.qty)} kg @ ${fmtK(d.price)}/kg · total ${fmt(totalOf(d))} · ${d.paid?'<span class="chip ok">Paid</span>':'<span class="chip warn">Payment pending</span>'}</div></div>
  <div class="row" style="flex-direction:column;align-items:flex-end;gap:8px">
   ${d.stage==='dispatched'?`<button class="btn s" data-act="deliver" data-id="${d.id}">${icon('check')}Confirm delivery</button>`:d.stage==='delivered'?'<span class="chip ok">Delivered</span>':'<span class="mut small">Farm is preparing dispatch</span>'}
   ${d.paid?'':`<button class="btn o sm" data-act="pay" data-id="${d.id}">${icon('wallet')}Pay now</button>`}
  </div></article>`}).join('')||`<div class="card">${emptyState('No orders yet','Accepted bids create orders that you can track here.','','truck')}</div>`}</div>`;
};

BUYER.saved=()=>{
 const L=db.listings.filter(l=>db.saved.includes(l.id));
 return `${pageHead('Saved Products','Produce you bookmarked to compare later.')}
 <div class="grid3">${L.map(l=>productCard(l,me())).join('')||`<div class="card" style="grid-column:1/-1">${emptyState('Nothing saved yet','Use the heart on any product to save it here.','<a class="btn p" href="'+BASE+'buyer/browse.html">Browse produce</a>','heart')}</div>`}</div>`;
};

BUYER.history=()=>{
 const ds=dealsForBuyer().slice().reverse();
 return `${pageHead('Transaction History','Every bid, offer, order and payment on your account.')}
 <div class="card pad0">${tbl(['Date',['Product',0],['Farmer',0],['Quantity',1],['Amount',1],['Type',0],['Status',0],['Payment',0]],ds.map(d=>{const l=listingOf(d.listing),f=userById(d.farmerId);return `<tr><td>${esc(d.t)}</td><td>${esc(l.name)}</td><td>${esc(f.farm)}</td>${tdN(num(d.qty)+' kg')}${tdN(fmt(totalOf(d)))}<td>${d.initiator==='farmer'?'Offer':'Bid'}</td><td>${dealChip(d)}</td><td>${d.status==='accepted'?(d.paid?'<span class="chip ok">Paid</span>':'<span class="chip warn">Pending</span>'):'<span class="mut">—</span>'}</td></tr>`}),emptyState('No transactions yet','Your bids and purchases will appear here.','','history'))}
 </div>`;
};

BUYER.product=()=>{
 const id=new URLSearchParams(location.search).get('id');
 const l=listingOf(id)||db.listings.find(x=>x.status==='active');
 if(!l)return `${pageHead('Product','')}<div class="card">${emptyState('Product not found','It may have been withdrawn.','<a class="btn p" href="'+BASE+'buyer/browse.html">Browse produce</a>','basket')}</div>`;
 const f=userById(l.farmer),v=me();
 if(!db.viewed.includes(l.id))db.viewed.unshift(l.id);db.viewed=db.viewed.slice(0,8);
 const rec=recPrice(l.crop,l.district),others=db.listings.filter(x=>x.farmer===f.id&&x.id!==l.id&&x.status==='active');
 const blocked=db.platform.requireVerifiedBuyers&&!v.verified;
 const saved=db.saved.includes(l.id);
 return `<nav class="row" style="justify-content:flex-start;font-size:13px;color:var(--mut-ink)"><a href="${BASE}buyer/browse.html">Browse produce</a><span>/</span><span>${esc(l.name)}</span></nav>
 ${pageHead(esc(l.name),`Grade ${esc(l.grade)} · ${esc(l.crop)} from ${esc(f.farm)}`,`<button class="btn o ${saved?'on':''}" data-act="save" data-id="${l.id}" aria-pressed="${saved}">${icon('heart')}${saved?'Saved':'Save product'}</button>`)}
 <div class="grid2">
  <div class="stack">
   <div class="card stack" style="gap:14px"><div class="photo tall">${l.img?`<img src="${l.img}" alt="${esc(l.name)} photo">`:`<span class="tile full" style="${tintOf(l.crop)}">${esc(l.crop[0])}</span>`}</div></div>
   <div class="card"><div class="row"><h2 style="margin:0">AI quality assessment</h2>${gradeChip(l.grade,l.conf)}</div>
    <div class="kv2" style="margin:14px 0;grid-template-columns:repeat(4,minmax(0,1fr))"><div><span>Grade</span><b>${l.grade}</b></div><div><span>Confidence</span><b>${l.conf}%</b></div><div><span>Visual condition</span><b>${l.grade==='A'?'Good':l.grade==='B'?'Fair':'Check photo'}</b></div><div><span>Harvested</span><b>${fmtDate(l.harvest)}</b></div></div>
    <div class="note"><b>Model prediction, not certification.</b> Confidence reflects the demonstration classifier. Request a manual inspection before a large order.</div></div>
   <div class="card"><h2>Price history · ${esc(l.crop)}</h2>${chartBox('cProdPrice',priceChartCfg(l.crop,l.district,12),'short','Price history for '+l.crop)}<p class="hint">Demonstration series, ₹ per kg.</p></div>
  </div>
  <div class="stack">
   <div class="card"><div class="row" style="justify-content:flex-start;gap:12px">${avatar(f,'lg')}<div><b style="font-size:16px">${esc(f.farm)}</b><div class="mut">${esc(f.name)}</div></div></div>
    <div style="margin:12px 0">${locOf(f)} ${verifiedOf(f)}</div>${distLine(v,f)}
    <div class="kv2" style="margin:14px 0"><div><span>Land</span><b>${f.acres} acres</b></div><div><span>Member since</span><b>${fmtDate(f.joined)}</b></div></div>
    <button class="btn o w" data-act="profile" data-id="${f.id}">${icon('eye')}View farm profile</button>
    ${others.length?`<h3 style="margin-top:16px">Other produce from this farm</h3>${others.map(o=>`<div class="lrow"><span>${esc(o.name)}<div class="mut small">${num(o.qty)} kg · ${fmtK(o.ask)}/kg</div></span><button class="btn g sm" data-act="product" data-id="${o.id}">View</button></div>`).join('')}`:''}
   </div>
   <div class="card" id="bidpanel">
    <h2>Place a bid</h2>
    ${blocked?`<div class="note warn small" style="margin-bottom:12px">Bids are disabled until your business is verified by the platform.</div>`:''}
    <div class="kvs" style="grid-template-columns:1fr 1fr;margin-bottom:14px">
     <div><div class="mut small">Asking price</div><b>${fmtK(l.ask)}/kg</b></div>
     <div><div class="mut small">Recommended</div><b style="color:var(--brand)">${fmtK(rec)}/kg</b></div>
    </div>
    <div class="form" style="grid-template-columns:1fr 1fr">
     <div class="field"><label for="bp">Your price / kg (₹)</label><input id="bp" type="number" min="1" step="any" value="${rec}" data-bid="price"></div>
     <div class="field"><label for="bq">Quantity (kg)</label><input id="bq" type="number" min="1" max="${l.qty}" value="${Math.min(l.qty,100)}" data-bid="qty"></div>
     <div class="field span2"><label for="bd">Delivery preference</label><select id="bd" data-bid="delivery"><option>Farm pickup</option><option>Mandi delivery</option><option>Doorstep delivery</option></select></div>
     <div class="field span2"><label for="bm">Message (optional)</label><textarea id="bm" data-bid="message" placeholder="Pickup timing, grading needs, payment terms"></textarea></div>
    </div>
    <div class="row" style="margin:14px 0;padding:12px 14px;background:var(--hover);border-radius:10px"><span class="mut">Estimated total</span><b id="bidtotal" style="font-size:18px">${fmt(rec*Math.min(l.qty,100))}</b></div>
    <button class="btn p w lg" data-act="place-bid" data-id="${l.id}" ${blocked?'disabled':''}>${icon('send')}Submit bid</button>
    <p class="hint">A bid is a proposal. The farm can accept, reject or counter it. Nothing is final until accepted.</p>
   </div>
  </div>
 </div>`;
};

BUYER.profile=()=>`${pageHead('Profile','Your business details. Buyers see your company name, type and district.')}
 <div class="grid2"><div class="stack">${profileForm(me(),'buyer')}
  <div class="card"><h2>Crops you buy</h2><p class="mut small" style="margin:-6px 0 10px">Used to rank nearby farms and offers.</p>
   <div class="stack" style="gap:8px">${CROPS.map(c=>`<label class="check"><input type="checkbox" data-interest="${c}" ${me().interests.includes(c)?'checked':''}> ${c}</label>`).join('')}</div></div></div>
  <div class="card stack"><div class="row" style="justify-content:flex-start;gap:12px">${avatar(me(),'lg')}<div><b style="font-size:16px">${esc(me().name)}</b><div class="mut">${esc(me().business)}</div></div></div>${verifiedOf(me())}
   <p class="hint">Verification is completed by a platform administrator. Until then, bids are disabled.</p></div>
 </div>`;
BUYER.settings=()=>`${pageHead('Settings','Preferences for this account.')}${settingsBlock(me())}`;

/* ================= ADMIN ================= */
const ADMIN={};
const trendsMonthly=[3,5,4,7,8,9,12,11,14,16,18,21];
ADMIN.overview=()=>{
 const farmers=db.users.filter(u=>u.role==='farmer').length,buyers=db.users.filter(u=>u.role==='buyer').length;
 const tx=db.deals.filter(d=>d.status==='accepted').length;
 const byCrop={};db.listings.forEach(l=>byCrop[l.crop]=(byCrop[l.crop]||0)+1);
 const months=[...Array(12)].map((_,i)=>{const d=new Date(2026,10-(11-i),1);return {k:d.getFullYear()+'-'+(d.getMonth()+1),l:MON[d.getMonth()]}});
 const regs=months.map(m=>db.users.filter(u=>u.joined&&u.joined.slice(0,7)===m.k.replace(/-(\d)$/,'-0$1')).length);
 const regCfg=C=>({type:'line',data:{labels:months.map(m=>m.l),datasets:[{label:'New registrations',data:regs,borderColor:C.brand,backgroundColor:'rgba(120,131,75,.12)',fill:true,tension:.3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,grid:{color:C.grid}},x:{grid:{display:false}}}}});
 const txCfg=C=>({type:'bar',data:{labels:months.map(m=>m.l),datasets:[{label:'Transaction value, ₹ lakh (demo)',data:trendsMonthly,backgroundColor:C.accent,borderRadius:5}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{grid:{color:C.grid}},x:{grid:{display:false}}}}});
 const cropCfg=C=>({type:'doughnut',data:{labels:Object.keys(byCrop),datasets:[{data:Object.values(byCrop),backgroundColor:[C.brand,C.accent,C.brand2],borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,usePointStyle:true}}}}});
 return `${pageHead('Overview','Platform health at a glance. Figures are demonstration data.','<span class="chip outline">Demonstration data</span>')}
 <div class="grid4">
  ${kpi('Registered farmers',num(farmers),'sprout',{dir:'up',text:'+2 this month (demo)'})}
  ${kpi('Registered buyers',num(buyers),'building',{dir:'up',text:'+3 this month (demo)'})}
  ${kpi('Products listed',num(db.listings.filter(l=>l.status==='active').length),'package',{dir:'up',text:'Active now'})}
  ${kpi('Completed transactions',num(tx),'transfer',{dir:'up',text:'+6 this month (demo)'},'brand')}
 </div>
 <div class="grid2">
  <div class="card"><h2>User registrations, last 12 months</h2>${chartBox('cRegs',regCfg,'short','User registrations line chart')}</div>
  <div class="card"><h2>Transaction value trend</h2>${chartBox('cTx',txCfg,'short','Transaction value bar chart')}</div>
 </div>
 <div class="grid2">
  <div class="card"><h2>Crop distribution</h2>${chartBox('cCrops',cropCfg,'short','Crop distribution doughnut chart')}</div>
  <div class="card"><h2>Recent platform activity</h2><div class="feed">${db.log.slice(0,8).map(x=>`<div>${esc(x)}</div>`).join('')}</div></div>
 </div>`;
};

function userRow(u){
 const verifyBtn=u.role==='admin'?'':u.verified?`<button class="btn o sm" data-act="ask" data-title="Revoke verification?" data-text="${esc(u.name)} will need to be verified again before bidding or listing." data-label="Revoke" data-then="verify" data-id="${u.id}" data-danger="1">Revoke</button>`:`<button class="btn s sm" data-act="verify" data-id="${u.id}">${icon('badge')}Verify</button>`;
 const susp=u.status==='suspended'?`<button class="btn o sm" data-act="reactivate" data-id="${u.id}">${icon('play')}Reactivate</button>`:`<button class="btn d sm" data-act="ask" data-title="Suspend this account?" data-text="${esc(u.name)} will not be able to sign in until reactivated." data-label="Suspend account" data-then="suspend" data-id="${u.id}" data-danger="1">${icon('ban')}Suspend</button>`;
 return `<tr><td><b>${esc(u.name)}</b><div class="mut small">${esc(u.email)}</div></td><td style="text-transform:capitalize">${u.role}</td><td>${esc(u.city||'—')}, ${esc(u.district||'')}</td><td>${fmtDate(u.joined)}</td><td>${u.role==='admin'?'<span class="mut">—</span>':u.verified?'<span class="chip ok">Verified</span>':'<span class="chip warn">Pending</span>'}</td><td>${u.status==='suspended'?'<span class="chip bad">Suspended</span>':'<span class="chip ok">Active</span>'}</td>
 <td class="act"><div class="row" style="gap:6px;justify-content:flex-end;flex-wrap:nowrap"><button class="iconbtn" data-act="profile" data-id="${u.id}" aria-label="View user" title="View user">${icon('eye')}</button>${verifyBtn}${u.role==='admin'?'':susp}</div></td></tr>`;
}
ADMIN.users=()=>{
 const st=tab('users','all'),q=SEARCH.toLowerCase();
 let L=db.users.filter(u=>(!q||u.name.toLowerCase().includes(q)||u.email.toLowerCase().includes(q)));
 if(st==='farmers')L=L.filter(u=>u.role==='farmer');
 if(st==='buyers')L=L.filter(u=>u.role==='buyer');
 if(st==='suspended')L=L.filter(u=>u.status==='suspended');
 if(st==='pending')L=L.filter(u=>u.role!=='admin'&&!u.verified);
 return `${pageHead('User Management','View, verify, suspend and reactivate accounts. Every change is recorded in the activity log.')}
 <div class="card pad0"><div class="table-head">${tabBar('users','all',[['all','All users'],['farmers','Farmers'],['buyers','Buyers'],['pending','Pending verification'],['suspended','Suspended']])}</div>
 ${tbl(['User',['Role',0],['Location',0],['Registered',0],['Verification',0],['Account',0],['Actions',0]],L.map(userRow),emptyState('No users match','Clear the search or change the tab.','','users'))}
 </div>`;
};
ADMIN.farmers=()=>{
 const q=SEARCH.toLowerCase();
 const L=db.users.filter(u=>u.role==='farmer'&&(!q||u.name.toLowerCase().includes(q)||u.farm.toLowerCase().includes(q)));
 return `${pageHead('Farmer Management','Verify farms and review their listings and activity.')}
 <div class="card pad0">${tbl(['Farm',['Owner',0],['Location',0],['Listings',1],['Deals',1],['Verification',0],['Account',0],['Actions',0]],L.map(f=>{
   const n=db.listings.filter(l=>l.farmer===f.id).length,dl=db.deals.filter(d=>d.farmerId===f.id).length;
   return `<tr><td><b>${esc(f.farm)}</b></td><td>${esc(f.name)}<div class="mut small">${esc(f.email)}</div></td><td>${locOf(f)}</td>${tdN(n)}${tdN(dl)}
   <td>${f.verified?'<span class="chip ok">Verified</span>':'<span class="chip warn">Pending</span>'}</td>
   <td>${f.status==='suspended'?'<span class="chip bad">Suspended</span>':'<span class="chip ok">Active</span>'}</td>
   <td class="act"><div class="row" style="gap:6px;justify-content:flex-end;flex-wrap:nowrap"><button class="iconbtn" data-act="profile" data-id="${f.id}" aria-label="View farm" title="View farm">${icon('eye')}</button>${f.verified?`<button class="btn o sm" data-act="ask" data-title="Revoke verification?" data-text="${esc(f.farm)} will need to be verified again." data-label="Revoke" data-then="verify" data-id="${f.id}" data-danger="1">Revoke</button>`:`<button class="btn s sm" data-act="verify" data-id="${f.id}">${icon('badge')}Verify farm</button>`}${f.status==='suspended'?`<button class="btn o sm" data-act="reactivate" data-id="${f.id}">Reactivate</button>`:`<button class="btn d sm" data-act="ask" data-title="Suspend this account?" data-text="${esc(f.farm)} cannot sign in until reactivated." data-label="Suspend" data-then="suspend" data-id="${f.id}" data-danger="1">Suspend</button>`}</div></td></tr>`;
 }),emptyState('No farmers match','Clear the search text to see every farm.','','sprout'))}</div>`;
};
ADMIN.buyers=()=>{
 const q=SEARCH.toLowerCase();
 const L=db.users.filter(u=>u.role==='buyer'&&(!q||u.name.toLowerCase().includes(q)));
 return `${pageHead('Buyer Management','Verify buyers before they can bid. Verified buyers show a badge on their profile.')}
 <div class="card pad0">${tbl(['Company',['Type',0],['Location',0],['Bids & orders',1],['Verification',0],['Account',0],['Actions',0]],L.map(b=>{const n=db.deals.filter(d=>d.buyerId===b.id).length;return `<tr><td><b>${esc(b.name)}</b><div class="mut small">${esc(b.contact)} · ${esc(b.email)}</div></td><td>${esc(b.business)}</td><td>${locOf(b)}</td>${tdN(n)}<td>${b.verified?'<span class="chip ok">Verified</span>':'<span class="chip warn">Pending</span>'}</td><td>${b.status==='suspended'?'<span class="chip bad">Suspended</span>':'<span class="chip ok">Active</span>'}</td><td class="act"><div class="row" style="gap:6px;justify-content:flex-end;flex-wrap:nowrap"><button class="iconbtn" data-act="profile" data-id="${b.id}" aria-label="View buyer" title="View buyer">${icon('eye')}</button>${b.verified?`<button class="btn o sm" data-act="ask" data-title="Revoke verification?" data-text="${esc(b.name)} will not be able to bid until verified again." data-label="Revoke" data-then="verify" data-id="${b.id}" data-danger="1">Revoke</button>`:`<button class="btn s sm" data-act="verify" data-id="${b.id}">${icon('badge')}Verify buyer</button>`}${b.status==='suspended'?`<button class="btn o sm" data-act="reactivate" data-id="${b.id}">Reactivate</button>`:`<button class="btn d sm" data-act="ask" data-title="Suspend this account?" data-text="${esc(b.name)} cannot sign in until reactivated." data-label="Suspend" data-then="suspend" data-id="${b.id}" data-danger="1">Suspend</button>`}</div></td></tr>`}),emptyState('No buyers match','','','building'))}</div>`;
};
ADMIN.products=()=>{
 const q=SEARCH.toLowerCase(),st=tab('products','all');
 let L=db.listings.filter(l=>(!q||l.name.toLowerCase().includes(q)||l.crop.toLowerCase().includes(q)));
 if(st!=='all')L=L.filter(l=>l.status===st);
 return `${pageHead('Product Management','Review listings across the platform. Hide a listing to remove it from buyer views.')}
 <div class="card pad0"><div class="table-head">${tabBar('products','all',[['all','All'],['active','Active'],['paused','Paused'],['sold','Sold'],['hidden','Hidden']])}</div>
 ${tbl(['Product',['Farm',0],['Quantity',1],['Grade',0],['Price / kg',1],['Status',0],['Actions',0]],L.map(l=>{const f=userById(l.farmer);return `<tr><td><b>${esc(l.name)}</b><div class="mut small">${esc(l.crop)} · ${esc(l.district)}</div></td><td>${esc(f.farm)}</td>${tdN(num(l.qty)+' kg')}<td>${gradeChip(l.grade,l.conf)}</td>${tdN(fmtK(l.ask))}<td>${statusChip(l.status)}</td><td class="act">${l.status==='hidden'?`<button class="btn o sm" data-act="mod" data-id="${l.id}">Restore</button>`:l.status==='sold'?'<span class="mut small">—</span>':`<button class="btn d sm" data-act="ask" data-title="Hide this listing?" data-text="Buyers will stop seeing ${esc(l.name)} until it is restored." data-label="Hide listing" data-then="mod" data-id="${l.id}" data-danger="1">Hide</button>`}</td></tr>`}),emptyState('No listings here','','','package'))}
 </div>`;
};
ADMIN.ai=()=>{
 if(typeof fetchMLMetrics === 'function' && (!window.ML_CACHE || !window.ML_CACHE.metricsData)){
   fetchMLMetrics().then(()=>{ if(typeof render==='function') render(); });
 }
 const m = window.ML_CACHE && window.ML_CACHE.metricsData;
 const hasML = !!m;
 const modelName = hasML && m.price_model ? m.price_model.best_model : 'GradientBoosting';
 const testMae = hasML && m.price_model ? '₹' + m.price_model.test_metrics.MAE + ' / qtl' : '₹88.09 / qtl';
 const testR2 = hasML && m.price_model ? m.price_model.test_metrics.R2 : '0.9499';
 const testMape = hasML && m.price_model ? m.price_model.test_metrics.MAPE_pct + '%' : '8.18%';
 const demandAcc = hasML && m.demand_model ? (m.demand_model.accuracy * 100).toFixed(1) + '%' : '49.1%';
 const splitSizes = hasML && m.price_model ? m.price_model.split_sizes : {train: 3066, validation: 660, test: 660};

 const g={A:0,B:0,C:0};db.assess.forEach(a=>g[a.grade]++);
 const demo={A:812,B:534,C:215};
 const cfg=C=>({type:'bar',data:{labels:['Grade A','Grade B','Grade C'],datasets:[{label:'Predictions (demo counts + saved sessions)',data:[demo.A+g.A,demo.B+g.B,demo.C+g.C],backgroundColor:[C.ok,C.info,C.warn],borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{grid:{color:C.grid}},x:{grid:{display:false}}}}});
 const total=demo.A+demo.B+demo.C+db.assess.length;
 
 return `${pageHead('AI Model Monitoring & Performance','Health and evaluation metrics of the price intelligence and demand forecasting engine.')}
 <div class="note ok" style="margin-bottom:6px"><b>${hasML ? 'Live Connected' : 'Production Trained Model'}</b> Active models: <b>${modelName}Regressor</b> (Price) & <b>RandomForestClassifier</b> (7-Day Demand Proxy). Tested on 4,386 Karnataka APMC records.</div>
 <div class="grid4">
  <div class="card stat"><div class="label">Price Champion Model${icon('cpu')}</div><span class="bigval" style="font-size:20px">${modelName}</span><span class="mut small">v1.0.0 (Chronological split)</span></div>
  <div class="card stat"><div class="label">ML API Status${icon('activity')}</div><span class="bigval ok" style="font-size:20px">${hasML ? 'Operational' : 'Ready'}</span><span class="mut small">${hasML ? 'Connected on :5000' : 'REST Engine'}</span></div>
  <div class="card stat"><div class="label">Evaluated Records${icon('scan')}</div><span class="bigval">4,386</span><span class="mut small">${splitSizes.train} train · ${splitSizes.test} test</span></div>
  <div class="card stat"><div class="label">Test MAE${icon('clock')}</div><span class="bigval">${testMae}</span><span class="mut small">MAPE: ${testMape}</span></div>
 </div>
 <div class="grid2">
  <div class="card"><div class="row"><h2 style="margin:0">Quality Prediction distribution</h2><span class="chip outline">Demo</span></div>${chartBox('cPred',cfg,'short','Prediction distribution by grade')}</div>
  <div class="card stack"><h2 style="margin:0">Model Evaluation Benchmarks</h2>
   <div class="lrow"><span>Champion Price Architecture</span><b>${modelName}Regressor</b></div>
   <div class="lrow"><span>Test Out-of-Sample MAE</span><b>${testMae}</b></div>
   <div class="lrow"><span>Test R² Score</span><b>${testR2}</b></div>
   <div class="lrow"><span>Demand Trend Accuracy</span><b>${demandAcc} (3-class)</b></div>
   <div class="lrow"><span>Feature Importances / XAI</span><b>TreeSHAP Enabled</b></div>
   <p class="hint">Trained without future leakage using chronological time splits on Karnataka APMC mandis.</p>
  </div>
 </div>
 <div class="card pad0"><div class="table-head"><h2 style="margin:0">Live Model Pipeline Audit</h2><span class="chip ok">Verified</span></div>
 ${tbl(['Component',['Model / Technique',0],['Status',0],['Performance / Notes',0]],[
  ['Price Prediction','GradientBoostingRegressor (120 trees)','<span class="chip ok">Active</span>','MAE: ' + testMae + ' | R²: ' + testR2],
  ['Demand Forecasting','RandomForestClassifier (7-day proxy)','<span class="chip ok">Active</span>','3-class trend accuracy: ' + demandAcc],
  ['Explainability','TreeSHAP + Domain Knowledge Engine','<span class="chip ok">Active</span>','Synthesizes price momentum, season, and arrivals'],
  ['REST Microservice','Flask API (CORS enabled)','<span class="chip ok">Port 5000</span>','Endpoints: /predict-price, /forecast-demand, /explain-price']
 ].map(([t,e,s,a])=>`<tr><td><b>${t}</b></td><td>${e}</td><td>${s}</td><td>${a}</td></tr>`))}
 </div>`;
};
ADMIN.transactions=()=>{
 const st=tab('tx','all');
 let ds=db.deals.slice().reverse();
 if(st!=='all')ds=ds.filter(d=>d.status===st);
 const value=db.deals.filter(d=>d.status==='accepted').reduce((a,d)=>a+totalOf(d),0);
 return `${pageHead('Marketplace Transactions','Every bid, offer and sale on the platform.')}
 ${statRow([['Transaction value',fmt(value),'Accepted deals','brand'],['Completed',num(db.deals.filter(d=>d.status==='accepted'&&d.stage==='delivered').length),'Delivered'],['Open negotiations',num(db.deals.filter(isOpen).length),'Pending or countered'],['Unpaid',fmt(db.deals.filter(d=>d.status==='accepted'&&!d.paid).reduce((a,d)=>a+totalOf(d),0)),'Awaiting payment','bad']])}
 <div class="card pad0"><div class="table-head">${tabBar('tx','all',[['all','All'],['accepted','Accepted'],['pending','Pending'],['rejected','Rejected']])}<button class="btn o sm" data-act="export">${icon('download')}Export CSV</button></div>
 ${tbl(['ID',['Product',0],['Farmer',0],['Buyer',0],['Qty',1],['Price / kg',1],['Total',1],['Status',0],['Payment',0]],ds.map(d=>{const l=listingOf(d.listing),f=userById(d.farmerId),b=userById(d.buyerId);return `<tr><td>${d.id.toUpperCase()}</td><td>${esc(l.name)}</td><td>${esc(f.farm)}</td><td>${esc(b.name)}</td>${tdN(num(d.qty))}${tdN(fmtK(d.price))}${tdN('<b>'+fmt(totalOf(d))+'</b>')}<td>${dealChip(d)}</td><td>${d.status==='accepted'?(d.paid?'<span class="chip ok">Paid</span>':'<span class="chip warn">Pending</span>'):'<span class="mut">—</span>'}</td></tr>`}),emptyState('No transactions here','','','transfer'))}
 </div>`;
};
ADMIN.bidding=()=>{
 const counts={pending:0,counter:0,accepted:0,rejected:0};db.deals.forEach(d=>counts[d.status]++);
 const rows=db.deals.map(d=>{const l=listingOf(d.listing),f=userById(d.farmerId),b=userById(d.buyerId);return `<tr><td>${esc(l.name)}</td><td>${esc(b.name)}</td><td>${esc(f.farm)}</td>${tdN(fmtK(d.price))}${tdN(num(d.qty))}${tdN(d.rounds)}<td>${d.by==='farmer'?'Farmer':'Buyer'}</td><td>${dealChip(d)}</td></tr>`});
 return `${pageHead('Bidding Management','Negotiation activity across buyers and farms.')}
 ${statRow([['Pending',counts.pending,'Awaiting response','warn'],['Counter offers',counts.counter,'Back and forth'],['Accepted',counts.accepted,'Converted to orders','ok'],['Rejected',counts.rejected,'Closed','bad']])}
 <div class="card pad0"><div class="table-head"><h2 style="margin:0">All bids and offers</h2></div>${tbl(['Product','Buyer','Farm',['Price / kg',1],['Qty (kg)',1],['Rounds',1],['Last by',0],['Status',0]],rows,emptyState('No bids yet','','','handshake'))}</div>`;
};
ADMIN.prices=()=>{
 const crop=PR.crop;
 const cfg=C=>({type:'line',data:{labels:series(crop,PR.district,12).map(p=>p.label),datasets:MARKETS.map((m,i)=>({label:m+' (demo)',data:series(crop,['Bengaluru Urban','Kolar','Chennai'][i],12).map(p=>p.v),borderColor:[C.brand,C.accent,C.info][i],tension:.3,pointRadius:1,borderWidth:2}))},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,usePointStyle:true}}},scales:{y:{ticks:{callback:v=>'₹'+v},grid:{color:C.grid}},x:{grid:{display:false}}}}});
 const regions=['Bengaluru Urban','Kolar','Chikkaballapur','Tumakuru','Mandya','Mysuru','Hassan'];
 return `${pageHead('Price Intelligence','Platform-wide market view. Demonstration series.',`<select data-p="crop" aria-label="Crop" style="width:auto">${selectOpts(CROPS,crop)}</select>`)}
 <div class="grid2"><div class="card"><h2>Market comparison · ${esc(crop)}</h2>${chartBox('cMarkets',cfg,'tall','Market price comparison line chart')}</div>
 <div class="card"><h2>Regional summary</h2>${tbl(['District',['Current / kg',1],['Recommended / kg',1],['Market Demand Index (Proxy)',0]],regions.map(r=>`<tr><td>${esc(r)}</td>${tdN(fmtK(currentPrice(crop,r)))}${tdN(fmtK(recPrice(crop,r)))}<td>${DEMAND_IDX[crop].label}</td></tr>`))}</div></div>`;
};
ADMIN.reports=()=>{
 const byStatus={accepted:0,pending:0,counter:0,rejected:0};db.deals.forEach(d=>byStatus[d.status]++);
 const dist={};db.listings.forEach(l=>dist[l.district]=(dist[l.district]||0)+1);
 const gr={A:0,B:0,C:0};db.listings.forEach(l=>gr[l.grade]++);
 const bar=(labels,data,title,color)=>C=>({type:'bar',data:{labels,datasets:[{label:title,data,backgroundColor:color,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,grid:{color:C.grid}},x:{grid:{display:false}}}}});
 return `${pageHead('Reports & Analytics','Summaries of listings, negotiations and outcomes.',`<button class="btn p" data-act="export">${icon('download')}Export transactions (CSV)</button>`)}
 <div class="grid2 even">
  <div class="card"><h2>Deals by status</h2>${chartBox('cRStatus',bar(Object.keys(byStatus),Object.values(byStatus),'Deals','#78834B'),'short','Deals by status bar chart')}</div>
  <div class="card"><h2>Listings by district</h2>${chartBox('cRDist',bar(Object.keys(dist),Object.values(dist),'Listings','#BD7049'),'short','Listings by district bar chart')}</div>
  <div class="card"><h2>Listings by quality grade</h2>${chartBox('cRGrade',bar(['A','B','C'],[gr.A,gr.B,gr.C],'Listings','#4F824A'),'short','Listings by grade bar chart')}</div>
  <div class="card"><h2>Key figures</h2><div class="stack" style="gap:0">
   <div class="lrow"><span>Registered users</span><b>${db.users.length}</b></div>
   <div class="lrow"><span>Active listings</span><b>${db.listings.filter(l=>l.status==='active').length}</b></div>
   <div class="lrow"><span>Accepted deals</span><b>${byStatus.accepted}</b></div>
   <div class="lrow"><span>Messages received</span><b>${db.messages.length}</b></div></div></div>
 </div>`;
};
ADMIN.settings=()=>{
 const p=db.platform;
 return `${pageHead('Platform Settings','Rules that apply across the marketplace. Changes take effect immediately.')}
 <div class="grid2 even">
  <div class="card"><h2>Marketplace rules</h2>
   <div class="switch"><span>Require verified buyers to place bids<br><span class="mut small">Unverified buyers can browse but cannot bid.</span></span><input type="checkbox" data-plat="requireVerifiedBuyers" ${p.requireVerifiedBuyers?'checked':''} aria-label="Require verified buyers"></div>
   <div class="switch"><span>Show approximate distances<br><span class="mut small">Distances are between district centres.</span></span><input type="checkbox" data-plat="showApproxDistance" ${p.showApproxDistance?'checked':''} aria-label="Show distances"></div>
  </div>
  <div class="card stack"><h2 style="margin:0">Demonstration data</h2><p class="mut small">Reset restores the original sample farms, buyers, listings and deals. Your local changes will be lost.</p>
   <div><button class="btn d" data-act="ask" data-title="Reset all demonstration data?" data-text="All changes made in this browser will be replaced by the original sample data." data-label="Reset data" data-then="reset" data-id="" data-danger="1">${icon('refresh')}Reset demonstration data</button></div></div>
 </div>`;
};

const VIEWS={};
for(const [role,map] of Object.entries({farmer:FARMER,buyer:BUYER,admin:ADMIN})){
 for(const [v,fn] of Object.entries(map))VIEWS[role+'.'+v]=fn;
}
