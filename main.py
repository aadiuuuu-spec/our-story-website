import json
import os
import secrets
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
DATA_FILE = Path(os.getenv("STORY_DATA_FILE", ROOT / "story_media.json"))
UPLOAD_DIR = Path(os.getenv("STORY_UPLOAD_DIR", ROOT / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ADMIN_USER = os.getenv("WEB_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD", "")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "30"))

CHAPTERS = [
    {"id":"place","title":"The Place That Changed My Life Forever","text":"The place that changed my life forever...\n\n📍 PLACE: “Shining Stars”"},
    {"id":"meeting","title":"How Could We Meet?","text":"Some stories begin with a hello. Ours became my favourite story. ❤️\n\n🎧 Here are the two voice notes from that special memory."},
    {"id":"yes","title":"The Beautiful “Yes” I'll Never Forget","text":"🗓 10th October · 7:17 PM\n\n“And my world changed forever.” ❤️"},
    {"id":"moments","title":"The Moments That Became My Favourite Chapter","text":"• Your love and caring\n• Staying up late to talk to you\n• Roasting each other 😂\n\nThese little moments mean the world to me."},
    {"id":"numbers","title":"Our Love In Numbers","text":"We could never explain our love in numbers...\n\nBecause some feelings are simply beyond counting. ♾️"},
    {"id":"eyes","title":"Where Did I Get Lost?","text":"Where did I get lost?\n\nIn your eyes. 👀❤️"},
    {"id":"stats","title":"❤️ Love Statistics","text":"Messages          1+\nLate Night Talks  Countless\nLaughter           ∞\nLove               ❤️ ∞\nMiss You           🥺 99999999999999+\nHugs               🤗 Loading...\nKisses             Loading...\nForever            ♾️ Confirmed"},
    {"id":"scan","title":"Scanning Heart Database...","text":"[██████████] 100%\n\n❤️ RESULT ❤️\n\nCurrent Heart Owner: Samriddhi\nStatus: Permanent Access Granted ❤️\nNo Replacement Found."},
    {"id":"speak","title":"If Love Could Speak...","text":"Even if I had a thousand lives,\nI would still search for you,\nFind you,\nFall for you,\nAnd choose you...\nAgain.\nAnd again.\nForever. ❤️"},
    {"id":"shayari","title":"Final Shayari","text":"Some moments fade like passing clouds,\nOurs quietly built a home.\nOut of all the paths the world could take,\nYours is the one I call my own.\nThrough every quiet sunrise and midnight turn,\nIn a crowded room or under an open sky,\nThe world can rush all it wants—\nMy calm will always begin with you. ✨"},
    {"id":"month","title":"One Month Of Our Relationship ❤️","text":"One month of our relationship will be completed. ❤️\n\nThank you for every smile.\nEvery memory.\nEvery moment.\nEvery piece of love.\n\nI love you.\nForever."},
    {"id":"ending","title":"Successfully Connected","text":"Connection Lost...\n⬇️ Searching New Heart Owner...\n❌ No Better Person Found.\n⬇️ Reconnecting...\n\n██████████ 100%\n\n❤️ Successfully Connected To\n\nSamriddhi\n\nForever ♾️"},
]
SURPRISE_KEY = "__surprise__"

app = FastAPI(title="Our Story ❤️")
security = HTTPBasic()

def load_db():
    try:
        value = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

def save_db(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, DATA_FILE)

def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="Set WEB_ADMIN_PASSWORD before using the admin panel.")
    valid_user = secrets.compare_digest(credentials.username.encode(), ADMIN_USER.encode())
    valid_pass = secrets.compare_digest(credentials.password.encode(), ADMIN_PASSWORD.encode())
    if not (valid_user and valid_pass):
        raise HTTPException(status_code=401, detail="Incorrect admin username or password.",
                            headers={"WWW-Authenticate": "Basic"})
    return True

def public_item(item):
    result = {"kind": item.get("kind", "unknown"), "caption": item.get("caption", "")}
    if item.get("local_path"):
        path = Path(item["local_path"])
        if path.exists():
            result["url"] = "/uploads/" + path.name
    # Telegram file_id media can only be displayed inside Telegram, not directly in a browser.
    return result

@app.get("/api/story")
def get_story():
    db = load_db()
    media = {}
    for key, items in db.items():
        media[key] = [public_item(x) for x in items if isinstance(x, dict)]
    return {
        "name": os.getenv("GIRLFRIEND_NAME", "Samriddhi"),
        "chapters": CHAPTERS,
        "media": media,
        "surprise_key": SURPRISE_KEY
    }

@app.get("/api/admin/check")
def admin_check(_=Depends(require_admin)):
    return {"ok": True}

@app.post("/api/admin/upload")
async def upload_media(
    chapter_id: str = Form(...),
    caption: str = Form(""),
    file: UploadFile = File(...),
    _=Depends(require_admin)
):
    valid_ids = {c["id"] for c in CHAPTERS} | {SURPRISE_KEY, "__hug_stickers__"}
    if chapter_id not in valid_ids:
        raise HTTPException(status_code=400, detail="Unknown story chapter.")
    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum is {MAX_UPLOAD_MB} MB.")
    ext = Path(file.filename or "").suffix[:12]
    safe_name = f"{uuid.uuid4().hex}{ext}"
    destination = UPLOAD_DIR / safe_name
    destination.write_bytes(content)
    mime = (file.content_type or "").lower()
    if mime.startswith("image/"):
        kind = "photo"
    elif mime.startswith("video/"):
        kind = "video"
    elif mime.startswith("audio/"):
        kind = "audio"
    elif ext.lower() == ".gif":
        kind = "animation"
    else:
        kind = "document"
    db = load_db()
    db.setdefault(chapter_id, []).append({
        "kind": kind, "local_path": str(destination.resolve()), "caption": caption
    })
    save_db(db)
    return {"ok": True, "kind": kind, "filename": safe_name}

@app.post("/api/admin/text")
def add_surprise_text(text: str = Form(...), _=Depends(require_admin)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Please enter some text.")
    db = load_db()
    db.setdefault(SURPRISE_KEY, []).append({"kind": "text", "text": text.strip()})
    save_db(db)
    return {"ok": True}

@app.post("/api/admin/clear")
def clear_chapter(chapter_id: str = Form(...), _=Depends(require_admin)):
    db = load_db()
    db.pop(chapter_id, None)
    save_db(db)
    return {"ok": True}

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/admin")
def admin_page():
    return FileResponse(ROOT / "static" / "admin.html")
