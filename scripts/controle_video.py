"""Contrôle complet d'une vidéo livrée, avant publication, contre le cahier des charges de l'utilisateur.

python scripts/controle_video.py <video.mp4> [--srt sous-titres.srt] [--out <dossier>] [--vers <dossier>] [--titre "..."]

Cahier des charges : profil.json > equipe > cahier_video (sinon valeurs par défaut ci-dessous). Mesures :
  format et durée · volume global (LUFS) · titre seul à l'écran avant la voix · débit de la voix (mots/s)
  · arrêts entre les phrases · bruitages trop forts par rapport à la voix · silences audibles
  · planches d'images (ouverture 0-4 s + toute la vidéo) à REGARDER pour le design des mots, le titre et le cadrage.
Sans --srt, le titre, le débit et les arrêts sont estimés à partir des silences du son (moins précis).
Écrit controle.json, controle.md, ouverture.png, planche.png dans --out (et les copie dans --vers).
Étape suivante : REGARDER ouverture.png et planche.png (Read), écrire ses observations dans un fichier et relancer avec --regard.
Code de sortie : 0 si tout est respecté, 3 s'il reste au moins un point non respecté.
"""
import argparse, json, os, re, shutil, statistics as st, subprocess, sys
from common import ffmpeg, profil, save, aujourdhui

DEFAUT = {"duree_max_s": 180, "format": "1080x1920", "lufs_cible": -14, "lufs_tolerance": 1.5,
          "titre_avant_voix_s": 1.5, "debit_max_mots_s": 2.5, "pause_phrase_min_s": 0.5, "part_phrases_avec_pause": 0.7,
          "pic_bruitage_max_db": 4.0, "bruit_dans_arrets_max_db": -6.0, "silence_seuil_db": -35}

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--srt")
ap.add_argument("--out")
ap.add_argument("--vers")
ap.add_argument("--titre")
ap.add_argument("--regard", help="fichier texte : ce que Claude a vu sur ouverture.png et planche.png (une ligne par observation)")
a = ap.parse_args()
C = {**DEFAUT, **((profil().get("equipe") or {}).get("cahier_video") or {})}
FF = ffmpeg()
nom = os.path.splitext(os.path.basename(a.video))[0]
out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.video)), f"controle_{nom}")
os.makedirs(out, exist_ok=True)


def run(args):
    return subprocess.run([FF, "-hide_banner", "-nostats"] + args, capture_output=True, text=True).stderr


info = run(["-i", a.video])
m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
duree = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None
m = re.search(r"Video:.*?(\d{3,5})x(\d{3,5})", info)
taille = f"{m.group(1)}x{m.group(2)}" if m else None
son = "Audio:" in info

points = []


def point(cle, lib, ok, mesure, cible, conseil=""):
    points.append({"cle": cle, "point": lib, "ok": ok, "mesure": mesure, "cible": cible, "conseil": conseil})


point("format", "Format vertical", taille == C["format"], taille or "?", C["format"])
point("duree", "Durée", duree is not None and duree <= C["duree_max_s"], f"{duree:.1f} s" if duree else "?",
      f"≤ {C['duree_max_s']} s")

# --- Son : volume global, momentané, silences
lufs, M, silences = None, [], []
if son:
    e = run(["-i", a.video, "-af", "ebur128=metadata=1,ametadata=print:key=lavfi.r128.M", "-f", "null", "-"])
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", e)
    lufs = float(m.group(1)) if m else None
    ts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", e)]
    Ms = [float(x) for x in re.findall(r"lavfi\.r128\.M=(-?[\d.]+)", e)]
    M = list(zip(ts, Ms))
    s = run(["-i", a.video, "-af", f"silencedetect=noise={C['silence_seuil_db']}dB:d=0.4", "-f", "null", "-"])
    deb = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", s)]
    fin = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", s)]
    silences = list(zip(deb, fin))
if lufs is not None:
    point("volume", "Volume global", abs(lufs - C["lufs_cible"]) <= C["lufs_tolerance"], f"{lufs:.1f} LUFS",
          f"{C['lufs_cible']} ± {C['lufs_tolerance']} LUFS")
else:
    point("volume", "Volume global", False, "pas de piste son" if not son else "?", f"{C['lufs_cible']} LUFS")

# --- Sous-titres (voix) : début, débit, arrêts
cues = []
if a.srt and os.path.exists(a.srt):
    txt = open(a.srt, encoding="utf-8-sig").read().replace("\r", "")

    def t(x):
        h, mi, se = x.replace(",", ".").split(":")
        return int(h) * 3600 + int(mi) * 60 + float(se)

    for d1, d2, body in re.findall(r"(\d\d:\d\d:\d\d[,.]\d+) --> (\d\d:\d\d:\d\d[,.]\d+)[^\n]*\n(.*?)(?:\n\n|\Z)", txt, re.S):
        body = re.sub(r"<[^>]+>|\{[^}]+\}", "", body).replace("\n", " ").strip()
        if body:
            cues.append((t(d1), t(d2), body))

