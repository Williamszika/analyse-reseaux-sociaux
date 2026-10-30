"""Registre des actions sur un compte (publier, commenter, répondre, booster, campagne, modifier le profil).

Rien ne se fait sur un compte sans une fiche « validee » ici. Chaque fiche garde le texte exact, le média,
le budget, l'accord de l'utilisateur (date et phrase), puis le résultat. Stockage : $ANALYSES_DONNEES/actions/<id>.json

python scripts/actions.py preparer --type publication --compte tiktok_awa --texte "..." [--texte-fichier f.txt]
                                   [--media video.mp4] [--quand "2026-11-02 18:30"]
                                   [--budget 20 --duree-jours 5 --cible "Côte d'Ivoire, 18-34 ans" --objectif vues]
python scripts/actions.py montrer <id>             ce qu'il faut montrer mot pour mot à l'utilisateur avant son accord
python scripts/actions.py valider <id> --accord "oui, publie-la"   (phrase de l'utilisateur, recopiée)
python scripts/actions.py fait <id> [--lien URL] [--note "..."]
python scripts/actions.py annuler <id> [--note "..."]
python scripts/actions.py liste [--compte cle] [--statut en_attente|validee|faite|annulee]

Garde-fous appliqués par le script :
- type avec budget (boost, campagne) : refusé si le budget dépasse profil.json > publicite (plafond_jour, plafond_total ;
  0 par défaut = aucune dépense), sauf --hors-plafond, qui exige que l'accord cite le montant.
- compte d'un client : refusé s'il n'a pas de consentement noté dans comptes.json.
- le texte validé est figé par une empreinte : « fait » refuse si le texte a changé depuis l'accord.
- règles de profil.json > regles : rappelées à chaque « montrer ».
"""
import argparse, datetime as dt, glob, hashlib, os, re, sys, uuid
from common import DONNEES, comptes, load, maintenant, profil, save

DOSSIER = os.path.join(DONNEES, "actions")
TYPES = {"publication": False, "commentaire": False, "reponse": False, "message": False, "profil": False,
         "programmation": False, "boost": True, "campagne": True}


def chemin(i):
    return os.path.join(DOSSIER, f"{i}.json")


def lire(i):
    f = load(chemin(i))
    if not f:
        sys.exit(f"Action {i} introuvable")
    return f


def empreinte(f):
    base = "|".join(str(f.get(k) or "") for k in ("type", "compte", "texte", "media", "quand", "budget", "duree_jours", "cible"))
    return hashlib.sha256(base.encode()).hexdigest()[:16]


def cmd_preparer(a):
    c = comptes().get(a.compte)
    if not c:
        sys.exit(f"Compte {a.compte} absent de comptes.json (donnees.py compte d'abord)")
    if c.get("client") and not c.get("consentement"):
        sys.exit(f"Compte du client « {c['client']} » sans consentement noté : aucune action possible")
    if not c.get("proprietaire") and not c.get("client"):
        sys.exit("Ce compte n'est ni à l'utilisateur ni à un client consentant : aucune action possible")
    texte = open(a.texte_fichier, encoding="utf-8").read().strip() if a.texte_fichier else (a.texte or "")
    if a.type in ("publication", "commentaire", "reponse", "message") and not (texte or a.media):
        sys.exit("Texte ou média obligatoire")
    payant = TYPES[a.type]
    if payant and not a.budget:
        sys.exit("Budget obligatoire pour un boost ou une campagne (--budget, total en devise du profil)")
    i = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{a.type}-{uuid.uuid4().hex[:4]}"
    f = {"id": i, "type": a.type, "compte": a.compte, "reseau": c.get("reseau"), "handle": c.get("handle"),
         "client": c.get("client"), "texte": texte, "media": a.media, "quand": a.quand, "budget": a.budget,
         "duree_jours": a.duree_jours, "cible": a.cible, "objectif": a.objectif, "statut": "en_attente",
         "cree": maintenant(), "hors_plafond": a.hors_plafond}
    if payant:
        pub = profil().get("publicite") or {}
        jour = a.budget / max(a.duree_jours or 1, 1)
        pj, pt = pub.get("plafond_jour") or 0, pub.get("plafond_total") or 0
        f["devise"] = pub.get("devise", "EUR")
        f["budget_jour"] = round(jour, 2)
        if (jour > pj or a.budget > pt) and not a.hors_plafond:
            sys.exit(f"Refusé : {a.budget} {f['devise']} ({jour:.2f}/jour) dépasse le plafond du profil "
                     f"({pj}/jour, {pt} au total). Faire relever le plafond par l'utilisateur "
                     f"(donnees.py init --plafond-pub-jour … --plafond-pub-total …) ou --hors-plafond avec son accord chiffré.")
    f["empreinte"] = empreinte(f)
    save(chemin(i), f)
    print(i)


