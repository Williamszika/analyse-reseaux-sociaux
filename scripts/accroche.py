"""Laboratoire des 3 premières secondes : mesurer l'ouverture d'une vidéo, noter une accroche, comparer à la niche.

python scripts/accroche.py video <video.mp4> --out <dossier> [--nom <id>]
      -> accroche.json (mouvement, visage, détails à l'écran, début de la voix, volume) + planche_3s.png (7 images de 0 à 3 s, à regarder)
python scripts/accroche.py noter --phrase "<première phrase dite>" [--titre "<titre à l'écran>"] [--voix-debut 0.2] [--mouvement 0.12]
      -> note /10 avec le détail des 7 critères (sert AVANT de fabriquer : script, plan.json)
python scripts/accroche.py comparer --miens <dossier1> [<dossier2> …] --niche <dossierA> [<dossierB> …]
      -> médianes de vos ouvertures contre celles des vidéos qui marchent dans la niche, et les écarts à corriger

Les mesures sont des indices : regarder toujours planche_3s.png avec Read avant de conclure.
"""
import argparse, glob, json, os, re, statistics as st, subprocess, sys

INTRO = ["salut", "bonjour", "hello", "coucou", "bienvenue", "aujourd hui je", "dans cette video", "je vais vous", "je vais te",
         "abonne toi", "abonnez vous", "avant de commencer", "petite video"]
TENSION = ["jamais", "personne", "pourquoi", "mais", "plus jamais", "dernier", "derniere", "seul", "seule", "tout perdu",
           "honte", "peur", "erreur", "secret", "verite", "arrete", "stop", "trop tard", "le jour ou", "sans"]
T = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
SEUIL_MOUV = 0.035  # en dessous : image presque fixe (seuls les sous-titres changent)


