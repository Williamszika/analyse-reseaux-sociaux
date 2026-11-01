"""Gagner de l'argent avec un compte : où en est-on des seuils de chaque programme, et kit média pour les marques.

python scripts/monetisation.py progres --reseau TikTok --abonnes 833 [--vues-30j 5800] [--duree-mediane 120] [--pays DE] [--age-ok]
      -> pour chaque programme du réseau (reference/plateformes.json, thème monetisation) : % atteint, ce qui manque,
         pays éligible ou non, et au rythme actuel (--gain-abonnes-mois) la date estimée
python scripts/monetisation.py kit --compte <clé> [--out kit.md]
      -> kit média pour partenariats : chiffres du dernier relevé (sourcés et datés), public, formats, contenus phares, contact à compléter

Les seuils changent : regles.py verifier signale ceux à revérifier ; toujours citer la source et la date.
"""
import argparse, datetime as dt, glob, json, os, sys
from common import DONNEES, aujourdhui, isnum, load

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference", "plateformes.json")
PAYS_TIKTOK_REWARDS = {"US", "GB", "UK", "DE", "FR", "JP", "KR", "MX", "BR"}


def regles(reseau):
    R = {r["id"]: r for r in (load(BASE, {}) or {}).get("regles", [])}
    for r in (load(os.path.join(DONNEES, "plateformes.json"), {}) or {}).get("regles", []):
        R[r["id"]] = {**R.get(r["id"], {}), **r}
    return [r for r in R.values() if r.get("theme") == "monetisation" and r.get("reseau", "").lower() == reseau.lower()]


def cmd_progres(a):
    R = regles(a.reseau)
    if not R:
        sys.exit(f"Aucun programme connu pour {a.reseau} : chercher les seuils officiels et les ajouter (regles.py maj)")
    for r in R:
        s = r.get("seuils", {})
        print(f"\n■ {r['id']} — {r['regle']}\n  (source : {r['source']}, vérifié le {r['verifie']}, {r['fiabilite']})")
        if "abonnes" in s and a.abonnes is not None:
            pct = min(100, round(100 * a.abonnes / s["abonnes"]))
            manque = max(0, s["abonnes"] - a.abonnes)
            ligne = f"  Abonnés : {a.abonnes} / {s['abonnes']} ({pct} %)" + (f", il en manque {manque}" if manque else " ✓")
            if manque and a.gain_abonnes_mois and a.gain_abonnes_mois > 0:
                mois = manque / a.gain_abonnes_mois
                ligne += f" — au rythme actuel ({a.gain_abonnes_mois:.0f}/mois) : environ {mois:.0f} mois"
            print(ligne)
        if "vues_30j" in s and a.vues_30j is not None:
            pct = min(100, round(100 * a.vues_30j / s["vues_30j"]))
            print(f"  Vues sur 30 jours : {a.vues_30j} / {s['vues_30j']} ({pct} %)")
        if "duree_min_s" in s and a.duree_mediane is not None:
            print(f"  Durée : médiane {a.duree_mediane:.0f} s, il faut plus de {s['duree_min_s'] - 1} s " +
                  ("✓" if a.duree_mediane >= s["duree_min_s"] else "✗"))
        if r["id"] == "tiktok_creator_rewards" and a.pays:
            print(f"  Pays du compte ({a.pays}) : " + ("éligible ✓" if a.pays.upper() in PAYS_TIKTOK_REWARDS else
                                                    "pas dans la liste publiée ✗ (vérifier dans l'appli : Outils pour créateurs)"))


def cmd_kit(a):
    H = sorted(glob.glob(os.path.join(DONNEES, "historique", a.compte, "*", "resume.json")))
    if not H:
        sys.exit(f"Aucune analyse archivée pour {a.compte}")
    r = load(H[-1], {}) or {}
    s = load(os.path.join(os.path.dirname(H[-1]), "stats_internes.json"), {}) or {}
    ret = load(os.path.join(os.path.dirname(H[-1]), "retention.json"), {}) or {}
    p = r.get("profil_actuel") or {}
    L = [f"# Kit média — {p.get('nom') or a.compte} ({p.get('pseudo') or ''}, {r.get('reseau')})", "",
         f"*Chiffres du {r.get('date')}, relevés dans les statistiques du compte.*", "",
         "## Le compte", "", f"- {p.get('categorie') or 'créateur'} — langue : {p.get('langue') or '?'}",
         f"- Abonnés : **{r.get('abonnes')}**", f"- Vues médianes par publication : **{r.get('vues_mediane')}**",
         f"- Engagement moyen : **{r.get('eng_moy')} %**"]
    for k, v in (r.get("internes") or {}).items():
        L.append(f"- {k} : {v}")
    if ret:
        L.append(f"- Temps moyen regardé (médiane) : {ret.get('moy_s_mediane')} s")
    if s.get("pays") or s.get("audience"):
        L += ["", "## Le public", "", json.dumps(s.get("pays") or s.get("audience"), ensure_ascii=False)]
    L += ["", "## Ce que je propose aux marques", "", "- Vidéo dédiée (histoire de 1 à 3 min où le produit a un vrai rôle)",
          "- Mention dans une série existante", "- Live ou questions-réponses", "",
          "## Contact", "", "<à compléter par le propriétaire : e-mail professionnel, ville, tarifs>", "",
          "*Aucun chiffre n'est arrondi à la hausse ; dates et sources disponibles sur demande.*"]
    out = "\n".join(L) + "\n"
    if a.out:
        open(a.out, "w", encoding="utf-8").write(out)
    print(out)


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
p = sp.add_parser("progres"); p.add_argument("--reseau", required=True); p.add_argument("--abonnes", type=int)
p.add_argument("--vues-30j", type=int); p.add_argument("--duree-mediane", type=float); p.add_argument("--pays")
p.add_argument("--gain-abonnes-mois", type=float)
k = sp.add_parser("kit"); k.add_argument("--compte", required=True); k.add_argument("--out")
a = ap.parse_args()
{"progres": cmd_progres, "kit": cmd_kit}[a.cmd](a)
