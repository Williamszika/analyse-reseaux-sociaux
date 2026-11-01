# Formats des fichiers

Dossier d'une analyse : `rapports/AAAA-MM-JJ_<reseau>_<sujet>/` dans le dossier de travail.
Espace de données de l'utilisateur (`$ANALYSES_DONNEES`, voir README) : `profil.json`, `comptes.json`,
`historique/<compte_cle>/<date>/` (+ `historique/index.json`), `coherence/<date>/`, `actions/<id>.json`, `journal.jsonl`,
`LISEZMOI.md`. Créer et contrôler avec `scripts/donnees.py`.

## profil.json (réglages de l'utilisateur)
```json
{"version": "4.0",
 "utilisateur": {"nom": "Awa Koné", "appel": "Awa", "tutoiement": false, "langue": "fr", "fuseau": "Europe/Paris"},
 "rapport": {"marque_client": "Mon agence · Audit réseaux sociaux", "marque_perso": "Analyse réseaux sociaux"},
 "memoire": {"type": "github", "depot": "awa/mes-analyses", "dossier": "donnees"},
 "connecteurs": {"metricool": {"brandId": 123456, "fuseau": "Europe/Paris", "comptes": ["instagram_awa"]}},
 "regles": ["Compte Instagram personnel : ne rien y publier sans demande explicite"],
 "reseaux": {"lemon8": {"bio_max": 80}},
 "contenus": {"skills": ["nom-d-un-skill-de-script-ou-de-video"]},
 "publicite": {"plafond_jour": 10, "plafond_total": 100, "devise": "EUR"},
 "usage": {"rapport_anonyme": "demander"}}
```
- `appel` : comment s'adresser à la personne ; `tutoiement` : false = vouvoiement.
- `memoire.type` : `github` (dépôt privé de l'utilisateur), `dossier` (dossier relié de son ordinateur) ou `aucune`.
- `regles` : consignes propres à la personne, à respecter dans chaque analyse (lues au démarrage).
- `publicite` : plafonds de dépense fixés par la personne ; 0 (défaut) = aucune dépense possible (`actions.py` refuse).
- `usage.rapport_anonyme` : `demander` (défaut, proposer une fois en fin d'analyse), `jamais`, ou `toujours` (envoyer sans redemander,
  seulement si la personne l'a dit).
- `reseaux` : limites vérifiées à la main pour un réseau non répertorié ou une règle qui a changé.

## comptes.json (mémoire)
```json
{"tiktok_awa": {"reseau": "TikTok", "handle": "@awa", "url": "https://www.tiktok.com/@awa",
  "proprietaire": true, "public": "francophone, 18-34 ans", "fuseaux_public": ["Africa/Abidjan", "Europe/Paris"],
  "fuseau_utilisateur": "Europe/Paris", "langue": "fr", "objectif": "...",
  "acces": {"metricool": null, "public": "navigateur", "interne": "TikTok Studio (connexion manuelle)"},
  "derniere_analyse": "2026-10-25"},
 "instagram_cafe-awa": {"reseau": "Instagram", "handle": "@cafe_awa", "proprietaire": false,
  "client": "Café Awa", "consentement": "2026-10-30, par e-mail : audit + publications validées par le client"}}
```
`client` + `consentement` : compte d'un client ; sans consentement noté, `donnees.py verifier` le signale et `actions.py` refuse toute action.
Jamais de mot de passe, code, jeton ou cookie dans ce fichier ni ailleurs dans le dépôt.

## posts.json
Liste de `{"id", "ts" (unix ou ISO), "type", "duree", "vues", "likes", "commentaires", "partages", "enregistrements", "lien", "sujet"}` (`null` si inconnu).

## stats_internes.json
```json
{"source": "Metricool", "date": "2026-10-25", "periode": "28 derniers jours",
 "kpis": {"Abonnés": 179, "Vues": 10, "Comptes atteints": 2},
 "sources_trafic": {"Pour toi": "61 %"},
 "demographie": {"Pays": "...", "Âge": "...", "Genre": "..."},
 "audience_heures": {"fuseau": "Europe/Paris", "Lun": [24 valeurs], "...": "...", "Dim": [24 valeurs]},
 "top_contenus": [{"titre": "...", "vues": 302, "retention": "..."}],
 "commentaires_sans_reponse": 6, "analyse": "..."}
```
Les KPI numériques entrent dans le suivi d'un rapport à l'autre : garder les **mêmes libellés** d'une fois sur l'autre.

## analysis.json
```json
{
  "titre": "...", "reseau": "TikTok", "compte_cle": "tiktok_awa", "style": "perso",
  "parametres": "Mode D · ...", "resume_executif": "5 à 8 lignes",
  "contenus": [{"cache": "cache/youtube_abc", "meta": {}, "resume_blocs": [{"debut": "00:00:00", "fin": "00:10:00", "points": ["..."]}],
    "discours": "...", "commentaires": "...", "retention": "...",
    "notes": {"accroche": 7, "discours": 8, "presence": 6, "cadrage": 7, "lumiere_etalonnage": 5, "montage_rythme": 6, "son": 8, "appel_action": 4},
    "observations": {"Cadrage": "..."}, "corrections": ["..."]}],
  "compte": {"nom": "@...", "lien": "...", "abonnes": 830, "nb_posts": 48, "frequence": "...", "analyse": "...",
    "posts": [{"date": "2026-10-20", "type": "reel", "likes": 16, "commentaires": 0, "partages": 1, "vues": 303, "lien": "...", "sujet": "..."}]},
  "horaires": {"analyse": "...", "creneaux_recommandes": [{"creneau": "Mar · Jeu — 18 h 30 Paris = 17 h 30 Abidjan", "jours": ["Mar", "Jeu"], "heure": "18:30", "pourquoi": "..."}],
    "frequence": "...", "plan_test": ["..."]},
  "profil": {"elements": [{"element": "Bio", "etat": "...", "note": 4, "reco": "..."}], "nom_affiche": ["..."],
    "bios": [{"version": "Claire", "texte": "..."}, {"version": "Percutante", "texte": "..."}, {"version": "Business", "texte": "..."}],
    "epingles": ["..."], "autres": ["..."]},
  "profil_actuel": {"photo": "description courte", "nom": "Awa", "pseudo": "@awa", "bio": "texte exact", "lien": "", "langue": "fr", "categorie": "créateur"},
  "prochains_contenus": [{"titre": "...", "angle": "accroche en une phrase", "format": "Reel / TikTok / carrousel", "duree": "60 s", "pourquoi": "donnée qui l'appuie"}],
  "reprises": ["Republier l'épisode X en Reel de 60 s"],
  "benchmark": "...", "recommandations": ["..."], "limites": ["..."]
}
```
- `heure` des créneaux : **fuseau de l'utilisateur** (`profil.json`), c'est ce que lit le calendrier.
- `profil_actuel` : obligatoire pour le mode K (cohérence) ; recopier les textes tels qu'ils sont sur le profil.
- Note de profil inconnue : `null`.

## coherence.json (proposition écrite par Claude, mode K)
```json
{"resume": "...", "identite": {"nom": "Awa", "pseudo_cible": "@awa (si libre)", "photo": "...", "promesse": "...", "langue": "fr"},
 "bios": {"TikTok": "...", "Instagram": "...", "Facebook": "..."}, "actions": ["..."]}
```

## publicites (dans analysis.json, mode M)
```json
"publicites": {"analyse": "Ce que font les concurrents et ce qu'il faut en retenir",
  "annonces": [{"annonceur": "...", "depuis": "2026-09-12", "format": "vidéo 9:16, 20 s", "accroche": "...", "offre": "-20 %",
                "cta": "Envoyer un message", "plateformes": "Instagram, Facebook", "lien": "lien de la bibliothèque"}],
  "campagne_proposee": {"objectif": "messages", "contenu": "vidéo du 12/10 (meilleure portée organique)", "cible": "Abidjan, 20-40 ans",
                        "budget": "30 € sur 6 jours", "duree": "6 jours", "texte": "...", "cta": "...",
                        "reussite": "coût par message < 0,50 €", "arret": "pas de message après 10 €"}}
```
Le rapport ajoute la section « Publicités ». Rien n'est lancé : le lancement passe par `actions.py` (type `boost` ou `campagne`).

## actions/<id>.json (écrit par actions.py)
`{"id", "type" (publication|commentaire|reponse|message|profil|programmation|boost|campagne), "compte", "reseau", "handle", "client",
"texte", "media", "quand", "budget", "duree_jours", "budget_jour", "devise", "cible", "objectif", "statut" (en_attente|validee|faite|annulee),
"cree", "accord" (phrase exacte de l'utilisateur), "valide", "empreinte", "empreinte_validee", "fait", "lien", "note"}`

## journal.jsonl (écrit par usage.py, une ligne par session, privé)
`{"id", "debut", "fin", "duree_min", "mode", "mode_nom", "reseau", "compte", "client", "version", "etapes": ["étape bloquée…"], "statut", "note"}`
Le rapport d'usage anonyme n'en garde que : jour, durée arrondie, mode, réseau, version, statut, catégories de blocage, audit client oui/non.

## historique/index.json (écrit par historique.py)
`{"genere", "nb", "analyses": [{"compte", "date", "reseau", "titre", "abonnes", "vues_mediane", "eng_moy", "note_profil", "internes",
"creneaux", "recommandations", "prochains_contenus", "resume_executif", "bio", "pdf", "dossier"}]}` — reconstruit seul s'il manque une analyse.

## Travail en équipe (profil.json > equipe, analysis.json > equipe, brief.py)
Quand d'autres dépôts fabriquent les contenus, `profil.json` les nomme :
```json
"equipe": {"videos": {"depot": "moi/mes-videos", "branche": "main", "dossier": "analyse/retours",
                      "role": "fabrique les vidéos ; lit analyse/retours/dernier.md avant chaque vidéo"},
           "scripts": {"depot": "moi/mes-scripts", "public": true, "dossier": "retours-video", "transmis_par": "videos",
                       "contenu": "seulement *_scripts.md"}}
```
Dans `analysis.json`, le bloc `equipe` (optionnel) : `a_garder`, `consignes_video` (chiffres permis), `consignes_script`
(consignes d'écriture : durées et nombre de mots permis, **aucune statistique du compte ni donnée d'audience**),
`livrables` (`fichier`, `publie_le`, `lien`, `vues`, `eng`, `verdict`) pour relier chaque vidéo livrée à ses résultats.
`brief.py rapports/<dossier> --vers <clone>/analyse/retours` écrit `AAAA-MM-JJ_<compte>.md` (complet, dépôt privé),
`AAAA-MM-JJ_<compte>_scripts.md` (sans statistiques, transmissible à un dépôt public), `.json`, `dernier.md`, `dernier_scripts.md`.

## Cahier des charges vidéo (profil.json > equipe > cahier_video, controle_video.py)
```json
"cahier_video": {"duree_max_s": 180, "format": "1080x1920", "lufs_cible": -14, "lufs_tolerance": 1.5,
  "titre_avant_voix_s": 1.5, "debit_max_mots_s": 2.5, "pause_phrase_min_s": 0.5, "part_phrases_avec_pause": 0.7,
  "pic_bruitage_max_db": 4.0, "bruit_dans_arrets_max_db": -6.0, "silence_seuil_db": -35}
```
`controle_video.py <video> --srt <sous-titres> --out <dossier> --vers <clone>/analyse/controles/<date>_<titre> --regard <observations.txt>`
écrit `controle.json`, `controle.md` (✅ respecté, ❌ non respecté, 👁 à regarder), `ouverture.png` (0 à 4 s), `planche.png` (12 images).
Code de sortie 3 s'il reste un point non respecté.

## Performance (performance.py)
- `posts.json` : champs de rétention facultatifs par vidéo : `moy_s` (temps de visionnage moyen, s), `complet_pct` (% qui ont tout regardé), `decrochage_s` (seconde où la plupart arrêtent), `pour_toi_pct`, `abonnes_gagnes`.
- `rapports/<dossier>/retention.json` : `n`, `moy_s_mediane`, `complet_mediane`, `ratio_mediane`, `duree_mediane`, `decrochage_avant_3s`, `decrochage_mesure`, `correlation_vues_moy_s`, `meilleures`, `constat`. `report.py` en fait la section « Rétention ».
- `etiquettes.json` (espace de données) : `{ "<id vidéo>": {"theme": …, "accroche": …, "format": …, "serie": …, "<autre>": …} }`. `etiquettes analyser` écrit `etiquettes_analyse.json` dans le dossier du rapport.
- `livrables_suivi.json` : `{ "<nom du livrable>": {titre, note_qualite, duree_s, video_id, publie_le, statut, lien, releves: {"J+1"|"J+7"|"J+30"|"dernier": {date, age_j, vues, eng, moy_s, complet_pct, commentaires, vs_mediane_compte}}} }`.
- `tests.json` : `{ "<nom>": {hypothese, variantes: {A, B}, critere, min, videos: {A: [ids], B: [ids]}, cree, statut, dernier_verdict} }`.
- `performance.py tableau` écrit `videos.json`, `historique.json`, `livrables.json`, `tests.json` (listes de lignes) pour un tableau de bord.
- `profil.json > tableau_de_bord` : adresse de l'artefact ; `profil.json > releve_soir` : identifiant et heure de la tâche du soir.

## Chaîne (chaine.py)
`chaine/<id>.json` : `id`, `titre`, `script`, `plan`, `statut`, `historique` [{date, statut, note}], `accords` {video, publication : {date, texte mot pour mot}}, `revues` [{date, texte}], `controles` [{date, texte}], champs libres (`livrable`, `lien`, `demande_video`, `demande_publication`), `cree`, `maj`.

## Messagerie (messagerie.py)
`messagerie/<compte>/cadre.json` : nom_affiche, plateforme, type (entreprise|perso), langue, tutoiement, ton, presentation, signature, faq [{mots, reponse}], rdv {actif, objet, duree_min, jours, plages, delai_min_h, horizon_j, lieu, fuseau, auto_confirmer}, escalade, interdits, limites {auto_par_jour, auto_par_contact_par_jour, premiers_messages_par_jour}, relance {delai_j, max}, hors_cadre, validation {date, accord, empreinte}.
`contacts.json` : {clé normalisée : {nom, canal, motif, source, consentement, note, relancer_le, relances, dernier_envoi, opposition, rdv}}. `journal.jsonl` : une ligne par message ou décision.

## Expertise
- `accroche.json` (accroche.py video) : mouvement_0_1s, mouvement_0_3s, visage_0_1s (null si non mesurable), details_ecran_0s, son_debut_s, volume_1re_seconde_db, volume_moyen_db, alertes ; `planche_3s.png`.
- `concurrents.json` : [{reseau, handle, note, ajoute}] ; `veille/<date>.json|md` : comptes, explosions, durées, jours, tendances, idees_a_adapter.
- `plateformes.json` (espace de données, prioritaire sur reference/plateformes.json) : {regles: [{id, reseau, theme, regle, consequence, seuils?, depuis, verifie, fiabilite, source}]}.
- `seo.json` : {compte: [{mot, source, ajoute}]} ; `stats_internes.json > sources_trafic` : {« Pour toi »: %, « Recherche »: %, …}.
- `commentaires_analyse.json` : n, emotions, pays, questions, histoires (extraits anonymes), demandes, mots, idees.
- `predictions.json` : [{n, compte, reco, type, metrique, base, cible, cree, echeance, statut, resultat?, n_videos?}].
