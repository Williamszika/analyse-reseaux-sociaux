"""Métadonnées, moments les plus revus, chapitres, commentaires, sous-titres et vidéo (option), en cache.
python scripts/fetch.py URL [--video] [--cookies] [--comments 300] [--force]"""
import argparse, glob, os
import yt_dlp
from common import BASE, ffmpeg, load, save

KEEP = ["id", "title", "description", "channel", "channel_follower_count", "uploader", "upload_date",
        "timestamp", "duration", "view_count", "like_count", "comment_count", "repost_count", "tags",
        "categories", "chapters", "heatmap", "webpage_url", "extractor_key", "language"]

ap = argparse.ArgumentParser()
ap.add_argument("url")
ap.add_argument("--video", action="store_true")
ap.add_argument("--cookies", action="store_true")
ap.add_argument("--comments", type=int, default=300)
ap.add_argument("--force", action="store_true")
a = ap.parse_args()

base = {"quiet": True, "no_warnings": True, "ffmpeg_location": ffmpeg()}
if a.cookies:
    base["cookiesfrombrowser"] = ("chrome",)

with yt_dlp.YoutubeDL({**base, "skip_download": True}) as y:
    info = y.extract_info(a.url, download=False)
d = os.path.join(BASE, "cache", f"{info['extractor_key'].lower()}_{info['id']}")
os.makedirs(d, exist_ok=True)
mp = os.path.join(d, "meta.json")

if a.force or not os.path.exists(mp):
    full = info
    if a.comments:
        opts = {**base, "skip_download": True, "getcomments": True,
                "extractor_args": {"youtube": {"max_comments": [str(a.comments)], "comment_sort": ["top"]}}}
        try:
            with yt_dlp.YoutubeDL(opts) as y:
                full = y.extract_info(a.url, download=False)
        except Exception as e:
            print("commentaires indisponibles :", e)
    meta = {k: full.get(k) for k in KEEP}
    cs = sorted(full.get("comments") or [], key=lambda c: c.get("like_count") or 0, reverse=True)
    meta["comments"] = [{"text": (c.get("text") or "")[:500], "likes": c.get("like_count") or 0}
                        for c in cs[:a.comments]]
    save(mp, meta)
meta = load(mp, {})

if a.force or not glob.glob(os.path.join(d, "subs*.vtt")):
    lang = meta.get("language")
    langs = [f"{lang}.*"] if lang else ["fr.*", "en.*"]
    try:
        with yt_dlp.YoutubeDL({**base, "skip_download": True, "writesubtitles": True,
                               "writeautomaticsub": True, "subtitleslangs": langs,
                               "subtitlesformat": "vtt", "outtmpl": os.path.join(d, "subs.%(ext)s")}) as y:
            y.download([a.url])
    except Exception as e:
        print("sous-titres indisponibles :", e)

if a.video and not glob.glob(os.path.join(d, "video.*")):
    h = 480 if (meta.get("duration") or 0) > 3600 else 720
    with yt_dlp.YoutubeDL({**base, "format": f"bv*[height<={h}]+ba/b[height<={h}]/b",
                           "merge_output_format": "mp4", "outtmpl": os.path.join(d, "video.%(ext)s")}) as y:
        y.download([a.url])

print(d)
