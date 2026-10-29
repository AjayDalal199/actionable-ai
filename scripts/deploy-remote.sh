#!/usr/bin/env bash
# Run on the Ampere VM. Expects env already exported (see scripts/ci-deploy-ssh.sh).
set -euo pipefail

case "${STACK_NAME:?STACK_NAME is required}" in
  a2i-staging | a2i-prod) ;;
  *)
    echo "STACK_NAME must be a2i-staging or a2i-prod, got: ${STACK_NAME}" >&2
    exit 1
    ;;
esac

if [[ ! "${DEPLOY_SHA:?DEPLOY_SHA is required}" =~ ^[0-9a-f]{7,40}$ ]]; then
  echo "DEPLOY_SHA must be a git SHA, got: ${DEPLOY_SHA}" >&2
  exit 1
fi

REPO_DIR="${DEPLOY_PATH:?DEPLOY_PATH is required}"
cd "${REPO_DIR}"

git fetch --prune origin "${DEPLOY_SHA}"
git checkout --detach "${DEPLOY_SHA}"

export COMPOSE_PROJECT_NAME="${STACK_NAME}"
export LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-ops@dactionlabs.com}"
export WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"

if [[ "${STACK_NAME}" == "a2i-staging" ]]; then
  export COMPOSE_PROFILES=adminer
else
  unset COMPOSE_PROFILES || true
fi

docker compose -f compose.yml -f compose.deploy.yml build
docker compose -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
docker compose -f compose.yml -f compose.deploy.yml up -d
docker compose -f compose.yml -f compose.deploy.yml ps
