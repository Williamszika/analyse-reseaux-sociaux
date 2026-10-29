"""Test automatique de la boîte à outils, sur des données fictives, sans Internet.

python3 tests/selftest.py            (depuis la racine de la boîte à outils)

Vérifie : espace de données (init, comptes, contrôle des secrets), réseaux connus/alias/inconnus, compilation de tous les scripts, timing, report (avec section Suivi), archivage,
calendrier + .ics, cohérence, transcription depuis sous-titres, mesures vidéo (si ffmpeg), PDF sans page vide.
Ne touche jamais à un vrai espace de données : tout se passe dans un dossier temporaire.
"""
import json, os, py_compile, shutil, subprocess, sys, tempfile, time

ICI = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(ICI), "scripts")
TMP = tempfile.mkdtemp(prefix="selftest_analyse_")
BASE, DON = os.path.join(TMP, "base"), os.path.join(TMP, "donnees")
os.makedirs(BASE), os.makedirs(DON)
ENV = {**os.environ, "ANALYSES_DIR": BASE, "ANALYSES_DONNEES": DON, "MPLBACKEND": "Agg"}
ok, ko = [], []


def run(nom, args, date=None, attendu=0):
    env = dict(ENV)
    if date:
        env["ANALYSES_DATE"] = date
    r = subprocess.run([sys.executable] + args, cwd=SCRIPTS, env=env, capture_output=True, text=True)
    good = r.returncode == attendu
    (ok if good else ko).append(nom)
    if not good:
        print(f"\n--- ÉCHEC {nom} (code {r.returncode}) ---\n{r.stdout[-1500:]}\n{r.stderr[-2500:]}")
    return r


def check(nom, cond, detail=""):
    (ok if cond else ko).append(nom)
    if not cond:
        print(f"--- ÉCHEC {nom} {detail}")


def w(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False) if not isinstance(data, str) else f.write(data)


# 1. Compilation
for f in sorted(os.listdir(SCRIPTS)):
    if f.endswith(".py"):
        try:
            py_compile.compile(os.path.join(SCRIPTS, f), doraise=True)
            ok.append("compile " + f)
        except py_compile.PyCompileError as e:
            ko.append("compile " + f)
            print(e)

# 2. Données fictives
t0 = 1790000000
posts = [{"id": str(i), "ts": t0 + i * 86400 * 1.7 + (i % 5) * 3600 * 3, "type": "vidéo" if i % 3 else "court",
          "duree": 30 + i * 7, "vues": 200 + (i * 37) % 300, "likes": 10 + i % 9, "commentaires": i % 4,
          "partages": i % 2, "lien": f"https://exemple.test/{i}", "sujet": f"Sujet {i}"} for i in range(20)]
dos1 = os.path.join(BASE, "rapports", "2026-09-01_tiktok_test")
w(os.path.join(dos1, "posts.json"), posts)
heures = {"fuseau": "Europe/Berlin", **{j: [max(0, 10 - abs(h - 18)) for h in range(24)] for j in
                                         ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]}}


def analyse(reseau, cle, abonnes, note, eng_bonus, nom, pseudo, bio, langue):
    return {
        "titre": f"{pseudo} — test", "reseau": reseau, "compte_cle": cle, "style": "perso",
        "parametres": "Test automatique", "resume_executif": "Résumé de test. " * 8,
        "compte": {"nom": pseudo, "abonnes": abonnes, "nb_posts": 20, "frequence": "3/semaine",
                   "analyse": "Analyse de test.",
                   "posts": [{"date": "2026-08-%02d" % (i + 1), "type": p["type"], "likes": p["likes"] + eng_bonus,
                              "commentaires": p["commentaires"], "partages": p["partages"], "vues": p["vues"],
                              "sujet": p["sujet"]} for i, p in enumerate(posts)]},
        "horaires": {"analyse": "Test.", "creneaux_recommandes": [
            {"creneau": "Mar 18 h 30", "jours": ["Mar", "Jeu"], "heure": "18:30", "pourquoi": "test"},
            {"creneau": "Sam 10 h 30", "jours": ["Sam"], "heure": "10:30", "pourquoi": "test"}],
            "frequence": "3/semaine", "plan_test": ["Semaine 1", "Semaine 2"]},
        "profil": {"elements": [{"element": "Bio", "etat": "x", "note": note, "reco": "y"},
                                {"element": "Lien", "etat": "x", "note": None, "reco": "y"}],
                   "nom_affiche": ["Nom 1"], "bios": [{"version": "Claire", "texte": "Bio courte de test"},
                                                       {"version": "Trop longue", "texte": "x" * 400}],
                   "epingles": ["a"], "autres": ["b"]},
        "profil_actuel": {"nom": nom, "pseudo": pseudo, "bio": bio, "lien": "", "langue": langue, "photo": "sombre"},
        "prochains_contenus": [{"titre": "Idée 1", "angle": "a", "format": "Reel", "duree": "60 s", "pourquoi": "p"}],
        "reprises": ["Republier X en Reel"],
        "recommandations": ["Faire A", "Faire B"], "limites": ["Test"]}