def cmd_montrer(a):
    f = lire(a.id)
    L = [f"Action à valider — {f['type']} sur {f.get('reseau')} {f.get('handle')}" + (f" (client : {f['client']})" if f.get("client") else "")]
    if f.get("texte"):
        L.append("Texte exact :\n«\n" + f["texte"] + "\n»")
    if f.get("media"):
        L.append(f"Média : {f['media']}")
    if f.get("quand"):
        L.append(f"Quand : {f['quand']}")
    if f.get("budget"):
        L.append(f"Budget : {f['budget']} {f.get('devise', '')} au total, {f.get('duree_jours') or 1} jour(s) "
                 f"({f.get('budget_jour')} par jour) · cible : {f.get('cible') or 'à préciser'} · objectif : {f.get('objectif') or 'à préciser'}")
        L.append("La dépense est réelle et prélevée sur le moyen de paiement déjà enregistré sur le compte publicitaire.")
    regles = profil().get("regles") or []
    if regles:
        L.append("Vos règles : " + " · ".join(regles))
    L.append("Répondez « oui » pour que je le fasse exactement ainsi, ou dites ce qu'il faut changer.")
    print("\n\n".join(L))


def cmd_valider(a):
    f = lire(a.id)
    if f["statut"] != "en_attente":
        sys.exit(f"Statut actuel : {f['statut']} (seule une action en attente se valide)")
    if not a.accord.strip():
        sys.exit("Recopier la phrase d'accord de l'utilisateur")
    if f.get("hors_plafond") and f.get("budget") and not re.search(re.escape(str(int(f["budget"]))), a.accord):
        sys.exit("Hors plafond : l'accord de l'utilisateur doit citer le montant")
    f.update(statut="validee", accord=a.accord, valide=maintenant(), empreinte_validee=empreinte(f))
    save(chemin(a.id), f)
    print(f"Validée : {a.id}")


def cmd_fait(a):
    f = lire(a.id)
    if f["statut"] != "validee":
        sys.exit(f"Refusé : statut {f['statut']} — aucune action sans validation")
    if empreinte(f) != f.get("empreinte_validee"):
        sys.exit("Refusé : le contenu a changé depuis l'accord, le refaire valider")
    f.update(statut="faite", fait=maintenant(), lien=a.lien, note=a.note)
    save(chemin(a.id), f)
    print(f"Faite : {a.id}" + (f" -> {a.lien}" if a.lien else ""))


def cmd_annuler(a):
    f = lire(a.id)
    f.update(statut="annulee", annule=maintenant(), note=a.note)
    save(chemin(a.id), f)
    print(f"Annulée : {a.id}")


def cmd_liste(a):
    fs = sorted((load(p, {}) for p in glob.glob(os.path.join(DOSSIER, "*.json"))), key=lambda x: x.get("id", ""))
    fs = [f for f in fs if (not a.compte or f.get("compte") == a.compte) and (not a.statut or f.get("statut") == a.statut)]
    if not fs:
        print("Aucune action")
        return
    depense = sum(f.get("budget") or 0 for f in fs if f.get("statut") == "faite")
    for f in fs:
        print(f"{f['id']} · {f['statut']:<10} · {f.get('reseau')} {f.get('handle')} · "
              f"{(f.get('texte') or f.get('media') or '')[:60]!r}" + (f" · {f['budget']} {f.get('devise', '')}" if f.get("budget") else ""))
    if depense:
        print(f"Dépense publicitaire faite : {depense:g}")


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
p = sp.add_parser("preparer")
p.add_argument("--type", choices=list(TYPES), required=True); p.add_argument("--compte", required=True)
p.add_argument("--texte"); p.add_argument("--texte-fichier"); p.add_argument("--media"); p.add_argument("--quand")
p.add_argument("--budget", type=float); p.add_argument("--duree-jours", type=int); p.add_argument("--cible"); p.add_argument("--objectif")
p.add_argument("--hors-plafond", action="store_true")
for nom in ("montrer", "valider", "fait", "annuler"):
    q = sp.add_parser(nom)
    q.add_argument("id")
    if nom == "valider":
        q.add_argument("--accord", required=True)
    if nom in ("fait", "annuler"):
        q.add_argument("--note")
    if nom == "fait":
        q.add_argument("--lien")
l = sp.add_parser("liste"); l.add_argument("--compte"); l.add_argument("--statut")
a = ap.parse_args()
{"preparer": cmd_preparer, "montrer": cmd_montrer, "valider": cmd_valider, "fait": cmd_fait, "annuler": cmd_annuler,
 "liste": cmd_liste}[a.cmd](a)
