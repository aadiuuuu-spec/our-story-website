import json
import os
import secrets
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
import uvicorn

ROOT = Path(__file__).resolve().parent
DATA_FILE = Path(os.getenv("STORY_DATA_FILE", ROOT / "story_media.json"))
UPLOAD_DIR = Path(os.getenv("STORY_UPLOAD_DIR", ROOT / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ADMIN_USER = os.getenv("WEB_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD", "")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "30"))

CHAPTERS = [
    {"id": "place", "title": "Where Our Story Found Its Spark", "text": "Some places are beautiful, but one place became special because it reminds me of you. ✨\n\nWhenever I think of that moment, I smile without even trying. Maybe it was just a place to everyone else — but to me, it became a page in our story.\n\nAnd if I could relive one little moment, I would happily find my way back to you. ❤️"},
    {"id": "meeting", "title": "The Hello That Started Everything", "text": "I still love thinking about how our paths crossed. One simple hello slowly became my favourite notification, my favourite conversation, and a feeling I never expected.\n\nI didn't know that meeting you would mean this much to me. Now I can't imagine this story without you, Samriddhi. 🦋"},
    {"id": "yes", "title": "The Beautiful “Yes” I'll Never Forget", "text": "10th October · 7:17 PM ❤️\n\nI remember that moment because it gave me a memory I will always keep close. Your yes made an ordinary evening feel unforgettable.\n\nIf I could save that second in a little glass box, I would — just so I could smile at it whenever I miss you. ✨"},
    {"id": "moments", "title": "The Little Things I Adore About You", "text": "It's not only the big moments that make me love you. It's the little things too:\n\n♡ The way you care.\n♡ Our late-night conversations.\n♡ Your random talks and sweet messages.\n♡ The way we tease and roast each other. 😂\n\nEvery small thing becomes special when it's with you. I love all these little pieces of us. ❤️"},
    {"id": "numbers", "title": "A Love Too Big for Numbers", "text": "I could count our messages, our calls, and all the hours we've spent talking — but numbers could never measure what you mean to me.\n\nThere are a thousand reasons to smile, countless memories to make, and one person I want to keep choosing.\n\nThat person is you. ♾️"},
    {"id": "eyes", "title": "Where Did I Get Lost?", "text": "Where did I get lost?\n\nSomewhere between your eyes, your smile, and the way you make even an ordinary day feel softer.\n\nI wasn't looking for a perfect world. I just found someone who makes my world feel a little more beautiful. 👀❤️"},
    {"id": "stats", "title": "Our Little Love Statistics", "text": "Late-night talks       Countless\nShared smiles           Too many to count\nRandom teasing          Always 😂\nMissing you             Every now and then… okay, always 🥺\nReasons to smile        Because of you\nHugs to give            Still waiting 🤗\nKisses to send          A whole lot 💋\nMy favourite person     Samriddhi\nMy love for you         ♾️\n\nThe best part of every statistic? It's ours. ❤️"},
    {"id": "scan", "title": "The One My Heart Keeps Choosing", "text": "If my heart had one favourite answer, it would always be you, Samriddhi. ❤️\n\nI don't love you because every day is perfect. I love you because even ordinary days feel special when I get to share them with you.\n\nI love your smile, your caring nature, your silly side, and all the little things that make you who you are.\n\nOne name. A thousand reasons. And a heart that keeps choosing you. ✨"},
    {"id": "speak", "title": "If Love Could Speak...", "text": "If love could speak, it would tell you how often you cross my mind.\n\nIt would tell you that your smile stays with me long after our conversations end.\n\nIt would say: I may not have the perfect words every time, but my feelings are real.\n\nI love you today, I'll love you through tomorrow, and I'll keep choosing you in all the little ways. ❤️"},
    {"id": "shayari", "title": "A Few Lines, Straight From My Heart", "text": "The world has a million stars above,\nBut you are the one I see.\nAmong a thousand little dreams,\nYou're the sweetest one to me.\n\nIf every heartbeat had a name,\nYour name would softly flow.\nAnd if you ever ask whom I love,\nIt's you — I hope you know. ❤️"},
    {"id": "month", "title": "One More Chapter, A Lifetime to Go", "text": "One month is a small number, but the memories already mean so much to me. ❤️\n\nThank you for every smile, every late-night talk, every silly joke, and every moment you've made brighter.\n\nI know we still have so many pages left to write. I don't need them to be perfect — I just hope we keep filling them with honesty, laughter, care, and love.\n\nI love you, Samriddhi. Here's to our next chapter. ♡"},
    {"id": "ending", "title": "My Favourite Person, My Forever", "text": "Among all the stories life could have written, I'm grateful ours crossed paths. ❤️\n\nYou are my favourite hello, my sweetest thought, and the person behind so many of my smiles.\n\nI can't promise every day will be perfect, but I can promise to keep caring, keep listening, keep making memories, and keep choosing you.\n\nSamriddhi, I love you — more than these little lines can ever explain.\n\nForever starts with the moments we make together. ♾️"}
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
        raise HTTPException(
            status_code=401,
            detail="Incorrect admin username or password.",
            headers={"WWW-Authenticate": "Basic"}
        )
    return True


def public_item(item):
    result = {"kind": item.get("kind", "unknown"), "caption": item.get("caption", "")}
    if item.get("kind") == "text":
        result["text"] = item.get("text", "")
    if item.get("local_path"):
        path = Path(item["local_path"])
        if path.exists():
            result["url"] = "/uploads/" + path.name
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
        "surprise_key": SURPRISE_KEY,
    }


@app.get("/api/admin/check")
def admin_check(_=Depends(require_admin)):
    return {"ok": True}


@app.post("/api/admin/upload")
async def upload_media(
    chapter_id: str = Form(...),
    caption: str = Form(""),
    file: UploadFile = File(...),
    _=Depends(require_admin),
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
