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
        notification_channels=channels,
        slack_webhook_url="",
        whatsapp_webhook_url="",
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
