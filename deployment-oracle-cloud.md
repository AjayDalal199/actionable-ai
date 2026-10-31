# Actionable AI — Oracle Cloud Always Free (dactionlabs.com)

Always Free Ampere is **2 OCPU and 12 GB total**. Split that into **two VMs**: staging and production each get **1 OCPU / 6 GB**. Each VM runs its own Compose stack and Traefik. Policy: [07 Deployment Strategy](./actionable-ai/docs/5_Development_and_Execution/07_Deployment_Strategy.md).

| Environment | Hostname | VM | Compose project | Git trigger |
| --- | --- | --- | --- | --- |
| Staging | `https://staging.dactionlabs.com` | Ampere 1 OCPU / 6 GB | `a2i-staging` | Push / merge to `develop` |
| Staging Adminer | `https://adminer.staging.dactionlabs.com` | same as staging | `a2i-staging` | Staging only |
| Production | `https://app.dactionlabs.com` | Ampere 1 OCPU / 6 GB | `a2i-prod` | Merge of a PR labeled `release` into `master` |

Do not point apex `dactionlabs.com` at either VM unless you add a Traefik Host rule for it.

The git remote is **public**. PR CI stays on GitHub-hosted `ubuntu-latest`. Deploy SSHs from GitHub into **that environment’s VM** and builds there (Ampere is ARM; GitHub runners are amd64). Do **not** install a GitHub Actions runner on either VM.

FastAPI Cloud ([`.github/workflows/deploy.yml`](./.github/workflows/deploy.yml)) is disabled.

**6 GB is tight.** Keep `WEB_CONCURRENCY=1` and a 4 GB swap file on each VM. `docker compose build` (Bun + uv on ARM) will swap; do not run two builds on the same box.

## Promotion

```text
feature PR → develop
  → CI
  → merge → auto deploy staging VM

when staging is good:
  Actions → Prepare Release (patch | minor | major)
  → PR into master labeled release (notes + version)
  → merge → auto deploy production VM
         → GitHub draft Release from the same notes
```

The human gate for production is **reviewing that release PR**. Do not merge random `develop` → `master` PRs.

## 1. Provision two VMs (OCI console)

Home region only. Retry another availability domain if Ampere is out of capacity. Do **not** also launch the AMD `E2.1.Micro` boxes — they eat boot-volume quota and cannot run this stack.

1. VCN wizard: public subnet + internet gateway.
2. Security list / NSG: TCP **22**, **80**, **443** from `0.0.0.0/0`. SSH is key-only (GitHub-hosted runners have no stable IP).
3. Launch **two** Always Free Ampere instances, each:
   - Image: Ubuntu **Always Free Eligible** (ARM)
   - Shape: `VM.Standard.A1.Flex`, **1 OCPU**, **6 GB**
   - Boot volume **70–80 GB** (200 GB Always Free total for both). This disk is also the MVP upload store: a Docker named volume on the boot volume, no object storage and no extra block volume
   - Public IPv4, SSH public key, no password SSH
   - Names: `a2i-staging`, `a2i-prod`
4. DNS at dactionlabs.com:
   - `staging` and `adminer.staging` → **staging** public IP
   - `app` → **production** public IP
   Confirm with `dig staging.dactionlabs.com +short` and `dig app.dactionlabs.com +short` before Traefik starts.

Idle Always Free VMs can be reclaimed if 7-day p95 CPU, network, and memory are all under 20%. PAYG while staying inside 2 OCPU / 12 GB is the $0 anti-reclaim path; this guide does not provision paid shapes.

Outbound TCP **25** is blocked. Use a real SMTP provider or OCI Email Delivery. From-address should be `@dactionlabs.com` (SPF/DKIM at the DNS host).

## 2. Bootstrap each VM

Run this on **staging and production** (swap is required at 6 GB):

```bash
# Oracle's image REJECTS every other port at rule 5. Insert above that rule.
sudo iptables -I INPUT 5 -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 5 -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || true

sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Docker Engine: https://docs.docker.com/engine/install/ubuntu/
sudo adduser deploy
sudo usermod -aG docker deploy
```

As `deploy`, clone the public repo (not a shallow clone):

```bash
sudo -u deploy -H git clone https://github.com/<org>/<repo>.git /home/deploy/actionable-ai
```

Create a **separate** SSH deploy key on each VM:

```bash
sudo -u deploy -H ssh-keygen -t ed25519 -f /home/deploy/.ssh/a2i_deploy -N ""
sudo -u deploy -H sh -c 'cat /home/deploy/.ssh/a2i_deploy.pub >> /home/deploy/.ssh/authorized_keys'
```

Keep that VM’s `/home/deploy/.ssh/a2i_deploy` for that GitHub Environment’s `SSH_PRIVATE_KEY`. Capture host keys **per IP**:

