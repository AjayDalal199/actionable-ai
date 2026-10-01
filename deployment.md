# Actionable AI — Deployment

**Primary path:** Docker Compose + Traefik on our own VPS (staging and production).

Policy (environments, promotion, secrets, what not to do): [07 Deployment Strategy](./actionable-ai/docs/5_Development_and_Execution/07_Deployment_Strategy.md).

Operator commands: [deployment-docker-compose.md](./deployment-docker-compose.md).

## What gets deployed

One FastAPI image: marketing + dashboard SPA, API at `/api/v1`, and later the widget script on the same origin. PostgreSQL is in the same Compose project. Redis, pgvector, an upload volume, and a worker process join that project when those product phases land — they are not separate products.

## FastAPI Cloud (not used)

The template included [FastAPI Cloud](https://fastapicloud.com) and `.github/workflows/deploy.yml`. **Do not use that as the A²I host.** Staging and production need Postgres we control (pgvector), Redis, disk for uploads, and a worker. Cloud is API + managed DB only.

Leave the Cloud workflow disabled or unused so a push to `master` cannot deploy there by accident. If you are reading older template docs, ignore Cloud as the happy path.
