"""
OUR STORY ❤️ — Telegram Love Story Bot
Python 3.10+ | python-telegram-bot 21.x

Termux setup:
    pkg update -y
    pkg install python -y
    pip install "python-telegram-bot==21.10"
    export BOT_TOKEN="YOUR_BOT_TOKEN"
    export OWNER_ID="YOUR_NUMERIC_TELEGRAM_USER_ID"
    export GIRLFRIEND_NAME="Samriddhi"
    python aadi.py

Admin:
    Send /admin to the bot from the OWNER_ID account.
    Choose a story chapter, then send a photo, video, audio, or voice note.
    Use the admin panel to add more media, clear a chapter, or edit the final name.
"""

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("our-story-bot")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID_RAW = os.getenv("OWNER_ID", "").strip()
GIRLFRIEND_NAME = os.getenv("GIRLFRIEND_NAME", "Samriddhi").strip() or "Samriddhi"
# Saved next to main.py (absolute path), so it no longer depends on which folder
# you start the bot from. Override with: export STORY_DATA_FILE="/path/story_media.json"
DATA_FILE = Path(
    os.getenv("STORY_DATA_FILE") or (Path(__file__).resolve().parent / "story_media.json")
)
BACKUP_FILE = DATA_FILE.with_suffix(".json.bak")


# Telegram controls its own app theme; Unicode small-caps style the bot's text.
_SMALL_CAPS = str.maketrans({
    "a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ꜰ","g":"ɢ",
    "h":"ʜ","i":"ɪ","j":"ᴊ","k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ",
    "o":"ᴏ","p":"ᴘ","q":"ǫ","r":"ʀ","s":"ꜱ","t":"ᴛ","u":"ᴜ",
    "v":"ᴠ","w":"ᴡ","x":"x","y":"ʏ","z":"ᴢ",
})

def fancy_heading(value: str) -> str:
    return value.translate(_SMALL_CAPS)

def story_frame(title: str, body: str, page: int, total: int) -> str:
    return (
        "╭━━━━━━━━━━━ ୨♡୧ ━━━━━━━━━━━╮\n"
        f"       ✦ {fancy_heading(title)} ✦\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{body}\n\n"
        "       ♡ ᴏᴜʀ ʟɪᴛᴛʟᴇ ꜰᴏʀᴇᴠᴇʀ ♡\n"
        f"              ᴘᴀɢᴇ {page:02d} / {total:02d}"
    )


def style_text(value: str) -> str:
    """Bold-italic Unicode font (𝑯𝒊𝒊𝒊) for normal bot text. Digits/emoji untouched."""
    out = []
    for ch in value:
        if "A" <= ch <= "Z":
            out.append(chr(0x1D468 + ord(ch) - ord("A")))
        elif "a" <= ch <= "z":
            out.append(chr(0x1D482 + ord(ch) - ord("a")))
        else:
            out.append(ch)
    return "".join(out)


def story_header(title: str) -> str:
    return (
        "╭━━━━━━━━━━━ ୨♡୧ ━━━━━━━━━━━╮\n"
        f"       ✦ {fancy_heading(title)} ✦\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
    )


async def safe_edit(msg, text: str, markup=None) -> None:
    """Edit a message without crashing on flood-limits or 'not modified'."""
    for _ in range(4):
        try:
            await msg.edit_text(text, reply_markup=markup)
            return
        except RetryAfter as e:
            delay = e.retry_after
            delay = delay.total_seconds() if hasattr(delay, "total_seconds") else float(delay)
            await asyncio.sleep(delay + 0.5)
        except BadRequest as e:
            if "not modified" in str(e).lower():
                return
            raise


