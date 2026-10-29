"""Cohérence de l'identité entre les réseaux de l'utilisateur (mode K).

python scripts/coherence.py --out rapports/AAAA-MM-JJ_coherence [--proposition coherence.json] [--style client]

Lit, pour chaque compte « proprietaire » de comptes.json, le profil_actuel de sa dernière analyse archivée
(nom, pseudo, bio, lien, langue, photo, categorie). Détecte automatiquement les écarts, puis met en page
la proposition d'identité unique écrite par Claude dans coherence.json :
{"resume": "...", "identite": {"nom": "...", "pseudo_cible": "...", "photo": "...", "promesse": "...", "langue": "fr"},
 "bios": {"TikTok": "...", "Instagram": "...", ...}, "actions": ["..."]}
"""
import argparse, datetime as dt, os, re
from jinja2 import Environment
from common import chemin, comptes, dernier_resume, historique, load, save, html_to_pdf, aujourdhui, reseau, marque

CHAMPS = [("photo", "Photo"), ("nom", "Nom affiché"), ("pseudo", "Pseudo"), ("bio", "Bio"),
          ("lien", "Lien"), ("langue", "Langue"), ("categorie", "Catégorie / type")]

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=None)
ap.add_argument("--proposition", default=None)
ap.add_argument("--style", choices=["perso", "client"], default="perso")
ap.add_argument("--comptes", default=None, help="clés séparées par des virgules (défaut : comptes de l'utilisateur déjà analysés)")
a = ap.parse_args()
jour = aujourdhui()
out = chemin(a.out or os.path.join("rapports", f"{jour}_coherence"))
os.makedirs(out, exist_ok=True)

lignes, non_analyses = [], []
choix = [c.strip() for c in a.comptes.split(",")] if a.comptes else None
for cle, fiche in sorted(comptes().items()):
    if choix is not None and cle not in choix:
        continue
    if choix is None and not fiche.get("proprietaire"):
        continue
    pa = {}
    h = historique(cle)
    if not h:
        non_analyses.append(fiche.get("handle", cle))
        continue
    if h:
        an = load(os.path.join(h[-1][1], "analysis.json"), {}) or {}
        pa = an.get("profil_actuel") or {}
    r = dernier_resume(cle) or {}
    lignes.append({"cle": cle, "reseau": fiche.get("reseau", ""), "handle": fiche.get("handle", cle),
                   "lab": f'{fiche.get("reseau", "")} {fiche.get("handle", cle)}',
                   "profil": pa, "date": r.get("date") or (h[-1][0] if h else None),
                   "abonnes": r.get("abonnes"), "note": r.get("note_profil")})
if len(lignes) < 2:
    raise SystemExit("Il faut au moins 2 comptes « proprietaire » analysés (avec profil_actuel) pour comparer")


def norm(x):
    return re.sub(r"[^a-z0-9]", "", (x or "").lower())


alertes = []
for k, lab in [("nom", "Nom affiché différent"), ("pseudo", "Pseudo différent"), ("langue", "Langue différente")]:
    vals = {l["lab"]: (l["profil"].get(k) or "") for l in lignes}
    distincts = {norm(v) for v in vals.values() if v}
    if len(distincts) > 1:
        alertes.append(f"{lab} selon le réseau : " + " · ".join(f"{r} = « {v} »" for r, v in vals.items() if v))
if non_analyses:
    print("Comptes pas encore analysés (exclus) :", ", ".join(non_analyses))
for l in lignes:
    p = l["profil"]
    if not p:
        alertes.append(f"{l['lab']} : profil_actuel absent de la dernière analyse, refaire le mode G")
        continue
    if not p.get("lien"):
        alertes.append(f"{l['lab']} : aucun lien dans le profil")
    if not p.get("bio"):
        alertes.append(f"{l['lab']} : bio vide")
    lim = reseau(l["reseau"]).get("bio_max")
    if lim and p.get("bio") and len(p["bio"]) > lim:
        alertes.append(f"{l['lab']} : bio de {len(p['bio'])} caractères, au-delà de la limite conseillée ({lim})")

