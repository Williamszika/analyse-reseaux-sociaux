"""Historique des analyses de l'utilisateur : index rapide, recherche, évolution, recommandations à vérifier.

python scripts/historique.py index                         reconstruit historique/index.json (archiver.py le fait seul)
python scripts/historique.py liste [--compte cle] [--reseau TikTok] [--depuis AAAA-MM-JJ]
python scripts/historique.py evolution --compte cle [--png fichier.png]   tableau (et courbe) de tous les indicateurs
python scripts/historique.py chercher "mot ou phrase"      dans résumés, recommandations, bios, prochains contenus
python scripts/historique.py recos --compte cle            recommandations passées, à vérifier à la prochaine analyse
python scripts/historique.py bilan                         vue d'ensemble : comptes, analyses, sessions, actions

À lancer au début de chaque analyse (étape 0) : c'est ce qui permet au skill de « se souvenir ».
Tout reste dans l'espace de données de l'utilisateur ($ANALYSES_DONNEES), jamais dans la boîte à outils.
"""
import argparse, glob, json, os, sys
from common import DONNEES, HISTO, JOURNAL, comptes, isnum, lire_jsonl, load, maintenant, save

P_INDEX = os.path.join(HISTO, "index.json")
KPIS = [("abonnes", "Abonnés"), ("vues_mediane", "Vues médianes"), ("eng_moy", "Engagement moyen (%)"),
        ("note_profil", "Note du profil /10")]


def construire():
    lignes = []
    for d in sorted(glob.glob(os.path.join(HISTO, "*", "*"))):
        if not os.path.isdir(d):
            continue
        cle, date = os.path.basename(os.path.dirname(d)), os.path.basename(d)
        r = load(os.path.join(d, "resume.json"), {}) or {}
        an = load(os.path.join(d, "analysis.json"), {}) or {}
        lignes.append({
            "compte": cle, "date": date, "reseau": r.get("reseau") or an.get("reseau"),
            "titre": an.get("titre"), "style": an.get("style", "perso"),
            **{k: r.get(k) for k, _ in KPIS},
            "internes": r.get("internes") or {},
            "creneaux": r.get("creneaux") or [],
            "recommandations": r.get("recommandations") or (an.get("recommandations") or [])[:6],
            "prochains_contenus": r.get("prochains_contenus") or [],
            "resume_executif": (an.get("resume_executif") or "")[:600],
            "bio": ((an.get("profil_actuel") or {}).get("bio") or ""),
            "pdf": os.path.exists(os.path.join(d, "rapport.pdf")),
            "dossier": os.path.relpath(d, DONNEES)})
    idx = {"genere": maintenant(), "nb": len(lignes), "analyses": lignes}
    save(P_INDEX, idx)
    return idx


def index():
    idx = load(P_INDEX)
    nb_dossiers = len([d for d in glob.glob(os.path.join(HISTO, "*", "*")) if os.path.isdir(d)])
    if not idx or idx.get("nb") != nb_dossiers:
        idx = construire()
    return idx


def fmt(x):
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:g}"
    return str(x)


def evo(x, y):
    if isnum(x) and isnum(y):
        d = round(y - x, 2)
        return f"{d:+g}" + (f" ({100 * d / x:+.0f} %)" if x else "")
    return ""


def cmd_index(a):
    idx = construire()
    print(f"Index reconstruit : {idx['nb']} analyse(s) -> {P_INDEX}")


def filtrer(a):
    out = index()["analyses"]
    if getattr(a, "compte", None):
        out = [l for l in out if l["compte"] == a.compte]
    if getattr(a, "reseau", None):
        from common import reseau
        cle = reseau(a.reseau)["cle"]
        out = [l for l in out if reseau(l.get("reseau"))["cle"] == cle]
    if getattr(a, "depuis", None):
        out = [l for l in out if l["date"] >= a.depuis]
    return out


def cmd_liste(a):
    out = filtrer(a)
    if not out:
        print("Aucune analyse archivée" + (" pour ce filtre" if (a.compte or a.reseau or a.depuis) else ""))
        return
    print(f"{'Date':<11} {'Compte':<28} {'Réseau':<10} {'Abonnés':>8} {'Vues méd.':>9} {'Eng. %':>7} {'Profil':>6}")
    for l in out:
        print(f"{l['date']:<11} {l['compte'][:28]:<28} {str(l.get('reseau') or '')[:10]:<10} "
              f"{fmt(l.get('abonnes')):>8} {fmt(l.get('vues_mediane')):>9} {fmt(l.get('eng_moy')):>7} {fmt(l.get('note_profil')):>6}")
    print(f"{len(out)} analyse(s)")


