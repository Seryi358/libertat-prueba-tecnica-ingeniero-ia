from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
import smtplib

from .config import settings
from .db import log_notification


OUTBOX_DIR = Path("data/outbox")


def _build_message(
    recipient: str,
    name: str,
    summary: str,
    status: str,
    score: float,
    certificate_path: Path | None,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = "Resultado de tu webinar de educacion financiera"
    certificate_note = (
        f"\nTu constancia fue generada correctamente: {certificate_path}\n"
        if certificate_path
        else "\nEn esta ocasion no se genero constancia porque el puntaje no supero el umbral.\n"
    )
    body = (
        f"Hola {name},\n\n"
        "Gracias por participar en el webinar.\n\n"
        f"Resumen personalizado:\n{summary}\n\n"
        f"Resultado del quiz: {status.upper()} con puntaje de {score:.0f}%.\n"
        f"{certificate_note}\n"
        "Equipo Libertat\n"
    )
    message.set_content(body)
    return message


def send_result_notification(
    registration_id: str,
    recipient: str,
    name: str,
    summary: str,
    status: str,
    score: float,
    certificate_path: Path | None,
) -> str:
    """Envia email real si SMTP esta configurado; si no, guarda evidencia local."""
    message = _build_message(recipient, name, summary, status, score, certificate_path)

    if settings.smtp_enabled:
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
            log_notification(registration_id, "email", recipient, "enviado", "SMTP")
            return "enviado"
        except smtplib.SMTPException as exc:
            log_notification(registration_id, "email", recipient, "error", str(exc))
            raise

    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTBOX_DIR / f"{registration_id}.eml"
    output.write_text(message.as_string(), encoding="utf-8")
    log_notification(registration_id, "email", recipient, "simulado", str(output))
    return str(output)