w(os.path.join(dos1, "analysis.json"), analyse("TikTok", "tiktok_test", 800, 3, 0, "Mr Test", "@test_tk", "bio tk", "fr"))
w(os.path.join(dos1, "stats_internes.json"), {"source": "test", "periode": "28 j", "kpis": {"Vues": 1000, "Abonnés gagnés": 5},
                                               "audience_heures": heures, "analyse": "test"})
# Espace de données d'un utilisateur fictif, créé avec donnees.py
run("donnees init", ["donnees.py", "init", "--nom", "Awa Test", "--tutoiement", "--fuseau", "Europe/Paris",
                     "--marque-client", "Agence Test · Audit"])
run("donnees fuseau invalide refusé", ["donnees.py", "init", "--fuseau", "Lune/Base"], attendu=1)
run("donnees compte tiktok", ["donnees.py", "compte", "--reseau", "tik tok", "--handle", "test_tk",
                              "--fuseaux-public", "Africa/Abidjan,Europe/Paris"])
run("donnees compte instagram", ["donnees.py", "compte", "--reseau", "Insta", "--handle", "@test_ig"])
cpt = json.load(open(os.path.join(DON, "comptes.json")))
check("clés de comptes normalisées", set(cpt) == {"tiktok_test_tk", "instagram_test_ig"}, str(list(cpt)))
# les analyses de test utilisent ces clés
cpt["tiktok_test"] = cpt.pop("tiktok_test_tk"); cpt["instagram_test"] = cpt.pop("instagram_test_ig")
w(os.path.join(DON, "comptes.json"), cpt)
run("donnees verifier", ["donnees.py", "verifier"])

# 3. Horaires + rapport 1 + archivage
run("timing", ["timing.py", os.path.join(dos1, "posts.json"), "--tz", "Africa/Abidjan", "--tz", "Europe/Berlin", "--out", dos1])
r = run("report 1", ["report.py", dos1], date="2026-09-01")
check("bio trop longue signalée", "ATTENTION" in r.stdout)
run("archiver 1", ["archiver.py", dos1], date="2026-09-01")

# 4. Rapport 2 (un mois plus tard) -> section Suivi
dos2 = os.path.join(BASE, "rapports", "2026-10-01_tiktok_test")
shutil.copytree(dos1, dos2)
for f in ["resume.json", "rapport.pdf", "rapport.html"]:
    if os.path.exists(os.path.join(dos2, f)):
        os.remove(os.path.join(dos2, f))
w(os.path.join(dos2, "analysis.json"), analyse("TikTok", "tiktok_test", 950, 6, 5, "Mr Test", "@test_tk", "bio tk", "fr"))
w(os.path.join(dos2, "stats_internes.json"), {"source": "test", "kpis": {"Vues": 1500, "Abonnés gagnés": 12}})
run("report 2", ["report.py", dos2], date="2026-10-01")
html = open(os.path.join(dos2, "rapport.html"), encoding="utf-8").read() if os.path.exists(os.path.join(dos2, "rapport.html")) else ""
check("section Suivi", "Suivi depuis le 2026-09-01" in html)
check("abonnés +150 dans le suivi", "+150" in html)
check("section Prochains contenus", "Prochains contenus" in html)
check("indicateur interne suivi", "(interne)" in html)
run("archiver 2", ["archiver.py", dos2, "--pdf"], date="2026-10-01")
check("historique 2 dates", len(os.listdir(os.path.join(DON, "historique", "tiktok_test"))) == 2)

# 5. Deuxième compte (Instagram)
dos3 = os.path.join(BASE, "rapports", "2026-10-01_instagram_test")
w(os.path.join(dos3, "analysis.json"), analyse("Instagram", "instagram_test", 180, 4, 0, "Mr_le_Test", "@test_ig",
                                               "Welcome to my kingdom", "en"))
run("report instagram", ["report.py", dos3], date="2026-10-01")
run("archiver instagram", ["archiver.py", dos3], date="2026-10-01")

# 6. Calendrier
cal = os.path.join(BASE, "rapports", "cal")
r = run("calendrier", ["calendrier.py", "--out", cal], date="2026-10-01")
check("fuseau du profil utilisé", "Europe/Paris" in open(os.path.join(cal, "calendrier.ics"), encoding="utf-8").read()
      if os.path.exists(os.path.join(cal, "calendrier.ics")) else False)
ics = open(os.path.join(cal, "calendrier.ics"), encoding="utf-8").read() if os.path.exists(os.path.join(cal, "calendrier.ics")) else ""
check("ics 6 événements", ics.count("BEGIN:VEVENT") == 6, f"({ics.count('BEGIN:VEVENT')})")
check("conflit détecté", "ALERTE" in r.stdout)

