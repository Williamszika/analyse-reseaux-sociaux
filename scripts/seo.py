"""Référencement (recherche TikTok, YouTube, Instagram) : les mots que le public tape, et leur place dans chaque vidéo.

python scripts/seo.py mots --compte <clé> --ajouter "motivation diaspora" "réussir loin de chez soi" … [--source "suggestions TikTok du 01/11"]
python scripts/seo.py mots --compte <clé>                 -> liste des mots-clés suivis
python scripts/seo.py verifier --compte <clé> --titre "<titre à l'écran>" --dits "<10 premiers mots dits>" --legende "<légende>"
      [--hashtags "#a #b"] [--soustitres <fichier.srt>]
      -> pour chaque mot-clé : présent ou non dans le titre, les premiers mots dits, la 1re ligne de la légende, les hashtags ;
         note /10 et corrections proposées
python scripts/seo.py trafic --stats rapports/<dossier>/stats_internes.json
      -> part des vues venues de la recherche (champ « sources de trafic » des statistiques internes)

Les mots-clés viennent de la vraie recherche : suggestions de la barre de recherche du réseau, « Autres recherches »,
TikTok Creative Center, vidIQ (YouTube). Jamais inventés.
"""
import argparse, json, os, re, sys, unicodedata
from common import DONNEES, aujourdhui, load, save

P = os.path.join(DONNEES, "seo.json")


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9# ]", " ", t).split())


def present(mot, texte):
    m, t = norm(mot).split(), norm(texte)
    if not m:
        return False
    if " ".join(m) in t:
        return True
    pleins = [w for w in m if len(w) > 3]
    return bool(pleins) and all(w in t.split() or w[:-1] in t for w in pleins)


def cmd_mots(a):
    S = load(P, {}) or {}
    L = S.setdefault(a.compte, [])
    for m in a.ajouter or []:
        if not any(norm(x["mot"]) == norm(m) for x in L):
            L.append({"mot": m, "source": a.source, "ajoute": aujourdhui()})
    if a.ajouter:
        if not a.source:
            sys.exit("Indiquez --source (d'où vient ce mot-clé : suggestions de recherche, Creative Center, vidIQ…)")
        save(P, S)
    for x in L:
        print(f"- {x['mot']}  ({x.get('source') or '?'}, {x.get('ajoute')})")


def cmd_verifier(a):
    mots = [x["mot"] for x in (load(P, {}) or {}).get(a.compte, [])]
    if not mots:
        sys.exit(f"Aucun mot-clé pour {a.compte} : seo.py mots --compte {a.compte} --ajouter … --source …")
    st_ = ""
    if a.soustitres and os.path.exists(a.soustitres):
        st_ = " ".join(l for l in open(a.soustitres, encoding="utf-8").read().splitlines()
                       if l.strip() and not re.match(r"^\d+$|^\d\d:\d\d", l.strip()))
    legende1 = (a.legende or "").strip().split("\n")[0]
    zones = {"titre": a.titre or "", "premiers mots dits": a.dits or "", "1re ligne de légende": legende1,
             "hashtags": a.hashtags or "", "sous-titres": st_}
    lignes, score = [], 0.0
    poids = {"titre": 3, "premiers mots dits": 3, "1re ligne de légende": 2.5, "hashtags": 1.5}
    principal = mots[0]
    for m in mots:
        z = {k: present(m, v) for k, v in zones.items()}
        lignes.append((m, z))
    zp = lignes[0][1]
    score = sum(p for k, p in poids.items() if zp[k])
    autres = sum(1 for m, z in lignes[1:] if any(z.values()))
    print(f"{'Mot-clé':<32}" + "".join(f"{k[:14]:>16}" for k in zones))
    for m, z in lignes:
        print(f"{m[:31]:<32}" + "".join(f"{'oui' if z[k] else '—':>16}" for k in zones))
    C = []
    if not zp["titre"]:
        C.append(f"mettre « {principal} » (ou ses mots forts) dans le titre à l'écran")
    if not zp["premiers mots dits"]:
        C.append(f"le dire dans les 10 premiers mots : la recherche lit aussi la voix")
    if not zp["1re ligne de légende"]:
        C.append("l'écrire en toutes lettres dans la 1re ligne de la légende (pas seulement en hashtag)")
    if len(re.findall(r"#\w+", a.hashtags or a.legende or "")) > 6:
        C.append("6 hashtags au plus : la recherche s'appuie surtout sur les mots écrits et dits")
    print(f"\nNote de référencement : {score}/10 (mot-clé principal « {principal} »), {autres} autre(s) mot(s)-clé(s) présent(s)")
    for c in C:
        print("  → " + c)
    print(json.dumps({"note": score, "principal": principal, "corrections": C}, ensure_ascii=False))


def cmd_trafic(a):
    s = load(a.stats, {}) or {}
    src = s.get("sources_trafic")
    if not src:
        sys.exit("Pas de « sources_trafic » dans stats_internes.json : relever dans les statistiques internes "
                 "(TikTok Studio → vidéo → Sources de trafic : Pour toi, Recherche, Profil, Abonnements, Son…)")
    tot = sum(v for v in src.values() if isinstance(v, (int, float)))
    rech = sum(v for k, v in src.items() if "recherche" in norm(k) or "search" in norm(k))
    print(f"Part des vues venues de la recherche : {round(100 * rech / tot, 1) if tot else 0} %")


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
m = sp.add_parser("mots"); m.add_argument("--compte", required=True); m.add_argument("--ajouter", nargs="*"); m.add_argument("--source")
v = sp.add_parser("verifier"); v.add_argument("--compte", required=True)
for k in ("titre", "dits", "legende", "hashtags", "soustitres"):
    v.add_argument("--" + k)
t = sp.add_parser("trafic"); t.add_argument("--stats", required=True)
a = ap.parse_args()
{"mots": cmd_mots, "verifier": cmd_verifier, "trafic": cmd_trafic}[a.cmd](a)
