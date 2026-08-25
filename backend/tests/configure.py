"""Point pytest at a dedicated database before the app is imported.

Default: same DATABASE_URL with the database name suffixed `_test`
(for example `app` → `app_test`). Override with TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
_ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
_ENV_REF = re.compile(r"\$\{([^}]+)\}")
_DB_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _expand_env_refs(value: str) -> str:
    return _ENV_REF.sub(
        lambda match: os.environ.get(match.group(1), match.group(0)), value
    )


def _libpq_url(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def _require_test_database_name(name: str) -> None:
    if not name.endswith("_test"):
        raise RuntimeError(
            f"Refusing to run pytest against database {name!r}; "
            "use a database name ending in '_test'"
        )


def database_url_for_tests() -> tuple[str, str]:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        url = _expand_env_refs(explicit)
        parsed = urlparse(_libpq_url(url))
        name = (parsed.path or "/app").lstrip("/").split("/")[0] or "app"
        _require_test_database_name(name)
        return urlunparse(parsed._replace(path=f"/{name}")), "postgres"
    url = _expand_env_refs(os.environ.get("DATABASE_URL", ""))
    if not url:
        raise RuntimeError("DATABASE_URL or TEST_DATABASE_URL must be set for pytest")
    parsed = urlparse(_libpq_url(url))
    name = (parsed.path or "/app").lstrip("/").split("/")[0]
    if not name:
        name = "app"
    if name.endswith("_test"):
        return urlunparse(parsed._replace(path=f"/{name}")), "postgres"
    test_url = urlunparse(parsed._replace(path=f"/{name}_test"))
    return test_url, name


def _ensure_database(url: str, *, maintenance_db: str) -> None:
    parsed = urlparse(_libpq_url(url))
    dbname = (parsed.path or "").lstrip("/").split("/")[0]
    if not _DB_NAME.fullmatch(dbname):
        raise RuntimeError(f"Refusing to create database with name {dbname!r}")
    if not _DB_NAME.fullmatch(maintenance_db):
        raise RuntimeError(f"Refusing to use maintenance database {maintenance_db!r}")
    admin_url = urlunparse(parsed._replace(path=f"/{maintenance_db}"))
    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if cur.fetchone() is None:
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname))
                )


def _upgrade_schema() -> None:
    config = Config(str(_ALEMBIC_INI))
    command.upgrade(config, "head")


_load_dotenv(_ENV_FILE)
_TEST_DATABASE_URL, _MAINTENANCE_DB = database_url_for_tests()
os.environ["DATABASE_URL"] = _TEST_DATABASE_URL
os.environ.setdefault("FASTAPI_ENV", "development")
_ensure_database(_TEST_DATABASE_URL, maintenance_db=_MAINTENANCE_DB)
_upgrade_schema()