async def reveal_page(
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    title: str,
    body: str,
    index: int,
    markup,
    framed: bool = True,
    delay: float = 1.0,
) -> None:
    """Print a page line by line (1 sec apart), then add footer + buttons."""
    lines = style_text(body).split("\n")
    head = story_header(title) if framed else ""
    shown: list[str] = []
    msg = None
    i = 0
    while i < len(lines):
        chunk = []
        while i < len(lines) and not lines[i].strip():
            chunk.append(lines[i])
            i += 1
        if i < len(lines):
            chunk.append(lines[i])
            i += 1
        shown.extend(chunk)
        text = head + "\n".join(shown)
        if msg is None:
            msg = await context.bot.send_message(chat_id, text)
        else:
            await asyncio.sleep(delay)
            await safe_edit(msg, text)
    shown_text = "\n".join(shown).rstrip()
    await asyncio.sleep(0.6)
    if framed:
        final = story_frame(title, shown_text, index + 1, len(CHAPTERS))
    else:
        final = shown_text
    await safe_edit(msg, final, markup)


# Extra messages / voice notes for the "A Little Surprise" button (added via /admin).
SURPRISE_KEY = "__surprise__"

# Hug stickers (max 5) are stored in story_media.json under this key.
HUG_KEY = "__hug_stickers__"
HUG_LIMIT = 5
# False = stickers arrive right after the Hugs line finishes.
# True  = stickers arrive after the whole stats page is complete.
HUG_STICKERS_AT_END = False

# (label, animation frames, final value)
STATS_ROWS = [
    ("Messages",         ["3", "4000", "32", "1", "0"],      "1+"),
    ("Late Night Talks", ["0", "12", "500", "7"],            "Countless"),
    ("Laughter",         ["😂 7", "😂 3000", "😂 42"],        "∞"),
    ("Love",             ["❤️ 1", "❤️ 500", "❤️ 9"],         "❤️ ∞"),
    ("Miss You",         ["🥺 9", "🥺 4000", "🥺 99999"],     "🥺 99999999999999+"),
    ("Hugs",             ["🤗 5", "🤗 300", "🤗 0"],          "🤗 Loading..."),
    ("Kisses",           ["💋 8", "💋 1000", "💋 0"],         "Loading..."),
    ("Forever",          ["♾️ 1", "♾️ 50", "♾️ 0"],           "♾️ Confirmed"),
]


def render_stats(rows: list[tuple[str, str]]) -> str:
    return "\n".join(f"{style_text(label):<18}{value}" for label, value in rows)

