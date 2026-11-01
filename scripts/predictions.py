"""Des conseils qui se corrigent tout seuls : chaque recommandation reçoit une prévision chiffrée, vérifiée plus tard.

python scripts/predictions.py ajouter --compte <clé> --reco "<la recommandation>" --type accroche|duree|horaire|seo|serie|profil|autre
      --metrique moy_s|vues|eng|complet_pct|abonnes --base <valeur actuelle> --cible <valeur prévue> [--echeance AAAA-MM-JJ | --jours 14]
python scripts/predictions.py verifier rapports/<dossier> [--compte <clé>] [--date AAAA-MM-JJ]
      -> pour chaque prévision arrivée à échéance : médiane de la métrique sur les vidéos publiées APRÈS la prévision
         (ou abonnés du dernier relevé), verdict réussie (cible atteinte), partielle (mieux que la base) ou ratée
python scripts/predictions.py bilan [--compte <clé>]   -> taux de réussite par type de conseil : garder ce qui marche, revoir le reste

Fichier : $ANALYSES_DONNEES/predictions.json. Le rapport cite le bilan (« nos conseils sur l'accroche ont marché 3 fois sur 4 »).
"""
import argparse, datetime as dt, json, os, statistics as st, sys
from collections import defaultdict
from common import DONNEES, aujourdhui, chemin, isnum, load, save

P = os.path.join(DONNEES, "predictions.json")


def eng(p):
    if isnum(p.get("vues")) and p["vues"] and all(isnum(p.get(k)) for k in ("likes", "commentaires", "partages")):
        return 100 * (p["likes"] + p["commentaires"] + p["partages"]) / p["vues"]
    return None


def cmd_ajouter(a):
    L = load(P, []) or []
    ech = a.echeance or (dt.date.fromisoformat(aujourdhui()) + dt.timedelta(days=a.jours)).isoformat()
    n = (max(x["n"] for x in L) + 1) if L else 1
    L.append({"n": n, "compte": a.compte, "reco": a.reco, "type": a.type, "metrique": a.metrique, "base": a.base,
              "cible": a.cible, "cree": aujourdhui(), "echeance": ech, "statut": "en_cours"})
    save(P, L)
    print(f"Prévision n° {n} : {a.metrique} de {a.base} à {a.cible} d'ici le {ech} — « {a.reco} »")


def cmd_verifier(a):
    L = load(P, []) or []
    d = chemin(a.dir)
    posts = load(os.path.join(d, "posts.json"), []) or []
    resume = load(os.path.join(d, "resume.json"), {}) or {}
    jour = a.date or aujourdhui()
    for x in L:
        if x["statut"] != "en_cours" or (a.compte and x["compte"] != a.compte) or x["echeance"] > jour:
            continue
        depuis = dt.datetime.fromisoformat(x["cree"]).timestamp()
        if x["metrique"] == "abonnes":
            val = resume.get("abonnes")
            n = 1 if isnum(val) else 0
        else:
            apres = [p for p in posts if isnum(p.get("ts")) and p["ts"] >= depuis]
            vals = [eng(p) if x["metrique"] == "eng" else p.get(x["metrique"]) for p in apres]
            vals = [v for v in vals if isnum(v)]
            n = len(vals)
            val = round(st.median(vals), 2) if vals else None
        if val is None:
            x["note"] = "pas encore de vidéo publiée depuis la prévision"
            continue
        monte = x["cible"] >= x["base"]
        ok = val >= x["cible"] if monte else val <= x["cible"]
        mieux = val > x["base"] if monte else val < x["base"]
        x.update(statut="reussie" if ok else "partielle" if mieux else "ratee", resultat=val, n_videos=n, verifie=jour)
        print(f"n° {x['n']} [{x['type']}] {x['metrique']} : base {x['base']}, cible {x['cible']}, obtenu {val} ({n} vidéo(s)) → {x['statut']}")
    save(P, L)


def cmd_bilan(a):
    L = [x for x in (load(P, []) or []) if not a.compte or x["compte"] == a.compte]
    par = defaultdict(lambda: {"reussie": 0, "partielle": 0, "ratee": 0, "en_cours": 0})
    for x in L:
        par[x["type"]][x["statut"]] += 1
    if not L:
        print("Aucune prévision")
        return
    print(f"{'Type de conseil':<14} {'réussies':>9} {'partielles':>11} {'ratées':>7} {'en cours':>9}")
    out = {}
    for t, c in sorted(par.items()):
        print(f"{t:<14} {c['reussie']:>9} {c['partielle']:>11} {c['ratee']:>7} {c['en_cours']:>9}")
        fin = c["reussie"] + c["partielle"] + c["ratee"]
        out[t] = {**c, "taux_reussite": round(100 * (c["reussie"] + 0.5 * c["partielle"]) / fin) if fin else None}
    for t, c in out.items():
        if c["taux_reussite"] is not None and c["taux_reussite"] < 40 and (c["ratee"] + c["partielle"] + c["reussie"]) >= 3:
            print(f"→ Les conseils « {t} » marchent mal ({c['taux_reussite']} %) : les revoir avant de les redonner")
    print(json.dumps(out, ensure_ascii=False))


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
j = sp.add_parser("ajouter"); j.add_argument("--compte", required=True); j.add_argument("--reco", required=True)
j.add_argument("--type", required=True, choices=["accroche", "duree", "horaire", "seo", "serie", "profil", "autre"])
j.add_argument("--metrique", required=True, choices=["moy_s", "vues", "eng", "complet_pct", "abonnes"])
j.add_argument("--base", type=float, required=True); j.add_argument("--cible", type=float, required=True)
j.add_argument("--echeance"); j.add_argument("--jours", type=int, default=14)
v = sp.add_parser("verifier"); v.add_argument("dir"); v.add_argument("--compte"); v.add_argument("--date")
b = sp.add_parser("bilan"); b.add_argument("--compte")
a = ap.parse_args()
{"ajouter": cmd_ajouter, "verifier": cmd_verifier, "bilan": cmd_bilan}[a.cmd](a)
