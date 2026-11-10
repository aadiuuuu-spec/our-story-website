let auth = "";
const $=id=>document.getElementById(id);
async function request(url,opts={}) { opts.headers={...(opts.headers||{}),Authorization:"Basic "+auth}; return fetch(url,opts); }
$("login").onclick=async()=>{
  auth=btoa(unescape(encodeURIComponent($("username").value+":"+$("password").value)));
  try {
    const r=await request("/api/admin/check");
    if(!r.ok) throw new Error(r.status===503?"Set WEB_ADMIN_PASSWORD on the server first.":"Login failed. Check username/password.");
    sessionStorage.setItem("ourStoryAuth",auth); await loadPanel();
  } catch(e){$("loginStatus").textContent=e.message;}
};
async function loadPanel(){
  const r=await request("/api/story"); if(!r.ok) return;
  const data=await r.json();
  ["chapter","clearChapter"].forEach(id=>$(id).innerHTML=data.chapters.map(c=>`<option value="${c.id}">${c.title}</option>`).join(""));
  $("loginCard").classList.add("hidden"); $("panel").classList.remove("hidden");
}
$("upload").onclick=async()=>{
  const f=$("file").files[0]; if(!f){$("panelStatus").textContent="Choose a file first.";return;}
  const fd=new FormData();fd.append("chapter_id",$("chapter").value);fd.append("caption",$("caption").value);fd.append("file",f);
  const r=await request("/api/admin/upload",{method:"POST",body:fd}); const d=await r.json();
  $("panelStatus").textContent=r.ok?( $("chapter").value==="__surprise__" ? "Surprise media saved! It will appear in A Little Surprise." : "Saved! It is now available on the website and Telegram bot."):(d.detail||"Upload failed.");\n  if(r.ok){$("file").value="";$("caption").value="";}
};
$("addText").onclick=async()=>{
  const fd=new FormData();fd.append("text",$("surpriseText").value);
  const r=await request("/api/admin/text",{method:"POST",body:fd});const d=await r.json();
  $("panelStatus").textContent=r.ok?"Surprise message saved.":(d.detail||"Could not save.");
  if(r.ok)$("surpriseText").value="";
};
$("clear").onclick=async()=>{
  if(!confirm("Delete all saved media for this chapter?"))return;
  const fd=new FormData();fd.append("chapter_id",$("clearChapter").value);
  const r=await request("/api/admin/clear",{method:"POST",body:fd});const d=await r.json();
  $("panelStatus").textContent=r.ok?"Chapter media cleared.":(d.detail||"Could not clear.");
};
auth=sessionStorage.getItem("ourStoryAuth")||"";
if(auth) loadPanel();