# Each chapter can have one or more attached media items.
CHAPTERS = [
    {
        "id": "place",
        "title": "Where Our Story Found Its Spark",
        "text": "Some places are beautiful, but one place became special because it reminds me of you. ✨\n\nWhenever I think of that moment, I smile without even trying. Maybe it was just a place to everyone else — but to me, it became a page in our story.\n\nAnd if I could relive one little moment, I would happily find my way back to you. ❤️",
    },
    {
        "id": "meeting",
        "title": "The Hello That Started Everything",
        "text": "I still love thinking about how our paths crossed. One simple hello slowly became my favourite notification, my favourite conversation, and a feeling I never expected.\n\nI didn't know that meeting you would mean this much to me. Now I can't imagine this story without you, Samriddhi. 🦋",
    },
    {
        "id": "yes",
        "title": "The Beautiful “Yes” I'll Never Forget",
        "text": "10th October · 7:17 PM ❤️\n\nI remember that moment because it gave me a memory I will always keep close. Your yes made an ordinary evening feel unforgettable.\n\nIf I could save that second in a little glass box, I would — just so I could smile at it whenever I miss you. ✨",
    },
    {
        "id": "moments",
        "title": "The Little Things I Adore About You",
        "text": "It's not only the big moments that make me love you. It's the little things too:\n\n♡ The way you care.\n♡ Our late-night conversations.\n♡ Your random talks and sweet messages.\n♡ The way we tease and roast each other. 😂\n\nEvery small thing becomes special when it's with you. I love all these little pieces of us. ❤️",
    },
    {
        "id": "numbers",
        "title": "A Love Too Big for Numbers",
        "text": "I could count our messages, our calls, and all the hours we've spent talking — but numbers could never measure what you mean to me.\n\nThere are a thousand reasons to smile, countless memories to make, and one person I want to keep choosing.\n\nThat person is you. ♾️",
    },
    {
        "id": "eyes",
        "title": "Where Did I Get Lost?",
        "text": "Where did I get lost?\n\nSomewhere between your eyes, your smile, and the way you make even an ordinary day feel softer.\n\nI wasn't looking for a perfect world. I just found someone who makes my world feel a little more beautiful. 👀❤️",
    },
    {
        "id": "stats",
        "title": "Our Little Love Statistics",
        "text": "Late-night talks       Countless\nShared smiles           Too many to count\nRandom teasing          Always 😂\nMissing you             Every now and then… okay, always 🥺\nReasons to smile        Because of you\nHugs to give            Still waiting 🤗\nKisses to send          A whole lot 💋\nMy favourite person     Samriddhi\nMy love for you         ♾️\n\nThe best part of every statistic? It's ours. ❤️",
    },
    {
        "id": "scan",
        "title": "The One My Heart Keeps Choosing",
        "text": "If my heart had one favourite answer, it would always be you, Samriddhi. ❤️\n\nI don't love you because every day is perfect. I love you because even ordinary days feel special when I get to share them with you.\n\nI love your smile, your caring nature, your silly side, and all the little things that make you who you are.\n\nOne name. A thousand reasons. And a heart that keeps choosing you. ✨",
    },
    {
        "id": "speak",
        "title": "If Love Could Speak...",
        "text": "If love could speak, it would tell you how often you cross my mind.\n\nIt would tell you that your smile stays with me long after our conversations end.\n\nIt would say: I may not have the perfect words every time, but my feelings are real.\n\nI love you today, I'll love you through tomorrow, and I'll keep choosing you in all the little ways. ❤️",
    },
    {
        "id": "shayari",
        "title": "A Few Lines, Straight From My Heart",
        "text": "The world has a million stars above,\nBut you are the one I see.\nAmong a thousand little dreams,\nYou're the sweetest one to me.\n\nIf every heartbeat had a name,\nYour name would softly flow.\nAnd if you ever ask whom I love,\nIt's you — I hope you know. ❤️",
    },
    {
        "id": "month",
        "title": "One More Chapter, A Lifetime to Go",
        "text": "One month is a small number, but the memories already mean so much to me. ❤️\n\nThank you for every smile, every late-night talk, every silly joke, and every moment you've made brighter.\n\nI know we still have so many pages left to write. I don't need them to be perfect — I just hope we keep filling them with honesty, laughter, care, and love.\n\nI love you, Samriddhi. Here's to our next chapter. ♡",
    },
    {
        "id": "ending",
        "title": "My Favourite Person, My Forever",
        "text": "Among all the stories life could have written, I'm grateful ours crossed paths. ❤️\n\nYou are my favourite hello, my sweetest thought, and the person behind so many of my smiles.\n\nI can't promise every day will be perfect, but I can promise to keep caring, keep listening, keep making memories, and keep choosing you.\n\nSamriddhi, I love you — more than these little lines can ever explain.\n\nForever starts with the moments we make together. ♾️",
    },
]

try:
    OWNER_ID = int(OWNER_ID_RAW)
except (TypeError, ValueError):
    OWNER_ID = 0


def _read_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def load_media() -> dict[str, list[dict[str, str]]]:
    if not DATA_FILE.exists():
        if BACKUP_FILE.exists():
            try:
                data = _read_json(BACKUP_FILE)
                if data is not None:
                    log.warning("Main media file missing; restored from backup.")
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return {}
    try:
        data = _read_json(DATA_FILE)
        if data is not None:
            return data
    except (json.JSONDecodeError, OSError):
        log.exception("Could not read media database.")
    # Main file is broken: keep a copy of it and fall back to the backup.
    try:
        DATA_FILE.replace(DATA_FILE.with_suffix(".json.corrupt"))
    except OSError:
        pass
    try:
        data = _read_json(BACKUP_FILE)
        if data is not None:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def save_media(data: dict[str, list[dict[str, str]]]) -> None:
    # Keep the previous good version as a backup, then write atomically.
    if DATA_FILE.exists():
        try:
            BACKUP_FILE.write_bytes(DATA_FILE.read_bytes())
        except OSError:
            log.exception("Could not write backup file.")
    tmp = DATA_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, DATA_FILE)


