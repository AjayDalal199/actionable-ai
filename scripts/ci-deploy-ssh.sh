#!/usr/bin/env bash
# GitHub Actions helper: SSH into the OCI VM and run scripts/deploy-remote.sh.
# Secrets are passed as env vars; they are never printed.
set -euo pipefail

if [[ ! "${DEPLOY_SHA:?}" =~ ^[0-9a-f]{7,40}$ ]]; then
  echo "DEPLOY_SHA must be a git SHA" >&2
  exit 1
fi

case "${STACK_NAME:?}" in
  a2i-staging | a2i-prod) ;;
  *)
    echo "STACK_NAME must be a2i-staging or a2i-prod" >&2
    exit 1
    ;;
esac

: "${SSH_HOST:?}"
: "${SSH_PRIVATE_KEY:?}"
: "${SSH_KNOWN_HOSTS:?}"
SSH_USER="${SSH_USER:-deploy}"
DEPLOY_PATH="${DEPLOY_PATH:-/home/deploy/actionable-ai}"
: "${DOMAIN:?}"
: "${PROJECT_NAME:?}"
: "${SECRET_KEY:?}"
: "${FIRST_SUPERUSER:?}"
: "${FIRST_SUPERUSER_PASSWORD:?}"
: "${POSTGRES_PASSWORD:?}"

umask 077
install -m 700 -d "${HOME}/.ssh"
printf '%s\n' "${SSH_KNOWN_HOSTS}" > "${HOME}/.ssh/known_hosts"
printf '%s\n' "${SSH_PRIVATE_KEY}" > "${HOME}/.ssh/id_ed25519"
chmod 600 "${HOME}/.ssh/known_hosts" "${HOME}/.ssh/id_ed25519"

ssh_cmd=(ssh -i "${HOME}/.ssh/id_ed25519" -o IdentitiesOnly=yes -o BatchMode=yes)

remote_env="/tmp/a2i-deploy.${STACK_NAME}.env"

python3 -c '
import os, shlex
keys = [
    "STACK_NAME",
    "DEPLOY_SHA",
    "DEPLOY_PATH",
    "DOMAIN",
    "PROJECT_NAME",
    "SECRET_KEY",
    "FIRST_SUPERUSER",
    "FIRST_SUPERUSER_PASSWORD",
    "POSTGRES_PASSWORD",
    "SMTP_HOST",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "EMAILS_FROM_EMAIL",
    "SENTRY_DSN",
    "WEB_CONCURRENCY",
    "LETSENCRYPT_EMAIL",
]
for key in keys:
    print(f"{key}={shlex.quote(os.environ.get(key, ''))}")
' | "${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" "umask 077 && cat > '${remote_env}'"

"${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" \
  "set -euo pipefail; set -a; . '${remote_env}'; set +a; rm -f '${remote_env}'; bash '${DEPLOY_PATH}/scripts/deploy-remote.sh'"
