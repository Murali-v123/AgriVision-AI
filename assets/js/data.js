/* Config, sample data, icons, persistence and helpers.
   Replace load()/save() and the db mutations with API calls when the backend exists. */
const BASE=(window.AV_PAGE&&window.AV_PAGE.base)||'';
const PAGES={
 farmer:{overview:'dashboard.html',produce:'my-produce.html',inspect:'quality-inspection.html',price:'price-intelligence.html',market:'marketplace.html',bids:'bids.html',sales:'sales-history.html'},
 buyer:{overview:'dashboard.html',explore:'explore.html',mybids:'my-bids.html',saved:'saved-listings.html',purchases:'purchases.html'},
 admin:{overview:'dashboard.html',users:'users.html',moderation:'moderation.html',activity:'activity.html'}
};
const goTo=(view,role)=>{location.href=BASE+role+'/'+PAGES[role][view]};

/* ---------- Sample data (replace with model and market feeds) ---------- */
const KEY='agrivision-demo-v2';
const $=(s,r=document)=>r.querySelector(s);
const fmt=n=>'₹'+Math.round(Number(n)).toLocaleString('en-IN');
const num=n=>Number(n).toLocaleString('en-IN');
const TRANS_RATE=8.5;     // sample: ₹ per quintal per km
const REF_PRICE=1800;     // sample mandi reference, ₹ per quintal
const REC_PRICE=1880;     // sample suggested selling price, ₹ per quintal
const PRED_RANGE=[1750,2010];
const PRED_CONF=78;       // sample forecast confidence, %
const MODEL_CONF=94;      // sample model confidence, %
const HM=['Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov'];
const HP=[1520,1610,1700,1640,1580,1690,1750,1830,1790,1720,1760,1800];
const PM=['Dec*','Jan*','Feb*'],PP=[1840,1890,1870];
const CROPS=['Tomato','Onion','Potato','Brinjal'];
const MARKETS=['Bengaluru APMC','Kolar APMC','Chennai Koyambedu'];
const FARM_LOCS=['Kolar, Karnataka','Chikkaballapur, Karnataka','Tumakuru, Karnataka'];
const DEMAND=[['Bengaluru Urban',92],['Chennai',83],['Kolar',61],['Hubballi',55],['Mysuru',48]];
const DISTRICTS=['Bagalkot','Ballari','Belagavi','Bengaluru Rural','Bengaluru Urban','Bidar','Chamarajanagar','Chikkaballapur','Chikkamagaluru','Chitradurga','Dakshina Kannada','Davanagere','Dharwad','Gadag','Hassan','Haveri','Kalaburagi','Kodagu','Kolar','Koppal','Mandya','Mysuru','Raichur','Ramanagara','Shivamogga','Tumakuru','Udupi','Uttara Kannada','Vijayapura','Yadgir','Vijayanagara'];

/* Navigation: [view, label, icon, short label for the mobile tab bar] */
const NAV={
 farmer:[['overview','Overview','overview','Home'],['produce','My produce','leaf','Produce'],['inspect','AI quality check','scan','Check'],['price','Price intelligence','trend','Prices'],['market','Marketplace','store','Market'],['bids','Bids','tag','Bids'],['sales','Sales history','receipt','Sales']],
 buyer:[['overview','Overview','overview','Home'],['explore','Explore produce','store','Explore'],['mybids','My bids','tag','Bids'],['saved','Saved listings','heart','Saved'],['purchases','Purchase history','receipt','Purchases']],
 admin:[['overview','Overview','overview','Home'],['users','Users','users','Users'],['moderation','Listing moderation','shield','Moderate'],['activity','Activity','activity','Activity']]
};

/* ---------- Icons (stroke-based, 24px grid) ---------- */
const ICONS={
 overview:'<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
 leaf:'<path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14z"/><path d="M5 19l8-8"/>',
 scan:'<path d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2"/><path d="M4 12h16"/>',
 trend:'<polyline points="3 17 9 11 13 15 21 7"/><polyline points="15 7 21 7 21 13"/>',
 store:'<path d="M4 10v10h16V10"/><path d="M3 10l1.5-6h15L21 10a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z"/>',
 tag:'<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.2"/>',
 receipt:'<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>',
 users:'<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20c0-2.6-1.4-4.6-3.5-5.5"/>',
 shield:'<path d="M12 3l8 3v6c0 4.8-3.4 8.2-8 9-4.6-.8-8-4.2-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
 activity:'<polyline points="3 12 7 12 10 5 14 19 17 12 21 12"/>',
 heart:'<path d="M12 20s-7.5-4.6-9.2-9.2C1.6 7.7 3.8 4.5 7.2 4.5c2 0 3.5 1.2 4.8 2.8 1.3-1.6 2.8-2.8 4.8-2.8 3.4 0 5.6 3.2 4.4 6.3C19.5 15.4 12 20 12 20z"/>',
 upload:'<path d="M12 16V4"/><path d="M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
 check:'<path d="M5 12.5l4.5 4.5L19 7.5"/>',
 close:'<path d="M6 6l12 12M18 6L6 18"/>',
 logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5M21 12H9"/>',
 pin:'<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>'
};
const icon=(n,cls='')=>`<svg class="ic ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[n]||''}</svg>`;

