from fastapi.testclient import TestClient

from libertat_webinar.app import app


def test_index_page_renders() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Registro de webinar financiero" in response.text
    assert "/static/libertat-logo.jpeg" in response.text


def test_static_logo_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/static/libertat-logo.jpeg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 1000
