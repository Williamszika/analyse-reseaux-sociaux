# Connecteurs — recettes qui marchent

Ordre : connecteur déjà relié → proposer d'en relier un (`SearchMcpRegistry` puis `SuggestConnectors`) → données publiques.
Les identifiants propres à l'utilisateur (brandId Metricool, comptes reliés) se lisent dans **son** `profil.json > connecteurs`
et dans `comptes.json > acces`, jamais ici. Ne jamais attendre qu'un connecteur soit relié pour avancer.

## Metricool
Trouver la marque : `getBrandSettings` liste les marques de l'utilisateur et les réseaux reliés à chacune
(noter `brandId` et le fuseau de la marque dans `profil.json > connecteurs > metricool`).
Champs vérifiés avec de vraies données (octobre 2026) : Instagram (évolution, pays, âge/genre, meilleurs moments) et
Facebook (évolution). TikTok : champs tirés du catalogue Metricool, requête par vidéo à confirmer sur un compte qui publie.

Outils (charger avec ToolSearch « metricool ») : `getBrandSettings`, `getAnalyticsAvailableMetrics`,
`getAnalyticsDataByMetrics(brandId, from, to, metrics[])`, `getBestTimeToPostByNetwork(brandId, fromDate, toDate, timezone, socialNetwork)`.

Règles apprises :
- Une requête = **un seul connecteur** (évolution, posts, reels, démographie…). Mélanger renvoie des colonnes vides.
- Dates en ISO avec fuseau (`2026-09-27T00:00:00+02:00`). Attention au passage heure d'été/hiver dans la période.
- Les lignes « evolution » arrivent **par jour**, non triées, avec la date en dernière colonne : agréger soi-même
  (`LAST` pour abonnés, `SUM` pour vues/portée/interactions). Beaucoup de `null` = jour sans donnée, pas une erreur.
- `posts` / `reels` vides = aucune publication dans la période : élargir à 90 jours avant de conclure.
- `getBestTimeToPostByNetwork` sur la **semaine à venir** donne l'activité de l'audience : 7 jours × 24 heures
  (`dayOfWeek` 1 = lundi). La recopier telle quelle dans `stats_internes.json` → `audience_heures`.
- Ne jamais utiliser les champs marqués « Deprecated ».

## Instagram
| Besoin | Champs |
|---|---|
| Vue d'ensemble 28 j | `IGEV01` abonnés · `IGEV02` abonnements · `IGEV05` vues · `IGEV06` portée · `IGEV37` contenus publiés · `IGEV22` reels · `IGEV16` stories · `IGEV38` interactions · `IGEV42` comptes ayant interagi · `IGEV43` abonnés gagnés · `IGEV44` perdus · `IGEV19` portée moy./post · `IGEV30` portée moy./reel |
| Reels (90 j) | `IGRE02` date+heure · `IGRE03` texte · `IGRE06` url · `IGRE23` vues · `IGRE11` portée · `IGRE10` likes · `IGRE07` comm. · `IGRE12` enreg. · `IGRE21` partages · `IGRE24` temps moyen · `IGRE26` durée · `IGRE27` rétention % · `IGRE28` taux de vue > 3 s |
| Posts (90 j) | `IGPO02` date+heure · `IGPO03` texte · `IGPO06` url · `IGPO07` type · `IGPO28` vues · `IGPO14` portée · `IGPO13` likes · `IGPO08` comm. · `IGPO15` enreg. · `IGPO27` partages · `IGPO29` abonnés gagnés |
| Pays | `IGDP01`, `IGDP02` (part 0–1) |
| Âge et genre | `IGAG01`, `IGAG02`, `IGAG03` (en %) |
| Abonnés / non-abonnés | `IGAC03`, `IGAC05`, `IGAC06` |

## TikTok
| Besoin | Champs |
|---|---|
| Vue d'ensemble | `TKEV07` abonnés · `TKEV01` vidéos · `TKEV02` vues · `TKEV11` portée · `TKEV06` interactions · `TKEV09` vues du profil · `TKEV16` abonnés gagnés · `TKEV17` perdus |
| Par vidéo | `TKPO02` date+heure · `TKPO05` description · `TKPO03` url · `TKPO06` durée · `TKPO07` vues · `TKPO11` portée · `TKPO08` likes · `TKPO09` comm. · `TKPO10` partages · `TKPO13` **visionnage complet %** · `TKPO15` temps moyen · sources : `TKPO16` Pour toi · `TKPO17` abonnements · `TKPO20` profil · `TKPO21` recherche · `TKPO18` hashtag · `TKPO19` son |
| Pays / genre | `TKDC01`, `TKDC02` · `TKDG01`, `TKDG02` |
| Sources d'impressions | `TKDS01`, `TKDS02` |

## Facebook (Page)
| Besoin | Champs |
|---|---|
| Vue d'ensemble | `FBEV17` abonnés · `FBEV47` gagnés · `FBEV48` perdus · `FBEV03` vues de la page · `FBEV49` vues des contenus · `FBEV33` contenus publiés · `FBEV34` interactions · `FBEV18` portée moy./post · `FBEV21` reels · `FBEV22` vues reels |

Pour les champs non listés : `getAnalyticsAvailableMetrics(network, connector)`.

## Supermetrics
`data_source_discovery()` → choisir la source (Instagram Insights, Facebook Pages, YouTube, LinkedIn Pages, TikTok…) →
`accounts_discovery` → `field_discovery` → `data_query` → `get_async_query_results`. Source non autorisée : donner le
lien de connexion renvoyé par l'outil et continuer avec les données publiques.

## vidIQ (YouTube, Instagram)
`vidiq_user_channels`, `vidiq_channel_analytics`, `vidiq_subscriber_insights`, `vidiq_video_transcript` (transcription sans
ordinateur), `vidiq_outliers` / `vidiq_instagram_tiktok_outlier_search` (contenus qui sortent du lot dans une niche),
`vidiq_instagram_owner_insights`.
