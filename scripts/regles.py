"""Règles des plateformes, toujours sourcées et datées (reference/plateformes.json + mises à jour de l'utilisateur).

python scripts/regles.py liste [--reseau TikTok] [--theme algorithme|recherche|monetisation|…]
python scripts/regles.py verifier [--jours 45]          -> règles trop anciennes à revérifier (recherche web) ; code 3 s'il y en a
python scripts/regles.py maj --id <id> [--regle "…"] [--consequence "…"] [--source <url>] [--fiabilite officielle|presse|communaute]
      [--reseau … --theme …]   -> écrit dans $ANALYSES_DONNEES/plateformes.json (prioritaire sur la boîte à outils), date du jour
python scripts/regles.py pour-rapport --reseau TikTok   -> lignes prêtes pour analysis.json > regles_plateforme

Une règle « communaute » se présente comme une tendance observée, jamais comme un fait de la plateforme.
"""
import argparse, datetime as dt, json, os, sys
from common import DONNEES, aujourdhui, load, save

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference", "plateformes.json")
PERSO = os.path.join(DONNEES, "plateformes.json")


def toutes():
    R = {r["id"]: r for r in (load(BASE, {}) or {}).get("regles", [])}
    for r in (load(PERSO, {}) or {}).get("regles", []):
        if r["id"] not in R or r.get("verifie", "") >= R[r["id"]].get("verifie", ""):
            R[r["id"]] = {**R.get(r["id"], {}), **r}
    return list(R.values())


def filtre(a):
    return [r for r in toutes() if (not getattr(a, "reseau", None) or r["reseau"].lower() == a.reseau.lower())
            and (not getattr(a, "theme", None) or r["theme"] == a.theme)]


def cmd_liste(a):
    for r in filtre(a):
        print(f"[{r['reseau']} · {r['theme']} · {r['fiabilite']} · vérifié {r['verifie']}] {r['regle']}\n   → {r.get('consequence', '')}\n   {r['source']}")


def cmd_verifier(a):
    lim = (dt.date.fromisoformat(aujourdhui()) - dt.timedelta(days=a.jours)).isoformat()
    vieux = [r for r in toutes() if r.get("verifie", "") < lim]
    for r in vieux:
        print(f"À revérifier ({r['verifie']}) : {r['id']} — {r['reseau']} — {r['regle'][:90]}…")
    print(f"{len(vieux)} règle(s) à revérifier sur {len(toutes())}")
    sys.exit(3 if vieux else 0)


def cmd_maj(a):
    P = load(PERSO, {"regles": []}) or {"regles": []}
    exist = next((r for r in toutes() if r["id"] == a.id), {})
    if not exist and not (a.reseau and a.theme and a.regle and a.source):
        sys.exit("Nouvelle règle : --reseau, --theme, --regle et --source sont obligatoires")
    r = {**exist, "id": a.id, "verifie": aujourdhui()}
    for k in ("regle", "consequence", "source", "fiabilite", "reseau", "theme"):
        if getattr(a, k):
            r[k] = getattr(a, k)
    if not r.get("source"):
        sys.exit("Une règle sans source n'est pas enregistrée")
    P["regles"] = [x for x in P["regles"] if x["id"] != a.id] + [r]
    save(PERSO, P)
    print(f"Règle {a.id} mise à jour (vérifiée le {r['verifie']})")


def cmd_pour_rapport(a):
    out = []
    for r in filtre(a):
        prefixe = "" if r["fiabilite"] == "officielle" else "Tendance observée par les créateurs : " if r["fiabilite"] == "communaute" else "Selon la presse spécialisée : "
        out.append({"texte": prefixe + r["regle"], "consequence": r.get("consequence"), "source": r["source"], "verifie": r["verifie"]})
    print(json.dumps(out, ensure_ascii=False, indent=1))


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
l = sp.add_parser("liste"); l.add_argument("--reseau"); l.add_argument("--theme")
v = sp.add_parser("verifier"); v.add_argument("--jours", type=int, default=45)
m = sp.add_parser("maj"); m.add_argument("--id", required=True)
for k in ("regle", "consequence", "source", "reseau", "theme"):
    m.add_argument("--" + k)
m.add_argument("--fiabilite", choices=["officielle", "presse", "communaute"])
p = sp.add_parser("pour-rapport"); p.add_argument("--reseau", required=True); p.add_argument("--theme")
a = ap.parse_args()
{"liste": cmd_liste, "verifier": cmd_verifier, "maj": cmd_maj, "pour-rapport": cmd_pour_rapport}[a.cmd](a)
