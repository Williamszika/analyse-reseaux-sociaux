"""Outils communs v3.0 — boîte à outils générique, pour n'importe quel utilisateur et n'importe quel réseau.

BASE    = dossier de travail (cache, rapports, .venv) : $ANALYSES_DIR ou ~/Analyses.
DONNEES = espace de données de l'utilisateur (profil.json, comptes.json, historique/, coherence/) :
          $ANALYSES_DONNEES ou ~/Analyses/donnees. Jamais dans la boîte à outils.
"""
import datetime as dt, glob, json, os, shutil

VERSION = "3.0"
BASE = os.environ.get("ANALYSES_DIR", os.path.expanduser("~/Analyses"))
DONNEES = os.environ.get("ANALYSES_DONNEES", os.path.join(BASE, "donnees"))
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTO = os.path.join(DONNEES, "historique")
JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


def ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def hms(s):
    s = int(s or 0)
    return f"{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}"


def isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def chemin(p):
    """Chemin relatif -> relatif à BASE."""
    return p if os.path.isabs(p) else os.path.join(BASE, p)


def comptes():
    return load(os.path.join(DONNEES, "comptes.json"), {}) or {}


def profil():
    """Réglages de l'utilisateur (profil.json de son espace de données), {} si absent."""
    return load(os.path.join(DONNEES, "profil.json"), {}) or {}


def fuseau_utilisateur(defaut="UTC"):
    return (profil().get("utilisateur") or {}).get("fuseau") or defaut


def marque(style):
    """Bandeau des rapports : « Analyse réseaux sociaux », ou la marque de l'utilisateur pour un audit client."""
    r = profil().get("rapport") or {}
    if style == "client":
        return r.get("marque_client") or "Audit réseaux sociaux"
    return r.get("marque_perso") or "Analyse réseaux sociaux"


def _norm(x):
    return "".join(ch for ch in str(x or "").lower() if ch.isalnum())


def reseau(nom):
    """Fiche d'un réseau (reference/reseaux.json + surcharges profil.json > reseaux).
    Réseau inconnu : fiche générique avec connu=False (limites None = pas de contrôle automatique)."""
    table = load(os.path.join(RACINE, "reference", "reseaux.json"), {}) or {}
    perso = profil().get("reseaux") or {}
    n = _norm(nom)
    trouve = None
    for cle, f in table.items():
        if cle.startswith("_"):
            continue
        if n and n in {_norm(cle), _norm(f.get("nom"))} | {_norm(a) for a in f.get("alias", [])}:
            trouve = cle
            break
    if trouve:
        fiche = {**table[trouve], "cle": trouve, "connu": True}
    else:
        fiche = {**table.get("_inconnu", {}), "nom": str(nom or "?"), "cle": n or "inconnu", "connu": False}
    for k in {fiche["cle"], n}:
        if k in perso:
            fiche.update(perso[k])
    return fiche


def historique(cle):
    """Liste triée (date, dossier) des analyses archivées d'un compte."""
    out = []
    for d in sorted(glob.glob(os.path.join(HISTO, cle, "*"))):
        if os.path.isdir(d):
            out.append((os.path.basename(d), d))
    return out


def dernier_resume(cle, avant=None):
    """Dernier resume.json archivé du compte, strictement avant la date `avant` (AAAA-MM-JJ) si donnée."""
    best = None
    for date, d in historique(cle):
        if avant and date >= avant:
            continue
        r = load(os.path.join(d, "resume.json"))
        if r:
            best = r
    return best


def aujourdhui():
    return os.environ.get("ANALYSES_DATE") or dt.date.today().isoformat()


def html_to_pdf(html_path, pdf_path):
    try:
        from weasyprint import HTML
        HTML(html_path).write_pdf(pdf_path)
    except Exception as e:
        import subprocess
        print("WeasyPrint indisponible, repli Chrome :", e)
        for chrome in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                       shutil.which("chromium") or "", shutil.which("google-chrome") or ""]:
            if chrome and os.path.exists(chrome):
                subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                                f"--print-to-pdf={pdf_path}", "file://" + os.path.abspath(html_path)], check=True)
                break
        else:
            raise SystemExit("Ni WeasyPrint ni Chrome : impossible de produire le PDF")
    return pdf_path
