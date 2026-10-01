import pytest

from tests.configure import database_url_for_tests


def test_explicit_test_database_url_must_end_with_test_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_DATABASE_URL", "postgresql://postgres:changethis@localhost:5433/app"
    )
    with pytest.raises(RuntimeError, match="ending in '_test'"):
        database_url_for_tests()


def test_explicit_test_database_url_with_test_suffix_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:changethis@localhost:5433/app_test",
    )
    url, maintenance_db = database_url_for_tests()
    assert url.endswith("/app_test")
    assert maintenance_db == "postgres"
