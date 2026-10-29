# Fiches réseaux

Limites, adresses et emplacements **susceptibles de changer** : si une adresse ne mène plus au bon écran,
naviguer depuis le menu du site ; en cas de doute sur une limite, vérifier (compteur du champ, recherche web) et le dire.
Ordre d'accès pour un compte de l'utilisateur : **connecteur → données publiques → connexion manuelle (option)**.
Limites chiffrées et alias : `reseaux.json` (lu par les scripts). Un réseau absent d'ici : section « Réseau non répertorié » en fin de fichier.

## TikTok
- **Connecteur** : Metricool, Supermetrics (si le compte y est relié, voir connecteurs.md). Sinon données publiques.
- **Public** (sans connexion, navigateur) : page profil → JSON `__UNIVERSAL_DATA_FOR_REHYDRATION__`
  (`__DEFAULT_SCOPE__['webapp.user-detail'].userInfo` : `user`, `statsV2`). Liens des posts :
  `[data-e2e="user-post-item"] a` après défilement. Pour chaque vidéo : `fetch(url)` depuis la page TikTok (même origine,
  1,2 s de pause) puis `webapp.video-detail.itemInfo.itemStruct` (`createTime`, `video.duration`, `statsV2`, `desc`,
  `textExtra`, `music`). Carrousels photo : seulement les vues de la grille. Fenêtre « Connecte-toi » : la fermer
  (« Ignorer » ou supprimer les éléments `[role=dialog]`), ne jamais se connecter.
  Images d'une vidéo : supprimer la fenêtre, `video.muted=true; video.pause(); video.currentTime=t`, capture, recadrer.
  Sur Mac : `collect.py <profil> --cookies`.
- **Interne** (option) : TikTok Studio https://www.tiktok.com/tiktokstudio/analytics → Vue d'ensemble, Contenu, Abonnés
  (activité par heure et jour, pays, âge, genre) ; par vidéo : temps moyen, visionnage complet, sources de trafic.
- **Engagement** : (likes + commentaires + partages) / vues.
- **Profil** : photo, nom (30 caractères, modifiable tous les 7 jours, indexé par la recherche), pseudo, bio (limite non
  publiée de façon unique : viser ≤ 80), lien (selon type de compte et abonnés), 3 vidéos épinglées, playlists,
  couvertures cohérentes, compte professionnel.

## Instagram
- **Connecteur** : Metricool (statistiques complètes sans connexion) ; Supermetrics
  (`instagram_insights`) ; vidIQ (`vidiq_instagram_owner_insights`).
- **Public** : `meta[property="og:description"]` du profil (abonnés, abonnements, nombre de publications) ;
  liens `a[href*="/p/"], a[href*="/reel/"]` ; page d'un post : `<time datetime>` et `og:description` (likes, commentaires).
  Refuser les cookies optionnels, fermer la fenêtre d'inscription (croix). Sur Mac : `collect.py <profil> --cookies`.
- **Interne** (option) : Tableau de bord professionnel → Statistiques ; Meta Business Suite
  https://business.facebook.com/latest/insights.
- **Engagement** : Reels / vues ; photos et carrousels / portée (interne) sinon / abonnés.
- **Profil** : photo, nom (30, indexé par la recherche), pseudo, bio (150), jusqu'à 5 liens, catégorie et boutons de
  contact, stories à la une avec couvertures cohérentes, 3 posts épinglés, grille cohérente.

## YouTube
- **Connecteur** : vidIQ (`vidiq_user_channels`, `vidiq_channel_analytics`, `vidiq_subscriber_insights`,
  `vidiq_video_transcript`), Supermetrics, Metricool si la chaîne y est reliée.
- **Public** : `collect.py https://www.youtube.com/@<chaîne>/videos` (et `/shorts`), `timestamp` = heure exacte ;
  `yt_search.py` pour la niche ; `fetch.py` pour la courbe des moments les plus revus et les commentaires.
- **Interne** (option) : YouTube Studio https://studio.youtube.com → Statistiques (impressions, taux de clic, durée moyenne,
  sources de trafic, Audience : moments où vos spectateurs sont sur YouTube) ; par vidéo : rétention.
- **Engagement** : / vues ; vidéos longues : rétention.
- **Profil** : photo, nom, handle, bannière 2560 × 1440 (zone utile centrale), description (1000), liens, bande-annonce
  non-abonnés, vidéo à la une abonnés, sections, playlists, filigrane, miniatures cohérentes.

## Facebook (Page)
- **Connecteur** : Metricool, Supermetrics.
- **Public** : vidéos et Reels via `collect.py <page>/videos --cookies` (Mac) ; posts dans le navigateur (heure exacte au survol de la date).
- **Interne** (option) : Meta Business Suite → Statistiques.
- **Engagement** : vidéos / vues ; posts / portée sinon / abonnés.
- **Profil** : photo, couverture, nom, catégorie, intro (≈ 100), bouton d'action (WhatsApp, Message…), coordonnées,
  post épinglé, avis, À propos complet.

