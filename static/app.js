let storyData, current = 0;
const $ = (id) => document.getElementById(id);
function escapeHtml(s="") { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
async function init() {
  const r = await fetch("/api/story");
  storyData = await r.json();
  $("name").textContent = storyData.name || "Samriddhi";
  $("chapterNav").innerHTML = storyData.chapters.map((c,i)=>`<button class="nav-chapter ${i===0?'active':''}" data-i="${i}"><span>${String(i+1).padStart(2,'0')}</span>${escapeHtml(c.title)}</button>`).join("");
  document.querySelectorAll(".nav-chapter").forEach(b=>b.addEventListener("click",()=>show(Number(b.dataset.i))));
  show(0);
}
function show(i) {
  current = Math.max(0, Math.min(i, storyData.chapters.length-1));
  const c = storyData.chapters[current];
  $("chapterCount").textContent = `CHAPTER ${String(current+1).padStart(2,'0')} / ${String(storyData.chapters.length).padStart(2,'0')}`;
  $("chapterTitle").textContent = c.title;
  $("chapterText").textContent = c.text;
  $("chapterMedia").innerHTML = "";
  const items = (storyData.media[c.id] || []);
  items.forEach(item=>{
    if (!item.url) return;
    const el = document.createElement(item.kind==="video" ? "video" : item.kind==="audio" ? "audio" : "img");
    el.src = item.url;
    if (el.tagName==="VIDEO") { el.controls=true; el.playsInline=true; }
    if (el.tagName==="AUDIO") el.controls=true;
    if (el.tagName==="IMG") el.alt = item.caption || "A memory";
    $("chapterMedia").appendChild(el);
    if (item.caption) { const cap=document.createElement("p"); cap.className="media-caption"; cap.textContent=item.caption; $("chapterMedia").appendChild(cap); }
  });
  document.querySelectorAll(".nav-chapter").forEach((b,n)=>b.classList.toggle("active",n===current));
  $("prev").disabled = current===0;
  $("next").textContent = current===storyData.chapters.length-1 ? "Read again ↻" : "Next page ♡";
  $("chapterTitle").scrollIntoView({behavior:"smooth",block:"center"});
}
$("openStory").addEventListener("click",()=>{ $("story").scrollIntoView({behavior:"smooth"}); show(0); });
$("prev").addEventListener("click",()=>show(current-1));
$("next").addEventListener("click",()=>show(current===storyData.chapters.length-1?0:current+1));
$("surpriseBtn").addEventListener("click",()=>{
  const box=$("surpriseContent"); box.classList.toggle("visible");
  if (!box.dataset.loaded) {
    const items=storyData.media[storyData.surprise_key]||[];
    box.innerHTML = `<p>${escapeHtml(storyData.name)}, if I could save one place to visit whenever life gets loud, it would be right beside you. 🥺</p>` +
      items.map(x=>x.kind==="text"?`<p>${escapeHtml(x.text).replace(/\n/g,"<br>")}</p>`:x.url? (x.kind==="video"?`<video controls src="${x.url}"></video>`:x.kind==="audio"?`<audio controls src="${x.url}"></audio>`:`<img src="${x.url}" alt="Surprise">`):"").join("");
    box.dataset.loaded="1";
  }
});
init().catch(()=>{$("chapterText").textContent="The story could not load. Please refresh the page.";});
