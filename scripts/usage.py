"""Journal des sessions (privé, chez l'utilisateur) et rapports d'usage anonymes (pour l'auteur du skill).

Journal privé — $ANALYSES_DONNEES/journal.jsonl, une ligne par session, complet, jamais envoyé à personne :
  python scripts/usage.py debut --mode D --reseau TikTok [--compte tiktok_awa] [--client "Nom"]   -> affiche l'id
  python scripts/usage.py etape "connecteur Metricool vide"     note une étape bloquée ou contournée
  python scripts/usage.py fin [--statut ok|partiel|echec] [--note "..."]
  python scripts/usage.py journal [--depuis AAAA-MM-JJ]           résumé de ses propres sessions

Rapport d'usage anonyme — seulement avec l'accord de l'utilisateur, texte montré avant :
  python scripts/usage.py rapport [--id <session>]
    -> rapport_usage.md + un lien « nouveau ticket » prérempli vers le dépôt public de la boîte à outils.
    Contient UNIQUEMENT : jour, durée arrondie, mode, réseau, version, statut, catégories d'étapes bloquées.
    Jamais : pseudo, nom, client, chiffres d'un compte, texte libre, liens, heure exacte.

Tableau de bord de l'auteur (propriétaire du dépôt de la boîte à outils) :
  gh issue list -R <depot> --label usage --state all --limit 1000 --json body,createdAt > tickets.json
  python scripts/usage.py tableau tickets.json [--out tableau.md]
"""
import argparse, json, os, re, statistics as st, sys, urllib.parse, uuid
from collections import Counter
from common import BASE, JOURNAL, VERSION, lire_jsonl, ecrire_jsonl, load, maintenant, projet, reseau, save
import datetime as dt

EN_COURS = os.path.join(BASE, ".session_en_cours.json")
MODES = {"A": "un contenu", "B": "recherche + analyse", "C": "recherche par période", "D": "analyse d'un compte",
         "E": "abonnement", "F": "horaires", "G": "profil", "H": "calendrier", "I": "suivi", "J": "stats internes",
         "K": "cohérence", "M": "publicités", "N": "publier / commenter"}
# Catégories autorisées dans un rapport anonyme : le texte libre des étapes n'en sort jamais.
CATEGORIES = [("connecteur", r"connecteur|metricool|supermetrics|vidiq"), ("connexion", r"connexion|login|captcha|vérification"),
              ("navigateur", r"navigateur|chrome|page|onglet"), ("ordinateur", r"ordinateur|mac|device|whisper|yt-dlp"),
              ("pdf", r"pdf|weasyprint|rapport"), ("script", r"script|erreur|traceback|exception"),
              ("donnees", r"dépôt|depot|github|push|données"), ("limite_reseau", r"limite|bloqu|rate|429")]


def sessions():
    return lire_jsonl(JOURNAL)


def maj(sid, **champs):
    lignes = sessions()
    for l in lignes:
        if l.get("id") == sid:
            l.update(champs)
    ecrire_jsonl(JOURNAL, lignes)
    return next((l for l in lignes if l.get("id") == sid), None)


def courante(sid=None):
    if sid:
        return sid
    e = load(EN_COURS, {}) or {}
    return e.get("id")


def cmd_debut(a):
    sid = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
    l = {"id": sid, "debut": maintenant(), "mode": a.mode.upper(), "mode_nom": MODES.get(a.mode.upper(), a.mode),
         "reseau": reseau(a.reseau)["nom"] if a.reseau else None, "compte": a.compte, "client": a.client,
         "version": VERSION, "etapes": [], "statut": "en_cours"}
    lignes = sessions() + [l]
    ecrire_jsonl(JOURNAL, lignes)
    save(EN_COURS, {"id": sid})
    print(sid)


def cmd_etape(a):
    sid = courante(a.id)
    if not sid:
        sys.exit("Aucune session en cours (usage.py debut d'abord)")
    l = next((x for x in sessions() if x.get("id") == sid), None)
    if not l:
        sys.exit(f"Session {sid} introuvable")
    maj(sid, etapes=(l.get("etapes") or []) + [a.texte])
    print("Noté :", a.texte)


def cmd_fin(a):
    sid = courante(a.id)
    if not sid:
        sys.exit("Aucune session en cours")
    l = next((x for x in sessions() if x.get("id") == sid), None)
    if not l:
        sys.exit(f"Session {sid} introuvable")
    fin = maintenant()
    try:
        duree = (dt.datetime.fromisoformat(fin) - dt.datetime.fromisoformat(l["debut"])).total_seconds() / 60
    except Exception:
        duree = None
    l = maj(sid, fin=fin, duree_min=round(duree, 1) if duree is not None else None, statut=a.statut,
            note=a.note or l.get("note"))
    if os.path.exists(EN_COURS) and (load(EN_COURS, {}) or {}).get("id") == sid:
        os.remove(EN_COURS)
    print(f"Session {sid} terminée : {l.get('duree_min')} min, statut {a.statut}")


def cmd_journal(a):
    s = [l for l in sessions() if not a.depuis or (l.get("debut") or "") >= a.depuis]
    if not s:
        print("Aucune session dans le journal")
        return
    fin = [l for l in s if isinstance(l.get("duree_min"), (int, float))]
    print(f"{len(s)} session(s), {sum(l['duree_min'] for l in fin):.0f} min au total")
    for k, titre in [("mode_nom", "Par mode"), ("reseau", "Par réseau"), ("statut", "Par statut")]:
        print(f"{titre} : " + ", ".join(f"{v or '—'} {n}" for v, n in Counter(l.get(k) for l in s).most_common()))
    for l in s[-10:]:
        print(f"- {l.get('debut', '')[:16]} · {l.get('mode_nom')} · {l.get('reseau') or '—'} · "
              f"{l.get('compte') or '—'} · {l.get('duree_min', '—')} min · {l.get('statut')}")


