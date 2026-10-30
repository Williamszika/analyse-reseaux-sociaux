"""Retour d'analyse pour l'équipe de production (dépôt des vidéos, puis dépôt des scripts).

python scripts/brief.py rapports/<dossier> [--vers <dossier>] [--date AAAA-MM-JJ]

Lit analysis.json (+ resume.json, stats_internes.json) et écrit, dans le dossier du rapport puis dans --vers
(ex. le clone du dépôt des vidéos : <clone>/analyse/retours) :
  AAAA-MM-JJ_<compte>.md         retour COMPLET pour l'équipe vidéo (chiffres compris) — dépôt privé seulement
  AAAA-MM-JJ_<compte>_scripts.md retour pour l'écriture des scripts : consignes et idées, AUCUN chiffre,
                                 AUCUNE statistique interne ni donnée d'audience (peut aller dans un dépôt public)
  AAAA-MM-JJ_<compte>.json       version machine des deux
  dernier.md, dernier_scripts.md copies du plus récent (ce que lisent les autres sessions)

Champs optionnels de analysis.json, bloc "equipe" :
  {"consignes_video": [...], "consignes_script": [...], "a_garder": [...],
   "livrables": [{"fichier": "livrables/2026-10-29_x.mp4", "publie_le": "2026-10-29", "lien": "...",
                  "vues": 261, "eng": 4.98, "verdict": "..."}]}
Sans bloc "equipe", les consignes vidéo reprennent les recommandations.
Destination par défaut : profil.json > equipe > videos (depot, branche, dossier) ; voir SKILL.md, étape 5.
"""
import argparse, json, os, re, shutil
from common import chemin, load, profil, save, aujourdhui

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--vers", help="dossier où copier les retours (ex. <clone du dépôt vidéos>/analyse/retours)")
ap.add_argument("--date")
a = ap.parse_args()
d = chemin(a.dir)
an = load(os.path.join(d, "analysis.json"))
if not an:
    raise SystemExit("analysis.json absent")
r = load(os.path.join(d, "resume.json"), {}) or {}
si = load(os.path.join(d, "stats_internes.json"), {}) or {}
eq = an.get("equipe") or {}
date = a.date or r.get("date") or aujourdhui()
cle = an.get("compte_cle") or r.get("compte") or "compte"
compte = an.get("compte") or {}
hor = an.get("horaires") or {}
idees = an.get("prochains_contenus") or []
CHIFFRE = re.compile(r"\d")


def accroche(x):
    return re.sub(r"^\s*accroche\s*:\s*", "", str(x.get("angle") or ""), flags=re.I)


def sans_chiffres(t):
    """Pour le retour public : retire les phrases qui contiennent des chiffres."""
    morceaux = re.split(r"(?<=[.;:!?])\s+", str(t or ""))
    return " ".join(m for m in morceaux if not CHIFFRE.search(m)).strip()


# ---------- Retour complet (équipe vidéo, dépôt privé)
L = [f"# Retour d'analyse — {an.get('reseau', '')} {compte.get('nom', cle)} — {date}", "",
     "Écrit par le skill analyse-reseaux-sociaux pour l'équipe qui fabrique les vidéos. "
     "À lire avant de faire la prochaine vidéo. Rien ici n'autorise une publication : le Patron valide toujours.", "",
     "## Constat", an.get("resume_executif", ""), ""]
chiffres = [("Abonnés", r.get("abonnes")), ("Vues médianes", r.get("vues_mediane")), ("Engagement moyen (%)", r.get("eng_moy"))]
chiffres += list((r.get("internes") or {}).items())
chiffres = [(k, v) for k, v in chiffres if v is not None]
if chiffres:
    L += ["| Indicateur | Valeur |", "|---|---|"] + [f"| {k} | {v} |" for k, v in chiffres] + [""]
if eq.get("a_garder"):
    L += ["## Ce qui marche — à garder"] + [f"- {x}" for x in eq["a_garder"]] + [""]
