# OUR STORY ❤️ — Website + Telegram Bot

This project gives you:
- A romantic, mobile-friendly story website.
- A private owner panel at `/admin` for uploading photos, videos, audio, GIFs and surprise text.
- Your original Telegram story bot (`aadi.py`), patched so media uploaded from the website can also be sent by Telegram.
- One shared `story_media.json` file for website uploads and Telegram admin uploads.

## Important: how the two parts connect

Run the website and Telegram bot from this same project folder on the same computer/server. Both read `story_media.json`. Website uploads are saved in `uploads/` and registered in that JSON file. The bot uses the saved local file path to send those files in Telegram.

Media uploaded directly inside Telegram using `/admin` still uses Telegram `file_id`. Telegram file IDs are not directly viewable by the website, so upload media through the website admin panel if you want it to appear in both places.

## 1. Install Python

Install Python 3.10 or newer. On Termux:
```bash
pkg update -y
pkg install python -y
```

On Windows, install Python from https://www.python.org/downloads/ and tick **Add Python to PATH**.

## 2. Install project packages

Open a terminal in this folder:
```bash
python -m pip install -r requirements.txt
```

On Termux, use `pip install -r requirements.txt` if `python -m pip` is unavailable.

## 3. Set your private settings

Copy `.env.example` to `.env` and fill in:
- `BOT_TOKEN`: token from BotFather.
- `OWNER_ID`: your numeric Telegram user ID (send `/id` to your bot to see it).
- `WEB_ADMIN_PASSWORD`: a strong password for the website owner panel.
- `GIRLFRIEND_NAME`: name shown on the site.

The app reads environment variables; it does not automatically load `.env`. For a quick Termux session, run:
```bash
export BOT_TOKEN="YOUR_BOT_TOKEN"
export OWNER_ID="YOUR_NUMERIC_ID"
export GIRLFRIEND_NAME="Samriddhi"
export WEB_ADMIN_USER="admin"
export WEB_ADMIN_PASSWORD="MAKE_A_LONG_PASSWORD"
```
Do not share your bot token or admin password. If a token is exposed, regenerate it with BotFather.

## 4. Start the website

From this folder:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
Open `http://127.0.0.1:8000` on the same device.
Open the owner panel at `http://127.0.0.1:8000/admin`.

To access from another phone on the same Wi-Fi, use the computer's local IP address, for example `http://192.168.1.5:8000`. Do not expose the admin panel to the public internet without HTTPS and a strong password.

## 5. Start the Telegram bot

Open a second terminal in the same project folder. Set the same `BOT_TOKEN`, `OWNER_ID`, `GIRLFRIEND_NAME`, `WEB_ADMIN_USER`, and `WEB_ADMIN_PASSWORD` variables in that terminal, then run:
```bash
python aadi.py
```
In Telegram, send `/start` to the bot. Send `/admin` from the account whose ID is `OWNER_ID` to use its Telegram admin panel.

### Termux tip
Use two Termux sessions: keep `uvicorn ...` running in the first session and `python aadi.py` running in the second. Do not close either session while you want the website/bot online.

## 6. Deploy website and bot together on Railway

This repository now includes `railway.json` and `start.sh`. Railway starts the Telegram bot in the background and keeps the FastAPI website in the foreground, so both run in **one Railway service** and share the same files.

1. In Railway, open the project connected to this GitHub repository and use one service for this repository.
2. In that service, open **Variables** and add:
   - `BOT_TOKEN` = your BotFather token
   - `OWNER_ID` = your numeric Telegram user ID
   - `GIRLFRIEND_NAME` = `Samriddhi`
   - `WEB_ADMIN_USER` = `admin`
   - `WEB_ADMIN_PASSWORD` = a strong private password
   - `STORY_DATA_FILE` = `/data/story_media.json`
   - `STORY_UPLOAD_DIR` = `/data/uploads`
3. Open **Volumes** and add a persistent volume mounted at `/data`. This is important: without a persistent volume, uploaded photos/videos and the story database can disappear when Railway redeploys the service.
4. In **Settings → Deploy**, leave the custom start command empty so Railway uses the repository's `railway.json` start command (`sh start.sh`). If a custom command is already set, replace it with `sh start.sh`.
5. Redeploy the service. Open its public domain for the website. The bot should also come online; send it `/start` in Telegram.
6. Check **Deployments → View Logs**. You should see both “Our Story bot is running” and “Starting Our Story website”. If the bot reports a missing/invalid token or owner ID, correct those Railway Variables and redeploy.

**Important:** Do not create two separate Railway services for this setup unless you also configure shared storage. Separate services do not automatically share their local files. This one-service setup keeps the website and bot on the same persistent volume.

Admin panel: `https://YOUR-RAILWAY-DOMAIN/admin`. Keep the admin password private.

## 7. Put it online on a VPS

For a public website and always-on bot, use a small Ubuntu VPS:
1. Upload this entire folder to the VPS.
2. Install Python 3.10+, then run `python3 -m pip install -r requirements.txt`.
3. Set the environment variables listed above.
4. Run the website on port 8000 and put it behind a domain + HTTPS reverse proxy (Caddy or Nginx).
5. Run `python aadi.py` as a separate long-running service (systemd is recommended).
6. Keep `story_media.json` and `uploads/` on persistent disk and back them up.

A simple local test is not the same as public hosting. The project ZIP does not include a hosting account or domain.

## Owner panel

- Upload a file and select a chapter to attach it to that chapter.
- Add text to the “A Little Surprise” section.
- Clear all media from a selected chapter.
- Website uploads are visible on the site and can be sent by the Telegram bot while both run on the same server.

## File layout

```text
our_story_website/
├── aadi.py
├── main.py
├── requirements.txt
├── story_media.json        # created when first upload is made
├── uploads/                # uploaded media is saved here
└── static/
    ├── index.html
    ├── admin.html
    ├── app.js
    ├── admin.js
    └── style.css
```

## Troubleshooting

- `BOT_TOKEN is missing`: export the token in the terminal where you start `aadi.py`.
- `OWNER_ID is missing/invalid`: export your numeric Telegram user ID, not your username.
- Website admin says password not set: set `WEB_ADMIN_PASSWORD` before starting `uvicorn`.
- Website upload works but bot cannot send the file: make sure bot and website run on the same device/server and use the same `STORY_DATA_FILE` and `STORY_UPLOAD_DIR`.
- Website not reachable from another network: local `127.0.0.1` only works on the same device; use a VPS/domain for public access.
