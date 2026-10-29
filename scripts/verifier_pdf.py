"""Contrôle d'un PDF produit : nombre de pages, pages presque vides, aperçus PNG.

python scripts/verifier_pdf.py rapports/<dossier>/rapport.pdf [--apercus] [--dpi 50]
Code de sortie 2 si une page est presque vide (à corriger avant d'envoyer).
"""
import argparse, os, sys
from common import chemin

ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("--apercus", action="store_true")
ap.add_argument("--dpi", type=int, default=50)
a = ap.parse_args()
try:
    import pymupdf as fitz
except ImportError:
    import fitz
p = chemin(a.pdf)
doc = fitz.open(p)
vides = []
for i, page in enumerate(doc, 1):
    texte = page.get_text().strip()
    images = page.get_images()
    dessins = len(page.get_drawings())
    if len(texte) < 120 and not images and dessins < 3:
        vides.append(i)
    if a.apercus:
        page.get_pixmap(dpi=a.dpi).save(os.path.join(os.path.dirname(p), f"apercu_p{i}.png"))
print(f"{p} : {doc.page_count} page(s)" + (f" · pages presque vides : {vides}" if vides else " · aucune page vide"))
if a.apercus:
    print("Aperçus :", ", ".join(f"apercu_p{i}.png" for i in range(1, doc.page_count + 1)))
sys.exit(2 if vides else 0)
