"""Calendrier de publication multi-réseaux + rappels .ics, à partir du dernier resume.json de chaque compte.
python scripts/calendrier.py [--tz <fuseau, défaut : profil.json>] [--out rapports/AAAA-MM-JJ_calendrier]"""
import argparse, datetime as dt, glob, os
from jinja2 import Environment
from common import BASE, HISTO, load, save, html_to_pdf, comptes as lire_comptes, dernier_resume, aujourdhui, chemin, fuseau_utilisateur

JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
NOMS_J = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
ICS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]

ap = argparse.ArgumentParser()
ap.add_argument("--tz", default=None, help="défaut : fuseau de profil.json, sinon UTC")
ap.add_argument("--out", default=None)
a = ap.parse_args()
a.tz = a.tz or fuseau_utilisateur()
today = dt.date.fromisoformat(aujourdhui())
out = a.out or os.path.join(BASE, "rapports", f"{today.isoformat()}_calendrier")
out = chemin(out)
os.makedirs(out, exist_ok=True)

comptes = lire_comptes()
cles = set(comptes) | {os.path.basename(p) for p in glob.glob(os.path.join(HISTO, "*"))}
latest = {}
for k in sorted(cles):
    r = dernier_resume(k)
    if r:
        latest[k] = r

slots = []
for k, r in latest.items():
    handle = comptes.get(k, {}).get("handle", k)
    for c in r.get("creneaux_struct", []):
        for j in c.get("jours", []):
            if j in JOURS:
                slots.append({"jour": j, "heure": c["heure"], "compte": k,
                              "reseau": r.get("reseau") or comptes.get(k, {}).get("reseau", ""), "handle": handle})
if not slots:
    raise SystemExit("Aucun créneau structuré : remplir horaires.creneaux_recommandes[].jours/heure puis relancer report.py")
slots.sort(key=lambda s: (JOURS.index(s["jour"]), s["heure"]))
sans = [k for k in comptes if k not in latest or not latest[k].get("creneaux_struct")]

mn = lambda h: int(h[:2]) * 60 + int(h[3:5])
alertes = []
for j in JOURS:
    js = [s for s in slots if s["jour"] == j]
    if len(js) > 3:
        alertes.append(f"{j} : {len(js)} publications prévues, charge élevée")
    for x, y in zip(js, js[1:]):
        if mn(y["heure"]) - mn(x["heure"]) < 30:
            alertes.append(f"{j} {x['heure']} ({x['handle']}) et {y['heure']} ({y['handle']}) : moins de 30 min d'écart, "
                           "impossible de répondre aux commentaires des deux")

stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//analyse-reseaux-sociaux//FR", "CALSCALE:GREGORIAN"]
for s in slots:
    i = JOURS.index(s["jour"])
    day = today + dt.timedelta(days=(i - today.weekday()) % 7)
    hh, mm = s["heure"][:2], s["heure"][3:5]
    lines += ["BEGIN:VEVENT", f"UID:{s['compte']}-{s['jour']}-{hh}{mm}@analyse-reseaux-sociaux", f"DTSTAMP:{stamp}",
              f"DTSTART;TZID={a.tz}:{day:%Y%m%d}T{hh}{mm}00", "DURATION:PT30M",
              f"RRULE:FREQ=WEEKLY;BYDAY={ICS[i]}", f"SUMMARY:Publier sur {s['reseau']} ({s['handle']})",
              "DESCRIPTION:Créneau recommandé par l'analyse. Rester 30 min après la publication pour répondre aux commentaires.",
              "BEGIN:VALARM", "TRIGGER:-PT15M", "ACTION:DISPLAY", "DESCRIPTION:Publication dans 15 minutes", "END:VALARM",
              "END:VEVENT"]
lines.append("END:VCALENDAR")
ics = os.path.join(out, "calendrier.ics")
open(ics, "w", encoding="utf-8", newline="").write("\r\n".join(lines) + "\r\n")

TPL = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>
@page{size:A4;margin:16mm 15mm}body{font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:10pt;color:#1f2937}
h1{font-size:20pt;margin:0 0 4px}.brand{color:#1d4ed8;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:9pt}
table{width:100%;border-collapse:collapse;margin:10px 0}th,td{border-bottom:1px solid #e5e7eb;padding:6px;text-align:left;vertical-align:top}
th{background:#f3f4f6;width:16%}.slot{display:inline-block;background:#eef2ff;border-radius:6px;padding:3px 8px;margin:2px 4px 2px 0}
.warn{background:#fff7ed;border-left:3px solid #ea580c;padding:7px 10px;margin:8px 0}
</style></head><body><div class="brand">Calendrier de publication · {{date}}</div><h1>Semaine type — tous les comptes</h1>
<p>Heures en {{tz}}. Rappels récurrents dans le fichier calendrier.ics (15 min avant chaque créneau).</p>
<table>{% for j in jours %}<tr><th>{{j.nom}}</th><td>{% for s in j.slots %}<span class="slot"><b>{{s.heure}}</b> · {{s.reseau}} {{s.handle}}</span>{% else %}<span style="color:#9ca3af">repos</span>{% endfor %}</td></tr>{% endfor %}</table>
{% for al in alertes %}<div class="warn">{{al}}</div>{% endfor %}
{% if sans %}<p><b>Comptes sans créneaux analysés :</b> {{sans|join(", ")}}.</p>{% endif %}
<p style="font-size:8pt;color:#666">Sources : derniers rapports de chaque compte ({{sources|join(", ")}}).</p></body></html>"""
jours = [{"nom": NOMS_J[i], "slots": [s for s in slots if s["jour"] == j]} for i, j in enumerate(JOURS)]
html = Environment(autoescape=True).from_string(TPL).render(
    jours=jours, alertes=alertes, sans=sans, tz=a.tz, date=today.strftime("%d/%m/%Y"),
    sources=[f"{k} du {r.get('date')}" for k, r in latest.items()])
hp = os.path.join(out, "calendrier.html")
open(hp, "w", encoding="utf-8").write(html)
save(os.path.join(out, "calendrier.json"), {"tz": a.tz, "creneaux": slots, "alertes": alertes, "sans_creneaux": sans})
print(html_to_pdf(hp, os.path.join(out, "calendrier.pdf")))
print(ics)
for al in alertes:
    print("ALERTE :", al)