def item_key(item: dict[str, str]) -> str:
    """Short stable id for a saved media item (used by the remove buttons)."""
    return hashlib.md5((item.get("file_id") or item.get("text", "")).encode()).hexdigest()[:8]


def is_owner(update: Update) -> bool:
    user = update.effective_user
    return bool(user and OWNER_ID and user.id == OWNER_ID)


def chapter_by_id(chapter_id: str) -> dict[str, Any] | None:
    return next((c for c in CHAPTERS if c["id"] == chapter_id), None)


def story_keyboard(index: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    if index > 0:
        row.append(InlineKeyboardButton("♡ ʙᴀᴄᴋ", callback_data=f"story:{index-1}"))
    if index < len(CHAPTERS) - 1:
        row.append(InlineKeyboardButton("ɴᴇxᴛ ᴘᴀɢᴇ ♡", callback_data=f"story:{index+1}"))
    else:
        row.append(InlineKeyboardButton("↻ ʀᴇʟɪᴠᴇ ᴏᴜʀ ꜱᴛᴏʀʏ ♡", callback_data="story:0"))
    buttons.append(row)
    return InlineKeyboardMarkup(buttons)


thirty_chars = 30


def admin_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for i, chapter in enumerate(CHAPTERS):
        rows.append([
            InlineKeyboardButton(
                f"📎 {i+1}. {chapter['title'][: thirty_chars]}",
                callback_data=f"admin:add:{chapter['id']}",
            )
        ])
    hug_count = len(load_media().get(HUG_KEY, []))
    rows.append([InlineKeyboardButton(
        f"🤗 Add Hug Stickers ({hug_count}/{HUG_LIMIT})", callback_data="admin:hugs"
    )])
    rows.append([InlineKeyboardButton("🗑 Clear Hug Stickers", callback_data="admin:hugs_clear")])
    surprise_count = len(load_media().get(SURPRISE_KEY, []))
    rows.append([InlineKeyboardButton(
        f"💌 Add to Surprise: voice/text ({surprise_count})", callback_data="admin:surprise"
    )])
    rows.append([InlineKeyboardButton("🗑 Clear Surprise", callback_data="admin:surprise_clear")])
    rows.append([InlineKeyboardButton("🗑 Remove One Picture/Item", callback_data="admin:rm_menu")])
    rows.append([InlineKeyboardButton("✕ ᴄʟᴇᴀʀ ᴄʜᴀᴘᴛᴇʀ ᴍᴇᴅɪᴀ", callback_data="admin:clear_menu")])
    rows.append([InlineKeyboardButton("ⓘ ᴀᴅᴍɪɴ ʜᴇʟᴘ", callback_data="admin:help")])
    return InlineKeyboardMarkup(rows)


async def send_media_item(chat_id: int, item: dict[str, str], context: ContextTypes.DEFAULT_TYPE, reply_markup=None) -> None:
    kind = item.get("kind")
    file_id = item.get("file_id")
    local_path = item.get("local_path")
    caption = item.get("caption", "")

    if kind == "text":
        try:
            await context.bot.send_message(
                chat_id, style_text(item.get("text", "")), reply_markup=reply_markup
            )
        except Exception:
            log.exception("Unable to send saved text item.")
        return

    if not local_path and not file_id:
        return

    try:
        # PTB treats strings as Telegram file IDs or URLs, not local filesystem paths.
        # Open website-uploaded files as binary streams before sending them.
        if local_path:
            with open(local_path, "rb") as media_file:
                await _send_telegram_media(
                    chat_id, kind, media_file, caption, reply_markup, context
                )
        else:
            await _send_telegram_media(
                chat_id, kind, file_id, caption, reply_markup, context
            )
    except Exception:
        log.exception("Unable to send saved media item (%s).", kind)


async def _send_telegram_media(chat_id, kind, media, caption, reply_markup, context):
    if kind == "photo":
        await context.bot.send_photo(chat_id, media, caption=caption or None, reply_markup=reply_markup)
    elif kind == "video":
        await context.bot.send_video(chat_id, media, caption=caption or None, reply_markup=reply_markup)
    elif kind == "audio":
        await context.bot.send_audio(chat_id, media, caption=caption or None, reply_markup=reply_markup)
    elif kind == "voice":
        await context.bot.send_voice(chat_id, media, caption=caption or None, reply_markup=reply_markup)
    elif kind == "animation":
        await context.bot.send_animation(chat_id, media, caption=caption or None, reply_markup=reply_markup)
    elif kind == "document":
        await context.bot.send_document(chat_id, media, caption=caption or None, reply_markup=reply_markup)
    elif kind == "sticker":
        await context.bot.send_sticker(chat_id, media, reply_markup=reply_markup)


async def send_hug_stickers(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    for item in load_media().get(HUG_KEY, [])[:HUG_LIMIT]:
        await send_media_item(chat_id, item, context)
        await asyncio.sleep(0.9)


async def show_chapter(
    chat_id: int,
    index: int,
    context: ContextTypes.DEFAULT_TYPE,
    edit_message=None,
) -> None:
    chapter = CHAPTERS[index]
    markup = story_keyboard(index)

    # The heart database chapter gets a live scanning animation.
    if chapter["id"] == "scan":
        progress_message = await context.bot.send_message(
            chat_id,
            "❤️ HEART DATABASE SCAN\n\nConnecting to heart database...\n"
            "□□□□□□□□□□ 0%\n\nPlease wait...",
        )
        for percent in (7, 18, 25, 32, 46, 53, 68, 74, 89, 100):
            filled = percent // 10
            bar = "█" * filled + "□" * (10 - filled)
            status = (
                "Searching memories..." if percent < 40 else
                "Checking heart signals..." if percent < 70 else
                "Verifying permanent connection..." if percent < 100 else
                "Scan complete!"
            )
            await asyncio.sleep(0.55)
            await progress_message.edit_text(
                f"❤️ HEART DATABASE SCAN\n\n{status}\n{bar} {percent}%"
            )
        final_text = (
            f"❤️ RESULT ❤️\n\n"
            f"Current Heart Owner: {GIRLFRIEND_NAME}\n"
            "Status: Permanent Access Granted ❤️\n"
            "No Replacement Found."
        )
        await reveal_page(chat_id, context, chapter["title"], final_text, index, markup, framed=False)
    elif chapter["id"] == "stats":
        progress_message = await context.bot.send_message(
            chat_id, story_header(chapter["title"]) + "Loading..."
        )
        done: list[tuple[str, str]] = []
        for label, frames, final in STATS_ROWS:
            for frame in frames:
                await safe_edit(
                    progress_message,
                    story_header(chapter["title"]) + render_stats(done + [(label, frame)]),
                )
                await asyncio.sleep(0.4)
            done.append((label, final))
            await safe_edit(
                progress_message,
                story_header(chapter["title"]) + render_stats(done),
            )
            await asyncio.sleep(0.5)
            if label == "Hugs" and not HUG_STICKERS_AT_END:
                await send_hug_stickers(chat_id, context)
        await safe_edit(
            progress_message,
            story_frame(chapter["title"], render_stats(done), index + 1, len(CHAPTERS)),
            markup,
        )
        if HUG_STICKERS_AT_END:
            await send_hug_stickers(chat_id, context)
    elif chapter["id"] == "ending":
        # Present the final chapter directly; do not simulate a network outage or search.
        await reveal_page(
            chat_id, context, chapter["title"], chapter["text"], index, markup
        )
    else:
        # Each page is a new message; earlier memories remain visible.
        await reveal_page(chat_id, context, chapter["title"], chapter["text"], index, markup)

    media_db = load_media()
    for item in media_db.get(chapter["id"], []):
        await send_media_item(chat_id, item, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("awaiting_media_for", None)
    welcome = (
        "╭━━━━━━━ ♡ ━━━━━━━╮\n"
        f"       ʜᴇʏ, {GIRLFRIEND_NAME} 🦋\n"
        "╰━━━━━━━ ♡ ━━━━━━━╯\n\n"
        "✧ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴏᴜʀ ʟɪᴛᴛʟᴇ ᴜɴɪᴠᴇʀꜱᴇ ✧\n\n"
        "I saved a few moments here…\n"
        "the laughs, the late-night talks,\n"
        "the little things that became everything.\n\n"
        "♡ Take your time. Every page is for you.\n"
        "      ᴍᴀᴅᴇ ᴡɪᴛʜ ʟᴏᴠᴇ, ᴊᴜꜱᴛ ꜰᴏʀ ʏᴏᴜ ♡"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("♡ ᴏᴘᴇɴ ᴏᴜʀ ᴍᴇᴍᴏʀɪᴇꜱ ♡", callback_data="story:0")],
        [InlineKeyboardButton("✦ ᴀ ʟɪᴛᴛʟᴇ ꜱᴜʀᴘʀɪꜱᴇ ✦", callback_data="surprise")],
    ])
    await update.effective_message.reply_text(style_text(welcome), reply_markup=keyboard)



async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        await update.effective_message.reply_text("⛔ Admin access only.")
        return
    context.user_data.pop("awaiting_media_for", None)
    await update.effective_message.reply_text(
        "🛠️ OWNER / ADMIN PANEL\n\n"
        "Choose a chapter. Then send its photo, video, audio, or voice note.\n"
        "You can attach multiple files to the same chapter.",
        reply_markup=admin_keyboard(),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "surprise":
        surprise_text = (
            "╭━━━━━━ ♡ ━━━━━━╮\n"
            "       ᴏɴᴇ ᴛɪɴʏ ꜱᴇᴄʀᴇᴛ\n"
            "╰━━━━━━ ♡ ━━━━━━╯\n\n"
            f"{GIRLFRIEND_NAME}, if I could save one place\n"
            "to visit whenever life gets loud,\n"
            "it would be right beside you. 🥺\n\n"
            "No grand promise can beat the little things:\n"
            "choosing you, listening to you,\n"
            "and making you smile again tomorrow.\n\n"
            "      ᴛᴏ ᴍʏ ꜰᴀᴠᴏᴜʀɪᴛᴇ ᴘᴇʀꜱᴏɴ ♡"
        )
        story_button = InlineKeyboardMarkup([[
            InlineKeyboardButton("♡ ʀᴇᴀᴅ ᴏᴜʀ ꜱᴛᴏʀʏ", callback_data="story:0")
        ]])
        extras = load_media().get(SURPRISE_KEY, [])
        if not extras:
            await query.message.reply_text(style_text(surprise_text), reply_markup=story_button)
            return
        chat_id = query.message.chat_id
        await query.message.reply_text(style_text(surprise_text))
        for n, item in enumerate(extras):
            await asyncio.sleep(1.0)
            last = n == len(extras) - 1
            await send_media_item(
                chat_id, item, context, reply_markup=story_button if last else None
            )
        return

    if data.startswith("story:"):
        try:
            index = int(data.split(":", 1)[1])
            if 0 <= index < len(CHAPTERS):
                await show_chapter(query.message.chat_id, index, context)
        except (ValueError, IndexError):
            pass
        return

    if data.startswith("admin:"):
        if not is_owner(update):
            await query.answer("Admin only.", show_alert=True)
            return

        parts = data.split(":")
        action = parts[1] if len(parts) > 1 else ""

        if action == "add" and len(parts) == 3:
            chapter = chapter_by_id(parts[2])
            if not chapter:
                await query.message.reply_text("Chapter not found.")
                return
            context.user_data["awaiting_media_for"] = chapter["id"]
            await query.message.reply_text(
                f"📥 Send the media for:\n{chapter['title']}\n\n"
                "Accepted: photo, video, audio, voice note, GIF/animation, or document.\n"
                "Send /cancel to stop. Send /admin when finished."
            )
        elif action == "hugs":
            count = len(load_media().get(HUG_KEY, []))
            if count >= HUG_LIMIT:
                await query.message.reply_text(
                    f"🤗 Already {HUG_LIMIT}/{HUG_LIMIT} hug stickers saved.\n"
                    "Tap “Clear Hug Stickers” in /admin to replace them."
                )
                return
            context.user_data["awaiting_media_for"] = HUG_KEY
            await query.message.reply_text(
                f"🤗 Send hug stickers one by one ({count}/{HUG_LIMIT} saved).\n"
                "Only stickers are accepted. Send /cancel to stop."
            )
        elif action == "hugs_clear":
            db = load_media()
            db.pop(HUG_KEY, None)
            save_media(db)
            await query.message.reply_text("🗑 Hug stickers cleared. Send /admin to add new ones.")
        elif action == "surprise":
            context.user_data["awaiting_media_for"] = SURPRISE_KEY
            count = len(load_media().get(SURPRISE_KEY, []))
            await query.message.reply_text(
                f"💌 Surprise mode ({count} saved).\n\n"
                "Send voice notes or text messages (also photo/video/audio/sticker) one by one. "
                "They play in the order you send them when she taps “A Little Surprise”.\n"
                "Send /cancel when finished."
            )
        elif action == "surprise_clear":
            db = load_media()
            db.pop(SURPRISE_KEY, None)
            save_media(db)
            await query.message.reply_text("🗑 Surprise extras cleared.")
        elif action == "rm_menu":
            db = load_media()
            rows = []
            for c in CHAPTERS:
                n = len(db.get(c["id"], []))
                if n:
                    rows.append([InlineKeyboardButton(
                        f"🖼 {c['title'][:26]} ({n})",
                        callback_data=f"admin:rmc:{c['id']}",
                    )])
            n = len(db.get(SURPRISE_KEY, []))
            if n:
                rows.append([InlineKeyboardButton(
                    f"💌 A Little Surprise ({n})", callback_data=f"admin:rmc:{SURPRISE_KEY}"
                )])
            if not rows:
                await query.message.reply_text("No saved media to remove.")
            else:
                await query.message.reply_text(
                    "Which chapter has the wrong item?", reply_markup=InlineKeyboardMarkup(rows)
                )
        elif action == "rmc" and len(parts) == 3:
            items = load_media().get(parts[2], [])
            if not items:
                await query.message.reply_text("Nothing saved in that chapter.")
                return
            chat_id = query.message.chat_id
            await query.message.reply_text("Tap 🗑 under the item you want to remove:")
            for item in items:
                await send_media_item(
                    chat_id, item, context,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        "🗑 Remove this",
                        callback_data=f"admin:rmi:{parts[2]}:{item_key(item)}",
                    )]]),
                )
        elif action == "rmi" and len(parts) == 4:
            db = load_media()
            items = db.get(parts[2], [])
            removed = False
            for i, it in enumerate(items):
                if item_key(it) == parts[3]:
                    items.pop(i)
                    removed = True
                    break
            if not items:
                db.pop(parts[2], None)
            if removed:
                save_media(db)
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.message.chat.send_message(
                f"✅ Removed. {len(items)} item(s) left in that chapter."
                if removed else "Already removed."
            )
        elif action == "clear_menu":
            rows = [[InlineKeyboardButton(
                f"🗑 {c['title'][:30]}",
                callback_data=f"admin:clear:{c['id']}",
            )] for c in CHAPTERS]
            await query.message.reply_text("Choose the chapter to clear:", reply_markup=InlineKeyboardMarkup(rows))
        elif action == "clear" and len(parts) == 3:
            chapter = chapter_by_id(parts[2])
            db = load_media()
            db.pop(parts[2], None)
            save_media(db)
            await query.message.reply_text(
                f"🗑 Removed saved media from {chapter['title'] if chapter else 'that chapter'}."
            )
        elif action == "help":
            await query.message.reply_text(
                "Admin help:\n"
                "1. Tap a chapter in /admin.\n"
                "2. Send one or more media files.\n"
                "3. Each file is saved in story_media.json using its Telegram file_id.\n"
                "4. Tap Remove One Picture/Item to delete a single wrong file, or Clear a chapter to remove all of its media.\n"
                "5. Send /cancel to leave media-upload mode."
            )


