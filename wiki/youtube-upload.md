# YouTube uploader (Zen Hour Music)

`scripts/yt_upload.py` uploads a finished video with the YouTube Data API: **private** by default, resumable (big 4K files are fine), title and description from the video's `jobs/<id>/youtube.md`, category Music, not made for kids. Own venv: `/Users/Maxi/Code/Tools/yt-venv` (google-api-python-client, google-auth-oauthlib). Credentials stay **outside the repo** in `~/.config/youtube-upload/` (never commit or back them up to jCore).

> **Important:** until Google has audited the API project, every API upload is **locked as private** and cannot be made public later. Until the audit passes, upload by hand in YouTube Studio (title/description from `youtube.md`); use the uploader only for a small test or after approval.

## One-time setup (in the Zen Hour Google account, ~10 min)
1. Open https://console.cloud.google.com signed in as the **Zen Hour** account → project picker → **New project** → name `zen-hour-uploader` → Create, and select it.
2. **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**.
3. **Google Auth Platform** (OAuth consent screen) → **Get started**: app name `Zen Hour Uploader`, support email = the Zen Hour address → Audience **External** → contact email → agree → Create.
4. **Audience → Test users → Add users** → the Zen Hour Gmail address → Save.
5. **Clients → Create client** → Application type **Desktop app** → name `zen-hour-desktop` → Create → **Download JSON**.
6. Save the downloaded file as `~/.config/youtube-upload/client_secret.json` (or leave it in Downloads and tell Claude).
7. Claude runs `--auth-only`: a browser opens → choose the Zen Hour account → "Google hasn't verified this app" → **Continue** → allow **Manage your YouTube videos** (upload) → done. `token.json` is saved (chmod 600).
8. Apply for the audit so uploads can go public: YouTube API Services audit form https://support.google.com/youtube/contact/yt_api_form — say it is a private tool that uploads the owner's own videos to their own channel (Zen Hour Music), private-by-default, ~2 uploads a week, no other users.

## Use (from the video folder)
```bash
/Users/Maxi/Code/Tools/yt-venv/bin/python ../scripts/yt_upload.py --file output/<id>_1hr_4k24.mp4 --meta jobs/<id>/youtube.md --dry-run    # check title/description
/Users/Maxi/Code/Tools/yt-venv/bin/python ../scripts/yt_upload.py --file output/<id>_1hr_4k24.mp4 --meta jobs/<id>/youtube.md [--thumbnail t.jpg]
```
Options: `--privacy private|unlisted|public`, `--publish-at 2026-10-20T20:00:00-07:00` (scheduled; private until then), `--synthetic` (YouTube's altered/synthetic label), `--tags "a,b"`, `--auth-only`. Every upload is logged in `~/.config/youtube-upload/uploads.log`. Uploading publishes to the channel, so Claude uploads only when the user asks.
