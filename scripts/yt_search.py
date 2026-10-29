"""Recherche YouTube, filtre par période, classe par vues.
python scripts/yt_search.py "motivation" --n 5 --days 7 [--pool 40] [--min-duration 61] [--lang fr] [--out f.json]"""
import argparse, datetime as dt, json, os, re, urllib.parse, urllib.request
import yt_dlp
from common import BASE, save, hms

KEYS = ["id", "title", "channel", "upload_date", "timestamp", "view_count", "like_count",
        "comment_count", "duration", "webpage_url", "channel_follower_count"]

def api_key():
    k = os.environ.get("YT_API_KEY")
    f = os.path.join(BASE, ".yt_api_key")
    if not k and os.path.exists(f):
        k = open(f).read().strip()
    return k

def iso_dur(d):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    dd, h, mi, s = [int(x or 0) for x in m.groups()] if m else (0, 0, 0, 0)
    return dd * 86400 + h * 3600 + mi * 60 + s

def get(url, params):
    return json.load(urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params)))

def via_api(key, q, days, pool, lang):
    p = {"part": "snippet", "q": q, "type": "video", "maxResults": min(pool, 50),
         "order": "viewCount", "key": key}
    if days:
        p["publishedAfter"] = (dt.datetime.utcnow() - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if lang:
        p["relevanceLanguage"] = lang
    ids = [i["id"]["videoId"] for i in get("https://www.googleapis.com/youtube/v3/search", p).get("items", [])]
    if not ids:
        return []
    v = get("https://www.googleapis.com/youtube/v3/videos",
            {"part": "snippet,statistics,contentDetails", "id": ",".join(ids), "key": key})
    out = []
    for it in v.get("items", []):
        s, st = it["snippet"], it.get("statistics", {})
        pub = dt.datetime.strptime(s["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        out.append({"id": it["id"], "title": s["title"], "channel": s["channelTitle"],
                    "upload_date": s["publishedAt"][:10].replace("-", ""), "timestamp": int(pub.timestamp()),
                    "view_count": int(st.get("viewCount", 0)), "like_count": int(st.get("likeCount", 0)),
                    "comment_count": int(st.get("commentCount", 0)),
                    "duration": iso_dur(it["contentDetails"]["duration"]),
                    "webpage_url": f"https://www.youtube.com/watch?v={it['id']}"})
    return out

def via_ytdlp(q, days, pool):
    prefix = "ytsearchdate" if days else "ytsearch"
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "ignoreerrors": True, "no_warnings": True}) as y:
        info = y.extract_info(f"{prefix}{pool}:{q}", download=False)
    return [{k: e.get(k) for k in KEYS} for e in (info.get("entries") or []) if e]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--pool", type=int, default=40)
    ap.add_argument("--min-duration", type=int, default=0)
    ap.add_argument("--lang", default=None)
    ap.add_argument("--out", default="recherche.json")
    a = ap.parse_args()
    key = api_key()
    rows, source = [], "yt-dlp"
    if key:
        try:
            rows, source = via_api(key, a.query, a.days, a.pool, a.lang), "YouTube Data API"
        except Exception as e:
            print("API indisponible, repli yt-dlp :", e)
    if not rows:
        rows = via_ytdlp(a.query, a.days, a.pool)
    cut = (dt.date.today() - dt.timedelta(days=a.days)).strftime("%Y%m%d") if a.days else None
    rows = [r for r in rows if (not cut or (r.get("upload_date") or "0") >= cut)
            and (r.get("duration") or 0) >= a.min_duration]
    rows.sort(key=lambda r: r.get("view_count") or 0, reverse=True)
    rows = rows[:a.n]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    save(a.out, {"requete": a.query, "jours": a.days, "source": source, "resultats": rows})
    for i, r in enumerate(rows, 1):
        print(f"{i}. {r.get('upload_date')} | {r.get('view_count') or 0:>10,} vues | {hms(r.get('duration'))} | {r.get('channel')} | {r.get('title')} | {r.get('webpage_url')}")
    print(f"{len(rows)} résultat(s) via {source} -> {a.out}")