def cmd_evolution(a):
    out = filtrer(a)
    if not out:
        sys.exit(f"Aucune analyse archivée pour {a.compte}")
    internes = sorted({k for l in out for k, v in (l.get("internes") or {}).items() if isnum(v)})
    series = [(lab, [l.get(k) for l in out]) for k, lab in KPIS] + \
             [(f"{k} (interne)", [(l.get("internes") or {}).get(k) for l in out]) for k in internes]
    series = [(lab, v) for lab, v in series if any(isnum(x) for x in v)]
    print(f"Évolution de {a.compte} sur {len(out)} analyse(s) : {out[0]['date']} -> {out[-1]['date']}")
    for lab, v in series:
        nums = [x for x in v if isnum(x)]
        tot = evo(nums[0], nums[-1]) if len(nums) > 1 else ""
        print(f"- {lab} : " + " → ".join(fmt(x) for x in v) + (f"   (total {tot})" if tot else ""))
    if a.png and series:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        n = len(series)
        fig, axs = plt.subplots(n, 1, figsize=(7, 1.7 * n), squeeze=False)
        dates = [l["date"] for l in out]
        for ax, (lab, v) in zip(axs[:, 0], series):
            pts = [(d, x) for d, x in zip(dates, v) if isnum(x)]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", color="#1d4ed8")
            ax.set_title(lab, fontsize=9, loc="left")
            ax.tick_params(labelsize=7)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
        fig.tight_layout()
        fig.savefig(a.png, dpi=150)
        print("Courbes :", a.png)


def cmd_chercher(a):
    q = a.texte.lower()
    n = 0
    for l in index()["analyses"]:
        champs = {"résumé": l.get("resume_executif") or "", "bio": l.get("bio") or "",
                  **{f"reco {i+1}": r for i, r in enumerate(l.get("recommandations") or [])},
                  **{f"idée {i+1}": r for i, r in enumerate(l.get("prochains_contenus") or [])}}
        for nom, txt in champs.items():
            if q in str(txt).lower():
                n += 1
                print(f"{l['date']} · {l['compte']} · {nom} : {str(txt)[:160]}")
    print(f"{n} résultat(s) pour « {a.texte} »")


def cmd_recos(a):
    out = filtrer(a)
    if not out:
        sys.exit(f"Aucune analyse archivée pour {a.compte}")
    for l in out[-3:]:
        print(f"Analyse du {l['date']} :")
        for r in l.get("recommandations") or []:
            print(f"  - {r}")
    print("À vérifier : lesquelles ont été appliquées, et l'effet sur les indicateurs (voir « evolution »).")


def cmd_bilan(a):
    idx = index()["analyses"]
    c = comptes()
    print(f"Espace de données : {DONNEES}")
    print(f"Comptes suivis : {len(c)}  ·  analyses archivées : {len(idx)}")
    for cle, f in sorted(c.items()):
        mes = [l for l in idx if l["compte"] == cle]
        der = mes[-1] if mes else {}
        qui = "client " + f["client"] if f.get("client") else ("à moi" if f.get("proprietaire") else "suivi")
        print(f"- {cle} ({f.get('reseau')}, {qui}) : {len(mes)} analyse(s)"
              + (f", dernière le {der['date']}, abonnés {fmt(der.get('abonnes'))}" if der else ", jamais analysé"))
    sess = lire_jsonl(JOURNAL)
    if sess:
        fin = [s for s in sess if s.get("duree_min") is not None]
        tot = sum(s["duree_min"] for s in fin)
        print(f"Sessions : {len(sess)} (dont {len(fin)} terminées, {tot:.0f} min au total) ; dernière le {sess[-1].get('debut', '')[:10]}")
    acts = [load(p, {}) for p in glob.glob(os.path.join(DONNEES, "actions", "*.json"))]
    if acts:
        from collections import Counter
        print("Actions sur les comptes : " + ", ".join(f"{k} {v}" for k, v in Counter(x.get("statut") for x in acts).items()))


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
sp.add_parser("index")
for nom in ("liste", "evolution", "recos"):
    p = sp.add_parser(nom)
    p.add_argument("--compte", required=nom != "liste")
    p.add_argument("--reseau")
    p.add_argument("--depuis")
    if nom == "evolution":
        p.add_argument("--png")
q = sp.add_parser("chercher")
q.add_argument("texte")
sp.add_parser("bilan")
a = ap.parse_args()
{"index": cmd_index, "liste": cmd_liste, "evolution": cmd_evolution, "chercher": cmd_chercher,
 "recos": cmd_recos, "bilan": cmd_bilan}[a.cmd](a)