def categories(etapes):
    out = set()
    for e in etapes or []:
        for cat, motif in CATEGORIES:
            if re.search(motif, str(e), re.I):
                out.add(cat)
                break
        else:
            out.add("autre")
    return sorted(out)


def anonyme(l):
    """Liste blanche stricte : rien d'autre ne sort du journal."""
    d = l.get("duree_min")
    duree = None if d is None else ("< 5 min" if d < 5 else "5-15 min" if d < 15 else "15-30 min" if d < 30
                                    else "30-60 min" if d < 60 else "> 60 min")
    r = reseau(l.get("reseau"))
    return {"type": "rapport_usage", "version_rapport": 1, "jour": (l.get("debut") or "")[:10],
            "duree": duree, "mode": l.get("mode"), "reseau": r["nom"] if r["connu"] else ("aucun" if not l.get("reseau") else "autre"),
            "version_skill": l.get("version"), "statut": l.get("statut"), "blocages": categories(l.get("etapes")),
            "audit_client": bool(l.get("client"))}


def cmd_rapport(a):
    s = sessions()
    if not s:
        sys.exit("Aucune session dans le journal")
    l = next((x for x in s if x.get("id") == a.id), None) if a.id else s[-1]
    if not l:
        sys.exit(f"Session {a.id} introuvable")
    r = anonyme(l)
    pj = projet()
    corps = ("Rapport d'usage anonyme du skill analyse-reseaux-sociaux, envoyé avec l'accord de son utilisateur.\n"
             "Il ne contient ni pseudo, ni nom, ni chiffres de compte.\n\n```json\n"
             + json.dumps(r, ensure_ascii=False, indent=1) + "\n```\n")
    titre = f"Usage {r['jour']} · mode {r['mode']} · {r['reseau']} · {r['statut']}"
    url = (f"https://github.com/{pj.get('depot_outils')}/issues/new?"
           + urllib.parse.urlencode({"title": titre, "labels": pj.get("label_usage", "usage"), "body": corps}))
    out = os.path.join(BASE, "rapport_usage.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# {titre}\n\n{corps}\n")
    print(corps)
    print("Fichier :", out)
    print("Lien pour l'envoyer (ouvre un ticket prérempli, rien n'est envoyé sans clic) :")
    print(url)


def cmd_tableau(a):
    brut = load(a.fichier)
    if brut is None:
        sys.exit("Fichier illisible : attendu la sortie JSON de « gh issue list ... --json body,createdAt »")
    rapports = []
    for t in brut if isinstance(brut, list) else brut.get("issues", []):
        m = re.search(r"```json\s*(\{.*?\})\s*```", t.get("body") or "", re.S)
        if not m:
            continue
        try:
            r = json.loads(m.group(1))
        except Exception:
            continue
        if r.get("type") == "rapport_usage":
            rapports.append(r)
    if not rapports:
        sys.exit("Aucun rapport d'usage valide dans ce fichier")
    jours = sorted(r.get("jour") or "" for r in rapports)
    L = [f"# Tableau de bord — usage du skill ({len(rapports)} rapports, {jours[0]} → {jours[-1]})", ""]

    def bloc(titre, compteur):
        L.append(f"## {titre}")
        L.append("| Valeur | Nombre | Part |")
        L.append("|---|---|---|")
        for v, n in compteur.most_common():
            L.append(f"| {v if v not in (None, '') else '—'} | {n} | {100 * n / len(rapports):.0f} % |")
        L.append("")

    bloc("Modes utilisés", Counter(f"{r.get('mode')} · {MODES.get(r.get('mode'), '?')}" for r in rapports))
    bloc("Réseaux", Counter(r.get("reseau") for r in rapports))
    bloc("Résultat", Counter(r.get("statut") for r in rapports))
    bloc("Étapes qui bloquent (une session peut en avoir plusieurs)", Counter(b for r in rapports for b in r.get("blocages") or []))
    bloc("Versions du skill", Counter(r.get("version_skill") for r in rapports))
    bloc("Durée", Counter(r.get("duree") for r in rapports))
    bloc("Par mois", Counter((r.get("jour") or "")[:7] for r in rapports))
    echecs = [r for r in rapports if r.get("statut") in ("echec", "partiel")]
    if echecs:
        L.append(f"## À améliorer en priorité\n{len(echecs)} session(s) en échec ou partielles ; blocages les plus fréquents : "
                 + ", ".join(f"{b} ({n})" for b, n in Counter(b for r in echecs for b in r.get("blocages") or []).most_common(3)) + ".")
    txt = "\n".join(L)
    print(txt)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(txt + "\n")
        print("\nÉcrit :", a.out)


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
d = sp.add_parser("debut"); d.add_argument("--mode", required=True); d.add_argument("--reseau"); d.add_argument("--compte"); d.add_argument("--client")
e = sp.add_parser("etape"); e.add_argument("texte"); e.add_argument("--id")
f = sp.add_parser("fin"); f.add_argument("--statut", choices=["ok", "partiel", "echec"], default="ok"); f.add_argument("--note"); f.add_argument("--id")
j = sp.add_parser("journal"); j.add_argument("--depuis")
r = sp.add_parser("rapport"); r.add_argument("--id")
t = sp.add_parser("tableau"); t.add_argument("fichier"); t.add_argument("--out")
a = ap.parse_args()
{"debut": cmd_debut, "etape": cmd_etape, "fin": cmd_fin, "journal": cmd_journal, "rapport": cmd_rapport,
 "tableau": cmd_tableau}[a.cmd](a)
