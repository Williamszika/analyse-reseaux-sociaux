"""Derniers posts d'un profil via yt-dlp (YouTube, TikTok, Instagram, vidéos Facebook) -> posts.json.
python scripts/collect.py <URL du profil> --n 30 [--cookies] [--pause 1.5] --out rapports/<dossier>/posts.json"""
import argparse, os, time
import yt_dlp
from common import save

ap = argparse.ArgumentParser()
ap.add_argument("url")
ap.add_argument("--n", type=int, default=30)
ap.add_argument("--cookies", action="store_true")
ap.add_argument("--pause", type=float, default=1.5)
ap.add_argument("--out", required=True)
a = ap.parse_args()

base = {"quiet": True, "no_warnings": True, "ignoreerrors": True, "skip_download": True}
if a.cookies:
    base["cookiesfrombrowser"] = ("chrome",)

with yt_dlp.YoutubeDL({**base, "extract_flat": "in_playlist", "playlistend": a.n}) as y:
    info = y.extract_info(a.url, download=False) or {}
entries = [e for e in (info.get("entries") or []) if e][:a.n]
if not entries:
    raise SystemExit("Aucun post trouvé : essayer --cookies, une autre URL (/videos, /shorts) ou la collecte navigateur")

posts = []
with yt_dlp.YoutubeDL(base) as y:
    for i, e in enumerate(entries, 1):
        url = e.get("webpage_url") or e.get("url")
        try:
            m = y.extract_info(url, download=False)
        except Exception as ex:
            print("ignoré :", url, ex)
            m = None
        if m:
            dur = m.get("duration")
            posts.append({"id": m.get("id"), "ts": m.get("timestamp"),
                          "type": "court" if dur and dur <= 60 else "vidéo", "duree": dur,
                          "vues": m.get("view_count"), "likes": m.get("like_count"),
                          "commentaires": m.get("comment_count"), "partages": m.get("repost_count"),
                          "enregistrements": None, "lien": m.get("webpage_url") or url,
                          "sujet": (m.get("title") or m.get("description") or "")[:80]})
            print(f"{i}/{len(entries)} {m.get('upload_date')} {m.get('view_count')} vues")
        time.sleep(a.pause)

os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
save(a.out, posts)
profil = {"nom": info.get("uploader") or info.get("channel") or info.get("title"),
          "abonnes": info.get("channel_follower_count"), "url": a.url}
save(os.path.join(os.path.dirname(os.path.abspath(a.out)), "profil_collecte.json"), profil)
print(f"{len(posts)} posts, {sum(1 for p in posts if p['ts'])} avec heure exacte -> {a.out}")