```bash
ssh-keyscan -t ed25519,rsa <PUBLIC_IP>
```

That output is that Environment’s `SSH_KNOWN_HOSTS`. Disable password SSH (`PasswordAuthentication no`).

## 3. GitHub Environments

Create Environments **`staging`** and **`production`**. Each Environment points at **its own VM**.

Variables (different values per Environment):

- `DOMAIN` — `staging.dactionlabs.com` or `app.dactionlabs.com`
- `STACK_NAME` — `a2i-staging` or `a2i-prod`
- `SSH_HOST` — that VM’s public IPv4
- `SSH_USER` — `deploy`
- `DEPLOY_PATH` — `/home/deploy/actionable-ai`
- `PROJECT_NAME` — `Actionable AI`
- `FIRST_SUPERUSER` — e.g. `ops@dactionlabs.com`
- Optional: `SMTP_HOST`, `SMTP_USER`, `EMAILS_FROM_EMAIL`, `SENTRY_DSN`, `LETSENCRYPT_EMAIL`, `WEB_CONCURRENCY` (keep **1**), `CHAT_MODEL` (default `gemini-3.5-flash-lite`)

Secrets (unique per environment — never copy staging into production):

- `SSH_PRIVATE_KEY` — that VM’s `a2i_deploy`
- `SSH_KNOWN_HOSTS` — `ssh-keyscan` for that VM
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `FIRST_SUPERUSER_PASSWORD`
- Optional: `SMTP_PASSWORD`
- `GEMINI_API_KEY` — embeddings and chat. Use a separate key per environment.

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Do not set `FASTAPI_ENV=development` on either server.

## 4. Branches and first staging deploy

1. Create `develop` from current `master` on GitHub and make **`develop` the default branch** so new PRs target staging.
2. Protect `develop` and `master`: required PRs + required CI.
3. Protect `master` so only PRs labeled `release` are merged.
4. After this repo change is on `develop` (or you have checked that SHA out on the **staging** VM), run **Actions → Deploy with Docker Compose → staging**.

Smoke:

- `https://staging.dactionlabs.com/api/v1/utils/health-check/`
- Login with `FIRST_SUPERUSER`
- `https://adminer.staging.dactionlabs.com` (staging only)

Later merges to `develop` deploy the staging VM automatically.

## 5. First production deploy

Staging must already be healthy. Bootstrap the **production** VM the same way, with its own secrets and DNS.

1. Actions → **Prepare Release** (`patch` / `minor` / `major`). That freezes `## Latest Changes` in `release-notes.md`, bumps `backend/pyproject.toml`, and opens a PR into `master` labeled `release`.
2. Review the notes. Merge the PR.
3. Production deploys to `https://app.dactionlabs.com`. A GitHub **draft** Release is created from the same notes; publish it when you want it public.

`Prepare Release` checkouts `develop`. Keep Latest Changes non-empty (the script refuses an empty section). Until a `latest-changes` workflow is added, add bullets under `## Latest Changes` in the same PRs that land on `develop`.

## Compose on a server

Never use `compose.override.yml` on a VM. Each VM runs one stack (`compose.yml` + `compose.deploy.yml`). Traefik in that stack owns 80/443.

```bash
export STACK_NAME=a2i-staging   # a2i-prod on the production VM
export DOMAIN=staging.dactionlabs.com
export COMPOSE_PROJECT_NAME="$STACK_NAME"
export COMPOSE_PROFILES=adminer  # staging VM only; omit on production
docker compose -f compose.yml -f compose.deploy.yml build
docker compose -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
docker compose -f compose.yml -f compose.deploy.yml up -d
```

## Landmines

- Ampere Always Free is often out of capacity; two 1-OCPU instances can be harder to place than one 2-OCPU instance.
- Let’s Encrypt fails if DNS does not already point at **that** VM, or if Traefik flaps (rate limits).
- A timeout on ports 80 and 443 with SSH still working means the subnet security list is missing those ports, or the VM `iptables` ACCEPT rules sit below the REJECT rule. `sudo iptables -L INPUT --line-numbers` should show 80 and 443 before REJECT.
- ARM `compose build` on 6 GB needs the 4 GB swap. Prune unused Docker images so the 80 GB boot volume does not fill. That disk also holds original uploads (10 MB cap). Leave room for the OS, images, and Postgres.
- The database image is `pgvector/pgvector:pg18`, not stock Postgres. An existing Postgres 18 data volume can stay; recreate the container before migrating so `CREATE EXTENSION vector` succeeds.
- Five Always Free volume backups + 20 GB Object Storage are for the **prod database dump**, not for application uploads. Copy the upload directory off-box before the first real client. Staging may be wiped.
- Staging’s Docker socket cannot reach production. Still never put production secrets on the staging Environment.