## LinkedIn
- **Connecteur** : Metricool (`linkedin`), Supermetrics.
- **Public** : navigateur, lentement, sans automatisation massive ; dates relatives (« 3 j »).
- **Interne** (option) : https://www.linkedin.com/analytics/creator/content/ ; page entreprise : Statistiques.
- **Engagement** : (réactions + commentaires + republications) / impressions sinon / abonnés.
- **Profil** : photo, bannière, titre (220), Infos (2600), Sélection, URL personnalisée, mode créateur.

## X (Twitter)
- **Connecteur** : Metricool (`twitter`). **Public** : `<time datetime>`, compteurs dans les libellés des boutons.
- **Engagement** : / vues. **Profil** : photo, bannière, nom (50), bio (160), lieu, site, post épinglé.

## RedNote (Xiaohongshu)
- **Public** : navigateur (dates et compteurs par note) ; `fetch.py <note> --cookies` pour une vidéo (Mac).
- **Interne** (option) : https://creator.xiaohongshu.com.
- **Engagement** : (likes + enregistrements + commentaires) / abonnés.
- **Profil** : photo, pseudo, bio courte, couvertures homogènes avec titre lisible, collections.

## Threads
- **Connecteur** : Metricool (selon l'offre). **Public** : profil et posts dans le navigateur (lié au compte Instagram).
- **Engagement** : (likes + réponses + republications) / vues. **Profil** : hérite de la photo et du nom Instagram, bio (150), lien.

## Pinterest
- **Connecteur** : Metricool, Supermetrics. **Public** : profil, tableaux, épingles (dates peu fiables : préférer le connecteur).
- **Interne** (option) : compte professionnel → Statistiques (impressions, enregistrements, clics sortants).
- **Engagement** : (enregistrements + clics) / impressions. **Profil** : photo, nom, « À propos » (500), site vérifié, tableaux bien nommés.

## Snapchat
- **Public** : profil public (Spotlight, Stories publiques) dans le navigateur, données limitées.
- **Interne** (option) : application → Statistiques du profil public. **Engagement** : / vues.

## Bluesky, Mastodon
- **Public** : profil et posts publics dans le navigateur (dates exactes dans `<time>`). Mastodon : bio limitée par l'instance (souvent 500).
- **Engagement** : (likes + republications + réponses) / abonnés.

## Twitch, Kick
- **Public** : chaîne, rediffusions et clips (`collect.py` sur l'ordinateur, yt-dlp les gère).
- **Interne** (option) : Tableau de bord du créateur → Statistiques (spectateurs moyens, pics, heures de stream).
- **Horaires** : analyser les heures de **début de live** et les spectateurs moyens, pas les vues de rediffusion.
- **Profil** : photo, bannière, bio (Twitch 300), panneaux, planning de stream affiché.

## Reddit
- **Public** : profil `/user/<nom>` ou communauté `/r/<nom>` ; dates exactes dans `<time>` ; votes et commentaires par post.
- **Engagement** : (votes + commentaires) ; comparer à la médiane de la communauté. Règles de chaque communauté à respecter.

## Telegram, WhatsApp (chaînes)
- **Public** : Telegram `https://t.me/s/<chaîne>` (aperçu public : vues et heure par message) ; WhatsApp : aperçu de chaîne limité.
- **Engagement** : vues (Telegram) ou réactions / abonnés.

## Douyin, Bilibili, Weibo, Kwai, VK
- **Public** : navigateur ; yt-dlp gère la plupart des vidéos (`fetch.py`). Pages souvent dans une autre langue : traduire les libellés.
- **Fuseau** : le public est souvent en `Asia/Shanghai` (Chine) ou `Europe/Moscow` (VK) : le vérifier.

## Réseau non répertorié (méthode générale)
Tout réseau fonctionne avec cette méthode ; les scripts s'adaptent (fiche générique, pas de contrôle automatique des limites).
1. **Connecteur** : `SearchMcpRegistry` avec le nom du réseau ; s'il en existe un, `SuggestConnectors` et continuer sans attendre.
2. **Public** : ouvrir le profil dans le navigateur ; chercher les données dans la page (JSON intégré, balises `<time datetime>`,
   `og:description`, libellés des boutons) ; sinon relever à la main 12 à 20 posts (date, vues, réactions, commentaires).
   Vidéos : tester `fetch.py` (yt-dlp gère plus de 1 000 sites).
3. **Règles du profil** : trouver les limites (nom, bio, liens) par le compteur du champ ou l'aide officielle (recherche web),
   avec la date ; les enregistrer dans `profil.json > reseaux > <réseau>` de l'utilisateur, ex. `{"lemon8": {"bio_max": 80}}`.
4. **Engagement** : (réactions + commentaires + partages) / vues si les vues sont visibles, sinon / abonnés ; le dire dans le rapport.
5. Écrire dans `limites` du rapport que le réseau n'est pas répertorié et ce qui a été vérifié à la main.
