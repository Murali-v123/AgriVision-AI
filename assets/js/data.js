/* AgriVision AI – configuration, demonstration data, persistence and helpers.
   All prices, distances, forecasts and model figures are simulated demonstration data.
   Replace load()/save() and the mutations in actions.js with API calls when a backend exists. */

const BASE=(window.AV_PAGE&&window.AV_PAGE.base)||'';
const PAGES={
 farmer:{overview:'dashboard.html',produce:'my-products.html',upload:'upload.html',quality:'quality.html',prices:'prices.html',buyers:'marketplace.html',bids:'bids.html',orders:'orders.html',earnings:'earnings.html',profile:'profile.html',settings:'settings.html'},
 buyer:{overview:'dashboard.html',browse:'browse.html',farmers:'farmers.html',verified:'verified.html',bids:'bids.html',purchases:'purchases.html',orders:'orders.html',saved:'saved.html',history:'history.html',profile:'profile.html',settings:'settings.html',product:'product.html'},
 admin:{overview:'dashboard.html',users:'users.html',farmers:'farmers.html',buyers:'buyers.html',products:'products.html',ai:'ai-monitoring.html',transactions:'transactions.html',bidding:'bidding.html',prices:'prices.html',reports:'reports.html',settings:'settings.html'}
};
const goTo=(view,role,q='')=>{location.href=BASE+role+'/'+PAGES[role][view]+q};

const KEY='agrivision-v3';
const THEME_KEY='agrivision-theme';
const $=(s,r=document)=>r.querySelector(s);
const TODAY=new Date('2026-11-14T10:00:00');
const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

