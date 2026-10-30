# Connexion, actions et publicités

Adresses et menus **susceptibles de changer** : si une page ne mène plus au bon écran, naviguer depuis le menu du site.

## 1. Connexion guidée (toujours par l'utilisateur)
1. Ouvrir la page de connexion du réseau dans le navigateur (celui que la personne préfère), onglet visible.
2. Dire en une phrase : « Connectez-vous dans cet onglet (identifiant, mot de passe, code reçu) ; dites-moi quand c'est fait. »
3. Pendant ce temps, continuer avec les connecteurs ou les données publiques. Ne jamais attendre sans rien faire.
4. Ensuite, vérifier que le compte connecté est le bon (pseudo affiché = `handle` de `comptes.json`). Mauvais compte : ne rien
   relever ni faire, le dire.
5. Proposer une fois de relier le compte à un connecteur (Metricool…) pour ne plus avoir à se connecter.

Claude ne tape jamais d'identifiant, de mot de passe, de code ni de réponse de sécurité (même écrits dans la conversation :
ne pas les répéter, demander de les taper dans la page), ne résout pas de captcha, ne crée pas de compte, n'accepte pas de
conditions d'utilisation à la place de la personne, ne touche pas aux réglages de sécurité, d'e-mail, de mot de passe ni de pseudo.

## 2. Tableaux internes à relever (après connexion)
| Réseau | Où | Quoi |
|---|---|---|
| TikTok | TikTok Studio → Statistiques | Vue d'ensemble, Contenu, Abonnés (heures d'activité, pays, âge, genre), par vidéo : temps moyen, visionnage complet, sources de trafic |
| Instagram / Facebook | Meta Business Suite → Statistiques ; app → Tableau de bord professionnel | Portée, interactions, abonnés, audience (heures, pays, âge), par post |
| YouTube | YouTube Studio → Statistiques | Impressions, taux de clic, durée moyenne, rétention, sources, « quand vos spectateurs sont sur YouTube » |
| LinkedIn | Statistiques créateur / page entreprise | Impressions, abonnés, données démographiques |
| X | Statistiques (selon l'abonnement) | Impressions, engagements, abonnés |
Copier les chiffres dans `stats_internes.json` (mêmes libellés d'une fois sur l'autre). Messages privés et revenus : seulement
si la personne le demande, en résumé.

## 3. Publier, commenter, répondre, programmer (mode N)
Toujours avec `scripts/actions.py` : `preparer` → `montrer` (le texte exact à l'utilisateur) → son « oui » → `valider --accord "<sa phrase>"`
→ faire l'action dans le navigateur → `fait --lien`. Si le texte change, nouvelle validation.
- **Une action = un accord.** Un « oui » vaut pour ce qui a été montré, pas pour la suite. Exception : l'utilisateur valide
  explicitement une liste numérotée (« publie les 3 ») ; créer alors une fiche par élément, toutes montrées avant.
- **Programmation** : de préférence l'outil du réseau (programmer la publication) ou un connecteur (Metricool
  `createScheduledPost` après accord) plutôt que de rester connecté.
- **Commentaires** : répondre aux commentaires reçus (la règle de la première heure) est utile ; commenter chez les autres,
  avec parcimonie et un vrai message. Jamais de commentaires en série, de copier-coller, de faux avis, de messages non
  sollicités en masse, d'abonnements ou de likes en boucle : c'est du spam, interdit par les réseaux, et le compte peut être bloqué.
- **Respecter** `profil.json > regles` (comptes où ne rien publier, liens interdits…).
- **Annonces** (mode N, sans payer) : post épinglé, story, annonce de live, publication d'une offre.

## 4. Publicités (mode M)
### 4a. Analyser les publicités (public, sans connexion)
| Source | Adresse | Ce qu'on y trouve |
|---|---|---|
| Bibliothèque publicitaire Meta | https://www.facebook.com/ads/library | Pubs actives (et passées pour l'UE / sujets politiques) d'une page, sur Facebook, Instagram, Messenger : date de début, visuels, textes, plateformes |
| TikTok Creative Center | https://ads.tiktok.com/business/creativecenter | Pubs les plus performantes par pays, secteur, objectif ; tendances, sons, hashtags |
| Bibliothèque de pubs TikTok (UE) | https://library.tiktok.com | Pubs diffusées dans l'UE, annonceur, dates, portée approximative |
| Centre de transparence Google | https://adstransparency.google.com | Pubs Google / YouTube d'un annonceur |
| Bibliothèque LinkedIn | https://www.linkedin.com/ad-library | Pubs d'une entreprise |
Pour chaque pub retenue : annonceur, depuis quand (une pub qui tourne longtemps est rentable), format, accroche (3 premières
secondes), offre, appel à l'action, plateformes. Remplir `publicites` dans `analysis.json` (voir formats.md) : le rapport
ajoute une section « Publicités ».
Côté compte de l'utilisateur (après connexion) : voir quelles vidéos ont été boostées et leurs résultats (TikTok Studio →
Promouvoir ; Meta → Gestionnaire de publicités → Campagnes).

### 4b. Préparer une campagne
Brief dans `campagne.json` (formats.md) : objectif (vues, visites du profil, messages, ventes), cible (pays, villes, âge,
langue, centres d'intérêt), budget total et durée, contenu (meilleur post organique de préférence), texte, appel à l'action,
indicateur de réussite et seuil d'arrêt. Montrer le brief ; rien n'est lancé à ce stade.

### 4c. Lancer ou booster (dépense réelle)
- Seulement sur un compte publicitaire **déjà configuré par la personne** avec son moyen de paiement. Claude ne saisit jamais
  de carte, d'IBAN ni de code de paiement, et ne crée pas de compte publicitaire.
- `actions.py preparer --type boost|campagne --budget … --duree-jours … --cible … --objectif …` : refusé au-delà du plafond
  de `profil.json > publicite` (0 par défaut = aucune dépense). Montrer, obtenir un « oui » qui vaut pour **ce montant**,
  valider, puis lancer.
- Où : TikTok → Promouvoir sur la vidéo, ou TikTok Ads Manager (https://ads.tiktok.com) ; Instagram / Facebook → bouton
  Booster, ou Gestionnaire de publicités (https://adsmanager.facebook.com) ; YouTube → Google Ads ; LinkedIn → Campaign Manager.
- Après lancement : noter le lien de la campagne (`fait --lien`) ; au suivi suivant, relever dépense, portée, coût par résultat,
  et recommander de couper, garder ou augmenter.
- Jamais : contourner un refus de la plateforme, publicités trompeuses, ciblage discriminatoire (logement, emploi, crédit),
  sujets politiques ou sociaux sans l'autorisation exigée par la plateforme.

## 5. Informations d'un client (audit ou gestion pour quelqu'un d'autre)
- Noter le client et son consentement : `donnees.py compte --reseau … --handle … --client "Nom" --consentement "date, moyen, périmètre"`.
  Sans consentement noté, `actions.py` refuse toute action.
- Recueillir seulement ce qui sert : marque, offre, cible, ton, budget, comptes, accès qu'il accorde lui-même (rôle dans
  Meta Business Suite, TikTok Business Center…), jamais son mot de passe.
- Ses données restent dans l'espace de données de la personne qui fait l'audit, dans les fiches de ce client ; les lui rendre
  ou les effacer s'il le demande.
