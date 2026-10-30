import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, settings


def test_health_check(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert response.status_code == 200
    assert response.json() is True


def test_health_check_fails_when_redis_is_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:1/0")
    response = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert response.status_code == 503
    assert response.json()["detail"] == "Redis unavailable"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "SECRET_KEY": "not-the-default-secret",
        "PROJECT_NAME": "Actionable AI",
        "DATABASE_URL": "postgresql://postgres:not-the-default@localhost/app",
        "FIRST_SUPERUSER": "admin@example.com",
        "FIRST_SUPERUSER_PASSWORD": "not-the-default",
        "FASTAPI_ENV": None,
        "REDIS_URL": None,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_redis_url_is_required_outside_development() -> None:
    with pytest.raises(ValidationError, match="REDIS_URL"):
        _settings()


def test_development_defaults_redis_url() -> None:
    configured = _settings(FASTAPI_ENV="development")
    assert str(configured.REDIS_URL) == "redis://localhost:6380/0"
