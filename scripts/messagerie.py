"""Messagerie (mode O) : répondre aux clients, prendre des rendez-vous, chercher des partenaires, relancer des contacts,
et faire un rapport au propriétaire — sur n'importe quel compte (WhatsApp, Telegram, Instagram, Messenger, LinkedIn…).

Tout vit dans l'espace de données : $ANALYSES_DONNEES/messagerie/<compte>/
  cadre.json      ce que Claude a le droit de répondre seul (comptes d'entreprise), validé par le propriétaire
  contacts.json   clients, partenaires visés, personnes à relancer, oppositions (« STOP »)
  journal.jsonl   chaque message reçu ou envoyé, et chaque décision

python scripts/messagerie.py cadre init --compte chapci_whatsapp --plateforme whatsapp --type entreprise --nom "Chap.ci"
python scripts/messagerie.py cadre montrer --compte …          -> le texte exact à faire valider
python scripts/messagerie.py cadre valider --compte … --accord "<ses mots exacts>"
python scripts/messagerie.py decider --compte … --de "<contact>" --message "<texte reçu>"   -> JSON : auto | rdv | stop | proprietaire
python scripts/messagerie.py creneaux --compte … [--occupe occupe.json] [--jours 7] [--n 3]
python scripts/messagerie.py noter --compte … --contact … --sens recu|envoye --texte … [--auto] [--decision …]
python scripts/messagerie.py contact --compte … --nom … [--canal …] [--motif client|partenaire|relance] [--source …]
      [--consentement "<date, comment>"] [--relancer-dans-j 7] [--note …]
python scripts/messagerie.py a-faire --compte …                -> relances dues et partenaires à contacter (brouillons à valider)
python scripts/messagerie.py rapport --compte … [--date AAAA-MM-JJ] [--out rapport.md]

Règles (aussi dans reference/messagerie.md) :
- Réponse automatique SEULEMENT sur un compte « entreprise », avec un cadre validé (empreinte inchangée depuis l'accord),
  à une personne qui a écrit la première, avec une réponse tirée du cadre. Tout le reste va au propriétaire.
- Jamais d'envoi en série, jamais d'écrit à quelqu'un qui a dit STOP, plafonds par jour.
- Premier message à un inconnu (partenaire) : brouillon validé par le propriétaire, un à la fois, et seulement sur un
  canal où c'est permis (pas de WhatsApp ou Telegram sans consentement de la personne).
"""
import argparse, datetime as dt, hashlib, json, os, re, sys, unicodedata
from common import DONNEES, load, save

PERMIS_PREMIER_MESSAGE = {"linkedin", "instagram", "email", "x", "facebook", "messenger", "tiktok"}
STOP = {"stop", "arret", "arrete", "desabonner", "desinscrire", "ne m ecrivez plus", "unsubscribe"}
RDV = {"rendez vous", "rdv", "rendez-vous", "disponible", "dispo", "creneau", "reserver", "rencontrer", "appel", "visio",
       "passer vous voir", "quand pouvez", "quand peut on"}
ESCALADE_DEFAUT = ["plainte", "rembourse", "avocat", "arnaque", "escroc", "police", "menace", "urgent", "malade", "deces",
                   "insulte", "facture", "paiement", "virement", "mot de passe", "code"]


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", t).split())


def dossier(compte):
    d = os.path.join(DONNEES, "messagerie", compte)
    os.makedirs(d, exist_ok=True)
    return d


def P(compte, nom):
    return os.path.join(dossier(compte), nom)


def maintenant():
    return dt.datetime.now().astimezone()