async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    chapter_id = context.user_data.get("awaiting_media_for")
    if not chapter_id:
        return

    message = update.effective_message

    # Hug-sticker upload mode: stickers only, max HUG_LIMIT.
    if chapter_id == HUG_KEY:
        if not message.sticker:
            await message.reply_text("🤗 Please send a sticker.")
            return
        db = load_media()
        stickers = db.setdefault(HUG_KEY, [])
        if len(stickers) >= HUG_LIMIT:
            context.user_data.pop("awaiting_media_for", None)
            await message.reply_text(f"Already {HUG_LIMIT}/{HUG_LIMIT} saved. Send /admin.")
            return
        stickers.append({"kind": "sticker", "file_id": message.sticker.file_id})
        save_media(db)
        count = len(stickers)
        if count >= HUG_LIMIT:
            context.user_data.pop("awaiting_media_for", None)
            await message.reply_text(f"✅ Hug sticker {count}/{HUG_LIMIT} saved. All done! 🤗 Send /admin.")
        else:
            await message.reply_text(f"✅ Hug sticker {count}/{HUG_LIMIT} saved. Send the next one.")
        return

    item = None
    if message.sticker:
        item = {"kind": "sticker", "file_id": message.sticker.file_id}
    elif message.photo:
        item = {"kind": "photo", "file_id": message.photo[-1].file_id}
    elif message.video:
        item = {"kind": "video", "file_id": message.video.file_id}
    elif message.audio:
        item = {"kind": "audio", "file_id": message.audio.file_id}
    elif message.voice:
        item = {"kind": "voice", "file_id": message.voice.file_id}
    elif message.animation:
        item = {"kind": "animation", "file_id": message.animation.file_id}
    elif message.document:
        item = {"kind": "document", "file_id": message.document.file_id}
    elif message.text and chapter_id == SURPRISE_KEY:
        item = {"kind": "text", "text": message.text}
    else:
        await message.reply_text("Please send a photo, video, audio, voice note, GIF, document, or sticker.")
        return

    if message.caption:
        item["caption"] = message.caption

    db = load_media()
    db.setdefault(chapter_id, []).append(item)
    save_media(db)
    chapter = chapter_by_id(chapter_id)
    count = len(db[chapter_id])
    label = "A Little Surprise 💌" if chapter_id == SURPRISE_KEY else (chapter["title"] if chapter else chapter_id)
    await message.reply_text(
        f"✅ Saved to “{label}”.\n"
        f"Media items in this chapter: {count}\n\n"
        "Send another media file, or /admin to return to the panel."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("awaiting_media_for", None)
    await update.effective_message.reply_text("Upload mode cancelled. Send /admin to open the panel.")


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        await update.effective_message.reply_text(f"Your Telegram user ID is:\n`{user.id}`", parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Commands:\n"
        "/start — open the love story\n"
        "/admin — owner media panel\n"
        "/id — show your Telegram numeric ID\n"
        "/cancel — stop an active media upload"
    )


def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit('BOT_TOKEN is missing. Set it first: export BOT_TOKEN="your_bot_token"')
    if not OWNER_ID:
        raise SystemExit('OWNER_ID is missing/invalid. Set your numeric Telegram user ID: export OWNER_ID="123456789"')

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE |
        filters.ANIMATION | filters.Document.ALL | filters.Sticker.ALL,
        receive_media,
    ))
    # Plain text is only used in surprise mode (owner types a message to add).
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_media))

    log.info("Our Story bot is running. Media database: %s", DATA_FILE)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

