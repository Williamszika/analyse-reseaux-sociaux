"""Performance des contenus : rétention, étiquettes, suivi des vidéos livrées, tests A/B.

Les chiffres par vidéo viennent de posts.json (format dans formats.md), enrichi des champs de rétention :
  "moy_s" (temps de visionnage moyen, s), "complet_pct" (% qui ont tout regardé), "decrochage_s" (moment où la plupart
  arrêtent, s), "abonnes_gagnes", "pour_toi_pct". TikTok : TikTok Studio → Données analytiques → la vidéo (actions.md §2).

python scripts/performance.py retention rapports/<dossier>            -> retention.json (+ section du rapport)
python scripts/performance.py etiquettes poser --id <video> [--theme ..] [--accroche ..] [--format ..] [--serie ..] [--autre cle=valeur]
python scripts/performance.py etiquettes analyser rapports/<dossier>  -> ce qui fait monter vues / rétention, par étiquette
python scripts/performance.py livrables rapports/<dossier> --livrables <dossier livrables/> [--date AAAA-MM-JJ]
      relie chaque vidéo livrée à sa publication, garde un relevé à J+1 et J+7, compare note qualité et résultat réel
python scripts/performance.py test creer --nom accroche-courte --hypothese "..." --a "..." --b "..." [--critere moy_s] [--min 3]
python scripts/performance.py test ajouter --nom accroche-courte --variante A --id <video>
python scripts/performance.py test verdict [--nom ..] rapports/<dossier>
python scripts/performance.py test liste
python scripts/performance.py tableau rapports/<dossier> --out <dossier> [--historique <compte>]
      -> videos.json, historique.json, livrables.json, tests.json : lignes prêtes pour un tableau de bord (fichiers joints)

Fichiers de l'espace de données : etiquettes.json, livrables_suivi.json, tests.json.
"""
import argparse, datetime as dt, glob, json, os, re, statistics as st, sys, unicodedata
from common import DONNEES, aujourdhui, chemin, isnum, load, save

P_ETIQ = os.path.join(DONNEES, "etiquettes.json")
P_LIV = os.path.join(DONNEES, "livrables_suivi.json")
P_TESTS = os.path.join(DONNEES, "tests.json")
CRITERES = {"vues": "vues", "eng": "engagement (%)", "moy_s": "temps de visionnage moyen (s)",
            "complet_pct": "visionnage complet (%)", "ratio": "part de la vidéo regardée (%)"}


def posts_de(d):
    p = load(os.path.join(chemin(d), "posts.json"))
    if p is None:
        sys.exit(f"posts.json absent dans {d}")
    return p


def eng(p):
    if isnum(p.get("vues")) and p["vues"] and all(isnum(p.get(k)) for k in ("likes", "commentaires", "partages")):
        return round(100 * (p["likes"] + p["commentaires"] + p["partages"]) / p["vues"], 2)
    return None


def ratio(p):
    if isnum(p.get("moy_s")) and isnum(p.get("duree")) and p["duree"]:
        return round(100 * p["moy_s"] / p["duree"], 1)
    return None


def valeur(p, c):
    return {"eng": eng(p), "ratio": ratio(p)}.get(c, p.get(c)) if c in ("eng", "ratio") else p.get(c)


def med(xs):
    xs = [x for x in xs if isnum(x)]
    return round(st.median(xs), 2) if xs else None


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", t).split())


