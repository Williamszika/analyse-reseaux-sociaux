"""Chaîne de production à trois (analyse → scripts → vidéo → contrôle → publication) : une fiche de suivi par vidéo.

Les fiches vivent dans le dépôt privé des vidéos : export CHAINE_DIR=<clone du dépôt des vidéos>/chaine (ou --dir avant la commande).
Chaque étape change le statut et garde une trace datée. Les accords de l'utilisateur sont gardés mot pour mot.

python scripts/chaine.py nouvelle --id 2026-11-01_<slug> --titre "..." --script <chemin du script> [--plan <chemin plan.json>]
python scripts/chaine.py statut <id> <nouveau statut> [--note "..."] [--champ cle=valeur ...]
python scripts/chaine.py accord <id> video|publication --texte "<les mots exacts de l'utilisateur>" [--ou veille|fabrication]
python scripts/chaine.py voir <id>
python scripts/chaine.py liste [--a-traiter]          -> fiches et l'étape suivante de chacune

Statuts, dans l'ordre :
  script_a_revoir → (script_a_reprendre → script_a_revoir, 2 fois au plus) → script_valide
  → [accord vidéo] video_autorisee → video_livree → (video_a_corriger → video_livree, 1 fois au plus) → video_conforme
  → [accord publication] publication_autorisee → publiee
  bloquee (avec une raison) à tout moment.
L'accord de publication peut aussi être donné dès video_livree, quand l'utilisateur vient de VOIR la vidéo et la légende
exacte (dans la conversation de la fabrication ou de la veille) : il attend le contrôle. Contrôle conforme → la fiche passe
seule à publication_autorisee ; contrôle à corriger → l'accord est annulé (la vidéo va changer) et il faudra le redemander.
"""
import argparse, datetime as dt, json, os, sys

ORDRE = ["script_a_revoir", "script_a_reprendre", "script_valide", "video_autorisee", "video_livree", "video_a_corriger",
         "video_conforme", "publication_autorisee", "publiee", "bloquee"]
SUIVANT = {
    "script_a_revoir": "analyse : relire le script",
    "script_a_reprendre": "scripts : réécrire selon la revue",
    "script_valide": "utilisateur : accord pour fabriquer la vidéo",
    "video_autorisee": "vidéo : fabriquer",
    "video_livree": "analyse : contrôler la vidéo",
    "video_a_corriger": "vidéo : corriger selon le contrôle",
    "video_conforme": "utilisateur : accord pour publier",
    "publication_autorisee": "publication : publier sur le Mac",
    "publiee": "terminé (suivi J+1 / J+7 par le relevé du soir)",
    "bloquee": "utilisateur : voir la raison",
}
PASSAGES = {  # statut de départ autorisé pour chaque statut d'arrivée
    "script_a_revoir": {None, "script_a_reprendre", "bloquee"},
    "script_a_reprendre": {"script_a_revoir"},
    "script_valide": {"script_a_revoir"},
    "video_autorisee": {"script_valide", "bloquee"},
    "video_livree": {"video_autorisee", "video_a_corriger"},
    "video_a_corriger": {"video_livree"},
    "video_conforme": {"video_livree"},
    "publication_autorisee": {"video_conforme"},
    "publiee": {"publication_autorisee"},
    "bloquee": set(ORDRE) | {None},
}
MAX = {"script_a_reprendre": 2, "video_a_corriger": 1}


def maintenant():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def dossier(a):
    d = a.dir or os.environ.get("CHAINE_DIR")
    if not d:
        sys.exit("Indiquez --dir <clone du dépôt des vidéos>/chaine ou CHAINE_DIR")
    os.makedirs(d, exist_ok=True)
    return d


def chemin(a, i):
    return os.path.join(dossier(a), f"{i}.json")


def lire(a, i):
    p = chemin(a, i)
    if not os.path.exists(p):
        sys.exit(f"Fiche {i} absente ({p})")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def ecrire(a, f):
    f["maj"] = maintenant()
    with open(chemin(a, f["id"]), "w", encoding="utf-8") as fh:
        json.dump(f, fh, ensure_ascii=False, indent=1)
    print(f"{f['id']} : {f['statut']} → suivant : {SUIVANT.get(f['statut'], '?')}")


def changer(f, s, note=None):
    if s not in ORDRE:
        sys.exit(f"Statut inconnu {s}. Possibles : {', '.join(ORDRE)}")
    if f.get("statut") not in PASSAGES[s]:
        sys.exit(f"Passage refusé : {f.get('statut')} → {s}. Depuis {f.get('statut')}, on attend : {SUIVANT.get(f.get('statut'))}")
    if s in ("video_autorisee", "publication_autorisee"):
        cle = "video" if s == "video_autorisee" else "publication"
        if not (f.get("accords") or {}).get(cle):
            sys.exit(f"Pas d'accord {cle} enregistré : chaine.py accord {f['id']} {cle} --texte \"<ses mots>\"")
    if s in MAX:
        n = sum(1 for h in f["historique"] if h["statut"] == s)
        if n >= MAX[s]:
            s, note = "bloquee", f"{s} déjà fait {n} fois : à voir avec l'utilisateur. {note or ''}".strip()
    f["statut"] = s
    f["historique"].append({"date": maintenant(), "statut": s, "note": note})


