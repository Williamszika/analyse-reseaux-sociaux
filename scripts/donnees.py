"""Espace de données d'un utilisateur : création, ajout de compte, vérification.

python scripts/donnees.py init --nom "Awa" [--appel "Awa"] [--tutoiement] [--langue fr] [--fuseau Europe/Paris]
                               [--marque-client "Mon agence · Audit"]
python scripts/donnees.py compte --reseau TikTok --handle @awa [--url ...] [--public "..."] [--fuseaux-public Africa/Abidjan,Europe/Paris]
                                 [--objectif "..."] [--metricool <brandId>] [--pas-a-moi]
python scripts/donnees.py verifier

L'espace est $ANALYSES_DONNEES (défaut ~/Analyses/donnees). Il ne contient jamais de mot de passe, code, jeton ou cookie.
"""
import argparse, os, re, sys
from zoneinfo import ZoneInfo
from common import DONNEES, load, save, reseau, VERSION

P_PROFIL = os.path.join(DONNEES, "profil.json")
P_COMPTES = os.path.join(DONNEES, "comptes.json")
INTERDIT = re.compile(r"(pass(word|e)?|mot.?de.?passe|token|jeton|cookie|secret|api.?key|sessionid)", re.I)


def fuseau_ok(tz):
    try:
        ZoneInfo(tz)
        return True
    except Exception:
        return False


def cle_compte(res, handle):
    return f"{reseau(res)['cle']}_{handle.lstrip('@').strip().lower()}"


def cmd_init(a):
    p = load(P_PROFIL, {}) or {}
    u = p.setdefault("utilisateur", {})
    u["nom"] = a.nom or u.get("nom")
    u["appel"] = a.appel or u.get("appel") or u["nom"]
    if a.tutoiement is not None:
        u["tutoiement"] = a.tutoiement
    u.setdefault("tutoiement", False)
    u["langue"] = a.langue or u.get("langue") or "fr"
    u["fuseau"] = a.fuseau or u.get("fuseau") or "UTC"
    if not fuseau_ok(u["fuseau"]):
        sys.exit(f"Fuseau inconnu : {u['fuseau']} (format attendu : Europe/Paris, Africa/Abidjan…)")
    r = p.setdefault("rapport", {})
    if a.marque_client:
        r["marque_client"] = a.marque_client
    p.setdefault("regles", [])
    p.setdefault("connecteurs", {})
    p.setdefault("reseaux", {})
    p.setdefault("contenus", {"skills": []})
    p["version"] = VERSION
    save(P_PROFIL, p)
    if not os.path.exists(P_COMPTES):
        save(P_COMPTES, {})
    os.makedirs(os.path.join(DONNEES, "historique"), exist_ok=True)
    print("Espace de données prêt :", DONNEES)


def cmd_compte(a):
    c = load(P_COMPTES, {}) or {}
    f = reseau(a.reseau)
    handle = a.handle if a.handle.startswith("@") or "/" in a.handle else "@" + a.handle
    cle = cle_compte(a.reseau, handle)
    e = c.get(cle, {})
    e.update({"reseau": f["nom"] if f["connu"] else a.reseau, "handle": handle, "proprietaire": not a.pas_a_moi})
    for k, v in [("url", a.url), ("public", a.public), ("objectif", a.objectif)]:
        if v:
            e[k] = v
    if a.fuseaux_public:
        e["fuseaux_public"] = [t.strip() for t in a.fuseaux_public.split(",") if t.strip()]
    e.setdefault("fuseau_utilisateur", ((load(P_PROFIL, {}) or {}).get("utilisateur") or {}).get("fuseau", "UTC"))
    acces = e.setdefault("acces", {"metricool": None, "public": "navigateur", "interne": "connexion manuelle (option)"})
    if a.metricool:
        acces["metricool"] = int(a.metricool) if str(a.metricool).isdigit() else a.metricool
    c[cle] = e
    save(P_COMPTES, c)
    print(cle, "→", "réseau répertorié" if f["connu"] else "réseau NON répertorié : appliquer la méthode « Réseau non répertorié »")


def cmd_verifier(a):
    pb = []
    p = load(P_PROFIL)
    c = load(P_COMPTES)
    if p is None:
        pb.append("profil.json absent : lancer « donnees.py init »")
    else:
        tz = (p.get("utilisateur") or {}).get("fuseau")
        if not tz or not fuseau_ok(tz):
            pb.append(f"profil.json : fuseau invalide ({tz})")
    if c is None:
        pb.append("comptes.json absent")
    else:
        for cle, e in c.items():
            for k in ("reseau", "handle"):
                if not e.get(k):
                    pb.append(f"{cle} : champ « {k} » manquant")
            for tz in e.get("fuseaux_public", []) + [e.get("fuseau_utilisateur") or "UTC"]:
                if not fuseau_ok(tz):
                    pb.append(f"{cle} : fuseau invalide {tz}")
            if not reseau(e.get("reseau")).get("connu"):
                print(f"Info : {cle} — réseau « {e.get('reseau')} » non répertorié (fonctionne, limites à vérifier à la main)")
    for racine, _, fichiers in os.walk(DONNEES):
        for n in fichiers:
            if n.endswith(".json"):
                txt = open(os.path.join(racine, n), encoding="utf-8").read()
                for m in re.finditer(r'"([^"]+)"\s*:', txt):
                    if INTERDIT.search(m.group(1)):
                        pb.append(f"{os.path.relpath(os.path.join(racine, n), DONNEES)} : clé suspecte « {m.group(1)} » (aucun secret ne doit être stocké)")
    for x in pb:
        print("PROBLÈME :", x)
    print("Espace de données valide" if not pb else f"{len(pb)} problème(s)")
    sys.exit(1 if pb else 0)


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
i = sp.add_parser("init")
i.add_argument("--nom"); i.add_argument("--appel"); i.add_argument("--langue"); i.add_argument("--fuseau")
i.add_argument("--tutoiement", action="store_true", default=None); i.add_argument("--marque-client")
k = sp.add_parser("compte")
k.add_argument("--reseau", required=True); k.add_argument("--handle", required=True); k.add_argument("--url")
k.add_argument("--public"); k.add_argument("--fuseaux-public"); k.add_argument("--objectif"); k.add_argument("--metricool")
k.add_argument("--pas-a-moi", action="store_true")
sp.add_parser("verifier")
a = ap.parse_args()
{"init": cmd_init, "compte": cmd_compte, "verifier": cmd_verifier}[a.cmd](a)
