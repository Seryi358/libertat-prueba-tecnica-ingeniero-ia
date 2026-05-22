from fastapi.testclient import TestClient

from libertat_webinar.app import app


def test_index_page_renders() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Registro de webinar financiero" in response.text
