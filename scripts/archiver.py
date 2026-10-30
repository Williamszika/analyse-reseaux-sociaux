"""Archive une analyse dans la mémoire versionnée (analyse/donnees/historique/<compte>/<date>/).

python scripts/archiver.py rapports/<dossier> [--pdf]

Copie analysis.json, resume.json et, s'ils existent, stats_internes.json, timing.json, posts.json
(et rapport.pdf avec --pdf). Met à jour derniere_analyse dans comptes.json.
Met aussi à jour l'index de l'historique (historique.py index).
Ensuite : git add/commit/push du dépôt de données (voir SKILL.md, étape 4).
"""
import argparse, os, shutil, subprocess, sys
from common import DONNEES, HISTO, chemin, comptes, load, save

FICHIERS = ["analysis.json", "resume.json", "stats_internes.json", "timing.json", "posts.json"]

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--pdf", action="store_true")
a = ap.parse_args()
d = chemin(a.dir)
r = load(os.path.join(d, "resume.json"))
if not r or not r.get("compte"):
    raise SystemExit("resume.json absent ou sans compte : lancer report.py avec compte_cle d'abord")
cle, date = r["compte"], r["date"]
dest = os.path.join(HISTO, cle, date)
os.makedirs(dest, exist_ok=True)
copies = []
for f in FICHIERS + (["rapport.pdf"] if a.pdf else []):
    src = os.path.join(d, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(dest, f))
        copies.append(f)

c = comptes()
fiche = c.setdefault(cle, {"reseau": r.get("reseau")})
fiche["derniere_analyse"] = date
save(os.path.join(DONNEES, "comptes.json"), c)
print(f"Archivé {cle} {date} : {', '.join(copies)} -> {dest}")
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "historique.py"), "index"], check=False)
