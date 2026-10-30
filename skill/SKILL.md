---
name: "analyse-reseaux-sociaux"
description: "Analyse complète d'UN réseau social par demande, pour n'importe quelle personne et n'importe quel réseau (TikTok, Instagram, YouTube, Facebook, LinkedIn, X, Threads, Pinterest, Twitch, Reddit, RedNote…) : contenus, stats internes, horaires, profil, cohérence, publicités, publications validées, historique et suivi, PDF."
---

# Analyse réseaux sociaux — v4.0

Analyse les comptes et contenus d'un réseau social, lit les statistiques internes des comptes de l'utilisateur, dit **quand publier**, **comment rendre le profil attractif**, vérifie la **cohérence entre ses réseaux**, analyse et prépare les **publicités**, **publie et commente** avec son accord, propose les **prochains contenus**, et livre un PDF. Chaque analyse est mémorisée dans l'espace de données de l'utilisateur et se compare aux précédentes.

Trois choses séparées :
- **La boîte à outils** (scripts, fiches réseaux, tests), publique et identique pour tout le monde : https://github.com/Williamszika/analyse-reseaux-sociaux (adresse dans `reference/projet.json > depot_outils`). Ce skill dit quoi faire ; la boîte à outils contient comment.
- **L'espace de données** de chaque utilisateur (`profil.json`, `comptes.json`, `historique/`, `actions/`, `journal.jsonl`, `coherence/`), à lui seul, de préférence dans un dépôt GitHub **privé** à lui. Jamais de données personnelles dans la boîte à outils.
- **Les rapports d'usage anonymes** que l'utilisateur accepte d'envoyer à l'auteur du skill (étape 5). Rien d'autre ne quitte son espace.

Rédaction : la langue et la forme d'adresse de `profil.json` (`langue`, `appel`, `tutoiement` ; par défaut : langue de la conversation, vouvoiement), phrases simples, chiffres toujours sourcés. Les intitulés fixes des PDF sont en français ; le contenu suit la langue de l'utilisateur.

## Règle n°1 : un seul réseau par demande

Si la demande mélange plusieurs réseaux, faire un réseau à la fois (demander l'ordre si l'utilisateur est là, sinon commencer par celui qui a un connecteur). Exceptions : modes H (calendrier) et K (cohérence), qui rassemblent des analyses déjà faites.

Modes :
- **A** un contenu précis · **B** recherche + analyse (« les 5 vidéos de motivation les plus vues ») · **C** recherche par période
- **D** analyse d'un compte (inclut horaires, profil, prochains contenus ; statistiques internes si c'est un compte de l'utilisateur)
- **E** s'abonner / se désabonner d'un compte nommé
- **F** horaires seuls · **G** profil seul
- **H** calendrier multi-réseaux · **I** suivi (« où j'en suis depuis la dernière fois ? »)
- **J** statistiques internes seules (« mes stats Instagram »)
- **K** cohérence de l'identité entre les réseaux de l'utilisateur
- **M** publicités : analyser celles des concurrents, préparer une campagne, booster ou lancer avec accord
- **N** publier, commenter, répondre, programmer sur un compte de l'utilisateur (ou d'un client consentant), avec accord
- **Historique** : « qu'est-ce qu'on a fait ? », « mon évolution depuis 6 mois » → `historique.py` (étape 0.6)

Défauts : 5 contenus, 30 jours, statistiques sur 28 jours, rapport « perso » (« client » = page de garde avec `rapport.marque_client`, pour un audit fait pour quelqu'un d'autre).

N'importe quel réseau fonctionne : s'il n'est pas dans `reference/reseaux.md`, suivre sa section « Réseau non répertorié » (connecteur cherché dans le registre, données publiques, limites vérifiées puis enregistrées dans `profil.json > reseaux`). Les scripts acceptent tout nom de réseau.

**Hors du périmètre** : rechercher une personne privée sur les réseaux, retrouver ses comptes à partir de son nom ou de sa photo, ou constituer un dossier sur elle. Le dire en une phrase et proposer ce que le skill fait.

## Étape 0 : démarrer

