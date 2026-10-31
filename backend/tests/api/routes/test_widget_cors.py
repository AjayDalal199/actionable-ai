from fastapi.testclient import TestClient

from app.core.config import settings


def test_dashboard_origin_is_not_repeated_on_widget_responses(
    client: TestClient,
) -> None:
    """The dashboard CORS middleware also matches this origin. One header must remain."""
    origin = settings.FRONTEND_HOST
    response = client.get("/widget.js", headers={"Origin": origin})
    assert response.headers.get_list("access-control-allow-origin") == [origin]
    assert "access-control-allow-credentials" not in response.headers


def test_customer_origin_is_reflected_once(client: TestClient) -> None:
    origin = "https://shop.example"
    response = client.get("/widget.js", headers={"Origin": origin})
    assert response.headers.get_list("access-control-allow-origin") == [origin]
    assert "access-control-allow-credentials" not in response.headers
