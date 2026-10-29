# Analyse réseaux sociaux — boîte à outils (v3.0)

Boîte à outils du skill Claude **analyse-reseaux-sociaux** : analyser un compte ou des contenus sur n'importe quel réseau
social (TikTok, Instagram, YouTube, Facebook, LinkedIn, X, Threads, Pinterest, Twitch, Reddit, Telegram, RedNote…
et tout réseau non répertorié), dire quand publier, rendre le profil attractif, vérifier la cohérence entre réseaux,
proposer les prochains contenus, suivre l'évolution d'un mois sur l'autre, et livrer un PDF.

Ce dépôt ne contient **que des outils**. Il ne contient aucun compte, aucune statistique, aucun rapport, aucun secret.
Les données de chaque personne vivent dans **son propre espace de données**, hors de ce dépôt.

| Dossier | Contenu |
|---|---|
| `scripts/` | `donnees` (espace de données), `collect`, `fetch`, `transcribe`, `measure`, `timing`, `report`, `archiver`, `calendrier`, `coherence`, `verifier_pdf`, `yt_search`, `install.sh` |
| `reference/` | `reseaux.md` (fiche par réseau + méthode pour un réseau non répertorié), `reseaux.json` (limites et alias lus par les scripts), `connecteurs.md` (Metricool, Supermetrics, vidIQ), `formats.md` |
| `modeles/` | `profil.exemple.json`, `comptes.exemple.json` |
| `tests/selftest.py` | Test complet sur un utilisateur fictif, sans Internet |

## Démarrer

```bash
git clone https://github.com/Williamszika/analyse-reseaux-sociaux
cd analyse-reseaux-sociaux
bash scripts/install.sh --leger        # ou sans --leger sur un ordinateur (vidéos, Whisper)
export ANALYSES_DIR=~/Analyses                     # dossier de travail
export ANALYSES_DONNEES=~/mes-analyses/donnees     # votre espace de données (idéalement un dépôt GitHub privé)
python3 scripts/donnees.py init --nom "Votre nom" --fuseau Europe/Paris
python3 scripts/donnees.py compte --reseau Instagram --handle @moncompte
python3 tests/selftest.py               # doit finir par « 0 échec(s) »
```

`ANALYSES_DATE` (AAAA-MM-JJ) force la date d'un rapport.

## Contribuer
Un réseau manque ou une limite a changé : modifier `reference/reseaux.json` (et la fiche dans `reseaux.md`),
lancer `tests/selftest.py`, proposer la modification. Licence MIT.