if cues:
    debut_voix = cues[0][0]
    source = "sous-titres"
elif silences and silences[0][0] <= 0.05:
    debut_voix = silences[0][1]
    source = "silences du son (estimation)"
else:
    debut_voix = 0.0
    source = "son (aucun silence au début)"
point("titre", "Titre seul avant la voix", debut_voix >= C["titre_avant_voix_s"], f"voix à {debut_voix:.1f} s ({source})",
      f"≥ {C['titre_avant_voix_s']} s", "Afficher le titre seul, puis lancer la voix")

if cues:
    mots = sum(len(c[2].split()) for c in cues)
    parole = sum(max(0.0, c[1] - c[0]) for c in cues)
    debit = mots / parole if parole else None
    point("debit", "Voix posée (débit)", debit is not None and debit <= C["debit_max_mots_s"],
          f"{debit:.2f} mots/s pendant la parole" if debit else "?", f"≤ {C['debit_max_mots_s']} mots/s",
          "Ralentir la voix (registres calmes, vitesse plus basse)")
    fins = [i for i in range(len(cues) - 1) if re.search(r"[.!?…»]\s*$", cues[i][2])]
    gaps = [cues[i + 1][0] - cues[i][1] for i in fins]
    avec = sum(g >= C["pause_phrase_min_s"] for g in gaps)
    part = avec / len(gaps) if gaps else 0
    point("arrets", "Arrêts entre les phrases", bool(gaps) and part >= C["part_phrases_avec_pause"],
          f"{avec}/{len(gaps)} fins de phrase suivies d'un arrêt ≥ {C['pause_phrase_min_s']} s ({100 * part:.0f} %)",
          f"≥ {100 * C['part_phrases_avec_pause']:.0f} %", "Ajouter pause_after après chaque phrase")
else:
    longs = [b - a_ for a_, b in silences if b - a_ >= C["pause_phrase_min_s"]]
    point("arrets", "Arrêts entre les phrases", None, f"{len(longs)} silences audibles ≥ {C['pause_phrase_min_s']} s (sans sous-titres)",
          "à confirmer avec --srt")

