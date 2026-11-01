# Analyse réseaux sociaux — skill Claude + boîte à outils (v4.0)

*English below.*

Un skill Claude pour analyser **son** compte ou n'importe quel compte public sur n'importe quel réseau social (TikTok,
Instagram, YouTube, Facebook, LinkedIn, X, Threads, Pinterest, Twitch, Reddit, Telegram, RedNote… et tout réseau non répertorié) :
- **analyser** contenus, statistiques internes, profil et cohérence entre réseaux ;
- dire **quand publier** et proposer les **prochains contenus** ;
- analyser et préparer des **publicités** ;
- **publier et commenter** avec votre accord ;
- gérer vos **messageries** (WhatsApp, Telegram, Instagram, LinkedIn…) : répondre aux clients dans un cadre que vous validez, prendre les **commandes** et les **rendez-vous**, chercher des **partenaires**, **relancer** vos contacts, et vous faire un **rapport** ;
- **garder l'historique** de chaque analyse et suivre votre évolution ;
- mesurer la **rétention** de chaque vidéo, trouver par **étiquettes** ce qui fait monter les vues, mener des **tests A/B** et suivre les vidéos livrées à J+1 / J+7 ;
- alimenter un **tableau de bord** ;
- analyser les **3 premières secondes** de vos vidéos et de celles qui marchent, suivre **concurrents et tendances**, travailler le **référencement**, comprendre vos **commentaires**, vérifier que ses **conseils marchent vraiment**, suivre votre chemin vers la **monétisation** ;
- livrer un **PDF**.

Ce dépôt est public et ne contient **que des outils** : aucun compte, aucune statistique, aucun rapport, aucun secret.
Les données de chaque personne vivent dans **son propre espace de données** (idéalement un dépôt GitHub privé à elle).

## Utiliser le skill (n'importe qui)
1. Téléchargez ce dépôt (**Code → Download ZIP**) et gardez le dossier `skill/`.
2. Dans Claude, ajoutez le skill depuis les réglages des skills, en important le dossier `skill/` compressé en .zip.
   L'emplacement exact du menu peut changer selon l'application.
3. Dans une conversation, tapez `/analyse-reseaux-sociaux` ou demandez « analyse mon TikTok @moncompte ».
4. La première fois, le skill pose au plus 4 questions (ou prend des valeurs par défaut si vous ne répondez pas) et propose de
   créer votre dépôt privé `mes-analyses` pour la mémoire.

Le skill télécharge lui-même cette boîte à outils à chaque utilisation : vous profitez des corrections sans rien réinstaller.

## Ce qui est protégé
- **Vos mots de passe** : Claude ne tape jamais de mot de passe ni de code. Vous vous connectez vous-même dans l'onglet ouvert.
- **Vos comptes** : rien n'est publié, commenté ni dépensé sans votre « oui » sur le texte exact.
  `scripts/actions.py` garde la trace de chaque action et refuse si le contenu a changé depuis votre accord.
- **Votre argent** : le plafond publicitaire est à 0 par défaut, et Claude ne saisit jamais de moyen de paiement.
- **Vos données** : elles restent dans votre espace. Si vous acceptez, l'auteur reçoit seulement un **rapport d'usage anonyme**
  (jour, durée, mode, réseau, version, étapes qui ont bloqué), dont vous voyez le texte exact avant l'envoi.
- **Les autres** : le skill ne recherche pas de particuliers et ne constitue pas de dossiers sur des personnes.

