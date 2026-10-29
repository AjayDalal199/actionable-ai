# Actionable AI — Docker Compose deployment

Deploy the app with Docker Compose. Traefik terminates HTTPS.

This is the **how**. Hosting on Oracle Cloud Always Free (two VMs, dactionlabs.com, GitHub SSH): [deployment-oracle-cloud.md](./deployment-oracle-cloud.md). Policy: [07 Deployment Strategy](./actionable-ai/docs/5_Development_and_Execution/07_Deployment_Strategy.md).

Staging and production must not share a VPS, a `SECRET_KEY`, a Postgres volume, or a Compose project.

## Files

| File | Role |
| --- | --- |
| `compose.yml` | App stack (Traefik, Postgres, backend, Adminer) |
| `compose.deploy.yml` | Server overlay: 80/443, Let’s Encrypt, Adminer profile |
| `compose.override.yml` | Local only. Never on a server. |

## Environment variables

```bash
export STACK_NAME=a2i-staging          # a2i-prod on production
export DOMAIN=staging.dactionlabs.com  # app.dactionlabs.com on production
export PROJECT_NAME="Actionable AI"
export FIRST_SUPERUSER=ops@dactionlabs.com
export COMPOSE_PROJECT_NAME="$STACK_NAME"
```

Optional: `SMTP_HOST`, `SMTP_USER`, `EMAILS_FROM_EMAIL`, `SENTRY_DSN`, `LETSENCRYPT_EMAIL`, `WEB_CONCURRENCY` (keep **1** on the 6 GB VMs).

Do **not** set `FASTAPI_ENV=development` on a server. Default secrets (`changethis`) must fail boot.

Generate unique secrets per environment:

```bash
export POSTGRES_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export FIRST_SUPERUSER_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

Never reuse staging `SECRET_KEY` or database passwords in production.

## Manual deploy (break-glass)

Prefer GitHub Actions over a laptop SSH as the happy path. On **that environment’s** VM:

```bash
cd /home/deploy/actionable-ai
export COMPOSE_PROFILES=adminer   # staging only; omit on production
docker compose -f compose.yml -f compose.deploy.yml build
docker compose -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
docker compose -f compose.yml -f compose.deploy.yml up -d
```

The backend image builds the frontend. The server does not need Bun. `prestart.sh` waits for Postgres, runs `alembic upgrade head`, and creates the first superuser.

## Deploy with GitHub Actions

[`.github/workflows/deploy-docker-compose.yml`](.github/workflows/deploy-docker-compose.yml) SSHs from `ubuntu-latest` into the Environment’s VM (`vars.SSH_HOST`).

- Merge to `develop` → staging VM
- Merge a PR labeled `release` into `master` → production VM
- **Actions → Deploy with Docker Compose** for a manual replay

Public repo: do **not** install a self-hosted runner on either VM. Configure GitHub Environments `staging` and `production` as in [deployment-oracle-cloud.md](./deployment-oracle-cloud.md).

## URLs

| Surface | Staging | Production |
| --- | --- | --- |
| App | `https://staging.dactionlabs.com` | `https://app.dactionlabs.com` |
| OpenAPI | `https://staging.dactionlabs.com/docs` | Gate or disable |
| Adminer | `https://adminer.staging.dactionlabs.com` | Not exposed |
