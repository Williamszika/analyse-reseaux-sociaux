"""Veille de la semaine : concurrents de la niche, vidéos qui explosent, sons et hashtags qui montent, idées à adapter.

python scripts/veille.py concurrent ajouter --reseau TikTok --handle @compte [--note "pourquoi le suivre"]
python scripts/veille.py concurrent liste
python scripts/veille.py analyser --posts <posts.json du concurrent 1> [<posts.json 2> …] [--tendances tendances.json]
      [--miens rapports/<dossier>/posts.json] [--date AAAA-MM-JJ] [--jours 14]
      -> $ANALYSES_DONNEES/veille/<date>.json et .md : par compte, vidéos qui font 3× sa médiane (« explosions »), durées,
         heures, formats ; sons et hashtags en hausse ; comparaison avec vos vidéos ; place pour 3 idées à adapter.

Chaque posts.json de concurrent : même format que le vôtre (formats.md), avec "compte": "@handle" en tête de chaque post
ou un fichier par compte nommé <handle>.json. Comptes publics seulement (créateurs, marques) : jamais de particulier.
tendances.json : [{"type": "son"|"hashtag"|"sujet", "nom": "...", "evolution": "+250 %", "source": "TikTok Creative Center"}]
"""
import argparse, datetime as dt, json, os, statistics as st, sys
from collections import Counter
from common import DONNEES, aujourdhui, isnum, load, save

P_CONC = os.path.join(DONNEES, "concurrents.json")
JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


def cmd_conc_ajouter(a):
    C = load(P_CONC, []) or []
    h = a.handle if a.handle.startswith("@") else "@" + a.handle
    if any(c["handle"].lower() == h.lower() and c["reseau"].lower() == a.reseau.lower() for c in C):
        sys.exit(f"{h} est déjà suivi")
    C.append({"reseau": a.reseau, "handle": h, "note": a.note, "ajoute": aujourdhui()})
    save(P_CONC, C)
    print(f"Suivi : {a.reseau} {h} ({len(C)} comptes)")


def cmd_conc_liste(a):
    for c in load(P_CONC, []) or []:
        print(f"{c['reseau']:<10} {c['handle']:<28} {c.get('note') or ''}")


def duree_cat(d):
    if not isnum(d):
        return "?"
    return "< 15 s" if d < 15 else "15–60 s" if d < 60 else "1–3 min" if d <= 180 else "> 3 min"


