"""Upload a finished video to YouTube (Zen Hour Music) with the YouTube Data API: private by default, big files resumable.
Run with the uploader's own venv, from the video folder:
  /Users/Maxi/Code/Tools/yt-venv/bin/python ../scripts/yt_upload.py --file output/<id>_1hr_4k24.mp4 --meta jobs/<id>/youtube.md [--thumbnail thumb.jpg] [--dry-run]
Credentials live OUTSIDE the repo in ~/.config/youtube-upload/: client_secret.json (Desktop OAuth client, downloaded from Google Cloud in the
Zen Hour account) and token.json (written on the first run after the browser approval; chmod 600). Scope: youtube.upload only.
--meta reads the "**Title:**" line and the text between "**Description:**" and the next "**...:**" line of youtube.md; --title/--description override.
Defaults: privacy private, category 10 (Music), not made for kids, no synthetic-media label (--synthetic sets it), --publish-at "2026-10-20T20:00:00-07:00"
schedules a private video to go public (only works once the API project has passed Google's audit: until then API uploads are LOCKED private).
Prints the video id and URL and appends a line to ~/.config/youtube-upload/uploads.log."""
import argparse, json, os, random, re, sys, time
CFG = os.path.expanduser("~/.config/youtube-upload"); SECRET = f"{CFG}/client_secret.json"; TOKEN = f"{CFG}/token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
ap = argparse.ArgumentParser()
ap.add_argument("--file", required=True); ap.add_argument("--meta"); ap.add_argument("--title"); ap.add_argument("--description")
ap.add_argument("--tags", default="sleep music,piano,relaxing music,study music,snow,winter,ambient"); ap.add_argument("--category", default="10")
ap.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"]); ap.add_argument("--publish-at")
ap.add_argument("--made-for-kids", action="store_true"); ap.add_argument("--synthetic", action="store_true"); ap.add_argument("--thumbnail")
ap.add_argument("--chunk-mb", type=int, default=32); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--auth-only", action="store_true")
a = ap.parse_args()

def read_meta(path):
    s = open(path, encoding="utf-8").read()
    t = re.search(r"^\*\*Title:\*\*\s*(.+)$", s, re.M); d = re.search(r"^\*\*Description:\*\*\s*\n(.*?)(?=^\*\*[^*\n]+:\*\*|\Z)", s, re.M | re.S)
    return (t.group(1).strip() if t else None), (d.group(1).strip() if d else None)
title, desc = read_meta(a.meta) if a.meta else (None, None)
title = a.title or title; desc = a.description or desc or ""
if not a.auth_only:
    if not title: sys.exit("no title: pass --title or a --meta file with a **Title:** line")
    if len(title) > 100: sys.exit(f"title is {len(title)} characters; YouTube allows 100")
    if "<" in title + desc or ">" in title + desc: sys.exit("YouTube rejects < and > in titles and descriptions")
    if not os.path.isfile(a.file): sys.exit(f"no such file: {a.file}")
body = {"snippet": {"title": title, "description": desc, "tags": [t.strip() for t in a.tags.split(",") if t.strip()], "categoryId": a.category},
        "status": {"privacyStatus": "private" if a.publish_at else a.privacy, "selfDeclaredMadeForKids": a.made_for_kids, "containsSyntheticMedia": a.synthetic}}
if a.publish_at: body["status"]["publishAt"] = a.publish_at
if a.dry_run:
    print(json.dumps(body, indent=1, ensure_ascii=False)); print(f"file: {a.file} ({os.path.getsize(a.file) / 1e9:.2f} GB)" if os.path.isfile(a.file) else ""); sys.exit(0)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
creds = Credentials.from_authorized_user_file(TOKEN, SCOPES) if os.path.exists(TOKEN) else None
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
    else:
        if not os.path.exists(SECRET): sys.exit(f"missing {SECRET}: download the Desktop OAuth client JSON from Google Cloud (Zen Hour account) and save it there")
        print("A browser window opens: sign in with the Zen Hour Google account and allow upload access.", flush=True)
        creds = InstalledAppFlow.from_client_secrets_file(SECRET, SCOPES).run_local_server(port=0, open_browser=True)
    os.makedirs(CFG, exist_ok=True); open(TOKEN, "w").write(creds.to_json()); os.chmod(TOKEN, 0o600)
if a.auth_only: print("authorized; token saved in", TOKEN); sys.exit(0)

yt = build("youtube", "v3", credentials=creds)
req = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(a.file, chunksize=a.chunk_mb * 1024 * 1024, resumable=True, mimetype="video/mp4"))
resp, tries, t0 = None, 0, time.time()
while resp is None:
    try:
        status, resp = req.next_chunk()
        if status: print(f"uploaded {status.progress() * 100:5.1f} %  ({(time.time() - t0) / 60:.1f} min)", flush=True); tries = 0
    except HttpError as e:
        if e.resp.status not in (500, 502, 503, 504) or tries >= 8: raise
        tries += 1; w = min(2 ** tries + random.random(), 120); print(f"server error {e.resp.status}, retry {tries} in {w:.0f} s", flush=True); time.sleep(w)
    except (ConnectionError, TimeoutError, OSError) as e:
        if tries >= 8: raise
        tries += 1; w = min(2 ** tries + random.random(), 120); print(f"network error ({e}), retry {tries} in {w:.0f} s", flush=True); time.sleep(w)
vid = resp["id"]; url = f"https://youtu.be/{vid}"
print(f"done: {url}  privacy {resp['status'].get('privacyStatus')}  upload status {resp['status'].get('uploadStatus')}")
if a.thumbnail:
    yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(a.thumbnail)).execute(); print("thumbnail set")
with open(f"{CFG}/uploads.log", "a") as f: f.write(f"{time.strftime('%Y-%m-%d %H:%M')}\t{vid}\t{body['status']['privacyStatus']}\t{a.file}\t{title}\n")
