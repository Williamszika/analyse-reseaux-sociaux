"""Analyse des horaires de publication.
python scripts/timing.py rapports/<dossier>/posts.json --tz Africa/Abidjan [--tz Europe/Paris] [--out rapports/<dossier>]
posts.json : liste de {"ts": unix ou ISO, "vues": .., "likes": .., "commentaires": .., "partages": ..}
Le premier --tz est le fuseau principal du public."""
import argparse, datetime as dt, os, statistics as st
from zoneinfo import ZoneInfo
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import load, save

JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
BLOCS = [(0, 6, "0–6 h"), (6, 9, "6–9 h"), (9, 12, "9–12 h"), (12, 15, "12–15 h"),
         (15, 18, "15–18 h"), (18, 21, "18–21 h"), (21, 24, "21–24 h")]
NOMS = [b[2] for b in BLOCS]

def bloc(h):
    return next(i for i, (a, b, _) in enumerate(BLOCS) if a <= h < b)

def to_ts(v):
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except Exception:
        return dt.datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()

ap = argparse.ArgumentParser()
ap.add_argument("posts")
ap.add_argument("--tz", action="append", default=None)
ap.add_argument("--out", default=None)
a = ap.parse_args()
tzs = a.tz or ["UTC"]
out = a.out or os.path.dirname(os.path.abspath(a.posts))
os.makedirs(out, exist_ok=True)

posts = [p for p in (load(a.posts, []) or []) if p.get("ts") and p.get("vues")]
if not posts:
    raise SystemExit("Aucun post avec horodatage et vues")
for p in posts:
    p["ts"] = to_ts(p["ts"])
med = st.median(p["vues"] for p in posts)
for p in posts:
    inter = (p.get("likes") or 0) + (p.get("commentaires") or 0) + (p.get("partages") or 0)
    p["indice"] = round(p["vues"] / med, 2) if med else 0
    p["eng"] = round(100 * inter / p["vues"], 2)

def summ(ps):
    return {"posts": len(ps), "indice": round(st.median(x["indice"] for x in ps), 2),
            "eng": round(st.median(x["eng"] for x in ps), 2)}

res = {"n": len(posts), "vues_mediane": med, "fuseau_principal": tzs[0], "fuseaux": {},
       "fiabilite": "faible" if len(posts) < 15 else "moyenne" if len(posts) < 40 else "bonne"}
for tz in tzs:
    z = ZoneInfo(tz)
    cells, days, hours = {}, {}, {}
    for p in posts:
        t = dt.datetime.fromtimestamp(p["ts"], z)
        cells.setdefault((t.weekday(), bloc(t.hour)), []).append(p)
        days.setdefault(t.weekday(), []).append(p)
        hours.setdefault(bloc(t.hour), []).append(p)
    res["fuseaux"][tz] = {
        "jours": {JOURS[k]: summ(v) for k, v in sorted(days.items())},
        "blocs": {NOMS[k]: summ(v) for k, v in sorted(hours.items())},
        "cellules": [{"jour": JOURS[d], "bloc": NOMS[b], **summ(v)} for (d, b), v in sorted(cells.items())]}

main = res["fuseaux"][tzs[0]]
cands = [c for c in main["cellules"] if c["posts"] >= 2] or main["cellules"]
res["meilleurs"] = sorted(cands, key=lambda c: (-c["indice"], -c["eng"]))[:3]
res["pires"] = sorted(cands, key=lambda c: (c["indice"], c["eng"]))[:2]

grid = np.full((len(BLOCS), 7), np.nan)
count = np.zeros((len(BLOCS), 7), dtype=int)
for c in main["cellules"]:
    i, j = NOMS.index(c["bloc"]), JOURS.index(c["jour"])
    grid[i, j], count[i, j] = c["indice"], c["posts"]
fig, ax = plt.subplots(figsize=(6.6, 3.1))
cmap = plt.get_cmap("Blues").copy()
cmap.set_bad("#f3f4f6")
im = ax.imshow(np.ma.masked_invalid(grid), cmap=cmap, aspect="auto", vmin=0,
               vmax=max(1.5, np.nanmax(grid) if np.isfinite(np.nanmax(grid)) else 1.5))
for i in range(len(BLOCS)):
    for j in range(7):
        if count[i, j]:
            ax.text(j, i, f"{grid[i, j]:.1f}\n({count[i, j]})", ha="center", va="center", fontsize=6.5,
                    color="white" if grid[i, j] > 1.1 else "#111")
ax.set_xticks(range(7)); ax.set_xticklabels(JOURS, fontsize=8)
ax.set_yticks(range(len(BLOCS))); ax.set_yticklabels(NOMS, fontsize=8)
ax.set_title(f"Indice de vues par créneau (1 = médiane du compte, nb de posts) — {tzs[0]}", fontsize=8.5)
fig.colorbar(im, ax=ax, shrink=.8)
hp = os.path.join(out, "horaires.png")
fig.savefig(hp, dpi=160, bbox_inches="tight")
plt.close(fig)
res["heatmap"] = hp
save(os.path.join(out, "timing.json"), res)

print(f"{res['n']} posts · vues médianes {med} · fiabilité {res['fiabilite']}")
for tz in tzs:
    print(tz, "jours :", {k: v["indice"] for k, v in res["fuseaux"][tz]["jours"].items()})
    print(tz, "tranches :", {k: v["indice"] for k, v in res["fuseaux"][tz]["blocs"].items()})
print("Meilleurs créneaux :", res["meilleurs"])
print("->", os.path.join(out, "timing.json"), hp)