def cmd_analyser(a):
    jour = dt.date.fromisoformat(a.date or aujourdhui())
    debut = jour - dt.timedelta(days=a.jours)
    comptes = {}
    for f in a.posts:
        P = load(f, []) or []
        nom_def = "@" + os.path.splitext(os.path.basename(f))[0].lstrip("@")
        for p in P:
            comptes.setdefault(p.get("compte") or nom_def, []).append(p)
    if not comptes:
        sys.exit("Aucun post de concurrent")
    R = {"date": jour.isoformat(), "periode_j": a.jours, "comptes": [], "explosions": []}
    toutes = []
    for h, P in comptes.items():
        vues = [p["vues"] for p in P if isnum(p.get("vues"))]
        if not vues:
            continue
        m = st.median(vues)
        rec = [p for p in P if isnum(p.get("ts")) and dt.datetime.fromtimestamp(p["ts"]).date() >= debut]
        ex = sorted([p for p in rec if isnum(p.get("vues")) and m and p["vues"] >= 3 * m], key=lambda p: -p["vues"])
        R["comptes"].append({"compte": h, "posts": len(P), "recents": len(rec), "vues_mediane": m, "explosions": len(ex),
                             "duree_mediane": st.median([p["duree"] for p in P if isnum(p.get("duree"))] or [0])})
        for p in ex[:3]:
            d = dt.datetime.fromtimestamp(p["ts"])
            R["explosions"].append({"compte": h, "sujet": p.get("sujet"), "vues": p["vues"], "x_mediane": round(p["vues"] / m, 1),
                                    "duree": p.get("duree"), "jour": JOURS[d.weekday()], "heure": d.strftime("%H:%M"),
                                    "lien": p.get("lien"), "type": p.get("type")})
        toutes += rec
    R["explosions"].sort(key=lambda e: -e["x_mediane"])
    R["durees_explosions"] = Counter(duree_cat(e["duree"]) for e in R["explosions"]).most_common()
    R["jours_explosions"] = Counter(e["jour"] for e in R["explosions"]).most_common()
    R["tendances"] = load(a.tendances, []) if a.tendances else []
    if a.miens:
        M = load(a.miens, []) or []
        mv = [p["vues"] for p in M if isnum(p.get("vues"))]
        R["miens"] = {"vues_mediane": st.median(mv) if mv else None,
                      "duree_mediane": st.median([p["duree"] for p in M if isnum(p.get("duree"))] or [0])}
    R["idees_a_adapter"] = []  # écrites par Claude après lecture : 3 idées, chacune reliée à une explosion ou une tendance
    d = os.path.join(DONNEES, "veille")
    os.makedirs(d, exist_ok=True)
    save(os.path.join(d, f"{jour.isoformat()}.json"), R)
    L = [f"# Veille de la semaine — {jour.isoformat()} ({a.jours} derniers jours)", "", "## Comptes suivis", "",
         "| Compte | Vues médianes | Publications récentes | Explosions (≥ 3× médiane) | Durée médiane |", "|---|---|---|---|---|"]
    L += [f"| {c['compte']} | {c['vues_mediane']:.0f} | {c['recents']} | {c['explosions']} | {c['duree_mediane']:.0f} s |" for c in R["comptes"]]
    if "miens" in R and R["miens"]["vues_mediane"] is not None:
        L += [f"| **vous** | {R['miens']['vues_mediane']:.0f} | | | {R['miens']['duree_mediane']:.0f} s |"]
    L += ["", "## Ce qui explose", ""]
    L += [f"- {e['compte']} — « {e['sujet'] or '(sans légende)'} » : {e['vues']} vues ({e['x_mediane']}× sa médiane), "
          f"{e['duree'] or '?'} s, {e['jour']} {e['heure']}" for e in R["explosions"][:10]] or ["- rien cette semaine"]
    if R["durees_explosions"]:
        L += ["", "Durées des explosions : " + ", ".join(f"{k} ({n})" for k, n in R["durees_explosions"]),
              "Jours : " + ", ".join(f"{k} ({n})" for k, n in R["jours_explosions"])]
    if R["tendances"]:
        L += ["", "## Sons, hashtags et sujets qui montent", ""] + \
             [f"- {t.get('type')} : {t.get('nom')} ({t.get('evolution', '')}) — {t.get('source', '')}" for t in R["tendances"]]
    L += ["", "## 3 idées à adapter cette semaine", "", "(à écrire : chaque idée reliée à une explosion ou une tendance ci-dessus, "
          "adaptée à votre style, jamais copiée)"]
    open(os.path.join(d, f"{jour.isoformat()}.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
c = sp.add_parser("concurrent"); cs = c.add_subparsers(dest="sous", required=True)
ca = cs.add_parser("ajouter"); ca.add_argument("--reseau", required=True); ca.add_argument("--handle", required=True); ca.add_argument("--note")
cs.add_parser("liste")
an = sp.add_parser("analyser"); an.add_argument("--posts", nargs="+", required=True); an.add_argument("--tendances")
an.add_argument("--miens"); an.add_argument("--date"); an.add_argument("--jours", type=int, default=14)
a = ap.parse_args()
if a.cmd == "concurrent":
    {"ajouter": cmd_conc_ajouter, "liste": cmd_conc_liste}[a.sous](a)
else:
    cmd_analyser(a)
