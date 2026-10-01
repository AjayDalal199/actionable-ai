from app.core.config import settings


def test_pytest_uses_dedicated_database() -> None:
    name = str(settings.DATABASE_URL).rsplit("/", 1)[-1]
    assert name.endswith("_test")
