"""Génère le PDF depuis rapports/<dossier>/analysis.json (+ timing.json / horaires.png / stats_internes.json),
écrit resume.json et compare avec le rapport précédent du même compte.
python scripts/report.py rapports/<dossier> [--style client|perso] [--compte <cle>]"""
import argparse, base64, datetime as dt, glob, io, os, statistics as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from jinja2 import Environment
from common import BASE, load, save, hms, html_to_pdf, isnum, dernier_resume, aujourdhui, chemin, reseau, marque

C = "#1d4ed8"
JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
CRITERES = {"accroche": "Accroche", "discours": "Discours", "presence": "Présence", "cadrage": "Cadrage",
            "lumiere_etalonnage": "Lumière / étalonnage", "montage_rythme": "Montage / rythme",
            "son": "Son", "appel_action": "Appel à l'action"}

def b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def b64file(path, mime):
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()

def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8)

def chart_scores(notes):
    items = [(CRITERES.get(k, k), v) for k, v in (notes or {}).items() if isinstance(v, (int, float))]
    if not items:
        return None
    items = items[::-1]
    fig, ax = plt.subplots(figsize=(6.5, 0.3 * len(items) + 0.5))
    vals = [v for _, v in items]
    ax.barh([l for l, _ in items], vals,
            color=["#16a34a" if v >= 7 else "#f59e0b" if v >= 5 else "#dc2626" for v in vals])
    for y, v in enumerate(vals):
        ax.text(v + 0.1, y, str(v), va="center", fontsize=8)
    ax.set_xlim(0, 10)
    style_ax(ax)
    return b64(fig)

def chart_retention(meta):
    hm = meta.get("heatmap")
    if not hm:
        return None
    fig, ax = plt.subplots(figsize=(7, 2))
    x = [h["start_time"] / 60 for h in hm]
    y = [h["value"] for h in hm]
    ax.fill_between(x, y, color=C, alpha=.3)
    ax.plot(x, y, color=C, lw=1)
    ax.set_xlabel("minutes", fontsize=8)
    ax.set_title("Moments les plus revus", fontsize=9)
    style_ax(ax)
    return b64(fig)

def chart_lum(me):
    pi = (me.get("etalonnage") or {}).get("par_image")
    if not pi:
        return None
    fig, ax = plt.subplots(figsize=(7, 2))
    t = [p["t"] / 60 for p in pi]
    ax.plot(t, [p["luminance"] for p in pi], color=C, lw=1.2, label="Luminance")
    ax.plot(t, [p["saturation"] for p in pi], color="#f59e0b", lw=1, label="Saturation")
    ax.axhspan(80, 180, color="#16a34a", alpha=.08)
    ax.set_ylim(0, 255)
    ax.legend(fontsize=7, frameon=False)
    ax.set_xlabel("minutes", fontsize=8)
    ax.set_title("Lumière et couleur dans le temps (zone verte = exposition correcte)", fontsize=9)
    style_ax(ax)
    return b64(fig)

def chart_account(posts):
    ps = sorted([p for p in posts if p.get("date")], key=lambda p: p["date"])
    if len(ps) < 3:
        return None
    fig, ax = plt.subplots(figsize=(7, 2.2))
    ax.bar(range(len(ps)), [p["eng"] for p in ps], color=C)
    ax.set_xticks(range(len(ps)))
    ax.set_xticklabels([p["date"][5:] for p in ps], rotation=60, fontsize=6)
    ax.set_ylabel("engagement %", fontsize=8)
    ax.set_title("Engagement par post", fontsize=9)
    style_ax(ax)
    return b64(fig)

def chart_activite(si):
    ah = (si or {}).get("audience_heures") or {}
    rows = [ah.get(j) for j in JOURS]
    if not any(isinstance(r, list) and len(r) == 24 for r in rows):
        return None
    m = np.array([r if isinstance(r, list) and len(r) == 24 else [np.nan] * 24 for r in rows], dtype=float)
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    cmap = plt.get_cmap("Blues").copy()
    cmap.set_bad("#f3f4f6")
    im = ax.imshow(np.ma.masked_invalid(m), cmap=cmap, aspect="auto")
    ax.set_yticks(range(7)); ax.set_yticklabels(JOURS, fontsize=8)
    ax.set_xticks(range(0, 24, 2)); ax.set_xticklabels([f"{h} h" for h in range(0, 24, 2)], fontsize=7)
    ax.set_title(f"Activité des abonnés ({ah.get('fuseau', 'fuseau non précisé')})", fontsize=9)
    fig.colorbar(im, ax=ax, shrink=.8)
    return b64(fig)

