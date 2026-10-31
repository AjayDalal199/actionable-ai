# Actionable AI — Deployment

**Primary path:** Docker Compose + Traefik on Oracle Cloud Always Free (two VMs: staging and production). Operator guide: [deployment-oracle-cloud.md](./deployment-oracle-cloud.md).

Policy (environments, promotion, secrets): [07 Deployment Strategy](./actionable-ai/docs/5_Development_and_Execution/07_Deployment_Strategy.md).

Compose commands: [deployment-docker-compose.md](./deployment-docker-compose.md).

## What gets deployed

One FastAPI image: marketing + dashboard SPA, API at `/api/v1`, and later the widget script on the same origin. PostgreSQL (pgvector) and Redis are in the same Compose project. An upload volume and a worker process join that project with knowledge ingestion — they are not separate products. Redis is ephemeral and is not published off the Docker network.

Original uploads for the MVP stay on each VM’s boot volume (about 80 GB). There is no object-storage bucket. The volume is a Docker named volume on that disk, shared with the OS, images, and Postgres.

## FastAPI Cloud (not used)

The template included [FastAPI Cloud](https://fastapicloud.com) and `.github/workflows/deploy.yml`. **Do not use that as the A²I host.** Staging and production need Postgres we control (pgvector), Redis, disk for uploads, and a worker. The Cloud workflow is disabled.