cv = eq.get("consignes_video") or an.get("recommandations") or []
L += ["## À changer dans les prochaines vidéos"] + [f"{i}. {x}" for i, x in enumerate(cv, 1)] + [""]
if eq.get("livrables"):
    L += ["## Résultats des vidéos livrées", "| Livrable | Publié le | Vues | Engagement | Verdict |", "|---|---|---|---|---|"]
    L += [f"| `{x.get('fichier')}` | {x.get('publie_le', '—')} | {x.get('vues', '—')} | {x.get('eng', '—')} % | {x.get('verdict', '')} |"
          for x in eq["livrables"]] + [""]
if idees:
    L += ["## Prochaines vidéos proposées"]
    for x in idees:
        L.append(f"- **{x.get('titre')}** — {x.get('format', '')}, {x.get('duree', '')}. Accroche : {accroche(x)}. "
                 f"Pourquoi : {x.get('pourquoi', '')}")
    L.append("")
cr = hor.get("creneaux_recommandes") or []
if cr:
    L += ["## Quand publier"] + [f"- {c.get('creneau')} — {c.get('pourquoi', '')}" for c in cr] + [""]
cs = eq.get("consignes_script") or []
L += ["## À transmettre au dépôt des scripts",
      f"Copier tel quel le fichier `{date}_{cle}_scripts.md` (ou `dernier_scripts.md`) : il ne contient aucune statistique du compte ni donnée d'audience.", ""]
complet = "\n".join(L).strip() + "\n"

# ---------- Retour scripts (sans chiffres : peut aller dans un dépôt public)
S = [f"# Consignes d'écriture — retour d'analyse du {date}", "",
     "Ce que les dernières vidéos publiées ont appris, traduit en consignes pour écrire les prochains scripts.",
     "Ce fichier ne contient volontairement aucune statistique du compte ni aucune donnée d'audience.", ""]
consignes = cs or [sans_chiffres(x) for x in cv]
consignes = [c for c in consignes if c]
if consignes:
    S += ["## Pour les prochains scripts"] + [f"{i}. {c}" for i, c in enumerate(consignes, 1)] + [""]
if eq.get("a_garder"):
    gard = [sans_chiffres(x) for x in eq["a_garder"]]
    gard = [g for g in gard if g]
    if gard:
        S += ["## Ce qui marche — à garder"] + [f"- {g}" for g in gard] + [""]
if idees:
    S += ["## Sujets proposés"]
    for x in idees:
        S.append(f"- **{x.get('titre')}** — {x.get('format', '')}. Accroche : {accroche(x)}")
    S.append("")
scripts = "\n".join(S).strip() + "\n"
fuite = CHIFFRE.findall("\n".join(consignes))
if fuite:
    print("NOTE : consignes_script contient des chiffres ; vérifier que ce sont des consignes (durées, nombre de mots) et non des statistiques du compte")

base = f"{date}_{cle}"
sortie = {"date": date, "compte": cle, "reseau": an.get("reseau"), "consignes_video": cv, "consignes_script": consignes,
          "a_garder": eq.get("a_garder") or [], "livrables": eq.get("livrables") or [],
          "prochains_contenus": idees, "creneaux": [c.get("creneau") for c in cr]}
for dossier in [d] + ([a.vers] if a.vers else []):
    os.makedirs(dossier, exist_ok=True)
    open(os.path.join(dossier, base + ".md"), "w", encoding="utf-8").write(complet)
    open(os.path.join(dossier, base + "_scripts.md"), "w", encoding="utf-8").write(scripts)
    save(os.path.join(dossier, base + ".json"), sortie)
    if dossier != d:
        shutil.copy(os.path.join(dossier, base + ".md"), os.path.join(dossier, "dernier.md"))
        shutil.copy(os.path.join(dossier, base + "_scripts.md"), os.path.join(dossier, "dernier_scripts.md"))
    print("Retours écrits dans", dossier)
dest = (profil().get("equipe") or {}).get("videos") or {}
if not a.vers and dest:
    print(f"Pour l'équipe : relancer avec --vers <clone de {dest.get('depot')}>/{dest.get('dossier', 'analyse/retours')}")
