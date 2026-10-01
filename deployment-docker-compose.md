# Actionable AI — Docker Compose deployment

Deploy the app to a remote server with Docker Compose. Traefik terminates HTTPS and routes traffic to the backend.

This is the **how**. For staging vs production, promotion, and secrets policy, read [07 Deployment Strategy](./actionable-ai/docs/5_Development_and_Execution/07_Deployment_Strategy.md) first. Staging and production must not share a VPS, a `SECRET_KEY`, or a Compose project.

## Preparation

* A remote server with [Docker Engine](https://docs.docker.com/engine/install/) (not Docker Desktop).
* DNS for the app hostname, for example `staging.actionable.ai` or `app.actionable.ai`.
* Staging only: optional Adminer hostname such as `adminer.staging.actionable.ai`. Do not expose Adminer on production.

## Copy the code

```bash
rsync -av --exclude=".git/" --filter=":- .gitignore" ./ root@your-server.example.com:/root/code/app/
```

The `--filter=":- .gitignore"` option uses the same ignore rules as Git (virtualenv, `node_modules`, local `.env`). Prefer GitHub Actions on a self-hosted runner over `rsync` as the happy path; `rsync` is break-glass.

## Configure the application

### Environment variables

```bash
export DOMAIN=staging.actionable.ai
export PROJECT_NAME="Actionable AI"
export FIRST_SUPERUSER=admin@example.com
```

Optional:

* `SMTP_HOST`, `SMTP_USER`, `EMAILS_FROM_EMAIL` — transactional email
* `SENTRY_DSN` — error reporting (on in staging and production)

Do **not** set `FASTAPI_ENV=development` on a server. Default secrets (`changethis`) must fail boot.

### Secrets

Generate unique values per environment:

```bash
export POSTGRES_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export FIRST_SUPERUSER_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

For an authenticated SMTP provider, also set `SMTP_PASSWORD`.

Never reuse staging `SECRET_KEY` or database passwords in production.

## Deploy

```bash
cd /root/code/app/
docker compose -f compose.yml -f compose.deploy.yml build
docker compose -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
docker compose -f compose.yml -f compose.deploy.yml up -d
```

`compose.deploy.yml` adds HTTPS and Let's Encrypt on top of `compose.yml`. Listing both files **excludes** `compose.override.yml` (local ports, Mailcatcher, insecure Traefik API).

The backend image builds the frontend. The server does not need Bun or a prebuilt SPA.

`prestart.sh` waits for Postgres, runs `alembic upgrade head`, and creates the first superuser.

## Deploy with GitHub Actions

`.github/workflows/deploy-docker-compose.yml` runs those commands on a self-hosted runner when you trigger **Deploy with Docker Compose**.

The strategy target is two workflows and two GitHub Environments (`staging`, `production`). Until that split exists, treat this workflow as a single-stack deploy and keep secrets on the environment you actually intend to update.

Use a self-hosted runner only on a repository whose contributors and workflow code you trust. GitHub recommends self-hosted runners with **private** repositories because workflows run directly on the machine.

### Configure repository variables and secrets

**Settings** → **Secrets and variables** → **Actions**.

Variables:

* `DOMAIN`
* `PROJECT_NAME`
* `FIRST_SUPERUSER`

Optional variables: `SMTP_HOST`, `SMTP_USER`, `EMAILS_FROM_EMAIL`, `SENTRY_DSN`.

Secrets:

* `POSTGRES_PASSWORD`
* `SECRET_KEY`
* `FIRST_SUPERUSER_PASSWORD`

Optional secret: `SMTP_PASSWORD`.

### Install a self-hosted runner

On the **environment's** VPS (staging runner on staging, production runner on production):

```bash
sudo adduser github
sudo usermod -aG docker github
sudo su - github
```

In the GitHub repo: **Settings** → **Actions** → **Runners** → **New self-hosted runner** → Linux. Install under `/home/github/actions-runner`.

Then as root:

```bash
cd /home/github/actions-runner
sudo ./svc.sh install github
sudo ./svc.sh start
sudo ./svc.sh status
```

See GitHub's guides for [adding a self-hosted runner](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners) and [running it as a service](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application?platform=linux).

### Run the deployment

When the runner is online: **Actions** → **Deploy with Docker Compose** → **Run workflow**.

## URLs

Replace the hostname with `DOMAIN`.

| Surface | URL |
| --- | --- |
| App (frontend and API) | `https://staging.actionable.ai` |
| OpenAPI | `https://staging.actionable.ai/docs` (keep on staging; gate or disable in production) |
| Adminer | `https://adminer.staging.actionable.ai` (staging only) |
