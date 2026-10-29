"""Mesures objectives : plans, étalonnage, son, moments les plus revus, engagement, planches.
python scripts/measure.py cache/<dossier> [--force]"""
import argparse, glob, os, re, subprocess
import numpy as np
from PIL import Image, ImageDraw
from common import BASE, ffmpeg, load, save, hms

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--force", action="store_true")
a = ap.parse_args()
d = a.dir if os.path.isabs(a.dir) else os.path.join(BASE, a.dir)
out = os.path.join(d, "measures.json")
if os.path.exists(out) and not a.force:
    print("Déjà mesuré (cache) ->", out)
    raise SystemExit
meta = load(os.path.join(d, "meta.json"), {})
dur = meta.get("duration") or 0
vids = glob.glob(os.path.join(d, "video.*"))
if not vids:
    raise SystemExit("Pas de vidéo : relancer fetch.py avec --video")
vid, FF, res = vids[0], ffmpeg(), {}

# Plans
limit = 900 if dur > 3600 else None
cmd = [FF, "-hide_banner", "-nostats"] + (["-t", str(limit)] if limit else []) + \
      ["-i", vid, "-vf", "scale=320:-2,select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"]
err = subprocess.run(cmd, capture_output=True, text=True).stderr
cuts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", err)]
span = limit or dur or (cuts[-1] if cuts else 60)
res["plans"] = {"coupes": len(cuts), "periode_analysee_s": span,
                "coupes_par_minute": round(len(cuts) / (span / 60), 2) if span else None,
                "duree_moyenne_plan_s": round(span / (len(cuts) + 1), 1),
                "coupes_5_premieres_s": sum(1 for c in cuts if c < 5)}

# Images
fd = os.path.join(d, "frames")
os.makedirs(fd, exist_ok=True)
step = max(dur / 36, 3) if dur else 10
ts = [round(i * step + 1, 1) for i in range(36) if not dur or i * step + 1 < dur]
if cuts:
    ts += [round(c + 0.4, 1) for c in cuts[::max(1, len(cuts) // 12)][:12]]
ts = sorted(set(ts))[:48]
paths = []
for t in ts:
    p = os.path.join(fd, f"f_{int(t*10):07d}.jpg")
    if not os.path.exists(p):
        subprocess.run([FF, "-loglevel", "error", "-y", "-ss", str(t), "-i", vid,
                        "-frames:v", "1", "-vf", "scale=480:-2", p])
    if os.path.exists(p):
        paths.append((t, p))

# Étalonnage
stats = []
for t, p in paths:
    img = Image.open(p).convert("RGB")
    im = np.asarray(img).astype(float)
    lum = 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
    sat = np.asarray(img.convert("HSV")).astype(float)[..., 1]
    stats.append({"t": t, "luminance": round(float(lum.mean()), 1), "contraste": round(float(lum.std()), 1),
                  "chaleur": round(float((im[..., 0] - im[..., 2]).mean()), 1),
                  "saturation": round(float(sat.mean()), 1),
                  "noirs_ecrases_pct": round(float((lum < 10).mean() * 100), 1),
                  "hautes_lumieres_brulees_pct": round(float((lum > 245).mean() * 100), 1)})
if stats:
    m = lambda k: round(float(np.mean([s[k] for s in stats])), 1)
    res["etalonnage"] = {"luminance_moy": m("luminance"), "contraste_moy": m("contraste"),
                         "chaleur_moy": m("chaleur"), "saturation_moy": m("saturation"),
                         "noirs_ecrases_pct": m("noirs_ecrases_pct"),
                         "hautes_lumieres_brulees_pct": m("hautes_lumieres_brulees_pct"),
                         "variation_luminance": round(float(np.std([s["luminance"] for s in stats])), 1),
                         "par_image": stats}

# Planches 4x3
sheets = []
for k in range(0, len(paths), 12):
    chunk = paths[k:k + 12]
    w, h = Image.open(chunk[0][1]).size
    sheet = Image.new("RGB", (w * 4, h * 3), "black")
    dr = ImageDraw.Draw(sheet)
    for j, (t, p) in enumerate(chunk):
        x, y = (j % 4) * w, (j // 4) * h
        sheet.paste(Image.open(p).convert("RGB").resize((w, h)), (x, y))
        dr.rectangle([x, y, x + 64, y + 16], fill="black")
        dr.text((x + 4, y + 2), hms(t), fill="white")
    sp = os.path.join(d, f"planche_{k//12+1:02d}.jpg")
    sheet.save(sp, quality=85)
    sheets.append(sp)
res["planches"] = sheets

# Son
ae = subprocess.run([FF, "-hide_banner", "-nostats", "-i", vid, "-vn", "-af",
                     "ebur128=framelog=quiet,silencedetect=noise=-35dB:d=0.7", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
I = re.findall(r"I:\s+(-?[\d.]+) LUFS", ae)
LRA = re.findall(r"LRA:\s+([\d.]+) LU", ae)
sil = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", ae)]
res["son"] = {"lufs_integre": float(I[-1]) if I else None, "plage_dynamique_LU": float(LRA[-1]) if LRA else None,
              "silences": len(sil), "silence_total_s": round(sum(sil), 1),
              "plus_long_silence_s": round(max(sil), 1) if sil else 0}

# Moments les plus revus
hm = meta.get("heatmap") or []
if hm:
    body = [x for x in hm if x["start_time"] > dur * 0.05]
    fmt = lambda x: {"t": hms(x["start_time"]), "valeur": round(x["value"], 2)}
    res["plus_revus"] = {"pics": [fmt(x) for x in sorted(hm, key=lambda x: -x["value"])[:5]],
                         "creux": [fmt(x) for x in sorted(body, key=lambda x: x["value"])[:5]]}

# Engagement
v = meta.get("view_count") or 0
if v:
    res["engagement"] = {"likes_par_vue_pct": round(100 * (meta.get("like_count") or 0) / v, 2),
                         "commentaires_par_vue_pct": round(100 * (meta.get("comment_count") or 0) / v, 3)}

save(out, res)
print({k: v for k, v in res.items() if k not in ("etalonnage", "planches")})
if "etalonnage" in res:
    print({k: v for k, v in res["etalonnage"].items() if k != "par_image"})
print("Planches :", sheets)
