from pathlib import Path

from libertat_webinar import db
from libertat_webinar import notifier
from libertat_webinar.config import Settings


def _settings(channels: tuple[str, ...]) -> Settings:
    return Settings(
        app_env="test",
        app_base_url="http://testserver",
        database_path=Path("data/test.sqlite3"),
        ollama_url="http://127.0.0.1:11434",
        ollama_model="llama3.1",
        ollama_enabled=False,
        smtp_enabled=False,
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        smtp_from="educacion@libertat.local",
        gmail_client_id="",
        gmail_client_secret="",
        gmail_refresh_token="",
        gmail_from="educacion@libertat.local",
        notification_channels=channels,
        slack_webhook_url="",
        whatsapp_webhook_url="",
        evolution_api_url="",
        evolution_api_key="",
        evolution_instance="",
        whatsapp_graph_api_version="v23.0",
        whatsapp_phone_number_id="",
        whatsapp_access_token="",
        whatsapp_default_to="",
    )


def test_email_notification_writes_local_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(notifier, "settings", _settings(("email",)))
    db.init_db()

    result = notifier.send_result_notification(
        registration_id="registro-1",
        recipient="usuario@example.com",
        name="Sergio Alejandro Castellanos",
        summary="Resumen personalizado",
        status="aprobado",
        score=100,
        certificate_path=Path("data/constancias/constancia.pdf"),
    )

    assert result.startswith("email:simulado:")
    evidence = tmp_path / "data/outbox/registro-1_email.eml"
    assert evidence.exists()
    assert "Hola Sergio Alejandro Castellanos" in evidence.read_text(encoding="utf-8")


def test_email_uses_gmail_api_when_refresh_token_is_configured(tmp_path, monkeypatch) -> None:
    config = _settings(("email",))
    config = Settings(
        **{
            **config.__dict__,
            "gmail_client_id": "client-id",
            "gmail_client_secret": "client-secret",
            "gmail_refresh_token": "refresh-token",
            "gmail_from": "sender@example.com",
        }
    )
    captured: dict = {}

    def fake_send_gmail_api(registration_id: str, recipient: str, message) -> str:
        captured["registration_id"] = registration_id
        captured["recipient"] = recipient
        captured["from"] = message["From"]
        return "email:gmail_api:enviado:{}"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(notifier, "settings", config)
    monkeypatch.setattr(notifier, "_send_gmail_api", fake_send_gmail_api)
    db.init_db()

    result = notifier.send_result_notification(
        registration_id="registro-gmail",
        recipient="usuario@example.com",
        name="Sergio Alejandro Castellanos",
        summary="Resumen personalizado",
        status="aprobado",
        score=100,
        certificate_path=None,
    )

    assert result.startswith("email:gmail_api:enviado")
    assert captured == {
        "registration_id": "registro-gmail",
        "recipient": "usuario@example.com",
        "from": "sender@example.com",
    }


def test_slack_and_whatsapp_notifications_write_evidence_without_credentials(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(notifier, "settings", _settings(("slack", "whatsapp")))
    db.init_db()

    result = notifier.send_result_notification(
        registration_id="registro-2",
        recipient="usuario@example.com",
        name="Sergio Alejandro Castellanos",
        summary="Resumen personalizado",
        status="reprobado",
        score=60,
        certificate_path=None,
        phone="+573001234567",
    )

    assert "slack:simulado:" in result
    assert "whatsapp:simulado:" in result
    assert (tmp_path / "data/outbox/registro-2_slack.json").exists()
    whatsapp_payload = tmp_path / "data/outbox/registro-2_whatsapp.json"
    assert whatsapp_payload.exists()
    assert "+573001234567" in whatsapp_payload.read_text(encoding="utf-8")


def test_evolution_api_payload_is_sent_when_configured(tmp_path, monkeypatch) -> None:
    captured: dict = {}
    config = _settings(("whatsapp",))
    config = Settings(
        **{
            **config.__dict__,
            "evolution_api_url": "https://evolution.example.com",
            "evolution_api_key": "secret",
            "evolution_instance": "libertat",
        }
    )

    def fake_post_json(url: str, payload: dict, headers: dict[str, str] | None = None) -> None:
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(notifier, "settings", config)
    monkeypatch.setattr(notifier, "_post_json", fake_post_json)
    db.init_db()

    result = notifier.send_result_notification(
        registration_id="registro-3",
        recipient="usuario@example.com",
        name="Sergio Alejandro Castellanos",
        summary="Resumen personalizado",
        status="aprobado",
        score=100,
        certificate_path=None,
        phone="+573001234567",
    )

    assert result == "whatsapp:evolution:enviado"
    assert captured["url"] == "https://evolution.example.com/message/sendText/libertat"
    assert captured["payload"]["number"] == "573001234567"
    assert captured["headers"] == {"apikey": "secret"}
