# Formats des fichiers

Dossier d'une analyse : `rapports/AAAA-MM-JJ_<reseau>_<sujet>/` dans le dossier de travail.
Espace de données de l'utilisateur (`$ANALYSES_DONNEES`, voir README) : `profil.json`, `comptes.json`,
`historique/<compte_cle>/<date>/`, `coherence/<date>/`. Créer et contrôler avec `scripts/donnees.py`.

## profil.json (réglages de l'utilisateur)
```json
{"version": "3.0",
 "utilisateur": {"nom": "Awa Koné", "appel": "Awa", "tutoiement": false, "langue": "fr", "fuseau": "Europe/Paris"},
 "rapport": {"marque_client": "Mon agence · Audit réseaux sociaux", "marque_perso": "Analyse réseaux sociaux"},
 "memoire": {"type": "github", "depot": "awa/mes-analyses", "dossier": "donnees"},
 "connecteurs": {"metricool": {"brandId": 123456, "fuseau": "Europe/Paris", "comptes": ["instagram_awa"]}},
 "regles": ["Compte Instagram personnel : ne rien y publier sans demande explicite"],
 "reseaux": {"lemon8": {"bio_max": 80}},
 "contenus": {"skills": ["nom-d-un-skill-de-script-ou-de-video"]}}
```
- `appel` : comment s'adresser à la personne ; `tutoiement` : false = vouvoiement.
- `memoire.type` : `github` (dépôt privé de l'utilisateur), `dossier` (dossier relié de son ordinateur) ou `aucune`.
- `regles` : consignes propres à la personne, à respecter dans chaque analyse (lues au démarrage).
- `reseaux` : limites vérifiées à la main pour un réseau non répertorié ou une règle qui a changé.

## comptes.json (mémoire)
```json
{"tiktok_awa": {"reseau": "TikTok", "handle": "@awa", "url": "https://www.tiktok.com/@awa",
  "proprietaire": true, "public": "francophone, 18-34 ans", "fuseaux_public": ["Africa/Abidjan", "Europe/Paris"],
  "fuseau_utilisateur": "Europe/Paris", "langue": "fr", "objectif": "...",
  "acces": {"metricool": null, "public": "navigateur", "interne": "TikTok Studio (connexion manuelle)"},
  "derniere_analyse": "2026-10-25"}}
```
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
