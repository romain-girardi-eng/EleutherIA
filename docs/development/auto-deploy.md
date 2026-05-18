# Auto-redeploy frontend (push → prod)

Chaque push sur `main` qui touche `frontend/**` déclenche
`.github/workflows/deploy-frontend.yml` qui :

1. build l'image Docker frontend
2. la push sur GHCR avec deux tags : `:latest` et `:sha-<short>`

the platform consomme `:latest`. Pour fermer la boucle, il faut UNE des deux
configurations côté host the platform (les deux marchent, à choisir selon le
setup existant).

## Option A — Watchtower (recommandé, zero-touch)

Si the platform n'a pas déjà Watchtower, l'ajouter à la compose master de
the platform (pas ici dans EleutherIA — c'est un service d'infra) :

```yaml
watchtower:
  image: containrrr/watchtower
  container_name: watchtower
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  command:
    - --label-enable     # n'auto-update que les containers avec le label
    - --interval=120     # check toutes les 2 min
    - --cleanup
  restart: unless-stopped
```

Le service `eleutheria-frontend` porte déjà le label
`com.centurylinklabs.watchtower.enable: "true"`. Watchtower va donc :

- détecter une nouvelle image `:latest` sur GHCR
- pull
- recréer le container avec la même config
- nettoyer l'ancienne image

**Latence push → prod : ~3-5 min** (GH Action build + watchtower poll).

## Option B — cron simple

Si tu préfères ne pas ajouter Watchtower, mets un cron sur le host
the platform qui pull et restart toutes les N minutes :

```cron
*/5 * * * * cd /opt/pragma && docker compose -f EleutherIA/deploy/deploy-compose.yml pull eleutheria-frontend && docker compose -f EleutherIA/deploy/deploy-compose.yml up -d eleutheria-frontend >> /var/log/eleutheria-deploy.log 2>&1
```

(adapte le chemin selon où le clone vit côté the platform)

## Bascule one-time

Premier déploiement après ce setup — le compose the platform actuel buildait
en local, on bascule sur l'image GHCR. À faire UNE FOIS sur le host
the platform :

```bash
cd <path-to-eleutheria-clone>
git pull origin main           # récupère la nouvelle deploy-compose.yml
docker login ghcr.io           # une fois seulement, l'image est publique mais facilite le pull
docker compose -f deploy/deploy-compose.yml pull eleutheria-frontend
docker compose -f deploy/deploy-compose.yml up -d eleutheria-frontend
```

À partir de là, tout push frontend → prod sans intervention manuelle.

## Trigger manuel

Si tu veux forcer un build depuis l'interface GitHub :

```
gh workflow run deploy-frontend.yml
# ou : Actions → Deploy Frontend (GHCR) → Run workflow
```

Optionnellement avec un tag custom (`gh workflow run deploy-frontend.yml -f tag=v1.2.3`).

## Backend / worker

Pour l'instant seul le frontend est auto-redeployé. Les images
`eleutheria-api` et `eleutheria-worker` continuent d'être buildées
côté the platform. Si on veut le même pattern pour le backend, dupliquer
le workflow avec `deploy-backend.yml` (cible `backend/`, `database/`,
`kg/`, `graphrag/`).