def empreinte(cadre):
    c = {k: v for k, v in cadre.items() if k not in ("validation",)}
    return hashlib.sha256(json.dumps(c, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def cadre_de(compte):
    c = load(P(compte, "cadre.json"))
    if c is None:
        sys.exit(f"Pas de cadre pour {compte} : messagerie.py cadre init --compte {compte} …")
    return c


def cadre_valide(c):
    v = c.get("validation") or {}
    return bool(v.get("accord")) and v.get("empreinte") == empreinte(c)


def journal(compte, **e):
    e = {"date": maintenant().isoformat(timespec="seconds"), **e}
    with open(P(compte, "journal.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")


def lire_journal(compte):
    p = P(compte, "journal.jsonl")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def contacts(compte):
    return load(P(compte, "contacts.json"), {}) or {}


# ---------------------------------------------------------------- cadre
MODELE = {
    "nom_affiche": "", "plateforme": "", "type": "entreprise", "langue": "fr", "tutoiement": False,
    "ton": "chaleureux, simple, professionnel ; phrases courtes ; 1 émoji au plus",
    "presentation": "Bonjour, ici <nom>. Merci pour votre message !",
    "signature": "",
    "faq": [
        {"mots": ["horaire", "ouvert", "heure"], "reponse": "Nous sommes ouverts du lundi au samedi, de 9 h à 18 h."},
        {"mots": ["prix", "tarif", "combien", "cout"], "reponse": "<à remplir : prix exacts, ou « je vous envoie la grille tarifaire »>"},
        {"mots": ["adresse", "ou etes", "situe", "localisation"], "reponse": "<à remplir>"},
    ],
    "rdv": {"actif": True, "objet": "rendez-vous", "duree_min": 30, "jours": ["Lun", "Mar", "Mer", "Jeu", "Ven"],
            "plages": ["09:00-12:00", "14:00-17:00"], "delai_min_h": 24, "horizon_j": 7, "lieu": "appel WhatsApp",
            "fuseau": "Europe/Berlin", "auto_confirmer": True},
    "escalade": ESCALADE_DEFAUT,
    "interdits": ["donner un prix, une remise ou un délai absent du cadre", "demander ou accepter un paiement",
                  "demander des données personnelles au-delà du nom et du créneau", "promettre un résultat",
                  "parler au nom du propriétaire de sa vie privée"],
    "limites": {"auto_par_jour": 50, "auto_par_contact_par_jour": 5, "premiers_messages_par_jour": 10},
    "relance": {"delai_j": 7, "max": 2},
    "hors_cadre": "Merci, je transmets votre message à <nom>, qui vous répond au plus vite.",
}


def cmd_cadre_init(a):
    p = P(a.compte, "cadre.json")
    if os.path.exists(p) and not a.forcer:
        sys.exit(f"Le cadre de {a.compte} existe déjà (--forcer pour le recréer)")
    c = json.loads(json.dumps(MODELE))
    c.update(nom_affiche=a.nom or a.compte, plateforme=a.plateforme.lower(), type=a.type)
    c["presentation"] = c["presentation"].replace("<nom>", c["nom_affiche"])
    c["hors_cadre"] = c["hors_cadre"].replace("<nom>", c["nom_affiche"])
    if a.type != "entreprise":
        c["rdv"]["auto_confirmer"] = False
    save(p, c)
    print(f"Cadre créé : {p}\nÀ compléter avec le propriétaire (FAQ, prix, horaires, rendez-vous), puis : cadre montrer, cadre valider.")


def cmd_cadre_montrer(a):
    c = cadre_de(a.compte)
    L = [f"Cadre des réponses automatiques — {c['nom_affiche']} ({c['plateforme']}, compte {c['type']})", "",
         f"Ton : {c['ton']}", f"Présentation : « {c['presentation']} »", "", "Questions auxquelles je réponds seul :"]
    for i, f in enumerate(c.get("faq", []), 1):
        L.append(f"  {i}. si le message parle de {', '.join(f['mots'])} → « {f['reponse']} »")
    r = c.get("rdv") or {}
    if r.get("actif"):
        L += ["", f"Rendez-vous : {r['objet']}, {r['duree_min']} min, {', '.join(r['jours'])}, {', '.join(r['plages'])} "
              f"({r['fuseau']}), au moins {r['delai_min_h']} h à l'avance, sur {r['horizon_j']} jours, {r['lieu']} ; "
              + ("je confirme seul et je l'ajoute à l'agenda" if r.get("auto_confirmer") else "je vous demande avant de confirmer")]
    L += ["", f"Je vous passe la main si le message parle de : {', '.join(c.get('escalade', []))}, ou de tout ce qui n'est pas ci-dessus.",
          f"Réponse d'attente : « {c['hors_cadre']} »", "Je ne fais jamais : " + " ; ".join(c.get("interdits", [])),
          f"Plafonds : {c['limites']['auto_par_jour']} réponses automatiques par jour, {c['limites']['auto_par_contact_par_jour']} par personne ; "
          "jamais à quelqu'un qui a dit STOP.", "", f"Empreinte : {empreinte(c)}"]
    if any("<à remplir" in json.dumps(c, ensure_ascii=False) for _ in [0]):
        L.append("ATTENTION : des champs « à remplir » restent : le cadre ne peut pas être validé ainsi.")
    print("\n".join(L))


def cmd_cadre_valider(a):
    c = cadre_de(a.compte)
    if "<à remplir" in json.dumps(c, ensure_ascii=False):
        sys.exit("Des champs « à remplir » restent dans le cadre : compléter avant de valider.")
    if c["type"] != "entreprise":
        sys.exit("Les réponses automatiques sont réservées aux comptes d'entreprise : sur un compte personnel, chaque message est validé.")
    if not a.accord.strip():
        sys.exit("Les mots exacts du propriétaire sont obligatoires")
    c["validation"] = {"date": maintenant().isoformat(timespec="seconds"), "accord": a.accord, "empreinte": empreinte(c)}
    save(P(a.compte, "cadre.json"), c)
    journal(a.compte, type="cadre_valide", accord=a.accord, empreinte=c["validation"]["empreinte"])
    print(f"Cadre validé ({c['validation']['empreinte']}). Toute modification du cadre demandera un nouvel accord.")


# ---------------------------------------------------------------- décider
def score_faq(msg, f):
    return sum(1 for m in f.get("mots", []) if norm(m) and norm(m) in msg)


def cmd_decider(a):
    c = cadre_de(a.compte)
    msg = norm(a.message)
    C = contacts(a.compte)
    k = norm(a.de)
    fiche = C.get(k) or {}
    J = lire_journal(a.compte)
    jour = maintenant().date().isoformat()
    out = {"compte": a.compte, "de": a.de, "decision": "proprietaire", "reponse": None, "raison": ""}
    if any(s in msg for s in STOP) and len(msg.split()) <= 6:
        fiche.update(nom=fiche.get("nom") or a.de, opposition=jour)
        C[k] = fiche
        save(P(a.compte, "contacts.json"), C)
        out.update(decision="stop", reponse="C'est noté, nous ne vous écrirons plus. Bonne journée.",
                   raison="la personne ne veut plus recevoir de messages (ajoutée aux oppositions)")
    elif c["type"] != "entreprise" or not cadre_valide(c):
        out["raison"] = "compte personnel ou cadre non validé (ou modifié depuis l'accord) : le propriétaire valide chaque réponse"
    elif any(norm(e) in msg for e in c.get("escalade", [])):
        out.update(reponse=c["hors_cadre"], raison="sujet à escalade : réponse d'attente seulement, le propriétaire répond")
        out["decision"] = "proprietaire_attente"
    else:
        auto_jour = sum(1 for e in J if e.get("auto") and e.get("sens") == "envoye" and e["date"][:10] == jour)
        auto_contact = sum(1 for e in J if e.get("auto") and e.get("sens") == "envoye" and e["date"][:10] == jour
                           and norm(e.get("contact")) == k)
        lim = c.get("limites", {})
        if auto_jour >= lim.get("auto_par_jour", 50) or auto_contact >= lim.get("auto_par_contact_par_jour", 5):
            out["raison"] = "plafond de réponses automatiques atteint : le propriétaire prend le relais"
        elif (c.get("rdv") or {}).get("actif") and any(norm(r) in msg for r in RDV):
            out.update(decision="rdv", raison="demande de rendez-vous : proposer les créneaux libres (messagerie.py creneaux)")
        else:
            best = max(c.get("faq", []), key=lambda f: score_faq(msg, f), default=None)
            if best and score_faq(msg, best) > 0:
                deja = any(e.get("auto") and norm(e.get("contact")) == k for e in J)
                rep = best["reponse"] if deja else f"{c['presentation']} {best['reponse']}"
                if c.get("signature"):
                    rep += f"\n{c['signature']}"
                out.update(decision="auto", reponse=rep, raison=f"réponse du cadre ({', '.join(best['mots'][:3])})")
            else:
                out.update(decision="proprietaire_attente", reponse=c["hors_cadre"],
                           raison="aucune réponse du cadre ne correspond : réponse d'attente, le propriétaire répond")
    journal(a.compte, type="decision", contact=a.de, sens="recu", texte=a.message, decision=out["decision"])
    print(json.dumps(out, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- créneaux
JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


def cmd_creneaux(a):
    c = cadre_de(a.compte)
    r = c.get("rdv") or {}
    if not r.get("actif"):
        sys.exit("Rendez-vous désactivés dans le cadre")
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(r.get("fuseau", "Europe/Berlin"))
    except Exception:
        tz = None
    occ = []
    if a.occupe:
        for o in json.load(open(a.occupe, encoding="utf-8")):
            occ.append((dt.datetime.fromisoformat(o["debut"]), dt.datetime.fromisoformat(o["fin"])))
    now = dt.datetime.now(tz) if tz else dt.datetime.now().astimezone()
    debut_min = now + dt.timedelta(hours=r.get("delai_min_h", 24))
    duree = dt.timedelta(minutes=r.get("duree_min", 30))
    res = []
    for j in range(a.jours or r.get("horizon_j", 7) + 1):
        jour = (now + dt.timedelta(days=j)).date()
        if JOURS[jour.weekday()] not in r.get("jours", []):
            continue
        for pl in r.get("plages", []):
            h1, h2 = pl.split("-")
            t = dt.datetime.combine(jour, dt.time.fromisoformat(h1), tzinfo=now.tzinfo)
            fin = dt.datetime.combine(jour, dt.time.fromisoformat(h2), tzinfo=now.tzinfo)
            while t + duree <= fin:
                if t >= debut_min and not any(t < o2 and t + duree > o1 for o1, o2 in occ):
                    res.append(t)
                    break  # un créneau par plage : des choix variés
                t += duree
        if len(res) >= a.n:
            break
    print(json.dumps([{"debut": t.isoformat(timespec="minutes"), "fin": (t + duree).isoformat(timespec="minutes"),
                       "texte": f"{JOURS[t.weekday()].lower()}. {t.day:02d}/{t.month:02d} à {t.hour} h {t.minute:02d}"}
                      for t in res[:a.n]], ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- contacts, journal, à faire, rapport
def cmd_noter(a):
    journal(a.compte, type="message", contact=a.contact, sens=a.sens, texte=a.texte, auto=bool(a.auto), decision=a.decision)
    if a.sens == "envoye":
        C = contacts(a.compte)
        f = C.setdefault(norm(a.contact), {"nom": a.contact})
        f["dernier_envoi"] = maintenant().date().isoformat()
        save(P(a.compte, "contacts.json"), C)
    print("noté")


def cmd_contact(a):
    C = contacts(a.compte)
    f = C.setdefault(norm(a.nom), {"nom": a.nom})
    for k in ("canal", "motif", "source", "consentement", "note"):
        v = getattr(a, k)
        if v:
            f[k] = v
    if a.relancer_dans_j is not None:
        f["relancer_le"] = (maintenant().date() + dt.timedelta(days=a.relancer_dans_j)).isoformat()
    f.setdefault("ajoute", maintenant().date().isoformat())
    save(P(a.compte, "contacts.json"), C)
    print(json.dumps(f, ensure_ascii=False))


def cmd_a_faire(a):
    c = cadre_de(a.compte)
    C = contacts(a.compte)
    jour = maintenant().date().isoformat()
    rel, part, refus = [], [], []
    for k, f in C.items():
        if f.get("opposition"):
            continue
        if f.get("motif") == "partenaire" and not f.get("dernier_envoi"):
            canal = (f.get("canal") or c["plateforme"]).lower()
            if canal in PERMIS_PREMIER_MESSAGE or f.get("consentement"):
                part.append(f)
            else:
                refus.append(f"{f['nom']} : premier message sur {canal} sans consentement de la personne → passer par un canal public "
                             "(LinkedIn, e-mail, Instagram) ou obtenir son accord")
        elif f.get("relancer_le") and f["relancer_le"] <= jour:
            n = f.get("relances", 0)
            if n < (c.get("relance") or {}).get("max", 2):
                rel.append(f)
    lim = (c.get("limites") or {}).get("premiers_messages_par_jour", 10)
    print(f"Relances dues : {len(rel)}")
    for f in rel:
        print(f"  - {f['nom']} ({f.get('canal', c['plateforme'])}) : {f.get('note', '')} — relance n° {f.get('relances', 0) + 1}")
    print(f"Partenaires à contacter (au plus {lim} aujourd'hui) : {len(part)}")
    for f in part[:lim]:
        print(f"  - {f['nom']} ({f.get('canal', '?')}) : {f.get('note', '')} — source {f.get('source', '?')}")
    for r in refus:
        print("  ✗ " + r)
    print("Chaque message ci-dessus est un BROUILLON : le propriétaire valide le texte exact (liste numérotée acceptée) "
          "avant tout envoi, puis messagerie.py noter --sens envoye.")


def cmd_rapport(a):
    jour = a.date or maintenant().date().isoformat()
    J = [e for e in lire_journal(a.compte) if e["date"][:10] == jour]
    C = contacts(a.compte)
    recus = [e for e in J if e.get("sens") == "recu"]
    auto = [e for e in J if e.get("sens") == "envoye" and e.get("auto")]
    manu = [e for e in J if e.get("sens") == "envoye" and not e.get("auto")]
    attente = [e for e in J if e.get("type") == "decision" and e.get("decision", "").startswith("proprietaire")]
    repondus = {norm(e.get("contact")) for e in manu}
    attente = [e for e in attente if norm(e.get("contact")) not in repondus]
    rdv = [e for e in J if e.get("type") == "rdv"]
    stop = [f for f in C.values() if f.get("opposition") == jour]
    dues = [f for f in C.values() if f.get("relancer_le") and f["relancer_le"] <= jour and not f.get("opposition")]
    L = [f"# Messagerie — {a.compte} — {jour}", "",
         f"- Personnes qui ont écrit : **{len({norm(e.get('contact')) for e in recus})}** ({len(recus)} messages)",
         f"- Réponses automatiques (dans le cadre) : **{len(auto)}** · réponses validées par vous : **{len(manu)}**",
         f"- Rendez-vous pris : **{len(rdv)}**", f"- En attente de votre réponse : **{len(attente)}**",
         f"- Relances dues : **{len(dues)}** · oppositions (STOP) : {len(stop)}", ""]
    if attente:
        L += ["## À vous de répondre", ""] + [f"- {e.get('contact')} : « {e.get('texte', '')[:140]} »" for e in attente] + [""]
    if rdv:
        L += ["## Rendez-vous", ""] + [f"- {e.get('contact')} : {e.get('texte')}" for e in rdv] + [""]
    if auto:
        L += ["## Réponses automatiques", ""] + [f"- {e.get('contact')} : « {e.get('texte', '')[:100]} »" for e in auto] + [""]
    if dues:
        L += ["## Relances à valider", ""] + [f"- {f['nom']} ({f.get('canal', '?')}) : {f.get('note', '')}" for f in dues] + [""]
    out = "\n".join(L)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)


def cmd_rdv(a):
    journal(a.compte, type="rdv", contact=a.contact, texte=a.texte, agenda=a.lien)
    C = contacts(a.compte)
    f = C.setdefault(norm(a.contact), {"nom": a.contact})
    f.setdefault("rdv", []).append({"texte": a.texte, "lien": a.lien})
    save(P(a.compte, "contacts.json"), C)
    print("rendez-vous noté")


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
cd = sp.add_parser("cadre"); cs = cd.add_subparsers(dest="sous", required=True)
ci = cs.add_parser("init"); ci.add_argument("--compte", required=True); ci.add_argument("--plateforme", required=True)
ci.add_argument("--type", choices=["entreprise", "perso"], default="entreprise"); ci.add_argument("--nom"); ci.add_argument("--forcer", action="store_true")
cm = cs.add_parser("montrer"); cm.add_argument("--compte", required=True)
cv = cs.add_parser("valider"); cv.add_argument("--compte", required=True); cv.add_argument("--accord", required=True)
d = sp.add_parser("decider"); d.add_argument("--compte", required=True); d.add_argument("--de", required=True); d.add_argument("--message", required=True)
cr = sp.add_parser("creneaux"); cr.add_argument("--compte", required=True); cr.add_argument("--occupe"); cr.add_argument("--jours", type=int)
cr.add_argument("--n", type=int, default=3)
n = sp.add_parser("noter"); n.add_argument("--compte", required=True); n.add_argument("--contact", required=True)
n.add_argument("--sens", choices=["recu", "envoye"], required=True); n.add_argument("--texte", required=True)
n.add_argument("--auto", action="store_true"); n.add_argument("--decision")
ct = sp.add_parser("contact"); ct.add_argument("--compte", required=True); ct.add_argument("--nom", required=True)
for k in ("canal", "motif", "source", "consentement", "note"):
    ct.add_argument("--" + k)
ct.add_argument("--relancer-dans-j", type=int)
af = sp.add_parser("a-faire"); af.add_argument("--compte", required=True)
rp = sp.add_parser("rapport"); rp.add_argument("--compte", required=True); rp.add_argument("--date"); rp.add_argument("--out")
rv = sp.add_parser("rdv"); rv.add_argument("--compte", required=True); rv.add_argument("--contact", required=True)
rv.add_argument("--texte", required=True); rv.add_argument("--lien")
a = ap.parse_args()
if a.cmd == "cadre":
    {"init": cmd_cadre_init, "montrer": cmd_cadre_montrer, "valider": cmd_cadre_valider}[a.sous](a)
else:
    {"decider": cmd_decider, "creneaux": cmd_creneaux, "noter": cmd_noter, "contact": cmd_contact, "a-faire": cmd_a_faire,
     "rapport": cmd_rapport, "rdv": cmd_rdv}[a.cmd](a)