prop = load(chemin(a.proposition), {}) if a.proposition else {}
bios = []
for res, txt in (prop.get("bios") or {}).items():
    lim = reseau(res).get("bio_max")
    bios.append({"reseau": res, "texte": txt, "n": len(txt), "lim": lim, "trop": bool(lim and len(txt) > lim)})
    if lim and len(txt) > lim:
        print(f"ATTENTION : bio {res} = {len(txt)} caractères, limite {lim}")

TPL = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>
@page{size:A4 landscape;margin:12mm 12mm;@bottom-right{content:counter(page);font-size:8pt;color:#888}}
body{font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:9.5pt;color:#1f2937;line-height:1.4}
h1{font-size:20pt;margin:0 0 4px}h2{font-size:13pt;border-bottom:2px solid #1d4ed8;padding-bottom:3px;margin:16px 0 6px}
.brand{color:#1d4ed8;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:8.5pt}
table{width:100%;border-collapse:collapse;font-size:8.6pt;page-break-inside:avoid}th,td{border:1px solid #e5e7eb;padding:4px 6px;text-align:left;vertical-align:top}
td{white-space:pre-line}th{background:#f3f4f6}.warn{background:#fff7ed;border-left:3px solid #ea580c;padding:5px 9px;margin:4px 0}
.box{background:#f9fafb;border-left:3px solid #1d4ed8;padding:6px 10px;margin:6px 0;page-break-inside:avoid}
.bio{white-space:pre-line;font-size:10.5pt}.over{color:#dc2626;font-weight:700}
</style></head><body>
<div class="brand">{{marque}} · cohérence entre réseaux · {{date}}</div><h1>Une seule identité sur tous vos réseaux</h1>
{% if prop.resume %}<p>{{prop.resume}}</p>{% endif %}
<h2>Aujourd'hui</h2><table><tr><th></th>{% for l in lignes %}<th>{{l.reseau}}<br><span style="font-weight:400">{{l.handle}} · analyse du {{l.date or "—"}}</span></th>{% endfor %}</tr>
{% for k,lab in champs %}<tr><th>{{lab}}</th>{% for l in lignes %}<td>{{l.profil.get(k) or "—"}}</td>{% endfor %}</tr>{% endfor %}
<tr><th>Abonnés</th>{% for l in lignes %}<td>{{l.abonnes if l.abonnes is not none else "—"}}</td>{% endfor %}</tr>
<tr><th>Note du profil</th>{% for l in lignes %}<td>{{l.note if l.note is not none else "—"}}{% if l.note is not none %}/10{% endif %}</td>{% endfor %}</tr></table>
{% if non_analyses %}<p style="font-size:8pt;color:#666">Pas encore analysés, donc absents du tableau : {{non_analyses|join(", ")}}.</p>{% endif %}
{% if alertes %}<h2>Écarts détectés</h2>{% for al in alertes %}<div class="warn">{{al}}</div>{% endfor %}{% endif %}
{% if prop.identite %}<h2>Identité proposée</h2><table>{% for k,v in prop.identite.items() %}<tr><th style="width:22%">{{k|capitalize}}</th><td>{{v}}</td></tr>{% endfor %}</table>{% endif %}
{% if bios %}<h2>Bios adaptées à chaque réseau</h2>{% for b in bios %}<div class="box"><b>{{b.reseau}}</b> · {{b.n}} caractères{% if b.lim %} / {{b.lim}}{% endif %}{% if b.trop %} <span class="over">— trop long</span>{% endif %}<div class="bio">{{b.texte}}</div></div>{% endfor %}{% endif %}
{% if prop.actions %}<h2>À faire, dans l'ordre</h2><ol>{% for x in prop.actions %}<li>{{x}}</li>{% endfor %}</ol>{% endif %}
</body></html>"""
html = Environment(autoescape=True).from_string(TPL).render(
    lignes=lignes, non_analyses=non_analyses, champs=CHAMPS, alertes=alertes, prop=prop, bios=bios,
    date=dt.date.fromisoformat(jour).strftime("%d/%m/%Y"),
    marque=marque(a.style))
hp = os.path.join(out, "coherence.html")
open(hp, "w", encoding="utf-8").write(html)
save(os.path.join(out, "coherence_auto.json"), {"comptes": lignes, "alertes": alertes})
print(html_to_pdf(hp, os.path.join(out, "coherence.pdf")))
for al in alertes:
    print("ÉCART :", al)
