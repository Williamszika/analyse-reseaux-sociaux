"""Espace de données d'un utilisateur : création, ajout de compte, vérification.

python scripts/donnees.py init --nom "Awa" [--appel "Awa"] [--tutoiement] [--langue fr] [--fuseau Europe/Paris]
                               [--marque-client "Mon agence · Audit"] [--memoire github:awa/mes-analyses:donnees | dossier:~/Analyses | aucune]
                               [--plafond-pub-jour 10] [--plafond-pub-total 100] [--devise EUR]
python scripts/donnees.py compte --reseau TikTok --handle @awa [--url ...] [--public "..."] [--fuseaux-public Africa/Abidjan,Europe/Paris]
                                 [--objectif "..."] [--metricool <brandId>] [--pas-a-moi]
                                 [--client "Nom du client" --consentement "2026-10-30, par e-mail : analyse + publications"]
python scripts/donnees.py verifier

Défauts quand personne ne répond (premier usage, tâche programmée) : langue fr, vouvoiement, fuseau UTC, mémoire aucune,
aucun plafond publicitaire = aucune dépense possible.

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
    if a.memoire:
        m = a.memoire.split(":")
        if m[0] == "github" and len(m) >= 2:
            p["memoire"] = {"type": "github", "depot": m[1], "dossier": m[2] if len(m) > 2 else "donnees"}
        elif m[0] == "dossier":
            p["memoire"] = {"type": "dossier", "chemin": ":".join(m[1:]) or DONNEES}
        elif m[0] == "aucune":
            p["memoire"] = {"type": "aucune"}
        else:
            sys.exit("--memoire attendu : github:proprietaire/depot[:dossier] | dossier:<chemin> | aucune")
    p.setdefault("memoire", {"type": "aucune"})
    pub = p.setdefault("publicite", {"plafond_jour": 0, "plafond_total": 0, "devise": "EUR"})
    for k, v in [("plafond_jour", a.plafond_pub_jour), ("plafond_total", a.plafond_pub_total), ("devise", a.devise)]:
        if v is not None:
            pub[k] = v
    p.setdefault("usage", {"rapport_anonyme": "demander"})
    p["version"] = VERSION
    save(P_PROFIL, p)
    if not os.path.exists(P_COMPTES):
        save(P_COMPTES, {})
    os.makedirs(os.path.join(DONNEES, "historique"), exist_ok=True)
    lisez = os.path.join(DONNEES, "LISEZMOI.md")
    if not os.path.exists(lisez):
        with open(lisez, "w", encoding="utf-8") as f:
            f.write(LISEZMOI)
    print("Espace de données prêt :", DONNEES)


def cmd_compte(a):
    c = load(P_COMPTES, {}) or {}
    f = reseau(a.reseau)
    handle = a.handle if a.handle.startswith("@") or "/" in a.handle else "@" + a.handle
    cle = cle_compte(a.reseau, handle)
    e = c.get(cle, {})
    e.update({"reseau": f["nom"] if f["connu"] else a.reseau, "handle": handle, "proprietaire": not a.pas_a_moi})
    if a.client:
        e["client"] = a.client
        e["proprietaire"] = False
        if a.consentement:
            e["consentement"] = a.consentement
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
            if e.get("client") and not e.get("consentement"):
                pb.append(f"{cle} : compte du client « {e['client']} » sans consentement noté (--consentement)")
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


LISEZMOI = """# Mon espace de données — analyse réseaux sociaux

Ce dossier est **à vous**. Il garde la mémoire de vos analyses pour que le skill compare chaque nouvelle analyse
avec les précédentes. Gardez-le **privé** (dépôt GitHub privé ou dossier de votre ordinateur).

| Élément | Contenu |
|---|---|
| `profil.json` | vos réglages : nom, langue, fuseau, règles, connecteurs, plafond publicitaire |
| `comptes.json` | vos comptes suivis (et ceux de vos clients, avec leur consentement) |
| `historique/<compte>/<date>/` | chaque analyse archivée ; `historique/index.json` = index rapide |
| `journal.jsonl` | vos sessions : date, durée, ce qui a été fait |
| `actions/` | chaque publication, commentaire ou publicité : texte exact, votre accord, résultat |
| `coherence/` | comparaisons entre vos réseaux |

Aucun mot de passe, code, jeton ni cookie n'est jamais écrit ici (`donnees.py verifier` le contrôle).
Pour tout effacer : supprimez ce dossier. Pour arrêter le suivi d'un compte : retirez-le de `comptes.json`.
"""

ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
i = sp.add_parser("init")
i.add_argument("--nom"); i.add_argument("--appel"); i.add_argument("--langue"); i.add_argument("--fuseau")
i.add_argument("--tutoiement", action="store_true", default=None); i.add_argument("--marque-client")
i.add_argument("--memoire"); i.add_argument("--plafond-pub-jour", type=float); i.add_argument("--plafond-pub-total", type=float)
i.add_argument("--devise")
k = sp.add_parser("compte")
k.add_argument("--reseau", required=True); k.add_argument("--handle", required=True); k.add_argument("--url")
k.add_argument("--public"); k.add_argument("--fuseaux-public"); k.add_argument("--objectif"); k.add_argument("--metricool")
k.add_argument("--pas-a-moi", action="store_true"); k.add_argument("--client"); k.add_argument("--consentement")
sp.add_parser("verifier")
a = ap.parse_args()
{"init": cmd_init, "compte": cmd_compte, "verifier": cmd_verifier}[a.cmd](a)
