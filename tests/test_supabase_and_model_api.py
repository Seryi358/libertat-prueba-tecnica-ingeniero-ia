from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from libertat_webinar import db, llm
from libertat_webinar.config import Settings
from libertat_webinar.schemas import GeneratedContent, QuizQuestion, RegistrationInput


class _Response:
    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _settings(**overrides) -> Settings:
    values = {
        "app_env": "test",
        "app_base_url": "http://testserver",
        "database_path": Path("data/test.sqlite3"),
        "ollama_url": "http://127.0.0.1:11434",
        "ollama_model": "llama3.1",
        "ollama_enabled": False,
        "smtp_enabled": False,
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "smtp_from": "educacion@libertat.local",
        "gmail_client_id": "",
        "gmail_client_secret": "",
        "gmail_refresh_token": "",
        "gmail_from": "educacion@libertat.local",
        "notification_channels": ("email",),
        "slack_webhook_url": "",
        "whatsapp_webhook_url": "",
        "evolution_api_url": "",
        "evolution_api_key": "",
        "evolution_instance": "",
        "whatsapp_graph_api_version": "v23.0",
        "whatsapp_phone_number_id": "",
        "whatsapp_access_token": "",
        "whatsapp_default_to": "",
    }
    values.update(overrides)
    return Settings(**values)


def test_registration_syncs_to_supabase_when_enabled(tmp_path, monkeypatch) -> None:
    captured: list[dict] = []

    def fake_urlopen(request, timeout=0):
        captured.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "data": json.loads(request.data.decode("utf-8")),
                "apikey": request.headers["Apikey"],
            }
        )
        return _Response()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        db,
        "settings",
        _settings(
            database_path=Path("data/test.sqlite3"),
            supabase_sync_enabled=True,
            supabase_url="https://project.supabase.co",
            supabase_service_key="server-key",
        ),
    )
    monkeypatch.setattr(db.urllib.request, "urlopen", fake_urlopen)
    db.init_db()

    content = GeneratedContent(
        resumen="Resumen",
        quiz=[
            QuizQuestion(pregunta="P1", opciones=["A", "B", "C"], respuesta_correcta=0),
            QuizQuestion(pregunta="P2", opciones=["A", "B", "C"], respuesta_correcta=1),
            QuizQuestion(pregunta="P3", opciones=["A", "B", "C"], respuesta_correcta=2),
        ],
    )
    db.create_registration(
        "registro-1",
        RegistrationInput(
            nombre="Sergio",
            email="sergio@example.com",
            telefono="+573001234567",
            tema_webinar="Presupuesto",
            fecha_asistencia=date(2026, 5, 23),
        ),
        content,
    )
    db.update_result("registro-1", "aprobado", 100, Path("data/constancias/demo.pdf"))

    assert captured[0]["url"] == "https://project.supabase.co/rest/v1/registros?on_conflict=id"
    assert captured[0]["method"] == "POST"
    assert captured[0]["data"]["id"] == "registro-1"
    assert captured[0]["data"]["quiz_json"]["quiz"][0]["respuesta_correcta"] == 0
    assert captured[1]["url"] == "https://project.supabase.co/rest/v1/registros?id=eq.registro-1"
    assert captured[1]["method"] == "PATCH"
    assert captured[1]["data"]["estado"] == "aprobado"


def test_model_api_generation_uses_structured_json(monkeypatch) -> None:
    payload = {
        "output": [
            {
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(
                            {
                                "resumen": "Resumen breve",
                                "quiz": [
                                    {"pregunta": "P1", "opciones": ["A", "B", "C"], "respuesta_correcta": 0},
                                    {"pregunta": "P2", "opciones": ["A", "B", "C"], "respuesta_correcta": 1},
                                    {"pregunta": "P3", "opciones": ["A", "B", "C"], "respuesta_correcta": 2},
                                ],
                            }
                        ),
                    }
                ]
            }
        ]
    }
    captured: dict = {}

    def fake_urlopen(request, timeout=0):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _Response(payload)

    monkeypatch.setattr(
        llm,
        "settings",
        _settings(
            model_api_enabled=True,
            model_api_url="https://model.example.com/v1/responses",
            model_api_key="model-key",
            model_api_model="fast-model",
        ),
    )
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)

    content = llm.generate_content("Presupuesto")

    assert captured["url"] == "https://model.example.com/v1/responses"
    assert captured["body"]["model"] == "fast-model"
    assert content.resumen == "Resumen breve"
    assert len(content.quiz) == 3