**1. Récupérer la boîte à outils (espace cloud)**
- `git clone --depth 1 https://github.com/Williamszika/analyse-reseaux-sociaux /home/claude/analyse-reseaux-sociaux` (s'il existe : `git -C … pull`). Si le clone est refusé : `add_repo(owner="Williamszika", repo="analyse-reseaux-sociaux", access="read")` puis suivre ses consignes.
- `R=/home/claude/analyse-reseaux-sociaux` ; `export ANALYSES_DIR=<scratchpad>/analyses` ; `bash $R/scripts/install.sh --leger`.
- Boîte à outils inaccessible : le dire en une ligne, faire l'analyse quand même et produire le PDF avec le skill pdf (sans suivi automatique).

**2. Trouver l'espace de données de l'utilisateur** (dans cet ordre, sans poser de question si une source répond) :
1. les instructions du projet ou du dépôt ouvert (CLAUDE.md…) et la mémoire de Claude, qui peuvent indiquer le dépôt et le dossier ;
2. `python3 $R/scripts/donnees.py trouver` : cherche tout `profil.json` déjà cloné (`*/analyse/donnees`, `*/donnees`…) et donne le nombre d'analyses de chacun ;
3. les dépôts GitHub de l'utilisateur (`list_repos`) : un dépôt nommé comme un espace de données (`mes-analyses`, `*reseau*`, `*bots*`…) se clone et se vérifie avec `donnees.py trouver --racine <clone>` ;
4. seulement si rien n'est trouvé, c'est un **premier usage** : voir ci-dessous. Ne jamais recréer un espace quand un existe déjà : les analyses d'avant seraient perdues pour le suivi.

Dépôt GitHub de l'utilisateur : `add_repo(owner, repo, access="push")`, cloner, puis `export ANALYSES_DONNEES=<clone>/<dossier>`. Dossier sur son ordinateur relié : y travailler par le pont de l'ordinateur ou en copier les fichiers. Ensuite : `python3 $R/scripts/donnees.py verifier`, lire `profil.json` (forme d'adresse, fuseau, **règles**, connecteurs, plafond publicitaire, `equipe`) et `comptes.json` (si le compte y est, reprendre ses réglages sans reposer de question ; sinon l'ajouter avec `donnees.py compte`).

**3. Lire** la fiche du réseau dans `$R/reference/reseaux.md`, `$R/reference/connecteurs.md`, et pour les modes M et N ou une connexion : `$R/reference/actions.md`.

**4. L'ordinateur, seulement pour les tâches lourdes** (télécharger une vidéo, transcrire avec Whisper, mesures image/son, `collect.py`/`fetch.py`/`yt_search.py`, qui ont besoin d'Internet ; l'espace cloud n'atteint pas les réseaux sociaux). Si l'ordinateur de l'utilisateur est relié (`mcp__remote-devices__device_bash`) :
- copier `$R/scripts/*` vers `/mnt/user-data/outputs/analyse-scripts/`, puis `device_commit_files` vers `~/Analyses/scripts/` ;
- `cd ~/Analyses && bash scripts/install.sh` la première fois, puis `. .venv/bin/activate && python scripts/<script>.py …` ;
- rapatrier les petits fichiers produits (`posts.json`, `meta.json`, `transcript.json`, `measures.json`, planches) avec `device_stage_files`.
Sans ordinateur : faire sans ces étapes et le noter dans `limites`. Pour YouTube, `vidiq_video_transcript` peut fournir la transcription.

**5. Journal** : `python3 $R/scripts/usage.py debut --mode <lettre> --reseau <réseau> [--compte <clé>] [--client "<nom>"]`. Chaque étape bloquée ou contournée : `usage.py etape "<ce qui a bloqué>"`. Le journal reste privé dans l'espace de données.

**6. Se souvenir** : `python3 $R/scripts/historique.py bilan`, puis pour le compte analysé `historique.py evolution --compte <clé>` et `historique.py recos --compte <clé>`. S'appuyer dessus dans toute l'analyse : ce qui a progressé, les recommandations passées appliquées ou non. Demande d'historique seule : `liste`, `evolution --png`, `chercher "<mot>"`, puis répondre en quelques lignes.

**7. Reprise** : s'il existe `rapports/*/etat.json` avec `en_attente`, proposer de reprendre là où l'analyse s'est arrêtée.

### Premier usage (aucun espace de données trouvé)

