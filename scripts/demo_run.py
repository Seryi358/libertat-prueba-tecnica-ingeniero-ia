from __future__ import annotations

from fastapi.testclient import TestClient

from libertat_webinar.app import app


def main() -> None:
    with TestClient(app) as client:
        registration = client.post(
            "/api/registros",
            json={
                "nombre": "Sergio Alejandro Castellanos",
                "email": "scastellanos@phinodia.com",
                "tema_webinar": "Manejo responsable del endeudamiento",
                "fecha_asistencia": "2026-05-22",
            },
        )
        registration.raise_for_status()
        registration_id = registration.json()["id"]

        evaluation = client.post(
            f"/api/registros/{registration_id}/evaluar",
            json={"respuestas": [0, 1, 2]},
        )
        evaluation.raise_for_status()
        print(evaluation.json())


if __name__ == "__main__":
    main()
