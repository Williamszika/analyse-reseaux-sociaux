"""Comprendre le public par ses commentaires : émotions, questions, histoires, pays, sujets demandés, idées de vidéos.

python scripts/commentaires.py analyser <commentaires.json> --out <dossier> [--mots-cles-compte "motivation,diaspora"]
  commentaires.json : [{"texte": "...", "video": "<id ou titre>", "likes": 3}]  (le nom de l'auteur n'est jamais gardé)
  -> commentaires_analyse.json et commentaires.md : émotions, questions qui reviennent, histoires racontées, pays cités,
     demandes de vidéos, mots les plus fréquents, et sujets à transformer en vidéos (avec le nombre de commentaires qui les portent)

Le rapport ne cite jamais un nom d'abonné ; les extraits sont courts et anonymes.
"""
import argparse, json, os, re, sys, unicodedata
from collections import Counter

EMOTIONS = {
    "gratitude": ["merci", "grace a toi", "grace a vous", "reconnaissant", "beni", "amen", "dieu te benisse", "que dieu"],
    "inspiration": ["motive", "motivation", "inspire", "force", "courage", "je vais", "a partir d aujourd", "declic", "puissant"],
    "identification": ["c est moi", "comme moi", "je me reconnais", "mon histoire", "moi aussi", "exactement", "vecu", "ca me parle"],
    "tristesse": ["triste", "pleure", "larmes", "mal", "difficile", "seul", "seule", "douleur", "dur"],
    "joie": ["haha", "mdr", "trop bien", "magnifique", "top", "bravo", "felicitations", "genial", "j adore"],
    "desaccord": ["pas d accord", "faux", "n importe quoi", "mensonge", "arrete", "bof", "nul"],
}
PAYS = {"Côte d'Ivoire": ["cote d ivoire", "ivoirien", "ivoirienne", "abidjan", "civ", "225"],
        "Sénégal": ["senegal", "senegalais", "dakar"], "Cameroun": ["cameroun", "camerounais", "douala", "yaounde"],
        "Mali": ["mali", "malien", "bamako"], "Burkina Faso": ["burkina", "burkinabe", "ouagadougou"],
        "Togo": ["togo", "togolais", "lome"], "Bénin": ["benin", "beninois", "cotonou"], "Guinée": ["guinee", "guineen", "conakry"],
        "RD Congo": ["rdc", "kinshasa", "congolais"], "Congo": ["brazzaville"], "Gabon": ["gabon", "gabonais", "libreville"],
        "Maroc": ["maroc", "marocain"], "Algérie": ["algerie", "algerien"], "Tunisie": ["tunisie", "tunisien"],
        "France": ["france", "paris", "francais"], "Belgique": ["belgique", "bruxelles", "belge"],
        "Allemagne": ["allemagne", "deutschland", "germany"], "Canada": ["canada", "quebec", "montreal"],
        "Suisse": ["suisse", "geneve"], "Italie": ["italie"], "Espagne": ["espagne"], "Haïti": ["haiti", "haitien"]}
DEMANDES = [r"fais (?:une|nous une|moi une) video sur (.{3,60})", r"parle(?:z)? (?:nous |moi )?(?:de|du|des) (.{3,60})",
            r"partie ?2|la suite|suite svp|suite stp", r"tu peux (?:faire|parler) (.{3,60})", r"j aimerais (?:une video|que tu parles) (.{3,60})"]
VIDES = set("le la les un une des de du d l et a au aux en dans sur pour par avec sans ce cet cette ces mon ma mes ton ta tes son sa ses "
            "notre nos votre vos leur leurs je tu il elle on nous vous ils elles me te se moi toi lui y ne pas plus que qui quoi est "
            "suis es sont ai as a ont ete etre avoir fait faire c ca cela tres trop bien aussi mais ou donc or ni car si tout tous toute "
            "toutes comme quand meme encore deja alors oui non merci bonjour bonsoir svp stp".split())


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9? ]", " ", t.replace("'", " ")).split())


def cmd_analyser(a):
    C = json.load(open(a.fichier, encoding="utf-8"))
    if not C:
        sys.exit("Aucun commentaire")
    emo, pays, mots, questions, histoires, demandes = Counter(), Counter(), Counter(), Counter(), [], Counter()
    for c in C:
        t = norm(c.get("texte"))
        for e, L in EMOTIONS.items():
            if any(x in t for x in L):
                emo[e] += 1
        for p, L in PAYS.items():
            if any(re.search(rf"\b{re.escape(x)}\b", t) for x in L):
                pays[p] += 1
        if "?" in (c.get("texte") or ""):
            q = re.sub(r"\s+", " ", t.split("?")[0])[-80:].strip()
            if len(q.split()) >= 3:
                questions[" ".join(q.split()[-8:])] += 1
        if len(t.split()) >= 25 and re.search(r"\b(je|j|ma|mon|mes|moi)\b", t):
            histoires.append({"video": c.get("video"), "extrait": " ".join((c.get("texte") or "").split()[:25]) + " …"})
        for r in DEMANDES:
            m = re.search(r, t)
            if m:
                demandes[(m.group(1).strip() if m.groups() else "la suite (partie 2)")[:60]] += 1
        mots.update(w for w in t.split() if w not in VIDES and len(w) > 3 and not w.isdigit())
    n = len(C)
    sujets = [(w, k) for w, k in mots.most_common(40) if k >= max(2, n // 50)][:12]
    R = {"n": n, "emotions": emo.most_common(), "pays": pays.most_common(10), "questions": questions.most_common(10),
         "histoires": histoires[:8], "nb_histoires": len(histoires), "demandes": demandes.most_common(10), "mots": sujets}
    idees = []
    for d, k in demandes.most_common(3):
        idees.append(f"Demandé {k} fois : « {d} »")
    if emo.get("identification"):
        idees.append(f"{emo['identification']} commentaires disent « c'est moi » : refaire une histoire du même type, avec la même situation de départ")
    if histoires:
        idees.append(f"{len(histoires)} personnes racontent leur propre histoire : en faire une série « vos histoires » (avec leur accord, anonymisée)")
    if questions:
        q, k = questions.most_common(1)[0]
        idees.append(f"Question qui revient ({k}×) : « {q} ? » — y répondre dans une vidéo")
    R["idees"] = idees
    os.makedirs(a.out, exist_ok=True)
    json.dump(R, open(os.path.join(a.out, "commentaires_analyse.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L = [f"# Ce que disent les commentaires ({n})", "", "**Émotions** : " + (", ".join(f"{e} {round(100 * k / n)} %" for e, k in emo.most_common()) or "—"),
         "", "**Pays cités** : " + (", ".join(f"{p} ({k})" for p, k in pays.most_common(8)) or "aucun"),
         "", "**Questions qui reviennent** :"] + [f"- {q} ? ({k})" for q, k in questions.most_common(5)] + \
        ["", "**Demandes de vidéos** :"] + ([f"- {d} ({k})" for d, k in demandes.most_common(5)] or ["- aucune"]) + \
        ["", f"**Histoires racontées** : {len(histoires)}"] + [f"- « {h['extrait']} »" for h in histoires[:3]] + \
        ["", "**Mots les plus fréquents** : " + ", ".join(f"{w} ({k})" for w, k in sujets)] + \
        ["", "## Idées de vidéos tirées des commentaires", ""] + [f"- {i}" for i in idees]
    open(os.path.join(a.out, "commentaires.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
an = sp.add_parser("analyser"); an.add_argument("fichier"); an.add_argument("--out", required=True); an.add_argument("--mots-cles-compte")
a = ap.parse_args()
cmd_analyser(a)
