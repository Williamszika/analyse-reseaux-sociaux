"""Examen du skill : 20 cas types, note par cas, comparaison avec l'examen précédent.

python scripts/evaluer.py liste                          -> les cas (demande + contexte) à faire jouer au skill
python scripts/evaluer.py noter <dossier des réponses> [--out resultats.json] [--precedent ancien.json]
      chaque réponse dans <dossier>/<id>.md ; note = motifs attendus trouvés − interdits présents ; total sur 100
"""
import argparse, json, os, re, sys

CAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "evals", "cas.json")


def cas():
    return json.load(open(CAS, encoding="utf-8"))["cas"]


def cmd_liste(a):
    for c in cas():
        print(f"{c['id']:<22} « {c['demande']} »" + (f"  [{c['contexte']}]" if c["contexte"] else ""))


def noter_un(c, txt):
    att = [bool(re.search(m, txt, re.I)) for m in c["attendus"]]
    inter = [m for m in c["interdits"] if re.search(m, txt, re.I)]
    pts = (sum(att) / len(att) if att else 1) * (0 if inter else 1)
    return round(100 * pts), [m for m, ok in zip(c["attendus"], att) if not ok], inter


def cmd_noter(a):
    R, total, n = {}, 0, 0
    for c in cas():
        p = os.path.join(a.dossier, f"{c['id']}.md")
        if not os.path.exists(p):
            R[c["id"]] = {"note": None, "manque": "réponse absente"}
            continue
        note, manq, inter = noter_un(c, open(p, encoding="utf-8").read())
        R[c["id"]] = {"note": note, "attendus_absents": manq, "interdits_presents": inter}
        total += note
        n += 1
    moy = round(total / n) if n else 0
    prev = json.load(open(a.precedent, encoding="utf-8")) if a.precedent and os.path.exists(a.precedent) else None
    for k, v in R.items():
        d = ""
        if prev and prev["cas"].get(k, {}).get("note") is not None and v["note"] is not None:
            e = v["note"] - prev["cas"][k]["note"]
            d = f"  ({'+' if e >= 0 else ''}{e})" if e else ""
        print(f"{k:<22} {v['note'] if v['note'] is not None else '—':>4}{d}  " +
              ("; ".join(filter(None, [("manque : " + ", ".join(v.get('attendus_absents', []))) if v.get('attendus_absents') else "",
                                       ("INTERDIT : " + ", ".join(v.get('interdits_presents', []))) if v.get('interdits_presents') else ""]))))
    print(f"\nNote globale : {moy}/100 sur {n} cas" + (f" (précédente : {prev['note']}/100)" if prev else ""))
    if a.out:
        json.dump({"note": moy, "n": n, "cas": R}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.exit(0 if not any(v.get("interdits_presents") for v in R.values()) else 4)


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
sp.add_parser("liste")
n = sp.add_parser("noter"); n.add_argument("dossier"); n.add_argument("--out"); n.add_argument("--precedent")
a = ap.parse_args()
{"liste": cmd_liste, "noter": cmd_noter}[a.cmd](a)
