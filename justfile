# List all available commands (default target)
default:
    @just --list --unsorted

# Install all frontend and backend dependencies
setup:
    /home/azzu199/.bun/bin/bun install
    cd backend && uv sync

# Start only the database and mailcatcher services in Docker
db:
    docker compose up -d db mailcatcher

# Run database migrations and prepare the database
prestart: db
    cd backend && uv run bash scripts/prestart.sh

# Run the FastAPI backend development server
backend:
    cd backend && uv run fastapi dev

# Run the Vite frontend development server
frontend:
    bun run dev

[parallel]
_dev-servers: backend frontend

# Start the local development environment (Docker DB + local servers)
dev: prestart _dev-servers


# Compile the frontend production bundle
build-frontend:
    /home/azzu199/.bun/bin/bun run --filter frontend build

# Compile the frontend production bundle (alias)
build: build-frontend

# Run built production app locally (FastAPI serving compiled frontend)
prod: build-frontend db prestart
    @echo "Starting production server locally..."
    cd backend && uv run fastapi run

# Run full stack in production mode using Docker Compose watch
compose-prod: build-frontend
    docker compose run --rm backend bash scripts/prestart.sh
    docker compose watch

# Deploy/Start production server with HTTPS (Traefik)
deploy:
    #!/usr/bin/env bash
    if [ -f .env.deploy ]; then
        echo "Using .env.deploy file for configuration..."
        docker compose --env-file .env.deploy -f compose.yml -f compose.deploy.yml build
        docker compose --env-file .env.deploy -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
        docker compose --env-file .env.deploy -f compose.yml -f compose.deploy.yml up -d
    else
        docker compose -f compose.yml -f compose.deploy.yml build
        docker compose -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
        docker compose -f compose.yml -f compose.deploy.yml up -d
    fi

# Stop Docker services
stop:
    docker compose down

# Stop Docker services and prune volumes (warning: deletes database data)
clean:
    docker compose down -v