def cmd_nouvelle(a):
    p = chemin(a, a.id)
    if os.path.exists(p):
        sys.exit(f"La fiche {a.id} existe déjà")
    f = {"id": a.id, "titre": a.titre, "script": a.script, "plan": a.plan, "statut": None, "historique": [],
         "accords": {}, "revues": [], "controles": [], "cree": maintenant()}
    changer(f, "script_a_revoir", "script écrit")
    ecrire(a, f)


def cmd_statut(a):
    f = lire(a, a.id)
    for kv in a.champ or []:
        k, _, v = kv.partition("=")
        if k in ("revues", "controles"):
            f[k].append({"date": maintenant(), "texte": v})
        elif k:
            f[k] = v
    changer(f, a.statut, a.note)
    pub = (f.get("accords") or {}).get("publication") or {}
    if pub.get("avant_controle"):
        if a.statut == "video_conforme":  # accord donné en voyant la vidéo + contrôle conforme : on peut publier
            pub["avant_controle"] = False
            changer(f, "publication_autorisee", f"accord donné avant le contrôle (« {pub['texte']} »), contrôle conforme")
            print("Accord de publication déjà donné : la fiche passe à publication_autorisee.")
        elif a.statut in ("video_a_corriger", "bloquee"):
            f.setdefault("accords_annules", []).append({**pub, "annule": maintenant(), "raison": a.statut})
            del f["accords"]["publication"]
            f["historique"].append({"date": maintenant(), "statut": f["statut"],
                                    "note": "accord de publication annulé : la vidéo doit être corrigée, le redemander"})
            print("Accord de publication annulé (vidéo à corriger) : il faudra le redemander.")
    ecrire(a, f)


def cmd_accord(a):
    f = lire(a, a.id)
    attendu = {"video": "script_valide", "publication": "video_conforme"}[a.quoi]
    avant = a.quoi == "publication" and f["statut"] == "video_livree"  # vu la vidéo, contrôle en cours
    if f["statut"] != attendu and not avant and not (a.quoi == "video" and f["statut"] == "bloquee"):
        sys.exit(f"Accord {a.quoi} impossible : la fiche est au statut {f['statut']} (attendu {attendu}"
                 + (" ou video_livree" if a.quoi == "publication" else "") + ")")
    if not a.texte.strip():
        sys.exit("Les mots exacts de l'utilisateur sont obligatoires")
    f.setdefault("accords", {})[a.quoi] = {"date": maintenant(), "texte": a.texte, "ou": a.ou, "avant_controle": avant}
    if avant:
        f["historique"].append({"date": maintenant(), "statut": f["statut"],
                                "note": f"accord de publication donné en voyant la vidéo : « {a.texte} » (attend le contrôle)"})
        print("Accord de publication enregistré : il servira dès que le contrôle sera conforme.")
    else:
        changer(f, "video_autorisee" if a.quoi == "video" else "publication_autorisee", f"accord : « {a.texte} »")
    ecrire(a, f)


def cmd_voir(a):
    print(json.dumps(lire(a, a.id), ensure_ascii=False, indent=1))


def cmd_liste(a):
    d = dossier(a)
    n = 0
    for nom in sorted(os.listdir(d)):
        if not nom.endswith(".json"):
            continue
        with open(os.path.join(d, nom), encoding="utf-8") as fh:
            f = json.load(fh)
        if a.a_traiter and f["statut"] in ("publiee",):
            continue
        n += 1
        pre = " [accord de publication déjà donné, attend le contrôle]" if \
            ((f.get("accords") or {}).get("publication") or {}).get("avant_controle") else ""
        print(f"{f['id']:<45} {f['statut']:<22} → {SUIVANT.get(f['statut'], '?')}{pre}  (maj {f.get('maj', '')[:16]})")
    if not n:
        print("Aucune fiche" + (" à traiter" if a.a_traiter else ""))


ap = argparse.ArgumentParser()
ap.add_argument("--dir")
sp = ap.add_subparsers(dest="cmd", required=True)
n = sp.add_parser("nouvelle"); n.add_argument("--id", required=True); n.add_argument("--titre", required=True)
n.add_argument("--script", required=True); n.add_argument("--plan")
s = sp.add_parser("statut"); s.add_argument("id"); s.add_argument("statut"); s.add_argument("--note")
s.add_argument("--champ", action="append")
c = sp.add_parser("accord"); c.add_argument("id"); c.add_argument("quoi", choices=["video", "publication"])
c.add_argument("--texte", required=True); c.add_argument("--ou", default="veille")
v = sp.add_parser("voir"); v.add_argument("id")
l = sp.add_parser("liste"); l.add_argument("--a-traiter", action="store_true")
a = ap.parse_args()
{"nouvelle": cmd_nouvelle, "statut": cmd_statut, "accord": cmd_accord, "voir": cmd_voir, "liste": cmd_liste}[a.cmd](a)
