# CareerOS Intelligence — Luca

Tableau personnel de candidatures WASH, hydraulique, hydrologie, doctorats et bourses. **Aucun CV ni numéro de téléphone n'est publié dans ce dépôt.**

## État

- Interface statique : `site/index.html` avec 15 dossiers initiaux.
- Veille gratuite automatisable : `scripts/veille_gratuite.py` (Remotive et flux de presse Google News RSS, classement par mots-clés). Les résultats sont **des pistes non vérifiées**, pas des offres ouvertes certifiées.
- Enrichissement IA optionnel : `scripts/veille_ia.py` (nécessite un compte API OpenAI facturé séparément).
- Planification : `05:17 UTC`, soit `08:17` à Madagascar, sous réserve des retards GitHub Actions.
- CV personnalisés : **uniquement dans l'archive locale**, pas sur GitHub.

## Terminer l'activation du site (une seule fois)

1. Sous le dépôt, ouvrir **Settings → Pages** : <https://github.com/Ratovoarisoa/careeros-intelligence/settings/pages>.
2. Dans **Build and deployment**, mettre **Source = GitHub Actions**, puis sauvegarder. Cette opération requiert une permission d'administration du dépôt et ne peut pas être réalisée par la connexion GitHub actuellement disponible à l'assistant.
3. Aller dans **Actions → CareerOS — veille quotidienne et publication → Run workflow** pour forcer une première actualisation : <https://github.com/Ratovoarisoa/careeros-intelligence/actions>.
4. Après succès : <https://ratovoarisoa.github.io/careeros-intelligence/>.

Sans la configuration Pages, le programme peut sauvegarder les nouveaux résultats, mais ne peut pas publier le site. Le workflow **ne marque pas la publication comme réussie** tant que Pages n'est pas activé.

## IA avancée (facultative)

- Obtenir une clé sur <https://platform.openai.com/api-keys>.
- Dans GitHub **Settings → Secrets and variables → Actions**, ajouter un *Repository secret* `OPENAI_API_KEY` : <https://github.com/Ratovoarisoa/careeros-intelligence/settings/secrets/actions>.
- Ne jamais copier la clé dans un fichier public, un ticket GitHub ou une conversation.
- Sans ce secret, le classement gratuit s'exécute tout de même. Avec secret, une recherche par modèle avec outil Web s'ajoute et consomme du budget API (distinct de ChatGPT Plus).

## Sécurité et transparence

Les annonces de la veille automatique ne sont jamais annoncées comme vérifiées. Les scores sont **des estimations de pertinence**, pas des probabilités de recrutement. Les statuts personnels sont stockés en `localStorage` dans le navigateur et ne sont pas synchronisés entre appareils. Exporter régulièrement le fichier JSON de sauvegarde depuis l'application.

Le programme gratuit est une recherche documentaire et un tri déterministe, **sans modèle IA**. Google News fournit des pistes indirectes nécessitant de retrouver l'offre officielle. Les sources peuvent changer leurs conditions d'accès ; une indisponibilité de source ne signifie pas absence d'offres.

## Tests

```bash
python -m unittest discover -s scripts -p 'test_*.py' -v
python scripts/veille_gratuite.py --demo
```