## Contenu du dépôt
| Dossier | Contenu |
|---|---|
| `skill/SKILL.md` | Le skill à installer dans Claude |
| `scripts/` | `donnees` (espace de données), `historique` (index, évolution, recherche), `usage` (journal privé, rapport anonyme, tableau de bord), `actions` (publications et publicités validées), `brief` (retour d'analyse pour les dépôts qui fabriquent les vidéos et les scripts), `controle_video` (contrôle d'une vidéo livrée contre le cahier des charges), `performance` (rétention, étiquettes, tests A/B, suivi des vidéos livrées, export pour tableau de bord), `chaine` (fiches de suivi script → vidéo → publication, avec accords obligatoires), `messagerie` (cadre de réponses validé, rendez-vous, partenaires, relances, rapport), `accroche` (3 premières secondes), `veille` (concurrents, tendances), `regles` (règles des plateformes sourcées), `seo`, `commentaires`, `predictions` (conseils vérifiés), `monetisation`, `evaluer` (examen du skill), `collect`, `fetch`, `transcribe`, `measure`, `timing`, `report`, `archiver`, `calendrier`, `coherence`, `verifier_pdf`, `yt_search`, `install.sh` |
| `reference/` | `reseaux.md` / `reseaux.json` (fiches et limites par réseau), `connecteurs.md` (Metricool, Supermetrics, vidIQ), `actions.md` (connexion, publication, publicités), `messagerie.md` (règles par plateforme, rendez-vous, partenaires), `plateformes.json` (règles et seuils datés et sourcés), `formats.md`, `projet.json` |
| `modeles/` | `profil.exemple.json`, `comptes.exemple.json` |
| `tests/evals/cas.json` | 20 cas d'examen du skill (`scripts/evaluer.py`) |
| `tests/selftest.py` | 267 vérifications sur un utilisateur fictif, sans Internet |

## En ligne de commande
```bash
git clone https://github.com/Williamszika/analyse-reseaux-sociaux && cd analyse-reseaux-sociaux
bash scripts/install.sh --leger                    # ou sans --leger sur un ordinateur (vidéos, Whisper)
export ANALYSES_DIR=~/Analyses                     # dossier de travail
export ANALYSES_DONNEES=~/mes-analyses/donnees     # votre espace de données (dépôt GitHub privé conseillé)
python3 scripts/donnees.py init --nom "Votre nom" --fuseau Europe/Paris --memoire github:moi/mes-analyses:donnees
python3 scripts/donnees.py compte --reseau Instagram --handle @moncompte
python3 scripts/historique.py bilan                # ce qui a déjà été fait
python3 tests/selftest.py                          # doit finir par « 0 échec(s) »
```

## Pour l'auteur : tableau de bord de l'usage
Les rapports anonymes arrivent comme tickets avec le label `usage`.
```bash
gh issue list -R Williamszika/analyse-reseaux-sociaux --label usage --state all --limit 1000 --json body,createdAt > tickets.json
python3 scripts/usage.py tableau tickets.json --out tableau.md
```
Vous publiez votre propre copie ? Changez `depot_outils` dans `reference/projet.json`.

## Contribuer
Un réseau manque ou une limite a changé : modifier `reference/reseaux.json` (et la fiche dans `reseaux.md`), lancer
`tests/selftest.py`, proposer la modification (ou ouvrir un ticket « Problème ou idée »). Licence MIT.

---

# Social media analysis — Claude skill + toolkit (v4.0)

A Claude skill to analyse **your own** account, or any public account, on any social network. It covers content, internal
stats, best posting times, profile, cross-network consistency, ads analysis and preparation, approved posting and commenting, messaging (customer replies within an owner-approved frame, bookings, partner outreach, follow-ups, owner reports),
analysis history with progress tracking, per-video retention, tags, A/B tests, delivered-video follow-up, a dashboard export, and a PDF report. This repo only contains tools; each person's data lives in their
own (ideally private) data space.

**Install for anyone:** download this repo, zip the `skill/` folder, add it to Claude's skills, then type
`/analyse-reseaux-sociaux`. The skill fetches this toolkit on each run.

**Safeguards:**
- Claude never types passwords or codes; you log in yourself in the tab it opens.
- Nothing is posted, commented or spent without your "yes" on the exact content (`scripts/actions.py` logs each action).
- The ad budget cap defaults to 0, and Claude never enters payment details.
- Usage reports to the author are anonymous, opt-in and shown before sending.
- The skill does not search for private individuals.

**Tests:** `python3 tests/selftest.py` (267 checks, offline). MIT licence.