# ---------------------------------------------------------------- rétention
def cmd_retention(a):
    d = chemin(a.dir)
    P = [p for p in posts_de(d) if isnum(p.get("moy_s"))]
    if not P:
        sys.exit("Aucune donnée de rétention dans posts.json (champs moy_s, complet_pct, decrochage_s)")
    dec = [p.get("decrochage_s") for p in P if isnum(p.get("decrochage_s"))]
    r = {"n": len(P), "moy_s_mediane": med(p["moy_s"] for p in P), "complet_mediane": med(p.get("complet_pct") for p in P),
         "ratio_mediane": med(ratio(p) for p in P), "duree_mediane": med(p.get("duree") for p in P),
         "decrochage_avant_3s": sum(1 for x in dec if x <= 3), "decrochage_mesure": len(dec)}
    paires = [(p["moy_s"], p["vues"]) for p in P if isnum(p.get("vues"))]
    if len(paires) >= 5:
        xs, ys = zip(*paires)
        try:
            r["correlation_vues_moy_s"] = round(st.correlation(xs, ys), 2)
        except Exception:
            pass
    best = sorted(P, key=lambda p: -p["moy_s"])[:3]
    r["meilleures"] = [{"id": p.get("id"), "sujet": p.get("sujet"), "moy_s": p["moy_s"], "complet_pct": p.get("complet_pct"),
                        "ratio": ratio(p)} for p in best]
    L = []
    if r["decrochage_mesure"] and r["decrochage_avant_3s"] >= 0.7 * r["decrochage_mesure"]:
        L.append(f"Pour {r['decrochage_avant_3s']} vidéos sur {r['decrochage_mesure']}, la plupart des spectateurs partent dans les "
                 "3 premières secondes : le problème est l'ouverture (première image, premier son, premiers mots), pas la durée.")
    if isnum(r["ratio_mediane"]) and r["ratio_mediane"] < 20:
        L.append(f"Les spectateurs voient en moyenne {r['ratio_mediane']} % de chaque vidéo (médiane {r['moy_s_mediane']} s "
                 f"sur {r['duree_mediane']} s).")
    if isnum(r["complet_mediane"]):
        L.append(f"Visionnage complet médian : {r['complet_mediane']} %.")
    r["constat"] = " ".join(L)
    save(os.path.join(d, "retention.json"), r)
    print(json.dumps(r, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- étiquettes
def cmd_etiq_poser(a):
    e = load(P_ETIQ, {}) or {}
    f = e.setdefault(a.id, {})
    for k in ("theme", "accroche", "format", "serie"):
        v = getattr(a, k)
        if v:
            f[k] = v
    for kv in a.autre or []:
        k, _, v = kv.partition("=")
        if k and v:
            f[k] = v
    save(P_ETIQ, e)
    print(a.id, f)


def cmd_etiq_analyser(a):
    e = load(P_ETIQ, {}) or {}
    P = posts_de(a.dir)
    lignes = []
    cles = sorted({k for v in e.values() for k in v})
    if not cles:
        sys.exit("Aucune étiquette : performance.py etiquettes poser --id … --theme … --accroche …")
    res = {}
    for k in cles:
        groupes = {}
        for p in P:
            v = (e.get(str(p.get("id"))) or {}).get(k)
            if v:
                groupes.setdefault(v, []).append(p)
        res[k] = {}
        for v, ps in sorted(groupes.items(), key=lambda kv: -len(kv[1])):
            res[k][v] = {"n": len(ps), "vues": med(p.get("vues") for p in ps), "eng": med(eng(p) for p in ps),
                         "moy_s": med(p.get("moy_s") for p in ps), "complet_pct": med(p.get("complet_pct") for p in ps)}
            lignes.append(f"{k:<10} {v[:28]:<28} n={len(ps):<3} vues {res[k][v]['vues']}  eng {res[k][v]['eng']} %  "
                          f"moy {res[k][v]['moy_s']} s  complet {res[k][v]['complet_pct']} %" + ("  (peu de vidéos)" if len(ps) < 4 else ""))
    save(os.path.join(chemin(a.dir), "etiquettes_analyse.json"), res)
    print("\n".join(lignes))
    print("Repère : une différence n'est fiable qu'à partir de 4 vidéos par groupe et ~30 vidéos étiquetées au total.")


# ---------------------------------------------------------------- livrables
def cmd_livrables(a):
    P = posts_de(a.dir)
    jour = dt.date.fromisoformat(a.date or aujourdhui())
    suivi = load(P_LIV, {}) or {}
    vues_med = med(p.get("vues") for p in P)
    for jf in sorted(glob.glob(os.path.join(a.livrables, "*.json"))):
        L = load(jf, {}) or {}
        nom = os.path.splitext(os.path.basename(jf))[0]
        leg = (L.get("legende_tiktok") or {})
        acc = norm(leg.get("accroche") or (leg.get("texte_a_coller") or "").split("\n")[0])
        s = suivi.setdefault(nom, {"titre": L.get("titre"), "note_qualite": L.get("note_qualite"), "duree_s": L.get("duree_s"),
                                   "releves": {}})
        post = None
        if s.get("video_id"):
            post = next((p for p in P if str(p.get("id")) == s["video_id"]), None)
        if post is None and acc:
            for p in P:
                if p.get("sujet") and norm(p["sujet"])[:40] and (norm(p["sujet"]).startswith(acc[:40]) or acc.startswith(norm(p["sujet"])[:40])):
                    post = p
                    break
        if post is None:
            s.setdefault("statut", "pas encore publiée (ou légende changée)")
            continue
        ts = post.get("ts")
        pub = dt.datetime.fromtimestamp(ts).date() if isnum(ts) else None
        s.update(video_id=str(post.get("id")), publie_le=pub.isoformat() if pub else None, statut="publiée", lien=post.get("lien"))
        age = (jour - pub).days if pub else None
        rel = {"date": jour.isoformat(), "age_j": age, "vues": post.get("vues"), "eng": eng(post), "moy_s": post.get("moy_s"),
               "complet_pct": post.get("complet_pct"), "commentaires": post.get("commentaires"),
               "vs_mediane_compte": round(post["vues"] / vues_med, 2) if isnum(post.get("vues")) and vues_med else None}
        cle = "J+1" if age is not None and age <= 3 else "J+7" if age is not None and age <= 10 else "J+30" if age is not None and age <= 40 else f"J+{age}"
        s["releves"].setdefault(cle, rel)
        s["releves"]["dernier"] = rel
    save(P_LIV, suivi)
    print(f"{'Livrable':<45} {'publiée':<11} {'note':>5} {'vues':>6} {'x méd.':>6} {'moy s':>6} {'complet':>7}")
    pairs = []
    for nom, s in suivi.items():
        r = (s.get("releves") or {}).get("dernier") or {}
        print(f"{nom[:45]:<45} {str(s.get('publie_le') or '—'):<11} {str(s.get('note_qualite') or '—'):>5} {str(r.get('vues') or '—'):>6} "
              f"{str(r.get('vs_mediane_compte') or '—'):>6} {str(r.get('moy_s') or '—'):>6} {str(r.get('complet_pct') or '—'):>7}")
        if isnum(s.get("note_qualite")) and isnum(r.get("vs_mediane_compte")):
            pairs.append((s["note_qualite"], r["vs_mediane_compte"]))
    if pairs:
        hautes = [v for n, v in pairs if n >= 8]
        if hautes and max(hautes) < 1:
            print(f"Calibrage : {len(hautes)} vidéo(s) notée(s) ≥ 8/10 par le skill vidéo, toutes sous la médiane du compte : "
                  "sa note qualité ne prédit pas encore le résultat (revoir surtout « Arrêt du scroll »).")


# ---------------------------------------------------------------- tests A/B
def tests():
    return load(P_TESTS, {}) or {}


def cmd_test_creer(a):
    T = tests()
    if a.nom in T:
        sys.exit(f"Le test {a.nom} existe déjà")
    T[a.nom] = {"hypothese": a.hypothese, "variantes": {"A": a.a, "B": a.b}, "critere": a.critere, "min": a.min,
                "videos": {"A": [], "B": []}, "cree": aujourdhui(), "statut": "en cours"}
    save(P_TESTS, T)
    print(f"Test {a.nom} créé : A = {a.a} · B = {a.b} · critère {CRITERES.get(a.critere, a.critere)} · {a.min} vidéos minimum par variante")


def cmd_test_ajouter(a):
    T = tests()
    t = T.get(a.nom) or sys.exit(f"Test {a.nom} inconnu")
    v = a.variante.upper()
    if v not in t["videos"]:
        sys.exit("Variante A ou B")
    if a.id not in t["videos"][v]:
        t["videos"][v].append(a.id)
    save(P_TESTS, T)
    print(f"{a.nom} : variante {v} = {t['videos'][v]}")


def verdict(t, P):
    par = {str(p.get("id")): p for p in P}
    c = t["critere"]
    vals = {v: [valeur(par[i], c) for i in ids if i in par] for v, ids in t["videos"].items()}
    vals = {v: [x for x in xs if isnum(x)] for v, xs in vals.items()}
    mA, mB = med(vals["A"]), med(vals["B"])
    out = {"A": {"n": len(vals["A"]), "mediane": mA}, "B": {"n": len(vals["B"]), "mediane": mB}}
    if min(len(vals["A"]), len(vals["B"])) < t["min"]:
        out["verdict"] = f"pas encore assez de vidéos ({len(vals['A'])} A, {len(vals['B'])} B ; {t['min']} chacune)"
    elif mA and mB:
        g = round(100 * (mB - mA) / mA)
        gagnant = "B" if g > 10 else "A" if g < -10 else None
        out["ecart_pct"] = g
        out["verdict"] = (f"{gagnant} gagne ({t['variantes'][gagnant]}) : {abs(g)} % d'écart sur {CRITERES.get(c, c)}"
                          if gagnant else f"pas de différence nette ({g:+d} %) : garder la plus simple")
    return out


def cmd_test_verdict(a):
    T = tests()
    P = posts_de(a.dir)
    for nom, t in T.items():
        if a.nom and nom != a.nom:
            continue
        v = verdict(t, P)
        t["dernier_verdict"] = {**v, "date": aujourdhui()}
        if "gagne" in v.get("verdict", "") or "pas de différence" in v.get("verdict", ""):
            t["statut"] = "terminé"
        print(f"{nom} — {t['hypothese']}\n  A ({t['variantes']['A']}) : n={v['A']['n']} médiane {v['A']['mediane']}\n"
              f"  B ({t['variantes']['B']}) : n={v['B']['n']} médiane {v['B']['mediane']}\n  → {v['verdict']}")
    save(P_TESTS, T)


def cmd_test_liste(a):
    for nom, t in tests().items():
        print(f"{nom} [{t['statut']}] {t['hypothese']} · A {len(t['videos']['A'])} / B {len(t['videos']['B'])} vidéos"
              + (f" · {t['dernier_verdict']['verdict']}" if t.get("dernier_verdict") else ""))


# ---------------------------------------------------------------- tableau de bord
def cmd_tableau(a):
    P = [p for p in posts_de(a.dir) if p.get("type") not in ("carrousel", "photo")]
    e = load(P_ETIQ, {}) or {}
    os.makedirs(a.out, exist_ok=True)
    V = []
    for p in P:
        if not isnum(p.get("vues")):
            continue
        et = e.get(str(p.get("id"))) or {}
        ts = p.get("ts")
        V.append({"id": str(p.get("id")), "publie": dt.datetime.fromtimestamp(ts).date().isoformat() if isnum(ts) else None,
                  "titre": p.get("sujet"), "duree_s": p.get("duree"), "vues": p.get("vues"), "likes": p.get("likes"),
                  "commentaires": p.get("commentaires"), "partages": p.get("partages"), "eng_pct": eng(p),
                  "moy_s": p.get("moy_s"), "complet_pct": p.get("complet_pct"), "decrochage_s": p.get("decrochage_s"),
                  "pour_toi_pct": p.get("pour_toi_pct"), "abonnes_gagnes": p.get("abonnes_gagnes"),
                  "theme": et.get("theme", "non étiquetée"), "serie": et.get("serie", "non étiquetée")})
    save(os.path.join(a.out, "videos.json"), V)
    H = []
    if a.historique:
        for f in sorted(glob.glob(os.path.join(DONNEES, "historique", a.historique, "*", "resume.json"))):
            r = load(f, {}) or {}
            H.append({"date": r.get("date") or os.path.basename(os.path.dirname(f)), "abonnes": r.get("abonnes"),
                      "vues_mediane": r.get("vues_mediane"), "eng_moy_pct": r.get("eng_moy")})
    save(os.path.join(a.out, "historique.json"), H)
    L = []
    for k, s in (load(P_LIV, {}) or {}).items():
        r = (s.get("releves") or {}).get("dernier") or {}
        L.append({"livrable": k, "titre": s.get("titre"), "note_qualite": s.get("note_qualite"), "statut": s.get("statut"),
                  "vues": r.get("vues"), "moy_s": r.get("moy_s"), "vs_mediane_compte": r.get("vs_mediane_compte"), "age_j": r.get("age_j")})
    save(os.path.join(a.out, "livrables.json"), L)
    T = [{"test": k, "hypothese": t["hypothese"], "variante_A": t["variantes"]["A"], "variante_B": t["variantes"]["B"],
          "critere": t["critere"], "min_par_variante": t["min"], "videos_A": len(t["videos"]["A"]), "videos_B": len(t["videos"]["B"]),
          "statut": t["statut"], "verdict": (t.get("dernier_verdict") or {}).get("verdict", "")} for k, t in tests().items()]
    save(os.path.join(a.out, "tests.json"), T)
    print(f"Tableau : {len(V)} vidéos, {len(H)} relevés du compte, {len(L)} livrables, {len(T)} tests -> {a.out}")


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
r = sp.add_parser("retention"); r.add_argument("dir")
e = sp.add_parser("etiquettes"); es = e.add_subparsers(dest="sous", required=True)
ep = es.add_parser("poser"); ep.add_argument("--id", required=True)
for k in ("theme", "accroche", "format", "serie"):
    ep.add_argument("--" + k)
ep.add_argument("--autre", action="append")
ea = es.add_parser("analyser"); ea.add_argument("dir")
lv = sp.add_parser("livrables"); lv.add_argument("dir"); lv.add_argument("--livrables", required=True); lv.add_argument("--date")
t = sp.add_parser("test"); ts = t.add_subparsers(dest="sous", required=True)
tc = ts.add_parser("creer"); tc.add_argument("--nom", required=True); tc.add_argument("--hypothese", required=True)
tc.add_argument("--a", required=True); tc.add_argument("--b", required=True)
tc.add_argument("--critere", default="moy_s", choices=list(CRITERES)); tc.add_argument("--min", type=int, default=3)
ta = ts.add_parser("ajouter"); ta.add_argument("--nom", required=True); ta.add_argument("--variante", required=True); ta.add_argument("--id", required=True)
tv = ts.add_parser("verdict"); tv.add_argument("dir"); tv.add_argument("--nom")
ts.add_parser("liste")
tb = sp.add_parser("tableau"); tb.add_argument("dir"); tb.add_argument("--out", required=True); tb.add_argument("--historique")
a = ap.parse_args()
if a.cmd == "retention":
    cmd_retention(a)
elif a.cmd == "etiquettes":
    {"poser": cmd_etiq_poser, "analyser": cmd_etiq_analyser}[a.sous](a)
elif a.cmd == "livrables":
    cmd_livrables(a)
elif a.cmd == "tableau":
    cmd_tableau(a)
else:
    {"creer": cmd_test_creer, "ajouter": cmd_test_ajouter, "verdict": cmd_test_verdict, "liste": cmd_test_liste}[a.sous](a)