# --- Bruitages trop forts : (1) pics au-dessus du niveau habituel de la voix pendant qu'elle parle,
#     (2) sons dans les arrêts presque aussi forts que la voix (avec sous-titres seulement)
pics_out, arrets_bruyants = [], []
if M:
    def parle(tt):
        return any(c0 <= tt <= c1 for c0, c1, _ in cues)
    voix = [v for tt, v in M if v > -60 and (parle(tt) if cues else True)]
    med = st.median(voix) if voix else None
    pics = []
    for tt, v in M:
        if med is not None and v > med + C["pic_bruitage_max_db"]:
            if pics and tt - pics[-1][0] < 1.0:
                pics[-1] = (pics[-1][0], max(pics[-1][1], v))
            else:
                pics.append((tt, v))
    pics_out = [{"t": round(p[0], 1), "db_au_dessus": round(p[1] - med, 1)} for p in pics]
    if cues and med is not None:
        for i in range(len(cues) - 1):
            g0, g1 = cues[i][1] + 0.15, cues[i + 1][0] - 0.05
            if g1 - g0 >= 0.3:
                vals = [v for tt, v in M if g0 <= tt <= g1]
                if vals and max(vals) > med + C["bruit_dans_arrets_max_db"]:
                    arrets_bruyants.append({"t": round(g0, 1), "db_vs_voix": round(max(vals) - med, 1)})
    total_arrets = sum(1 for i in range(len(cues) - 1) if cues[i + 1][0] - cues[i][1] - 0.2 >= 0.3) if cues else 0
    ok = len(pics) <= 2 and (not cues or len(arrets_bruyants) <= max(1, total_arrets // 5))
    mes = f"{len(pics)} pic(s) > +{C['pic_bruitage_max_db']:g} dB au-dessus de la voix ({med:.1f} LUFS)"
    if pics:
        mes += " à " + ", ".join(f"{p[0]:.0f} s" for p in pics[:6]) + ("…" if len(pics) > 6 else "")
    if cues:
        mes += f" ; {len(arrets_bruyants)}/{total_arrets} arrêts où un son dépasse voix {C['bruit_dans_arrets_max_db']:g} dB"
    point("bruitages", "Bruitages sous la voix", ok, mes,
          f"≤ 2 pics ; sons des arrêts ≥ {-C['bruit_dans_arrets_max_db']:g} dB sous la voix",
          "Baisser sfx/foley et renforcer la compression sous la voix")
point("silences", "Silences audibles (pas d'encombrement)", None if not son else len(silences) >= max(3, int((duree or 60) / 20)),
      f"{len(silences)} silences ≥ 0,4 s sous {C['silence_seuil_db']} dB", f"au moins 1 toutes les 20 s",
      "Baisser l'ambiance de pièce et les nappes pendant les arrêts")

# --- Planches à regarder (design du titre et des mots)
ouv = []
for tt in [0, 0.5, 1, 1.5, 2, 3, 4]:
    if duree and tt < duree:
        p = os.path.join(out, f"_o_{tt}.png")
        run(["-y", "-ss", str(tt), "-i", a.video, "-frames:v", "1", "-vf", "scale=270:-1", p])
        if os.path.exists(p):
            ouv.append(p)
pl = []
if duree:
    n = 12
    for i in range(n):
        tt = duree * (i + 0.5) / n
        p = os.path.join(out, f"_p_{i:02d}.png")
        run(["-y", "-ss", f"{tt:.2f}", "-i", a.video, "-frames:v", "1", "-vf", "scale=270:-1", p])
        if os.path.exists(p):
            pl.append((tt, p))
try:
    from PIL import Image, ImageDraw

    def bande(chemins, cols, legendes, dest):
        ims = [Image.open(c) for c in chemins]
        if not ims:
            return None
        w, h = ims[0].size
        rows = (len(ims) + cols - 1) // cols
        S = Image.new("RGB", (w * cols, (h + 22) * rows), "white")
        d = ImageDraw.Draw(S)
        for i, im in enumerate(ims):
            x, y = (i % cols) * w, (i // cols) * (h + 22)
            S.paste(im, (x, y + 22))
            d.text((x + 6, y + 4), legendes[i], fill="black")
        S.save(dest)
        for c in chemins:
            os.remove(c)
        return dest

    bande(ouv, len(ouv), [f"{t} s" for t in [0, 0.5, 1, 1.5, 2, 3, 4][:len(ouv)]], os.path.join(out, "ouverture.png"))
    bande([p for _, p in pl], 6, [f"{int(t // 60)}:{int(t % 60):02d}" for t, _ in pl], os.path.join(out, "planche.png"))
except Exception as e:
    print("Planches non créées :", e)
point("design", "Design du titre et des mots", None, "à regarder : ouverture.png et planche.png",
      "titre grand et lisible, un mot-clé mis en valeur par phrase, zones sûres respectées")

# --- Sortie
ko = [p for p in points if p["ok"] is False]
res = {"video": os.path.basename(a.video), "titre": a.titre or nom, "date": aujourdhui(), "cahier": C,
       "duree_s": duree, "format": taille, "lufs": lufs, "debut_voix_s": debut_voix, "pics_bruitages": pics_out, "arrets_bruyants": arrets_bruyants,
       "points": points, "respecte": not ko}
save(os.path.join(out, "controle.json"), res)
sym = {True: "✅", False: "❌", None: "👁"}
L = [f"# Contrôle vidéo — {res['titre']} — {res['date']}", "",
     f"Fichier : `{res['video']}` · {taille} · {duree:.1f} s" if duree else f"Fichier : `{res['video']}`", "",
     "| | Point | Mesure | Cible | À faire |", "|---|---|---|---|---|"]
L += [f"| {sym[p['ok']]} | {p['point']} | {p['mesure']} | {p['cible']} | {p['conseil'] if p['ok'] is False else ''} |" for p in points]
L += ["", f"**{len(ko)} point(s) non respecté(s).**" if ko else "**Tout ce qui se mesure est respecté.**",
      "👁 = à vérifier à l'œil sur `ouverture.png` et `planche.png`."]
regard = [l.strip("- ").strip() for l in open(a.regard, encoding="utf-8")] if a.regard and os.path.exists(a.regard) else []
regard = [l for l in regard if l]
if regard:
    L += ["", "## Ce que montrent les images"] + [f"- {l}" for l in regard]
    res["regard"] = regard
    save(os.path.join(out, "controle.json"), res)
open(os.path.join(out, "controle.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
if a.vers:
    os.makedirs(a.vers, exist_ok=True)
    for f in ["controle.json", "controle.md", "ouverture.png", "planche.png"]:
        if os.path.exists(os.path.join(out, f)):
            shutil.copy(os.path.join(out, f), os.path.join(a.vers, f))
print("\n".join(L))
print("->", out)
sys.exit(3 if ko else 0)
