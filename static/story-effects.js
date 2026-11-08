/* OUR STORY interactive effects. Load AFTER app.js. */
(()=>{
"use strict";
const $=s=>document.querySelector(s),title=$("#chapterTitle"),body=$("#chapterText");
if(!title||!body)return;
const reduced=matchMedia("(prefers-reduced-motion: reduce)").matches;
let last="",tap=0,timer=null,typing=null;
const wait=n=>new Promise(r=>setTimeout(r,n));
function kicker(){
document.querySelector(".os-kicker")?.remove();
const k=document.createElement("div");k.className="os-kicker";
k.textContent="A LITTLE UNIVERSE, MADE FOR TWO";title.parentNode.insertBefore(k,title);
}
function typeText(){
if(reduced)return;clearInterval(typing);
const full=body.textContent||"";if(full.length<45||full.length>1600)return;
body.textContent="";const cursor=document.createElement("span");cursor.textContent="▍";body.append(cursor);
let i=0;typing=setInterval(()=>{if(!cursor.isConnected){clearInterval(typing);return}
cursor.insertAdjacentText("beforebegin",full.slice(i,i+2));i+=2;
if(i>=full.length){clearInterval(typing);cursor.remove()}},18);
}
async function scan(){
document.querySelector(".os-scan")?.remove();
const box=document.createElement("div");box.className="os-scan";
box.innerHTML='<div>♡ HEART DATABASE // PRIVATE ARCHIVE</div><div class="bar"><div class="fill"></div></div><span class="status">Initializing heart connection...</span><span class="percent">0%</span>';
body.insertAdjacentElement("afterend",box);
const fill=box.querySelector(".fill"),status=box.querySelector(".status"),pct=box.querySelector(".percent");
for(const [n,msg] of [[7,"Waking up old memories..."],[18,"Checking tiny moments..."],[32,"Reading the unsent smiles..."],[46,"Verifying heart signals..."],[61,"Matching unforgettable memories..."],[78,"Checking forever access..."],[92,"Almost found the answer..."],[100,"MATCH FOUND // ONE NAME ONLY"]]){
if(!box.isConnected)return;fill.style.width=n+"%";pct.textContent=n+"%";status.textContent=msg;await wait(reduced?0:420)}
status.textContent="SAMRIDDHI ❤️ — Permanent place in this story.";
}
function update(){
const key=(title.textContent+" "+body.textContent.slice(0,100)).toLowerCase();
if(!key.trim()||key===last)return;last=key;kicker();
title.classList.remove("os-enter");void title.offsetWidth;title.classList.add("os-enter");
body.classList.remove("os-enter");void body.offsetWidth;body.classList.add("os-enter");
document.querySelector(".os-scan")?.remove();
if(/scan|search|database|heart owner/.test(key))scan();else typeText();
}
new MutationObserver(update).observe(title,{childList:true,subtree:true,characterData:true});
new MutationObserver(update).observe(body,{childList:true,subtree:true,characterData:true});
update();
document.addEventListener("click",e=>{
if(!e.target.closest("button,a,#chapterNav,#openStory"))return;
for(let i=0;i<5;i++){const h=document.createElement("span");h.className="os-heart-burst";
h.textContent=["♡","♥","✦"][i%3];h.style.left=e.clientX+"px";h.style.top=e.clientY+"px";
h.style.setProperty("--dx",((Math.random()-.5)*110)+"px");h.style.setProperty("--dy",(-25-Math.random()*95)+"px");
document.body.append(h);setTimeout(()=>h.remove(),1200)}
});
title.addEventListener("click",()=>{
tap++;clearTimeout(timer);timer=setTimeout(()=>tap=0,1800);if(tap<7)return;tap=0;
const layer=document.createElement("div");layer.className="os-secret";
layer.innerHTML='<div class="os-secret-card"><div>✦ SECRET MEMORY UNLOCKED ✦</div><h2>Only You.</h2><p>Out of all the moments this world could have given me, I would still choose the ones that led me to you. ♡</p><button type="button">Keep this secret</button></div>';
layer.addEventListener("click",e=>{if(e.target===layer||e.target.tagName==="BUTTON")layer.remove()});document.body.append(layer);
});
})();