/* Crop colours for placeholder tiles (used until a real photo exists) */
const CROP_STYLE={Tomato:['#B5452F','#FBE9E4'],Onion:['#7A4D9A','#F2EAF7'],Potato:['#8C6A2D','#F6EFDF'],Brinjal:['#4A3D7E','#EBE8F6']};
function cropTile(crop,px){
 const [c,b]=CROP_STYLE[crop]||['#2E6B53','#E3F1E7'];
 const size=px?`width:${px}px;height:${px}px;font-size:${Math.round(px*.42)}px;`:'';
 return `<span class="tile ${px?'':'full'}" style="${size}background:${b};color:${c}" aria-hidden="true">${esc(crop[0])}</span>`;
}

/* ---------- Seed data ---------- */
function seed(){
 return{
  users:[
   {id:'f1',role:'farmer',name:'Ramesh Kumar',email:'ramesh@demo.in',pass:'farmer123',loc:'Kolar, Karnataka',phone:'9800000001'},
   {id:'b1',role:'buyer',name:'FreshMart Wholesale',email:'buyer@demo.in',pass:'buyer123',loc:'Bengaluru',verified:true},
   {id:'b2',role:'buyer',name:'Bharat Fresh Foods',email:'bharat@demo.in',pass:'buyer123',loc:'Hosur',verified:true},
   {id:'b3',role:'buyer',name:'Annapurna Processing',email:'annapurna@demo.in',pass:'buyer123',loc:'Chennai',verified:false},
   {id:'a1',role:'admin',name:'Platform Admin',email:'admin@demo.in',pass:'admin123',loc:'Bengaluru'}
  ],
  listings:[{id:'L1',farmer:'f1',crop:'Tomato',qty:100,grade:'A',loc:'Kolar',ask:1800,status:'active',verified:true}],
  bids:[
   {id:'B1',listing:'L1',buyerId:'b1',buyer:'FreshMart Wholesale',price:1850,qty:100,deliver:'Bengaluru APMC',t:'14 Nov, 09:12',status:'pending'},
   {id:'B2',listing:'L1',buyerId:'b2',buyer:'Bharat Fresh Foods',price:1820,qty:80,deliver:'Hosur',t:'14 Nov, 10:40',status:'pending'},
   {id:'B3',listing:'L1',buyerId:'b3',buyer:'Annapurna Processing',price:1790,qty:100,deliver:'Chennai',t:'14 Nov, 11:05',status:'pending'}
  ],
  saved:[],log:['Sample data loaded'],session:null,
  insp:{crop:'Tomato',qty:100,loc:'Kolar, Karnataka',st:'idle',img:null,ask:REF_PRICE}
 };
}
function load(){try{const s=JSON.parse(localStorage.getItem(KEY));if(s&&s.users&&s.listings)return s}catch(e){}return seed()}
function save(){try{localStorage.setItem(KEY,JSON.stringify(db));return true}catch(e){return false}}
let db=load();
let F={q:'',loc:'',grade:'',minQ:'',sort:'asc'};
let PR={crop:'Tomato',mkt:MARKETS[0],range:12,bl:null};
let CH={};
const me=()=>db.users.find(u=>u.id===db.session);
const userById=id=>db.users.find(u=>u.id===id);
const log=m=>{db.log.unshift(new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'})+' · '+m);db.log=db.log.slice(0,40)};
const listingOf=id=>db.listings.find(l=>l.id===id);
const bidsOn=lid=>db.bids.filter(b=>b.listing===lid);
const myListings=()=>db.listings.filter(l=>l.farmer===db.session);
const stamp=()=>new Date().toLocaleString('en-IN',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
function movement(){
 const last=HP[HP.length-1],prev=HP[HP.length-2],pct=(last-prev)/prev*100;
 return{pct,up:pct>=0,text:(pct>=0?'▲ ':'▼ ')+Math.abs(pct).toFixed(1)+'%'};
}

/* ---------- Helpers ---------- */
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function toast(msg,ok){const t=document.createElement('div');t.className='toast'+(ok?' ok':'');t.setAttribute('role','status');t.textContent=msg;$('#toasts').appendChild(t);setTimeout(()=>t.remove(),2800)}
function openM(html){const m=$('#modal');m.innerHTML=`<div class="mbox" role="dialog" aria-modal="true"><button class="x" data-act="closem" aria-label="Close">${icon('close')}</button>${html}</div>`;m.classList.add('open')}
function closeM(){$('#modal').classList.remove('open')}
/* Downscale a picked photo to JPEG so it fits in browser storage. */
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