/* ---------- Formatting ---------- */
const fmt=n=>'₹'+Math.round(Number(n)).toLocaleString('en-IN');
const fmtK=n=>'₹'+(Math.round(Number(n)*10)/10).toLocaleString('en-IN',{maximumFractionDigits:1});
const num=n=>Number(n).toLocaleString('en-IN');
const fmtDate=iso=>iso?new Date(iso+(iso.length===10?'T00:00:00':'')).toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'}):'—';
const stamp=()=>new Date(TODAY).toLocaleString('en-IN',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
const daysAgo=n=>new Date(TODAY.getTime()-n*864e5).toISOString().slice(0,10);
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

/* ---------- Places (district centres, used only for approximate distances) ---------- */
const PLACES={
 'Bengaluru Urban':['Karnataka',12.97,77.59],'Bengaluru Rural':['Karnataka',13.20,77.71],'Mysuru':['Karnataka',12.30,76.64],
 'Mandya':['Karnataka',12.52,76.90],'Tumakuru':['Karnataka',13.34,77.10],'Hassan':['Karnataka',13.00,76.10],
 'Kolar':['Karnataka',13.14,78.13],'Chikkaballapur':['Karnataka',13.43,77.73],'Ramanagara':['Karnataka',12.72,77.28],
 'Dharwad':['Karnataka',15.46,75.01],'Davanagere':['Karnataka',14.47,75.92],'Belagavi':['Karnataka',15.85,74.50],
 'Hosur':['Tamil Nadu',12.74,77.83],'Chennai':['Tamil Nadu',13.08,80.27],'Coimbatore':['Tamil Nadu',11.00,76.96]
};
const KA_DISTRICTS=['Bagalkot','Ballari','Belagavi','Bengaluru Rural','Bengaluru Urban','Bidar','Chamarajanagar','Chikkaballapur','Chikkamagaluru','Chitradurga','Dakshina Kannada','Davanagere','Dharwad','Gadag','Hassan','Haveri','Kalaburagi','Kodagu','Kolar','Koppal','Mandya','Mysuru','Raichur','Ramanagara','Shivamogga','Tumakuru','Udupi','Uttara Kannada','Vijayapura','Yadgir','Vijayanagara'];
const STATES=['Karnataka','Tamil Nadu','Andhra Pradesh','Telangana','Kerala','Maharashtra'];
const CROPS=['Tomato','Onion','Potato'];
const MARKETS=['Bengaluru APMC','Kolar APMC','Chennai Koyambedu'];
const CROP_BASE={Tomato:28,Onion:21,Potato:18};
const DEMAND_IDX={Tomato:{v:82,label:'High'},Onion:{v:58,label:'Medium'},Potato:{v:41,label:'Low'}};

function km(a,b){
 const R=6371,t=x=>x*Math.PI/180;
 const dLat=t(b[0]-a[0]),dLng=t(b[1]-a[1]);
 const h=Math.sin(dLat/2)**2+Math.cos(t(a[0]))*Math.cos(t(b[0]))*Math.sin(dLng/2)**2;
 return Math.round(2*R*Math.asin(Math.sqrt(h)));
}
const coords=district=>PLACES[district]?[PLACES[district][1],PLACES[district][2]]:null;
/* Approximate distance between two district centres. Null when either side has hidden its location. */
function distanceBetween(u1,u2){
 if(!u1||!u2||u1.locShare===false||u2.locShare===false)return null;
 const a=coords(u1.district),b=coords(u2.district);
 return a&&b?km(a,b):null;
}

/* ---------- Simulated market data ---------- */
/* Deterministic demonstration series ending in November 2026. Labelled as demo data in the UI. */
function currentPrice(crop,district){
 const f=0.97+((district||'').length%8)*0.01;
 return Math.round((CROP_BASE[crop]||20)*f*10)/10;
}
function series(crop,district,months){
 const base=CROP_BASE[crop]||20,s=(district||'').length*0.37+crop.length;
 const raw=[];
 for(let i=0;i<months;i++){
  const k=months-1-i,m=(10-k+120)%12;
  raw.push({label:MON[m],v:base*(1+0.14*Math.sin(i/2.1+s)+0.03*Math.cos(i*1.7))});
 }
 const now=currentPrice(crop,district),last=raw[raw.length-1].v;
 return raw.map(p=>({label:p.label,v:Math.round(p.v*now/last*10)/10}));
}
/* Demonstration rule: 1.04 × average of the last three months. Not a trained forecast. */
function recPrice(crop,district){
 const l=series(crop,district,12).slice(-3);
 return Math.round(l.reduce((a,p)=>a+p.v,0)/3*1.04*10)/10;
}

/* ---------- Icons ---------- */
const icon=(name,cls='')=>{const d=(typeof ICONS!=='undefined'&&ICONS[name])||'';return `<svg class="ic ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`};

/* ---------- Navigation ---------- */
const NAV={
 farmer:[['overview','Overview','overview'],['produce','My Products','package'],['upload','Upload Produce','upload'],['quality','AI Quality Assessment','scan'],['prices','Market Price Intelligence','chart'],['buyers','Buyer Marketplace','store'],['bids','Bids & Offers','handshake'],['orders','Orders','truck'],['earnings','Earnings','wallet'],['profile','Profile','user'],['settings','Settings','settings']],
 buyer:[['overview','Overview','overview'],['browse','Browse Products','basket'],['farmers','Search Farmers','users'],['verified','AI Verified Produce','badge'],['bids','Place Bids','handshake'],['purchases','My Purchases','receipt'],['orders','Orders & Delivery','truck'],['saved','Saved Products','heart'],['history','Transaction History','history'],['profile','Profile','user'],['settings','Settings','settings']],
 admin:[['overview','Overview','overview'],['users','User Management','users'],['farmers','Farmer Management','sprout'],['buyers','Buyer Management','building'],['products','Product Management','package'],['ai','AI Model Monitoring','cpu'],['transactions','Marketplace Transactions','transfer'],['bidding','Bidding Management','handshake'],['prices','Price Intelligence','chart'],['reports','Reports & Analytics','report'],['settings','Platform Settings','settings']]
};
const EXTRA_VIEWS={buyer:['product']};

/* ---------- Seed data ---------- */
function seed(){
 const user=(o)=>Object.assign({verified:true,status:'active',locShare:true,prefs:{notifyBids:true,notifyPrices:false},joined:'2025-06-01'},o);
 const users=[
  user({id:'f1',role:'farmer',name:'Ramesh Kumar',email:'ramesh@demo.in',pass:'farmer123',phone:'9800000001',farm:'Ramesh Vegetable Farm',village:'Mulbagal',city:'Mulbagal',district:'Kolar',state:'Karnataka',acres:6,joined:'2025-03-10'}),
  user({id:'f2',role:'farmer',name:'Lakshmi Devi',email:'lakshmi@demo.in',pass:'farmer123',phone:'9800000002',farm:'Lakshmi Organic Farms',village:'Gudibande',city:'Gudibande',district:'Chikkaballapur',state:'Karnataka',acres:9,joined:'2025-04-02'}),
  user({id:'f3',role:'farmer',name:'Suresh Gowda',email:'suresh@demo.in',pass:'farmer123',phone:'9800000003',farm:'Gowda Green Fields',village:'Kunigal',city:'Kunigal',district:'Tumakuru',state:'Karnataka',acres:12,joined:'2025-05-18'}),
  user({id:'f4',role:'farmer',name:'Anitha R',email:'anitha@demo.in',pass:'farmer123',phone:'9800000004',farm:'Anitha Agro',village:'Maddur',city:'Maddur',district:'Mandya',state:'Karnataka',acres:4,joined:'2025-06-22'}),
  user({id:'f5',role:'farmer',name:'Mahesh B',email:'mahesh@demo.in',pass:'farmer123',phone:'9800000005',farm:'Malnad Farms',village:'Arsikere',city:'Arsikere',district:'Hassan',state:'Karnataka',acres:5,verified:false,joined:'2025-08-09'}),
  user({id:'f6',role:'farmer',name:'Venkatesh N',email:'venkat@demo.in',pass:'farmer123',phone:'9800000006',farm:'Venkat Produce',village:'Hunsur',city:'Hunsur',district:'Mysuru',state:'Karnataka',acres:8,joined:'2025-07-01'}),
  user({id:'f7',role:'farmer',name:'Pushpa K',email:'pushpa@demo.in',pass:'farmer123',phone:'9800000007',farm:'Pushpa Farm',village:'Magadi',city:'Magadi',district:'Ramanagara',state:'Karnataka',acres:3,joined:'2025-09-14'}),
  user({id:'f8',role:'farmer',name:'Basavaraj P',email:'basava@demo.in',pass:'farmer123',phone:'9800000008',farm:'Basava Fields',village:'Malur',city:'Malur',district:'Kolar',state:'Karnataka',acres:7,joined:'2025-10-03'}),
  user({id:'f9',role:'farmer',name:'Savitha M',email:'savitha@demo.in',pass:'farmer123',phone:'9800000009',farm:'Savitha Harvest',village:'Chintamani',city:'Chintamani',district:'Chikkaballapur',state:'Karnataka',acres:2,verified:false,joined:'2025-11-01'}),
  user({id:'f10',role:'farmer',name:'Ravi Shankar',email:'ravi@demo.in',pass:'farmer123',phone:'9800000010',farm:'Shankar Agri',village:'Tiptur',city:'Tiptur',district:'Tumakuru',state:'Karnataka',acres:10,joined:'2025-02-20'}),
  user({id:'b1',role:'buyer',name:'FreshMart Wholesale',contact:'Priya Nair',email:'buyer@demo.in',pass:'buyer123',phone:'9900000001',business:'Wholesaler',city:'Bengaluru',district:'Bengaluru Urban',state:'Karnataka',interests:['Tomato','Onion'],joined:'2025-05-05'}),
  user({id:'b2',role:'buyer',name:'Bharat Fresh Foods',contact:'Arun Kumar',email:'bharat@demo.in',pass:'buyer123',phone:'9900000002',business:'Food Processor',city:'Hosur',district:'Hosur',state:'Tamil Nadu',interests:['Tomato','Onion'],joined:'2025-06-12'}),
  user({id:'b3',role:'buyer',name:'Annapurna Processing',contact:'Meena S',email:'annapurna@demo.in',pass:'buyer123',phone:'9900000003',business:'Food Processor',city:'Chennai',district:'Chennai',state:'Tamil Nadu',interests:['Tomato','Potato'],verified:false,joined:'2025-07-20'}),
  user({id:'b4',role:'buyer',name:'GreenMart Wholesale',contact:'Kiran Rao',email:'greenmart@demo.in',pass:'buyer123',phone:'9900000004',business:'Wholesaler',city:'Mysuru',district:'Mysuru',state:'Karnataka',interests:['Tomato'],joined:'2025-04-18'}),
  user({id:'b5',role:'buyer',name:'Fresh Foods Pvt Ltd',contact:'Sandeep J',email:'freshfoods@demo.in',pass:'buyer123',phone:'9900000005',business:'Food Processor',city:'Bengaluru',district:'Bengaluru Urban',state:'Karnataka',interests:['Tomato','Onion'],joined:'2025-08-30'}),
  user({id:'b6',role:'buyer',name:'Daily Basket',contact:'Rahul M',email:'dailybasket@demo.in',pass:'buyer123',phone:'9900000006',business:'Retailer',city:'Mandya',district:'Mandya',state:'Karnataka',interests:['Tomato','Potato'],joined:'2025-09-09'}),
  user({id:'b7',role:'buyer',name:'Namma Kirana',contact:'Lata P',email:'nammakirana@demo.in',pass:'buyer123',phone:'9900000007',business:'Retailer',city:'Tumakuru',district:'Tumakuru',state:'Karnataka',interests:['Onion','Potato'],joined:'2025-10-11'}),
  user({id:'b8',role:'buyer',name:'Hubballi Veg Hub',contact:'Iqbal K',email:'hubballi@demo.in',pass:'buyer123',phone:'9900000008',business:'Wholesaler',city:'Hubballi',district:'Dharwad',state:'Karnataka',interests:['Potato'],verified:false,joined:'2025-10-25'}),
  user({id:'b9',role:'buyer',name:'Coimbatore Fresh Mart',contact:'Selvi R',email:'cbefresh@demo.in',pass:'buyer123',phone:'9900000009',business:'Retailer',city:'Coimbatore',district:'Coimbatore',state:'Tamil Nadu',interests:['Tomato'],joined:'2025-11-02'}),
  user({id:'b10',role:'buyer',name:'Davanagere Food Works',contact:'Manjunath H',email:'davanagere@demo.in',pass:'buyer123',phone:'9900000010',business:'Food Processor',city:'Davanagere',district:'Davanagere',state:'Karnataka',interests:['Onion','Potato'],joined:'2025-11-08'}),
  user({id:'a1',role:'admin',name:'Platform Admin',email:'admin@demo.in',pass:'admin123',phone:'9000000000',joined:'2025-01-01'})
 ];
 /* id, farmer, name, crop, qty (kg), ask (₹/kg), grade, status, district, days since harvest */
 const L=[
  ['l1','f1','Hybrid Tomato','Tomato',1200,24,'A','active','Kolar',2],
  ['l2','f1','Desi Onion','Onion',800,19,'B','sold','Kolar',5],
  ['l3','f2','Organic Tomato','Tomato',600,27,'A','sold','Chikkaballapur',1],
  ['l4','f2','Kufri Potato','Potato',1500,17,'B','active','Chikkaballapur',8],
  ['l5','f3','Round Tomato','Tomato',900,22,'B','active','Tumakuru',3],
  ['l6','f3','Red Onion','Onion',1100,21,'A','paused','Tumakuru',10],
  ['l7','f4','Cherry Tomato','Tomato',300,34,'A','sold','Mandya',1],
  ['l8','f4','Agria Potato','Potato',1000,18,'C','active','Mandya',12],
  ['l9','f5','Local Tomato','Tomato',750,20,'C','active','Hassan',4],
  ['l10','f5','Bellary Onion','Onion',1300,18,'B','sold','Hassan',15],
  ['l11','f6','Hybrid Tomato','Tomato',1000,25,'A','active','Mysuru',2],
  ['l12','f6','Kufri Jyoti Potato','Potato',700,16,'B','active','Mysuru',6],
  ['l13','f7','Country Tomato','Tomato',500,23,'B','active','Ramanagara',2],
  ['l14','f7','Nasik Onion','Onion',900,22,'A','active','Ramanagara',4],
  ['l15','f8','Plum Tomato','Tomato',400,29,'A','active','Kolar',1],
  ['l16','f8','Chips Grade Potato','Potato',1200,19,'A','active','Kolar',7],
  ['l17','f9','Sun Ripe Tomato','Tomato',650,26,'A','active','Chikkaballapur',2],
  ['l18','f9','Small Onion','Onion',600,15,'C','withdrawn','Chikkaballapur',20],
  ['l19','f10','Bulk Tomato','Tomato',1400,21,'B','active','Tumakuru',3],
  ['l20','f10','Bulk Potato','Potato',2000,15,'C','active','Tumakuru',9]
 ].map(([id,farmer,name,crop,qty,ask,grade,status,district,ago])=>({id,farmer,name,crop,qty,ask,grade,status,district,harvest:daysAgo(ago),listedAt:daysAgo(Math.max(ago-1,0)),conf:grade==='A'?92:grade==='B'?84:72,img:null,unit:'kg'}));
 /* id, listing, initiator role, price (₹/kg), qty, status, by, stage, paid, buyer id, time */
 const D=[
  ['d1','l1','buyer',25,500,'pending','buyer',null,false,'b1','13 Nov, 09:12'],
  ['d2','l1','buyer',24,300,'counter','farmer',null,false,'b2','13 Nov, 10:40'],
  ['d3','l2','farmer',19.5,400,'pending','farmer',null,false,'b5','13 Nov, 11:05'],
  ['d4','l3','buyer',27,200,'accepted','buyer','dispatched',false,'b1','12 Nov, 15:20'],
  ['d5','l7','buyer',34,100,'accepted','buyer','delivered',true,'b6','11 Nov, 12:02'],
  ['d6','l10','buyer',18,1300,'accepted','buyer','confirmed',false,'b7','10 Nov, 17:45'],
  ['d7','l11','buyer',22,400,'rejected','buyer',null,false,'b4','09 Nov, 08:30'],
  ['d8','l2','buyer',19.5,800,'accepted','buyer','delivered',true,'b2','08 Nov, 14:10'],
  ['d9','l16','buyer',19,500,'pending','buyer',null,false,'b9','14 Nov, 08:05']
 ].map(([id,listing,initiator,price,qty,status,by,stage,paid,buyerId,t])=>{
  const li=L.find(x=>x.id===listing);
  return {id,listing,farmerId:li.farmer,buyerId,initiator,price,qty,status,by,stage,paid,t,message:'',rounds:status==='counter'?2:1};
 });
 return{
  users,listings:L,deals:D,
  assess:[{id:'A1',farmer:'f1',crop:'Tomato',name:'Hybrid Tomato',grade:'A',conf:91,uniformity:88,defects:3,brightness:62,ripeness:'Ripe (stage 4 of 6)',img:null,saved:true,t:'12 Nov, 16:30'}],
  lastAssess:'A1',
  draft:{crop:'Tomato',name:'',qty:'',unit:'kg',harvest:daysAgo(1),district:'Kolar',img:null},
  saved:['l4','l11'],savedFarmers:['f3'],viewed:[],
  messages:[],
  platform:{requireVerifiedBuyers:true,showApproxDistance:true},
  session:null,
  nav:'overview',
  log:['Sample data loaded','Platform started in demonstration mode']
 };
}
function load(){try{const s=JSON.parse(localStorage.getItem(KEY));if(s&&s.users&&s.listings&&s.deals)return s}catch(e){}return seed()}
function save(){try{localStorage.setItem(KEY,JSON.stringify(db));return true}catch(e){return false}}
let db=load();

/* ---------- Transient UI state (not persisted) ---------- */
let F={q:'',grade:'',crop:'',sort:'distance',tab:'all',minP:'',maxP:'',district:'',minQ:''};
let PR={crop:'Tomato',mkt:MARKETS[0],district:'Bengaluru Urban',range:12};
let NB={tab:'nearby',sort:'distance'};
let SEARCH='';
let POP=null;
let REG_ROLE='farmer';
let CHARTS=[];

/* ---------- Accessors ---------- */
const me=()=>(db.users&&db.users.find(u=>u.id===db.session))||(db.users&&db.users[0]);
const userById=id=>(db.users&&db.users.find(u=>u.id===id||u.email===id))||{id:id||'u_partner',name:'Verified Buyer / Partner',farm:'Partner Farm',village:'Mulbagal',city:'Kolar',district:'Kolar',state:'Karnataka'};
const listingOf=id=>(db.listings&&db.listings.find(l=>l.id===id))||{id:id||'l_produce',name:'Fresh Farm Produce (Grade A)',crop:'Tomato',qty:1000,ask:28,grade:'A',conf:95,district:'Kolar'};
const dealsOn=lid=>(db.deals||[]).filter(d=>d.listing===lid);
const log=m=>{db.log.unshift(new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'})+' · '+m);db.log=db.log.slice(0,60)};
const myListings=()=>(db.listings||[]).filter(l=>l.farmer===db.session||(me()&&l.farmer===me().id)||l.farmer==='f1');

/* ---------- Theme ---------- */
const getTheme=()=>{try{return localStorage.getItem(THEME_KEY)||'system'}catch(e){return 'system'}};
function applyTheme(t){
 const dark=t==='dark'||(t==='system'&&window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches);
 document.documentElement.dataset.theme=dark?'dark':'light';
 document.documentElement.dataset.themeChoice=t;
}
function setTheme(t){try{localStorage.setItem(THEME_KEY,t)}catch(e){}applyTheme(t)}

/* Reads an image file and returns a downsized JPEG data URL, so it fits in browser storage. */
function readImage(file){
 return new Promise((res,rej)=>{
  const r=new FileReader();
  r.onerror=()=>rej(r.error);
  r.onload=()=>{
   const img=new Image();
   img.onload=()=>{
    const s=Math.min(1,900/Math.max(img.width,img.height));
    const c=document.createElement('canvas');
    c.width=Math.round(img.width*s);c.height=Math.round(img.height*s);
    c.getContext('2d').drawImage(img,0,0,c.width,c.height);
    res(c.toDataURL('image/jpeg',.85));
   };
   img.onerror=()=>rej(new Error('not an image'));
   img.src=r.result;
  };
  r.readAsDataURL(file);
 });
}