1. **Préremplir** avec ce qui est déjà connu (conversation, mémoire de Claude, fuseau et langue de la session, pseudos cités) et ne demander que ce qui manque.
2. Poser **une seule fois** (AskUserQuestion, 4 questions au plus, réponse recommandée en premier) :
   1. comment s'adresser à la personne (prénom ; tutoiement ou vouvoiement) et dans quelle langue ;
   2. le compte à analyser en premier (réseau + pseudo) et ses autres comptes ;
   3. où garder la mémoire : **un dépôt GitHub privé** (recommandé) · **un dossier de son ordinateur** (s'il est relié) · **pas de mémoire** ;
   4. des règles à respecter (compte où ne rien publier, liens interdits…) et un plafond de dépense publicitaire (défaut : 0, aucune dépense).
3. **Sans réponse** (« pas de préférence », question ignorée, tâche programmée) : appliquer les défauts sans redemander et l'écrire en une ligne en tête de la réponse : langue de la conversation, vouvoiement, fuseau déduit de la session (sinon UTC), compte cité ou connu (sinon demander seulement celui-là), mémoire temporaire, plafond publicitaire 0.
4. `python3 $R/scripts/donnees.py init --nom … --appel … [--tutoiement] --langue … --fuseau … --memoire github:<propriétaire>/<dépôt>:donnees|dossier:<chemin>|aucune [--plafond-pub-jour … --plafond-pub-total …]`, puis un `donnees.py compte --reseau … --handle …` par compte, les règles dans `profil.json > regles`.
5. **Dépôt GitHub de données** : si l'outil de création de dépôt est disponible, proposer de créer `<pseudo-github>/mes-analyses` en **privé** et le faire sur un oui ; sinon donner les étapes exactes (https://github.com/new → nom `mes-analyses` → **Private** → **Create repository**). L'attacher avec `add_repo(access="push")`, y copier l'espace temporaire, committer. Ne jamais bloquer : travailler dans `$ANALYSES_DIR/donnees` en attendant, et rappeler en fin de réponse que la mémoire est temporaire tant que le dépôt n'existe pas.

## Étape 1 : accéder aux données — connecteurs d'abord, jamais bloquant

Ordre pour un compte de l'utilisateur (`proprietaire: true`) ou d'un client consentant :

1. **Connecteurs** (statistiques officielles, aucune connexion à faire) :
   - **Metricool** : marque et comptes reliés dans `profil.json > connecteurs > metricool` (sinon `getBrandSettings`, puis les enregistrer). Champs et règles dans `connecteurs.md` (une requête par connecteur ; agréger les lignes par jour ; `getBestTimeToPostByNetwork` sur la semaine à venir = activité de l'audience par heure).
   - **Supermetrics**, **vidIQ** : si une source n'est pas autorisée, donner le lien de connexion qu'ils renvoient et continuer sans attendre.
   - Un connecteur utile absent : `SearchMcpRegistry` puis `SuggestConnectors`, et continuer.
2. **Données publiques** (navigateur : celui que l'utilisateur préfère, sinon l'autre) selon la fiche du réseau. Suffisant pour posts, horaires de publication, vues, likes, commentaires, profil.
3. **Connexion guidée** (tableaux internes, actions) — `actions.md` §1 : ouvrir la page de connexion du réseau de façon visible, dire en une phrase « Connectez-vous dans cet onglet ; je continue avec les données publiques en attendant », poursuivre, vérifier ensuite que le compte connecté est le bon (pseudo = `handle`), puis relever les tableaux internes (`actions.md` §2). Proposer une fois de relier le compte à un connecteur pour ne plus avoir à se connecter.

Sécurité, sans exception : Claude ne tape jamais d'identifiant, de mot de passe, de code ou de réponse de sécurité (même écrits dans la conversation : ne pas les répéter, demander de les taper dans la page) ; ne résout pas de captcha ; ne crée pas de compte ; n'accepte pas de conditions à la place de la personne ; refuse les cookies non essentiels ; ne touche ni au pseudo, ni au mot de passe, ni à l'e-mail, ni aux réglages de sécurité ; ne saisit jamais de carte bancaire ni de moyen de paiement. Messages privés et revenus : seulement si l'utilisateur le demande, en résumé. Exports et téléchargements : demander l'accord (nom, source, taille). Jamais de mot de passe, jeton ou cookie dans un fichier (`donnees.py verifier` le contrôle).

Comptes qui ne sont ni à l'utilisateur ni à un client consentant : seulement des comptes publics de créateurs, marques, entreprises ou personnalités publiques, en lecture seule ; un particulier privé → le dire et s'arrêter.

Informations internes à relever (28 jours) → `stats_internes.json` (format dans `formats.md`, **mêmes libellés de KPI d'une fois sur l'autre**) : abonnés gagnés/perdus, vues, portée, interactions, visites du profil, clics sur le lien, temps moyen et visionnage complet, sources de trafic, pays, âge, genre, **activité de l'audience par jour et heure**, top 5 contenus, commentaires sans réponse, contenus boostés et leurs résultats.

## Étape 2 : collecter

- Posts d'un compte → `rapports/AAAA-MM-JJ_<reseau>_<sujet>/posts.json` (12 à 30 posts, **heure exacte** obligatoire pour les horaires). Méthode : fiche réseau (connecteur, JSON de la page, ou `collect.py` sur l'ordinateur). Aller doucement, pas de défilement massif.
- **Rétention par vidéo** (son compte, à chaque analyse) : dans les statistiques internes de chaque vidéo récente (TikTok : `https://www.tiktok.com/tiktokstudio/analytics/<id de la vidéo>`, lecture seule), relever le temps de visionnage moyen, la part qui a tout regardé, le moment où la plupart arrêtent, la part « Pour toi » et les abonnés gagnés → champs `moy_s`, `complet_pct`, `decrochage_s`, `pour_toi_pct`, `abonnes_gagnes` de `posts.json`. Relier les valeurs par l'**identifiant complet** de la vidéo, jamais par ses derniers chiffres. Puis `python $R/scripts/performance.py retention rapports/<dossier>` (section Rétention du rapport).
- Profil → noter `profil_actuel` (photo décrite, nom, pseudo, bio **telle quelle**, lien, langue, catégorie) : indispensable au mode K.
- Recherche (modes B, C) : YouTube `yt_search.py` (ordinateur) ; ailleurs : recherche dans le navigateur ; vidIQ `vidiq_outliers` / `vidiq_instagram_tiktok_outlier_search` pour la niche.
- Une vidéo à fond (modes A, B) : `fetch.py <url> [--video] [--cookies]` puis `transcribe.py cache/<dossier>` (sous-titres d'abord, Whisper sinon, reprise automatique ; > 1 h : en arrière-plan avec `nohup`, annoncer le temps) puis `measure.py cache/<dossier>` (plans/minute, étalonnage, LUFS, silences, moments les plus revus, planches à regarder avec Read). Transcription > 90 min : un sous-agent par tranche de 30 min. Sans ordinateur : 3 à 6 captures dans le navigateur (`video.currentTime`), recadrées.
- Publicités (mode M) : bibliothèques publicitaires publiques (`actions.md` §4a) ; 5 à 10 annonces de la niche ou des concurrents nommés.

## Étape 3 : analyser

**Contenus** : résumé par blocs horodatés, message, structure, ton, appels à l'action, débit, ce que dit le public (commentaires), moments les plus revus reliés à ce qui se passe. Toujours citer la mesure (« luminance 72, sous-exposée »). Repères : luminance < 80 sombre, > 180 surexposée ; contraste < 40 plat ; LUFS idéal ≈ -14 ; vidéos courtes verticales : plans < 2 s.

Grille fixe 0–10 (vidéo), toujours ces 8 clés : `accroche` (9 = promesse + tension en < 5 s) · `discours` (progression claire, exemples forts) · `presence` (énergie, regard caméra) · `cadrage` · `lumiere_etalonnage` (look cohérent) · `montage_rythme` (rythme maîtrisé, B-roll utile) · `son` (voix pleine, niveaux équilibrés) · `appel_action` (naturel). 3 = faible, 6 = correct, 9 = excellent. Post texte/photo : accroche, clarté, valeur, visuel, appel à l'action. Live (Twitch, Kick…) : régularité, durée, heure de début, interaction avec le chat.

**Compte** : engagement (base de la fiche réseau, le script le calcule), formats, top/flop, fréquence, thèmes, légendes/hashtags ; croiser avec les statistiques internes **et l'historique** (étape 0.6). Comparer à 3–5 comptes de la niche et exprimer l'écart en actions.

**Horaires** (modes D et F) :
1. Où est le public : `fuseaux_public` du compte ou démographie interne. Signaler les changements d'heure (Europe : fin mars / fin octobre ; beaucoup de pays n'en ont pas).
2. Données par fiabilité : activité réelle de l'audience (connecteur, statistiques internes) > historique du compte (`timing.py posts.json --tz <fuseau public> --tz <fuseau de l'utilisateur> --out <dossier>` : indice de vues par créneau, fiabilité faible < 15 posts) > niche > repères généraux (présentés comme hypothèse).
3. Conclure : 2–3 créneaux avec l'heure du public **et** celle de l'utilisateur, la raison, une fréquence réaliste, la règle de la première heure (répondre aux commentaires), un plan de test de 2 semaines. Dans `analysis.json` : `jours` (Lun…Dim) et `heure` (HH:MM, fuseau de l'utilisateur) pour le calendrier.

**Profil** (modes D et G) : noter sur 10 photo, nom affiché, pseudo, bio, lien(s), contenus mis en avant, visuel d'ensemble, organisation (playlists, stories à la une, tableaux…), cohérence, type de compte. Si le profil n'a pas changé depuis la dernière analyse archivée, reprendre sa note globale (`profil.note`) pour que le suivi reste comparable. Livrer 2–3 noms affichés, **3 bios prêtes à copier** (claire, percutante, business) sous la limite du réseau (`reseaux.json`, ou vérifiée à la main) avec 5 caractères de marge, contenus à épingler/archiver, autres réglages. Changer de pseudo casse les liens : le déconseiller sauf vrai problème. Appliquer un changement de profil seulement sur demande, un champ à la fois, texte exact montré avant (`actions.py --type profil`) ; jamais de changement de pseudo, mot de passe, e-mail ou sécurité.

**Publicités** (mode M) : pour chaque annonce, depuis quand elle tourne (longtemps = rentable), format, accroche des 3 premières secondes, offre, appel à l'action, plateformes ; ce qu'il faut copier et ce qu'il faut éviter. Proposer une campagne (`publicites.campagne_proposee`, ou `campagne.json` seule) : objectif, contenu (de préférence le meilleur post organique), cible, budget, durée, texte, appel à l'action, seuil de réussite et seuil d'arrêt.

**Ce qui fait monter les vues** : poser des étiquettes sur chaque vidéo nouvelle (`performance.py etiquettes poser --id <id> --theme … --accroche … --format … --serie …`) puis `etiquettes analyser rapports/<dossier>` : médianes par thème, accroche, format. Une différence n'est fiable qu'à partir de 4 vidéos par groupe : le dire.

**Tests A/B** : une idée à vérifier (ouverture, durée, heure…) devient un test (`performance.py test creer --nom … --hypothese … --a … --b … --critere moy_s|vues|eng|complet_pct|ratio --min 3`) ; chaque vidéo publiée est rangée dans sa variante (`test ajouter`) ; `test verdict rapports/<dossier>` ne conclut qu'avec assez de vidéos et plus de 10 % d'écart. Citer le test en cours dans le retour d'équipe pour que les vidéos suivantes le respectent.

**Vidéos livrées** (si `equipe` existe) : `performance.py livrables rapports/<dossier> --livrables <clone>/livrables` relie chaque vidéo livrée à sa publication (par l'accroche de sa légende), garde un relevé à J+1, J+7 et J+30 et le compare à la médiane du compte. Si les vidéos bien notées par le skill vidéo restent sous la médiane, le dire dans le retour : sa note qualité doit être recalibrée.

**Prochains contenus** (toujours en mode D) : 3 sujets tirés de ce qui marche (meilleurs posts, commentaires, niche) avec accroche, format, durée et la donnée qui les justifie (`prochains_contenus`), plus les reprises d'un réseau à l'autre (`reprises`). En fin de réponse, proposer une fois de passer un sujet en script ou en vidéo avec les skills de `profil.json > contenus > skills` s'ils sont disponibles ; sinon proposer d'écrire le script directement.

## Étape 4 : agir sur le compte (modes N et M) — toujours avec accord

Toute action passe par `python3 $R/scripts/actions.py` (détails dans `actions.md` §3–5) :
1. `preparer --type publication|commentaire|reponse|message|profil|programmation|boost|campagne --compte <clé> --texte … [--media …] [--quand …] [--budget … --duree-jours … --cible … --objectif …]`
2. `montrer <id>` : montrer ce texte **mot pour mot** à l'utilisateur (texte, média, heure, budget, cible, ses règles).
3. Son « oui » → `valider <id> --accord "<sa phrase exacte>"`. Sans oui explicite : ne rien faire.
4. Faire l'action dans le navigateur (compte connecté vérifié), puis `fait <id> --lien <url>`. Le script refuse si le contenu a changé depuis l'accord.

Règles :
- Une action = un accord. Une liste numérotée validée explicitement (« publie les 3 ») = une fiche par élément.
- **Chaque vidéo récupérée** (par exemple dans `livrables/`) est contrôlée en entier avant d'être proposée : `python $R/scripts/controle_video.py <video> --srt <sous-titres de la production> --out <dossier> --vers <clone>/analyse/controles/<date>_<titre>` (format, durée, volume, titre seul avant la voix, débit, arrêts entre les phrases, bruitages sous la voix, silences, contre `profil.json > equipe > cahier_video`), puis **regarder** `ouverture.png` et `planche.png` (titre, design des mots, coupures de phrases, texte illisible dans les images, cohérence du personnage), écrire ces observations et relancer avec `--regard`. Montrer le tableau à l'utilisateur. Point non respecté : proposer de demander une nouvelle version (fichier `demandes/AAAA-MM-JJ_<objet>.md` dans le dépôt des vidéos, avec les mesures et les cibles) plutôt que publier.
- Avant de publier une vidéo venue d'un autre dépôt, vérifier aussi qu'elle n'est pas déjà en ligne sur le compte (même légende ou même durée) : republier une vidéo identique réduit sa portée.
- Retour de l'utilisateur sur une vidéo (« titre d'abord », « voix trop rapide »…) : le traduire en cibles mesurables dans `cahier_video`, l'écrire dans la demande et, si le skill vidéo a un journal (`profil.json > equipe > journal_video`), dans la section « Retour de l'utilisateur » de sa fiche.
- Dépenses : `actions.py` refuse au-delà du plafond de `profil.json > publicite` (0 par défaut). Pour dépasser, l'utilisateur relève son plafond ou donne un accord qui cite le montant (`--hors-plafond`). Seulement sur un compte publicitaire déjà configuré par lui ; jamais de saisie de paiement.
- Jamais : commentaires, likes, abonnements ou messages en série ou en boucle (spam, blocage du compte), faux avis, publicité trompeuse ou discriminatoire, contournement d'un refus de la plateforme. Respecter `profil.json > regles`.
- Client : seulement si `comptes.json` note son consentement (`donnees.py compte … --client "<nom>" --consentement "<date, moyen, périmètre>"`) ; `actions.py` refuse sinon.
- Mode E (abonnement) : un compte nommé à la fois, nom confirmé avant de cliquer, jamais en masse.
- Programmer via un connecteur (Metricool `createScheduledPost`) : même circuit, l'appel n'est fait qu'après `valider`.

## Étape 5 : rapport, contrôle, mémoire, fin

1. Écrire `analysis.json` dans le dossier du rapport (schéma : `formats.md` ; `compte_cle` = la clé de `comptes.json` ; `publicites` en mode M).
2. `python $R/scripts/report.py rapports/<dossier> [--style client]` : intègre `stats_internes.json`, `timing.json` + `horaires.png`, Prochains contenus, Publicités, et la section **Suivi** (évolution depuis la dernière analyse archivée + recommandations d'alors à vérifier). En mode I, commenter ce suivi dans le résumé exécutif, avec `historique.py evolution --png` si utile.
3. `python $R/scripts/verifier_pdf.py rapports/<dossier>/rapport.pdf --apercus` : code 2 = page presque vide → corriger (raccourcir, déplacer une section) et régénérer. Regarder 2–3 aperçus avec Read.
4. Si une mémoire existe : `python $R/scripts/archiver.py rapports/<dossier> --pdf` (met aussi à jour `historique/index.json`) ; mettre à jour `comptes.json` si un réglage a changé.
5. Mémoire dans un dépôt GitHub : `git pull --rebase`, `git add <dossier de données>`, commit « Analyse <réseau> <compte> du <date> » (avec les lignes d'attribution de la session), `git push`. En cas d'échec : le dire, le rapport reste livré.
6. `usage.py fin --statut ok|partiel|echec`, puis committer le journal avec le reste.
7. **Rapport d'usage anonyme** selon `profil.json > usage > rapport_anonyme` : `demander` (défaut) → proposer **une fois** en une phrase ; sur un oui, `usage.py rapport`, montrer le bloc JSON tel quel, puis soit créer le ticket dans le dépôt de la boîte à outils avec un outil GitHub disponible, soit donner le lien prérempli (rien n'est envoyé sans clic). Dire que le ticket sera public et lié à son compte GitHub. `jamais` → ne pas proposer. Ne jamais ajouter au rapport d'autres informations que celles produites par `usage.py`. Enregistrer la réponse dans `profil.json > usage` s'il dit « toujours » ou « jamais ».
8. **Équipe** (si `profil.json > equipe` existe) : remplir `equipe` dans `analysis.json` (ce qui marche, consignes vidéo, consignes d'écriture **sans statistiques**, résultats de chaque vidéo de `livrables/` déjà publiée, aussi écrits dans la section « Après publication » de sa fiche si `equipe.journal_video` existe), puis `python $R/scripts/brief.py rapports/<dossier> --vers <clone de equipe.videos.depot>/<equipe.videos.dossier>`, commit « Retour d'analyse <réseau> <compte> du <date> » et push sur `equipe.videos.branche`. Le dépôt des vidéos lit `dernier.md` avant chaque vidéo et transmet `dernier_scripts.md` (et lui seul) au dépôt des scripts. Ne jamais écrire soi-même de chiffres du compte dans un dépôt marqué `public`.
9. **Tableau de bord** (si `profil.json > tableau_de_bord` donne l'adresse d'un artefact Dashboard) : `python $R/scripts/performance.py tableau rapports/<dossier> --out <scratchpad>/tableau --historique <clé du compte>`, téléverser chaque fichier dans l'artefact (Artifact `asset: true`), puis mettre à jour le `url`, le `name` et `updated` des jeux de données `videos`, `historique`, `livrables`, `tests` (ArtifactData, en lisant chaque document avant). Ne pas réécrire la page.
10. Envoyer le PDF (SendUserFile), supprimer `etat.json`, conclure en 2–3 phrases : le constat, les 3 leviers, la prochaine étape.

Le rapport ne contient jamais : transcription intégrale, messages privés, noms d'abonnés.

## Mode K : cohérence entre réseaux

1. Vérifier que chaque compte à comparer a une analyse archivée avec `profil_actuel` ; sinon faire d'abord le mode G pour ce réseau.
2. Écrire `coherence.json` (identité proposée : nom, pseudo cible, photo, promesse, langue ; une bio par réseau ; actions dans l'ordre).
3. `python $R/scripts/coherence.py --out rapports/<date>_coherence --proposition coherence.json [--comptes cle1,cle2]` : tableau côte à côte, écarts détectés automatiquement (noms, pseudos, langues, liens manquants, bios trop longues).
4. Vérifier le PDF, copier `coherence.json` et `coherence.pdf` dans `coherence/<date>/` de l'espace de données, committer, envoyer.

Un compte de marque garde son identité propre : ne le comparer à un compte personnel que si l'utilisateur le demande ou si ses `regles` le prévoient.

## Mode H : calendrier

`python $R/scripts/calendrier.py --out rapports/<date>_calendrier` (fuseau de `profil.json`, sinon `--tz`) : lit le dernier `resume.json` de chaque compte → `calendrier.pdf` + `calendrier.ics` (rappel hebdomadaire 15 min avant chaque créneau), conflits signalés (< 30 min d'écart, > 3 publications par jour). Comptes sans créneaux : proposer le mode F. Ajouter dans un agenda relié seulement sur demande, après avoir montré la liste exacte des événements.

## Suivi mensuel automatique

Sur demande, créer une tâche programmée (le 1er du mois, heure choisie avec l'utilisateur) qui relance le mode I pour ses comptes reliés à un connecteur. Sa consigne nomme : la boîte à outils, le dépôt et le dossier de ses données, les comptes, et rappelle : ne poser aucune question, ne pas ouvrir de page de connexion, ne rien publier ni dépenser, archiver, pousser, envoyer les PDF avec un résumé de 5 lignes par compte, pousser le retour d'équipe si `equipe` existe, ne pas envoyer de rapport d'usage sauf `rapport_anonyme: toujours`. Noter la tâche dans `profil.json > suivi_mensuel`.

## Relevé du soir (vidéos récentes)

Sur demande, une tâche programmée locale (elle a besoin du navigateur connecté) relève chaque soir les vidéos des 7 derniers jours : vues, réactions et rétention dans les statistiques internes, en lecture seule ; met à jour `posts.json` du dernier dossier d'historique ; lance `performance.py livrables`, `test verdict`, `retention` et `tableau` ; écrit les résultats dans « Après publication » de la fiche de chaque vidéo livrée si `equipe.journal_video` existe ; rafraîchit le tableau de bord ; pousse. Elle ne publie, ne commente et ne dépense rien. La noter dans `profil.json > releve_soir`.

## Pour l'auteur du skill (propriétaire du dépôt de la boîte à outils)

Tableau de bord de l'usage : `gh issue list -R <depot_outils> --label usage --state all --limit 1000 --json body,createdAt > tickets.json` (ou un outil GitHub équivalent), puis `python3 $R/scripts/usage.py tableau tickets.json --out tableau.md` : modes, réseaux, versions, durées, étapes qui bloquent le plus. S'en servir pour prioriser les corrections.

## Si quelque chose bloque

- Espace de données inaccessible : le dire ; travailler sans mémoire et noter que le suivi n'a pas pu être fait.
- Connecteur vide : vérifier la période (90 jours) et le compte relié ; une requête vide = aucune publication, pas une panne.
- yt-dlp échoue (ordinateur) : `pip install -U yt-dlp`, `--cookies`, sinon navigateur.
- Page de connexion sur un compte qui n'est pas à l'utilisateur : la fermer et rester sur les données publiques.
- Mauvais compte connecté dans le navigateur : ne rien relever ni faire, le dire.
- Captcha, blocage, vérification : ne jamais contourner ; prévenir.
- Script en erreur : le contourner pour livrer, le dire, `usage.py etape "<script> : <erreur>"` ; si l'utilisateur maintient la boîte à outils (droit d'écriture), corriger, lancer `tests/selftest.py`, committer « Correctif <script> ».

## Tests (après chaque modification du skill ou des scripts)

`python3 $R/tests/selftest.py` (149 vérifications, utilisateur fictif, sans Internet). Puis, à la main : (1) un nouvel utilisateur sans espace de données → 4 questions au plus, défauts appliqués s'il ne répond pas ; (2) « mes stats Instagram » avec un connecteur → sans connexion, section Suivi ; (3) un réseau non répertorié (ex. Lemon8) → méthode générale ; (4) « mes réseaux sont-ils cohérents ? » → coherence.pdf ; (5) « fais mon planning » → .ics au fuseau du profil ; (6) l'utilisateur écrit un mot de passe → non utilisé, non répété ; (7) « publie cette vidéo » → texte montré, rien sans oui ; (8) « booste à 50 € » avec plafond 0 → refus expliqué ; (9) « mon évolution depuis le début » → historique.py ; (10) fin d'analyse → rapport anonyme proposé une fois, sans pseudo ; (11) avec `equipe` → retour poussé dans le dépôt des vidéos, retour scripts sans statistiques ; (12) vidéo récupérée → controle_video.py, planches regardées, tableau montré avant toute publication ; (13) « analyse mon TikTok » alors qu'un espace existe déjà dans un dépôt de l'utilisateur → `donnees.py trouver` / `list_repos` le retrouvent, aucune question de premier usage ; (14) rétention relevée → `performance.py retention`, section Rétention du rapport.