def num(x):
    if x is None:
        return "—"
    if isinstance(x, int) and not isinstance(x, bool):
        return f"{x:,}".replace(",", "\u202f")
    return x


TPL = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>
@page{size:A4;margin:16mm 15mm;@bottom-right{content:counter(page);font-size:8pt;color:#888}}
body{font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:10pt;color:#1f2937;line-height:1.45}
h1{font-size:24pt;margin:0 0 6px}h2{font-size:14pt;border-bottom:2px solid {{c}};padding-bottom:3px;margin:20px 0 8px;page-break-after:avoid}
h3{font-size:11pt;margin:12px 0 4px;color:{{c}};page-break-after:avoid}
.cover{height:235mm;display:flex;flex-direction:column;justify-content:center;page-break-after:always}
.brand{color:{{c}};font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:9pt}
table{width:100%;border-collapse:collapse;font-size:9pt;margin:6px 0;page-break-inside:avoid}th,td{border-bottom:1px solid #e5e7eb;padding:4px 6px;text-align:left;vertical-align:top}th{background:#f3f4f6}
.kpis{margin:6px 0}.kpi{display:inline-block;width:22.5%;margin:0 1.5% 6px 0;background:#f3f4f6;border-radius:6px;padding:5px 7px;font-size:8pt;color:#555;vertical-align:top}.kpi b{display:block;font-size:12pt;color:#111}
.box{background:#f9fafb;border-left:3px solid {{c}};padding:7px 10px;margin:8px 0;page-break-inside:avoid}
.bio{white-space:pre-line;font-size:11pt;margin-top:4px}.over{color:#dc2626;font-weight:700}
.up{color:#16a34a;font-weight:700}.down{color:#dc2626;font-weight:700}
img{max-width:100%;margin:4px 0}.item{page-break-before:always}ul,ol{margin:4px 0 4px 18px;padding:0}
.note{font-size:20pt;font-weight:700;color:{{c}}}
</style></head><body>
{% if style == "client" %}<div class="cover"><div class="brand">{{marque}}</div><h1>{{a.titre}}</h1><p>{{a.reseau}} · {{date}}</p>{% if a.parametres %}<div class="box">{{a.parametres}}</div>{% endif %}</div>
{% else %}<div class="brand">{{marque}} · {{a.reseau}} · {{date}}</div><h1>{{a.titre}}</h1>{% if a.parametres %}<div class="box">{{a.parametres}}</div>{% endif %}{% endif %}
{% if a.resume_executif %}<h2>Résumé exécutif</h2><p>{{a.resume_executif}}</p>{% endif %}
{% if suivi %}<h2>Suivi depuis le {{prev.date}}</h2><table><tr><th>Indicateur</th><th>Avant</th><th>Maintenant</th><th>Évolution</th></tr>{% for l,x,y,e,cls in suivi %}<tr><td>{{l}}</td><td>{{x|num}}</td><td>{{y|num}}</td><td class="{{cls}}">{{e}}</td></tr>{% endfor %}</table>
{% if prev.recommandations %}<h3>Recommandations du dernier rapport — à vérifier</h3><ul>{% for r in prev.recommandations %}<li>{{r}}</li>{% endfor %}</ul>{% endif %}{% endif %}
{% if si %}<div class="item"><h2>Statistiques internes</h2><p style="font-size:8pt;color:#666">Source : {{si.source}} · période : {{si.periode or "—"}} · relevé le {{si.date or "—"}}</p>
{% if si.kpis %}<div class="kpis">{% for k,v in si.kpis.items() %}<div class="kpi">{{k}}<b>{{v|num}}</b></div>{% endfor %}</div>{% endif %}
{% if act_img %}<img src="{{act_img}}">{% endif %}
{% if si.sources_trafic %}<h3>Sources de trafic</h3><table>{% for k,v in si.sources_trafic.items() %}<tr><td>{{k}}</td><td>{{v}}</td></tr>{% endfor %}</table>{% endif %}
{% if si.demographie %}<h3>Audience</h3><table>{% for k,v in si.demographie.items() %}<tr><th style="width:25%">{{k}}</th><td>{{v}}</td></tr>{% endfor %}</table>{% endif %}
{% if si.top_contenus %}<h3>Meilleurs contenus de la période</h3><table><tr><th>Contenu</th><th>Vues</th><th>Visionnage</th></tr>{% for t in si.top_contenus %}<tr><td>{{t.titre}}</td><td>{{t.vues|num}}</td><td>{{t.retention or "—"}}</td></tr>{% endfor %}</table>{% endif %}
{% if si.commentaires_sans_reponse is not none and si.commentaires_sans_reponse is defined %}<p>Commentaires sans réponse : <b>{{si.commentaires_sans_reponse}}</b></p>{% endif %}
{% if si.analyse %}<p>{{si.analyse}}</p>{% endif %}</div>{% endif %}
{% if contenus %}<h2>Contenus analysés</h2><table><tr><th>#</th><th>Titre</th><th>Chaîne</th><th>Date</th><th>Vues</th><th>Durée</th><th>Note</th></tr>
{% for x in contenus %}<tr><td>{{loop.index}}</td><td>{{x.meta.title}}</td><td>{{x.meta.channel or x.meta.uploader or "—"}}</td><td>{{x.meta.upload_date or "—"}}</td><td>{{x.meta.view_count|num}}</td><td>{{x.duree}}</td><td>{{x.note or "—"}}</td></tr>{% endfor %}</table>{% endif %}
{% for x in contenus %}<div class="item"><h2>{{loop.index}}. {{x.meta.title}}</h2>
{% if x.meta.webpage_url %}<p style="font-size:8pt;color:#666">{{x.meta.webpage_url}}</p>{% endif %}
{% if x.note %}<p><span class="note">{{x.note}}/10</span> note globale</p>{% endif %}
<div class="kpis">{% for k,v in x.kpis %}<div class="kpi">{{k}}<b>{{v|num}}</b></div>{% endfor %}</div>
{% if x.scores_img %}<img src="{{x.scores_img}}">{% endif %}
{% if x.resume_blocs %}<h3>Ce que dit la personne</h3>{% for b in x.resume_blocs %}<p style="margin:6px 0 0"><b>{{b.debut}} – {{b.fin}}</b></p><ul>{% for p in b.points %}<li>{{p}}</li>{% endfor %}</ul>{% endfor %}{% endif %}
{% if x.discours %}<h3>Analyse du discours</h3><p>{{x.discours}}</p>{% endif %}
{% if x.retention_img or x.retention %}<h3>Moments les plus revus</h3>{% if x.retention_img %}<img src="{{x.retention_img}}">{% endif %}{% if x.retention %}<p>{{x.retention}}</p>{% endif %}{% endif %}
{% if x.observations %}<h3>Analyse visuelle et sonore</h3><table>{% for k,v in x.observations.items() %}<tr><th style="width:28%">{{k}}</th><td>{{v}}</td></tr>{% endfor %}</table>{% endif %}
{% if x.lum_img %}<img src="{{x.lum_img}}">{% endif %}{% if x.planche %}<img src="{{x.planche}}">{% endif %}
{% if x.commentaires %}<h3>Ce que dit le public</h3><p>{{x.commentaires}}</p>{% endif %}
{% if x.corrections %}<h3>Corrections</h3><ol>{% for c2 in x.corrections %}<li>{{c2}}</li>{% endfor %}</ol>{% endif %}
</div>{% endfor %}
{% if compte %}<div class="item"><h2>Analyse du compte {{compte.nom}}</h2>{% if compte.lien %}<p style="font-size:8pt;color:#666">{{compte.lien}}</p>{% endif %}
<div class="kpis"><div class="kpi">Abonnés<b>{{compte.abonnes|num}}</b></div><div class="kpi">Posts<b>{{compte.nb_posts|num}}</b></div><div class="kpi">Engagement moyen<b>{{compte.eng_moy}} %</b></div><div class="kpi">Fréquence<b>{{compte.frequence or "—"}}</b></div></div>
<p style="font-size:8pt;color:#666">Engagement = (likes + commentaires + partages) / {{compte.base_eng}}.</p>
{% if compte.analyse %}<p>{{compte.analyse}}</p>{% endif %}
{% if compte.img %}<img src="{{compte.img}}">{% endif %}
{% if compte.par_type %}<h3>Par format</h3><table><tr><th>Format</th><th>Posts</th><th>Engagement moyen</th></tr>{% for t,n,e in compte.par_type %}<tr><td>{{t}}</td><td>{{n}}</td><td>{{e}} %</td></tr>{% endfor %}</table>{% endif %}
{% for titre_l, lst in [("Top 3", compte.top), ("Flop 3", compte.flop)] %}{% if lst %}<h3>{{titre_l}}</h3><table><tr><th>Date</th><th>Type</th><th>Sujet</th><th>Likes</th><th>Comm.</th><th>Eng.</th></tr>{% for p in lst %}<tr><td>{{p.date}}</td><td>{{p.type}}</td><td>{{p.sujet or ""}}</td><td>{{p.likes|num}}</td><td>{{p.commentaires|num}}</td><td>{{p.eng}} %</td></tr>{% endfor %}</table>{% endif %}{% endfor %}
</div>{% endif %}
{% if horaires or timing %}<div class="item"><h2>Quand publier</h2>
{% if timing %}<div class="kpis"><div class="kpi">Posts analysés<b>{{timing.n}}</b></div><div class="kpi">Vues médianes<b>{{timing.vues_mediane|num}}</b></div><div class="kpi">Fiabilité<b>{{timing.fiabilite}}</b></div><div class="kpi">Fuseau principal<b style="font-size:9pt">{{timing.fuseau_principal}}</b></div></div>{% endif %}
{% if heat %}<img src="{{heat}}">{% endif %}
{% if timing and timing.meilleurs %}<h3>Meilleurs créneaux observés</h3><table><tr><th>Jour</th><th>Tranche</th><th>Posts</th><th>Indice vues</th><th>Engagement</th></tr>{% for c2 in timing.meilleurs %}<tr><td>{{c2.jour}}</td><td>{{c2.bloc}}</td><td>{{c2.posts}}</td><td>{{c2.indice}}</td><td>{{c2.eng}} %</td></tr>{% endfor %}</table>{% endif %}
{% if horaires.analyse %}<p>{{horaires.analyse}}</p>{% endif %}
{% if horaires.creneaux_recommandes %}<h3>Créneaux recommandés</h3><table><tr><th style="width:40%">Créneau</th><th>Pourquoi</th></tr>{% for c2 in horaires.creneaux_recommandes %}<tr><td><b>{{c2.creneau}}</b></td><td>{{c2.pourquoi}}</td></tr>{% endfor %}</table>{% endif %}
{% if horaires.frequence %}<p><b>Fréquence :</b> {{horaires.frequence}}</p>{% endif %}
{% if horaires.plan_test %}<h3>Plan de test</h3><ol>{% for s in horaires.plan_test %}<li>{{s}}</li>{% endfor %}</ol>{% endif %}
</div>{% endif %}
{% if profil %}<div class="item"><h2>Rendre le profil attractif</h2>
{% if profil_note %}<p><span class="note">{{profil_note}}/10</span> attractivité actuelle du profil</p>{% endif %}
{% if profil.elements %}<table><tr><th>Élément</th><th>Aujourd'hui</th><th>Note</th><th>À faire</th></tr>{% for e in profil.elements %}<tr><td><b>{{e.element}}</b></td><td>{{e.etat}}</td><td>{{e.note if e.note is not none else "—"}}</td><td>{{e.reco}}</td></tr>{% endfor %}</table>{% endif %}
{% if profil.nom_affiche %}<h3>Nom affiché proposé</h3><ul>{% for n in profil.nom_affiche %}<li>{{n}} <span style="color:#888">({{n|length}} caractères)</span></li>{% endfor %}</ul>{% endif %}
{% if bios %}<h3>Bios prêtes à copier</h3>{% for b in bios %}<div class="box"><b>{{b.version}}</b> · {{b.n}} caractères{% if limite %} / {{limite}}{% endif %}{% if b.trop %} <span class="over">— trop long</span>{% endif %}<div class="bio">{{b.texte}}</div></div>{% endfor %}{% endif %}
{% if profil.epingles %}<h3>Contenus à mettre en avant</h3><ol>{% for e in profil.epingles %}<li>{{e}}</li>{% endfor %}</ol>{% endif %}
{% if profil.autres %}<h3>Autres réglages</h3><ul>{% for e in profil.autres %}<li>{{e}}</li>{% endfor %}</ul>{% endif %}
</div>{% endif %}
{% if a.prochains_contenus %}<div class="item"><h2>Prochains contenus</h2><p style="font-size:8pt;color:#666">Sujets tirés de ce qui marche sur le compte et dans la niche, prêts à passer en script.</p>
<table><tr><th>#</th><th style="width:30%">Sujet</th><th>Angle / accroche</th><th>Format</th><th>Pourquoi</th></tr>{% for p in a.prochains_contenus %}<tr><td>{{loop.index}}</td><td><b>{{p.titre}}</b></td><td>{{p.angle or ""}}</td><td>{{p.format or ""}}{% if p.duree %} · {{p.duree}}{% endif %}</td><td>{{p.pourquoi or ""}}</td></tr>{% endfor %}</table>
{% if a.reprises %}<h3>À republier ailleurs</h3><ul>{% for r in a.reprises %}<li>{{r}}</li>{% endfor %}</ul>{% endif %}</div>{% endif %}
{% if ret %}<h2>Rétention : combien de temps on regarde</h2><p>{{ret.constat}}</p>
<table><tr><th>Temps moyen regardé</th><th>Part de la vidéo vue</th><th>Visionnage complet</th><th>Décrochage avant 3 s</th></tr>
<tr><td>{{ret.moy_s_mediane}} s (médiane)</td><td>{{ret.ratio_mediane}} %</td><td>{{ret.complet_mediane}} %</td><td>{{ret.decrochage_avant_3s}} / {{ret.decrochage_mesure}} vidéos</td></tr></table>
{% if ret.meilleures %}<h3>Les vidéos qui retiennent le mieux</h3><ul>{% for m in ret.meilleures %}<li>{{m.sujet or m.id}} : {{m.moy_s}} s en moyenne, {{m.complet_pct}} % jusqu'au bout</li>{% endfor %}</ul>{% endif %}{% endif %}
{% if a.publicites %}{% set pb = a.publicites %}<h2>Publicités</h2>{% if pb.analyse %}<p>{{pb.analyse}}</p>{% endif %}
{% if pb.annonces %}<table><tr><th>Annonceur</th><th>Depuis</th><th>Format</th><th>Accroche / offre</th><th>Appel à l'action</th><th>Plateformes</th></tr>{% for x in pb.annonces %}<tr><td>{{x.annonceur}}</td><td>{{x.depuis or "—"}}</td><td>{{x.format or "—"}}</td><td>{{x.accroche or ""}}{% if x.offre %}<br><i>{{x.offre}}</i>{% endif %}</td><td>{{x.cta or "—"}}</td><td>{{x.plateformes or "—"}}</td></tr>{% endfor %}</table>{% endif %}
{% if pb.campagne_proposee %}{% set cp = pb.campagne_proposee %}<h3>Campagne proposée (rien n'est lancé sans votre accord)</h3><table>{% for k,lab in [("objectif","Objectif"),("contenu","Contenu"),("cible","Cible"),("budget","Budget"),("duree","Durée"),("texte","Texte"),("cta","Appel à l'action"),("reussite","Réussite si"),("arret","Arrêter si")] %}{% if cp.get(k) %}<tr><th style="width:22%">{{lab}}</th><td>{{cp.get(k)}}</td></tr>{% endif %}{% endfor %}</table>{% endif %}{% endif %}
{% if a.benchmark %}<h2>Comparaison avec la niche</h2><p>{{a.benchmark}}</p>{% endif %}
{% if a.recommandations %}<h2>Recommandations prioritaires</h2><ol>{% for r in a.recommandations %}<li>{{r}}</li>{% endfor %}</ol>{% endif %}
{% if a.limites %}<h2>Méthode et limites</h2><ul>{% for l in a.limites %}<li>{{l}}</li>{% endfor %}</ul>{% endif %}
</body></html>"""

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--style", choices=["client", "perso"])
ap.add_argument("--compte", default=None)
args = ap.parse_args()
d = chemin(args.dir)
a = load(os.path.join(d, "analysis.json"))
if not a:
    raise SystemExit("analysis.json introuvable ou invalide")
style = args.style or a.get("style", "perso")
key = args.compte or a.get("compte_cle")

contenus = []
for c in a.get("contenus", []):
    cd = os.path.join(BASE, c["cache"]) if c.get("cache") else None
    meta = {**(load(os.path.join(cd, "meta.json"), {}) if cd else {}), **c.get("meta", {})}
    me = load(os.path.join(cd, "measures.json"), {}) if cd else {}
    tr = load(os.path.join(cd, "transcript.json"), {}) if cd else {}
    nv = [v for v in (c.get("notes") or {}).values() if isnum(v)]
    planche = None
    pl = (me.get("planches") or [None])[0]
    if pl and os.path.exists(pl):
        planche = b64file(pl, "image/jpeg")
    v = meta.get("view_count") or 0
    kpis = [("Vues", meta.get("view_count")),
            ("Likes / vues", f"{100*(meta.get('like_count') or 0)/v:.1f} %" if v and meta.get("like_count") else None),
            ("Commentaires", meta.get("comment_count")),
            ("Durée", hms(meta.get("duration")) if meta.get("duration") else None),
            ("Mots / min", tr.get("mots_par_minute")),
            ("Coupes / min", (me.get("plans") or {}).get("coupes_par_minute")),
            ("Son (LUFS)", (me.get("son") or {}).get("lufs_integre")),
            ("Luminance moy.", (me.get("etalonnage") or {}).get("luminance_moy"))]
    contenus.append({**c, "meta": meta, "kpis": [k for k in kpis if k[1] is not None],
                     "duree": hms(meta.get("duration")) if meta.get("duration") else "—",
                     "note": round(st.mean(nv), 1) if nv else None,
                     "scores_img": chart_scores(c.get("notes")), "retention_img": chart_retention(meta),
                     "lum_img": chart_lum(me), "planche": planche})

compte = a.get("compte")
if compte:
    f = compte.get("abonnes") or 0
    posts = compte.get("posts", [])
    par_vues = any(p.get("vues") for p in posts)
    compte["base_eng"] = "vues" if par_vues else "abonnés"
    for p in posts:
        inter = (p.get("likes") or 0) + (p.get("commentaires") or 0) + (p.get("partages") or 0)
        if par_vues:
            p["eng"] = round(100 * inter / p["vues"], 2) if p.get("vues") and p.get("likes") is not None else None
        else:
            p["eng"] = round(100 * inter / f, 2) if f else None
    ok = [p for p in posts if p["eng"] is not None]
    compte["eng_moy"] = round(st.mean([p["eng"] for p in ok]), 2) if ok else "—"
    types = {}
    for p in ok:
        types.setdefault(p.get("type", "?"), []).append(p["eng"])
    compte["par_type"] = [(k, len(v), round(st.mean(v), 2)) for k, v in
                          sorted(types.items(), key=lambda kv: -st.mean(kv[1]))]
    s = sorted(ok, key=lambda p: -p["eng"])
    compte["top"] = s[:3]
    compte["flop"] = s[-3:][::-1] if len(s) > 3 else []
    compte["img"] = chart_account(ok)

timing = load(os.path.join(d, "timing.json"))
hp = os.path.join(d, "horaires.png")
heat = b64file(hp, "image/png") if os.path.exists(hp) else None
horaires = a.get("horaires") or {}
si = load(os.path.join(d, "stats_internes.json"))
ret = load(os.path.join(d, "retention.json"))
act_img = chart_activite(si) if si else None

profil = a.get("profil") or {}
fiche_reseau = reseau(a.get("reseau"))
limite = fiche_reseau.get("bio_max")
if not fiche_reseau["connu"]:
    print(f"NOTE : réseau « {a.get('reseau')} » non répertorié — limite de bio non contrôlée (voir reseaux.md)")
bios = [{**b, "n": len(b.get("texte", "")), "trop": bool(limite and len(b.get("texte", "")) > limite)}
        for b in profil.get("bios", [])]
pn = [e["note"] for e in profil.get("elements", []) if isnum(e.get("note"))]
profil_note = profil.get("note") or (round(st.mean(pn), 1) if pn else None)
for b in bios:
    if b["trop"]:
        print(f"ATTENTION : bio « {b.get('version')} » = {b['n']} caractères, limite {limite}")

# Résumé pour le suivi et le calendrier
jour = aujourdhui()
vues_posts = [p["vues"] for p in (compte or {}).get("posts", []) if isnum(p.get("vues"))]
resume = {"compte": key, "date": jour, "reseau": a.get("reseau"),
          "abonnes": (compte or {}).get("abonnes"),
          "vues_mediane": (timing or {}).get("vues_mediane") or (st.median(vues_posts) if vues_posts else None),
          "eng_moy": (compte or {}).get("eng_moy") if isnum((compte or {}).get("eng_moy")) else None,
          "note_profil": profil_note,
          "internes": {k: v for k, v in ((si or {}).get("kpis") or {}).items() if isnum(v)},
          "creneaux": [c.get("creneau") for c in horaires.get("creneaux_recommandes", [])],
          "creneaux_struct": [{"jours": c["jours"], "heure": c["heure"]}
                              for c in horaires.get("creneaux_recommandes", []) if c.get("jours") and c.get("heure")],
          "recommandations": (a.get("recommandations") or [])[:6],
          "profil_actuel": a.get("profil_actuel") or {},
          "prochains_contenus": [p.get("titre") for p in (a.get("prochains_contenus") or [])],
          "moy_s": (ret or {}).get("moy_s_mediane"), "complet_pct": (ret or {}).get("complet_mediane")}
prev, suivi = None, []
if key:
    prev = dernier_resume(key, avant=jour)

def ligne(lab, x, y):
    if isnum(x) and isnum(y):
        diff = round(y - x, 2)
        evo = f"{diff:+g}" + (f" ({100*diff/x:+.0f} %)" if x else "")
        return (lab, x, y, evo, "up" if diff > 0 else "down" if diff < 0 else "")
    return (lab, x, y, "—", "")

if prev:
    for lab, k in [("Abonnés", "abonnes"), ("Vues médianes", "vues_mediane"),
                   ("Engagement moyen (%)", "eng_moy"), ("Note du profil /10", "note_profil"),
                   ("Temps moyen regardé (s)", "moy_s"), ("Visionnage complet (%)", "complet_pct")]:
        suivi.append(ligne(lab, prev.get(k), resume.get(k)))
    for k, y in resume["internes"].items():
        x = (prev.get("internes") or {}).get(k)
        if x is not None:
            suivi.append(ligne(f"{k} (interne)", x, y))
if key:
    save(os.path.join(d, "resume.json"), resume)
else:
    print("Pas de compte_cle : pas de resume.json ni de suivi")

env = Environment(autoescape=True)
env.filters["num"] = num
html = env.from_string(TPL).render(
    a=a, contenus=contenus, compte=compte, timing=timing, heat=heat, horaires=horaires, si=si, act_img=act_img,
    profil=profil, bios=bios, ret=ret, limite=limite, profil_note=profil_note, prev=prev, suivi=suivi,
    style=style, c=C, date=dt.date.fromisoformat(jour).strftime("%d/%m/%Y"),
    marque=marque(style))
html_path = os.path.join(d, "rapport.html")
open(html_path, "w", encoding="utf-8").write(html)
print(html_to_pdf(html_path, os.path.join(d, "rapport.pdf")))
