let auth = "";
const $ = id => document.getElementById(id);
async function request(url, opts = {}) {
  opts.headers = { ...(opts.headers || {}), Authorization: "Basic " + auth };
  return fetch(url, opts);
}
$("login").onclick = async () => {
  auth = btoa(unescape(encodeURIComponent($("username").value + ":" + $("password").value)));
  try {
    const r = await request("/api/admin/check");
    if (!r.ok) throw new Error(r.status === 503 ? "Set WEB_ADMIN_PASSWORD on the server first." : "Login failed. Check username/password.");
    sessionStorage.setItem("ourStoryAuth", auth);
    await loadPanel();
  } catch (e) { $("loginStatus").textContent = e.message; }
};
async function loadPanel() {
  const r = await request("/api/story");
  if (!r.ok) return;
  const data = await r.json();
  const options = data.chapters.map(c => `<option value="${c.id}">${c.title}</option>`).join("");
  $("chapter").innerHTML = options + '<option value="__surprise__">💌 A Little Surprise</option>';
  $("clearChapter").innerHTML = options + '<option value="__surprise__">💌 A Little Surprise</option>';
  $("loginCard").classList.add("hidden");
  $("panel").classList.remove("hidden");
}
async function uploadFile(fileInputId, captionInputId, chapterId) {
  const file = $(fileInputId).files[0];
  if (!file) { $("panelStatus").textContent = "Choose a file first."; return; }
  const fd = new FormData();
  fd.append("chapter_id", chapterId);
  fd.append("caption", $(captionInputId).value);
  fd.append("file", file);
  const r = await request("/api/admin/upload", { method: "POST", body: fd });
  const data = await r.json();
  $("panelStatus").textContent = r.ok
    ? (chapterId === "__surprise__" ? "💌 Surprise media added successfully!" : "Memory uploaded successfully!")
    : (data.detail || "Upload failed.");
  if (r.ok) { $(fileInputId).value = ""; $(captionInputId).value = ""; }
}
$("upload").onclick = () => uploadFile("file", "caption", $("chapter").value);
$("uploadSurprise").onclick = () => uploadFile("surpriseFile", "surpriseCaption", "__surprise__");
$("addText").onclick = async () => {
  const fd = new FormData();
  fd.append("text", $("surpriseText").value);
  const r = await request("/api/admin/text", { method: "POST", body: fd });
  const data = await r.json();
  $("panelStatus").textContent = r.ok ? "Surprise message saved." : (data.detail || "Could not save.");
  if (r.ok) $("surpriseText").value = "";
};
$("clear").onclick = async () => {
  if (!confirm("Delete all saved media for this chapter?")) return;
  const fd = new FormData();
  fd.append("chapter_id", $("clearChapter").value);
  const r = await request("/api/admin/clear", { method: "POST", body: fd });
  const data = await r.json();
  $("panelStatus").textContent = r.ok ? "Selected media cleared." : (data.detail || "Could not clear.");
};
auth = sessionStorage.getItem("ourStoryAuth") || "";
if (auth) loadPanel();
