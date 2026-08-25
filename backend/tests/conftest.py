from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

import tests.configure as _configure_test_database  # noqa: F401
from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, User, Workspace, WorkspaceMembership
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


def pytest_report_header() -> str:
    return f"test database: {str(settings.DATABASE_URL).rsplit('/', 1)[-1]}"


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(Item)
        session.execute(statement)
        statement = delete(WorkspaceMembership)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        statement = delete(Workspace)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