def norm(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ?]", " ", t).split())


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def cmd_video(a):
    try:
        import cv2
        import numpy as np
    except ImportError:
        sys.exit("pip install opencv-python-headless numpy")
    os.makedirs(a.out, exist_ok=True)
    frames = []
    for t in T:
        p = os.path.join(a.out, f"_f{t:.1f}.png")
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", a.video, "-frames:v", "1", "-vf", "scale=360:-2", p])
        im = cv2.imread(p)
        if im is not None:
            frames.append((t, im))
    if not frames:
        sys.exit("Impossible de lire la vidéo")
    gris = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for _, f in frames]
    mouv = [float(np.mean(cv2.absdiff(gris[i], gris[i + 1]))) / 255 for i in range(len(gris) - 1)]
    visages = None
    try:
        casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
        if not casc.empty():
            visages = [len(casc.detectMultiScale(g, 1.1, 5, minSize=(30, 30))) for g in gris]
    except Exception:
        visages = None
    details = [float(np.mean(cv2.Canny(g, 100, 200) > 0)) for g in gris]
    # premier son (voix ou bruitage) : première fin de silence
    r = run(["ffmpeg", "-hide_banner", "-t", "6", "-i", a.video, "-af", "silencedetect=noise=-35dB:d=0.15", "-f", "null", "-"])
    fins = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    debuts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    voix = 0.0 if (not debuts or debuts[0] > 0.05) else (fins[0] if fins else None)
    vol = {}
    for nom, (s, d) in {"0_1s": (0, 1), "total": (0, 60)}.items():
        r = run(["ffmpeg", "-hide_banner", "-ss", str(s), "-t", str(d), "-i", a.video, "-af", "volumedetect", "-f", "null", "-"])
        m = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr)
        vol[nom] = float(m.group(1)) if m else None
    h = frames[0][1].shape[0]
    planche = np.hstack([cv2.putText(f.copy(), f"{t:.1f}s", (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 215, 255), 2)
                         for t, f in frames if f.shape[0] == h])
    cv2.imwrite(os.path.join(a.out, "planche_3s.png"), planche)
    for p in glob.glob(os.path.join(a.out, "_f*.png")):
        os.remove(p)
    res = {"video": os.path.basename(a.video), "nom": a.nom or os.path.splitext(os.path.basename(a.video))[0],
           "mouvement_0_1s": round(st.mean(mouv[:2]), 4), "mouvement_0_3s": round(st.mean(mouv), 4),
           "visage_0_1s": any(v > 0 for v in visages[:3]) if visages is not None else None,
           "visage_0_3s": sum(1 for v in visages if v > 0) if visages is not None else None,
           "details_ecran_0s": round(details[0], 4), "son_debut_s": voix,
           "volume_1re_seconde_db": vol.get("0_1s"), "volume_moyen_db": vol.get("total")}
    L = []
    if res["mouvement_0_1s"] < SEUIL_MOUV:
        L.append("image presque fixe pendant la 1re seconde : ajouter un mouvement (zoom, geste, objet qui bouge)")
    if voix is None or voix > 0.6:
        L.append(f"le premier son (voix ou bruitage) ne vient qu'à {voix if voix is not None else "> 6"} s : rien n'accroche l'oreille au début")
    if vol.get("0_1s") is not None and vol.get("total") is not None and vol["0_1s"] < vol["total"] - 6:
        L.append("la 1re seconde est bien plus calme que le reste : elle ne réveille pas le spectateur")
    if res["visage_0_1s"] is False:
        L.append("pas de visage dans la 1re seconde (un regard ou un visage retient mieux dans beaucoup de niches)")
    res["alertes"] = L
    json.dump(res, open(os.path.join(a.out, "accroche.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"Regarder : {os.path.join(a.out, 'planche_3s.png')}")


def noter(phrase, titre=None, voix_debut=None, mouvement=None):
    p = norm(phrase)
    mots = p.split()
    C = []

    def c(nom, pts, ok, pourquoi):
        C.append({"critere": nom, "points": pts if ok else 0, "sur": pts, "ok": ok, "pourquoi": pourquoi})

    c("voix ou texte animé dès la 1re demi-seconde", 2, voix_debut is not None and voix_debut <= 0.5,
      f"voix à {voix_debut} s" if voix_debut is not None else "début de la voix inconnu (mesurer avec « video »)")
    c("première phrase courte (12 mots au plus)", 1.5, 0 < len(mots) <= 12, f"{len(mots)} mots")
    tens = [t for t in TENSION if t in p] + (["chiffre"] if re.search(r"\d|\b(deux|deuxieme|trois|troisieme|quatre|cinq|six|sept|huit|neuf|dix|zero|cent|mille|premier|premiere|derniere fois)\b", p) else []) \
           + (["question"] if "?" in phrase else [])
    c("tension dès la 1re phrase (conflit, chiffre, question, négation)", 1.5, bool(tens), ", ".join(tens[:4]) or "aucune")
    c("parle au spectateur (tu, toi, ton, ta)", 1, bool(re.search(r"\b(tu|toi|ton|ta|tes|t)\b", p)), "")
    nt = len(norm(titre).split()) if titre else 0
    c("titre à l'écran de 3 à 6 mots", 1, 3 <= nt <= 6, f"{nt} mots" if titre else "pas de titre")
    c("mouvement dans la 1re seconde", 1.5, mouvement is not None and mouvement >= SEUIL_MOUV,
      f"indice {mouvement}" if mouvement is not None else "inconnu (mesurer avec « video »)")
    intro = [i for i in INTRO if p.startswith(i) or f" {i} " in f" {p[:40]} "]
    c("aucune formule d'introduction (salut, aujourd'hui je vais…)", 1.5, not intro, ", ".join(intro) or "")
    total = round(sum(x["points"] for x in C), 1)
    return {"note": total, "sur": 10, "criteres": C,
            "a_corriger": [x["critere"] for x in C if not x["ok"]]}


def cmd_noter(a):
    r = noter(a.phrase, a.titre, a.voix_debut, a.mouvement)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    print(f"\nNote d'accroche : {r['note']}/10" + (" — à retravailler avant de fabriquer (8 visé)" if r["note"] < 8 else ""))


def charge(dirs):
    out = []
    for d in dirs:
        for f in glob.glob(os.path.join(d, "**", "accroche.json"), recursive=True) + glob.glob(os.path.join(d, "accroche.json")):
            try:
                out.append(json.load(open(f, encoding="utf-8")))
            except Exception:
                pass
    uniq = {json.dumps(x, sort_keys=True): x for x in out}
    return list(uniq.values())


def cmd_comparer(a):
    M, N = charge(a.miens), charge(a.niche)
    if not M or not N:
        sys.exit("Il faut des accroche.json des deux côtés (accroche.py video …)")
    def med(L, k):
        v = [x[k] for x in L if isinstance(x.get(k), (int, float)) and not isinstance(x.get(k), bool)]
        return round(st.median(v), 3) if v else None
    def part(L, k):
        v = [x for x in L if x.get(k) is not None]
        return round(100 * sum(1 for x in v if x.get(k)) / len(v)) if v else None
    lignes = [("mouvement 0–1 s", med(M, "mouvement_0_1s"), med(N, "mouvement_0_1s")),
              ("premier son (s)", med(M, "son_debut_s"), med(N, "son_debut_s")),
              ("visage dans la 1re seconde (%)", part(M, "visage_0_1s"), part(N, "visage_0_1s")),
              ("détails à l'écran à 0 s", med(M, "details_ecran_0s"), med(N, "details_ecran_0s"))]
    print(f"{'':34} {'vous (' + str(len(M)) + ')':>12} {'niche (' + str(len(N)) + ')':>12}")
    for n, x, y in lignes:
        print(f"{n:34} {str(x):>12} {str(y):>12}")
    E = []
    if lignes[0][1] is not None and lignes[0][2] and lignes[0][1] < 0.7 * lignes[0][2]:
        E.append("vos premières images bougent beaucoup moins que celles de la niche")
    if lignes[1][1] is not None and lignes[1][2] is not None and lignes[1][1] > lignes[1][2] + 0.4:
        E.append("votre premier son arrive plus tard que dans la niche")
    if lignes[2][1] is not None and lignes[2][2] is not None and lignes[2][1] + 25 < lignes[2][2]:
        E.append("la niche montre plus souvent un visage dès la 1re seconde")
    print("\nÉcarts : " + ("; ".join(E) if E else "aucun écart net sur ces mesures — comparer les planches à l'œil"))
    if a.out:
        json.dump({"miens": len(M), "niche": len(N), "lignes": lignes, "ecarts": E}, open(a.out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
v = sp.add_parser("video"); v.add_argument("video"); v.add_argument("--out", required=True); v.add_argument("--nom")
n = sp.add_parser("noter"); n.add_argument("--phrase", required=True); n.add_argument("--titre")
n.add_argument("--voix-debut", type=float); n.add_argument("--mouvement", type=float)
c = sp.add_parser("comparer"); c.add_argument("--miens", nargs="+", required=True); c.add_argument("--niche", nargs="+", required=True)
c.add_argument("--out")
a = ap.parse_args()
{"video": cmd_video, "noter": cmd_noter, "comparer": cmd_comparer}[a.cmd](a)