# 7. Cohérence
w(os.path.join(BASE, "coherence.json"), {"resume": "test", "identite": {"nom": "Mr Test"},
                                         "bios": {"TikTok": "Bio TikTok", "Instagram": "Bio Instagram"},
                                         "actions": ["Changer le nom"]})
r = run("coherence", ["coherence.py", "--out", os.path.join(BASE, "rapports", "coh"), "--proposition", "coherence.json"],
        date="2026-10-01")
check("écarts nom/langue détectés", "Nom affiché différent" in r.stdout and "Langue différente" in r.stdout)

# 7b. Réseaux : alias et réseau non répertorié
sys.path.insert(0, SCRIPTS)
os.environ["ANALYSES_DONNEES"] = DON
import importlib, common
importlib.reload(common)
check("alias twitter -> X (160)", common.reseau("Twitter")["cle"] == "x" and common.reseau("twitter")["bio_max"] == 160)
check("alias xiaohongshu -> rednote", common.reseau("Xiaohongshu")["cle"] == "rednote")
check("réseau inconnu générique", common.reseau("Lemon8")["connu"] is False)
dos4 = os.path.join(BASE, "rapports", "2026-10-01_lemon8_test")
w(os.path.join(dos4, "analysis.json"), analyse("Lemon8", "lemon8_test", 50, 5, 0, "Awa", "@awa_l8", "bio", "fr"))
r = run("report réseau non répertorié", ["report.py", dos4], date="2026-10-01")
check("note réseau non répertorié", "non répertorié" in r.stdout)
dos5 = os.path.join(BASE, "rapports", "2026-10-01_x_test")
w(os.path.join(dos5, "analysis.json"), analyse("Twitter", "x_test", 50, 5, 0, "Awa", "@awa", "bio", "fr"))
r = run("report alias twitter", ["report.py", dos5, "--style", "client"], date="2026-10-01")
h5 = open(os.path.join(dos5, "rapport.html"), encoding="utf-8").read() if os.path.exists(os.path.join(dos5, "rapport.html")) else ""
check("limite X appliquée (160)", "/ 160" in h5)
check("marque client du profil", "Agence Test · Audit" in h5 and "KIGROUP" not in h5)
# Surcharge d'une limite dans profil.json
pr = json.load(open(os.path.join(DON, "profil.json"))); pr["reseaux"] = {"lemon8": {"bio_max": 90}}
w(os.path.join(DON, "profil.json"), pr)
check("surcharge de limite par l'utilisateur", common.reseau("Lemon8")["bio_max"] == 90)
# Un secret glissé dans un fichier est détecté
w(os.path.join(DON, "piege.json"), {"password": "x"})
run("secret détecté", ["donnees.py", "verifier"], attendu=1)
os.remove(os.path.join(DON, "piege.json"))

# 8. Transcription depuis sous-titres
cache = os.path.join(BASE, "cache", "test_video")
w(os.path.join(cache, "meta.json"), {"duration": 60, "language": "fr", "webpage_url": "https://exemple.test"})
vtt = "WEBVTT\n\n" + "\n\n".join(f"00:00:{i*5:02d}.000 --> 00:00:{i*5+5:02d}.000\nPhrase numéro {i} du test" for i in range(8))
w(os.path.join(cache, "subs.fr.vtt"), vtt)
run("transcribe (sous-titres)", ["transcribe.py", "cache/test_video"])
tr = json.load(open(os.path.join(cache, "transcript.json"))) if os.path.exists(os.path.join(cache, "transcript.json")) else {}
check("transcription 8 segments", len(tr.get("segments", [])) == 8)

# 9. Mesures vidéo (si ffmpeg disponible)
try:
    from common import ffmpeg
    FF = ffmpeg()
    subprocess.run([FF, "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=duration=8:size=320x568:rate=25",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=8", "-shortest", "-pix_fmt", "yuv420p",
                    os.path.join(cache, "video.mp4")], check=True)
    run("measure", ["measure.py", "cache/test_video"])
    check("measures.json", os.path.exists(os.path.join(cache, "measures.json")))
except Exception as e:
    print("measure ignoré (ffmpeg indisponible) :", e)

# 10. PDF sans page vide
for nom, pdf in [("pdf rapport 2", os.path.join(dos2, "rapport.pdf")), ("pdf instagram", os.path.join(dos3, "rapport.pdf")),
                 ("pdf calendrier", os.path.join(cal, "calendrier.pdf")),
                 ("pdf cohérence", os.path.join(BASE, "rapports", "coh", "coherence.pdf"))]:
    if os.path.exists(pdf):
        run(nom + " sans page vide", ["verifier_pdf.py", pdf])
    else:
        check(nom + " existe", False)

print(f"\n{len(ok)} vérifications réussies, {len(ko)} échec(s)" + (f" : {ko}" if ko else ""))
print("Dossier de test :", TMP)
sys.exit(1 if ko else 0)
