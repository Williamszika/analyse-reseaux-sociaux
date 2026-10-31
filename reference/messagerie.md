# Messagerie (mode O) : clients, rendez-vous, partenaires, relances, rapport

Outil : `scripts/messagerie.py`. Données : `$ANALYSES_DONNEES/messagerie/<compte>/` (cadre, contacts, journal) — dans
l'espace privé de l'utilisateur, jamais dans la boîte à outils. Les numéros et noms des clients ne sortent jamais de cet espace.

## 1. Ce que Claude fait seul, et ce qu'il demande

| Situation | Compte d'entreprise avec cadre validé | Compte personnel (ou cadre non validé) |
|---|---|---|
| Question à laquelle le cadre répond (horaires, prix listés, adresse…) | répond seul, mot pour mot du cadre | brouillon → « oui » du propriétaire |
| Demande de rendez-vous | propose 3 créneaux libres de l'agenda ; confirme et crée l'événement si `auto_confirmer` | brouillon → « oui » |
| Plainte, paiement, remboursement, sujet sensible, ou hors cadre | réponse d'attente du cadre, puis le propriétaire répond | brouillon → « oui » |
| « STOP » | confirme une fois, ne réécrit plus jamais | idem |
| Relance d'un contact, premier message à un partenaire | brouillon → « oui » (liste numérotée acceptée) | brouillon → « oui » |

Le cadre est validé par le propriétaire sur son texte exact (`cadre montrer` puis `cadre valider --accord "<ses mots>"`).
Toute modification du cadre change son empreinte : plus rien n'est automatique jusqu'au nouvel accord.
Les réponses automatiques sont réservées aux comptes d'entreprise (Chap.ci, une boutique, une agence) et à des personnes
qui ont écrit les premières.

## 2. Par plateforme

| Plateforme | Comment | Premier message à un inconnu |
|---|---|---|
| **WhatsApp** (personnel ou WhatsApp Business app) | WhatsApp Web dans le navigateur de l'utilisateur, connecté par lui (QR code scanné par lui) | non, sauf si la personne a donné son numéro pour ça |
| **WhatsApp Business Platform** (API, via Twilio ou Meta) | réponses dans les 24 h suivant le message du client ; au-delà, seulement des modèles approuvés par Meta et à des personnes qui ont accepté (skills twilio-whatsapp-*) | modèles approuvés + consentement |
| **Telegram** (compte) | Telegram Web dans le navigateur | non, sauf contact existant |
| **Telegram** (bot) | API Bot : le bot ne peut écrire qu'à ceux qui l'ont démarré | impossible |
| **Instagram / Messenger / TikTok** | messagerie du site dans le navigateur, ou Meta Business Suite | oui pour une demande de partenariat à un compte public, un message à la fois |
| **LinkedIn / e-mail** | navigateur ou connecteur e-mail | oui, personnalisé, un à la fois |

Connexion : toujours par l'utilisateur lui-même (QR code, mot de passe, code) dans l'onglet ouvert ; Claude ne tape jamais
d'identifiant ni de code. Mauvais compte connecté → ne rien lire ni envoyer.

## 3. Rendez-vous

1. `messagerie.py creneaux --compte … --occupe occupe.json` : `occupe.json` = les périodes prises de l'agenda (connecteur
   Google Calendar : événements des 7 prochains jours → `[{"debut": ISO, "fin": ISO}]`).
2. Proposer les 3 créneaux au client (texte du cadre). Quand il en choisit un : créer l'événement (titre « <objet> — <nom> »,
   lieu ou lien d'appel, rappel), puis `messagerie.py rdv --compte … --contact … --texte "<jour heure>" --lien <lien de l'événement>`.
3. Sans `auto_confirmer` : montrer l'événement au propriétaire et attendre son « oui » avant de le créer.

## 4. Partenaires et relances

- `messagerie.py contact --compte … --nom … --canal linkedin --motif partenaire --source "<où on l'a trouvé>" --note "<pourquoi>"` :
  seulement des entreprises, créateurs ou personnalités **publics** ; jamais un particulier trouvé par son nom ou sa photo.
- `messagerie.py a-faire` liste les relances dues et les partenaires à contacter, sous le plafond du jour. Pour chacun :
  un brouillon personnalisé (qui on est, pourquoi lui, une proposition claire, une question simple), montré au propriétaire.
- Relance : 2 au plus, espacées de `relance.delai_j` jours ; sans réponse ensuite, on arrête.

## 5. Boucle de travail (session ou tâche programmée)

1. Ouvrir la messagerie du compte (vérifier le compte connecté).
2. Pour chaque conversation non lue : `decider` → selon la décision, envoyer la réponse (auto), proposer des créneaux (rdv),
   envoyer la réponse d'attente et ajouter à « à vous de répondre » (proprietaire_attente), ou ne rien envoyer (proprietaire).
   Après chaque envoi : `noter --sens envoye [--auto]`. Une action toutes les quelques secondes, jamais en rafale.
3. `a-faire` → brouillons de relances et de premiers messages → liste numérotée au propriétaire.
4. `rapport --out …` → envoyer au propriétaire (et l'ajouter au rapport PDF des réseaux sociaux si une analyse est en cours).
Une tâche programmée tourne au plus toutes les heures : pour des réponses en quelques secondes, il faut un numéro
WhatsApp Business Platform relié à un service toujours allumé (Twilio + webhook) — à proposer, pas à installer sans accord.
