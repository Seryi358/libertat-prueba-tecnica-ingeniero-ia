from __future__ import annotations

import json
from email.message import EmailMessage
from pathlib import Path
import smtplib
import urllib.error
import urllib.request

from .config import settings
from .db import log_notification


OUTBOX_DIR = Path("data/outbox")


def _notification_text(
    name: str,
    summary: str,
    status: str,
    score: float,
    certificate_path: Path | None,
) -> str:
    certificate_note = (
        f"\nTu constancia fue generada correctamente: {certificate_path}\n"
        if certificate_path
        else "\nEn esta ocasion no se genero constancia porque el puntaje no supero el umbral.\n"
    )
    return (
        f"Hola {name},\n\n"
        "Gracias por participar en el webinar.\n\n"
        f"Resumen personalizado:\n{summary}\n\n"
        f"Resultado del quiz: {status.upper()} con puntaje de {score:.0f}%.\n"
        f"{certificate_note}\n"
        "Equipo Libertat\n"
    )


def _build_email_message(
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
    message.set_content(_notification_text(name, summary, status, score, certificate_path))
    return message


def _save_outbox(registration_id: str, channel: str, suffix: str, content: str) -> Path:
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTBOX_DIR / f"{registration_id}_{channel}.{suffix}"
    output.write_text(content, encoding="utf-8")
    return output


def _post_json(url: str, payload: dict, headers: dict[str, str] | None = None) -> None:
    data = json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = urllib.request.Request(url, data=data, headers=request_headers, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status >= 400:
            raise urllib.error.HTTPError(url, response.status, "HTTP error", response.headers, None)


def _send_email(
    registration_id: str,
    recipient: str,
    name: str,
    summary: str,
    status: str,
    score: float,
    certificate_path: Path | None,
) -> str:
    message = _build_email_message(recipient, name, summary, status, score, certificate_path)

    if settings.smtp_enabled and settings.smtp_host:
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
            log_notification(registration_id, "email", recipient, "enviado", "SMTP")
            return "email:enviado"
        except (OSError, smtplib.SMTPException) as exc:
            output = _save_outbox(registration_id, "email_error", "eml", message.as_string())
            log_notification(registration_id, "email", recipient, "error", str(exc))
            return f"email:error:{output}"

    output = _save_outbox(registration_id, "email", "eml", message.as_string())
    log_notification(registration_id, "email", recipient, "simulado", str(output))
    return f"email:simulado:{output}"


def _send_slack(
    registration_id: str,
    name: str,
    summary: str,
    status: str,
    score: float,
    certificate_path: Path | None,
) -> str:
    text = _notification_text(name, summary, status, score, certificate_path)
    payload = {
        "text": f"Resultado webinar Libertat - {name}",
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Resultado webinar Libertat*\n{text}"},
            },
        ],
    }

    if settings.slack_webhook_url:
        try:
            _post_json(settings.slack_webhook_url, payload)
            log_notification(registration_id, "slack", "webhook", "enviado", "Slack Incoming Webhook")
            return "slack:enviado"
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            output = _save_outbox(
                registration_id,
                "slack_error",
                "json",
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
            log_notification(registration_id, "slack", "webhook", "error", str(exc))
            return f"slack:error:{output}"

    output = _save_outbox(
        registration_id,
        "slack",
        "json",
        json.dumps(payload, ensure_ascii=False, indent=2),
    )
    log_notification(registration_id, "slack", "webhook", "simulado", str(output))
    return f"slack:simulado:{output}"


def _send_whatsapp(
    registration_id: str,
    name: str,
    phone: str | None,
    summary: str,
    status: str,
    score: float,
    certificate_path: Path | None,
) -> str:
    destination = phone or settings.whatsapp_default_to
    text = _notification_text(name, summary, status, score, certificate_path)
    payload = {
        "to": destination,
        "name": name,
        "message": text,
        "channel": "whatsapp",
    }

    if settings.whatsapp_webhook_url and destination:
        try:
            _post_json(settings.whatsapp_webhook_url, payload)
            log_notification(registration_id, "whatsapp", destination, "enviado", "Webhook WhatsApp")
            return "whatsapp:enviado"
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            output = _save_outbox(
                registration_id,
                "whatsapp_error",
                "json",
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
            log_notification(registration_id, "whatsapp", destination, "error", str(exc))
            return f"whatsapp:error:{output}"

    if settings.whatsapp_phone_number_id and settings.whatsapp_access_token and destination:
        cloud_payload = {
            "messaging_product": "whatsapp",
            "to": destination.lstrip("+"),
            "type": "text",
            "text": {"body": text},
        }
        api_version = settings.whatsapp_graph_api_version.strip("/")
        url = f"https://graph.facebook.com/{api_version}/{settings.whatsapp_phone_number_id}/messages"
        try:
            _post_json(url, cloud_payload, {"Authorization": f"Bearer {settings.whatsapp_access_token}"})
            log_notification(registration_id, "whatsapp", destination, "enviado", "WhatsApp Cloud API")
            return "whatsapp:enviado"
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            output = _save_outbox(
                registration_id,
                "whatsapp_error",
                "json",
                json.dumps(cloud_payload, ensure_ascii=False, indent=2),
            )
            log_notification(registration_id, "whatsapp", destination, "error", str(exc))
            return f"whatsapp:error:{output}"

    output = _save_outbox(
        registration_id,
        "whatsapp",
        "json",
        json.dumps(payload, ensure_ascii=False, indent=2),
    )
    log_notification(registration_id, "whatsapp", destination or "sin_destino", "simulado", str(output))
    return f"whatsapp:simulado:{output}"


def send_result_notification(
    registration_id: str,
    recipient: str,
    name: str,
    summary: str,
    status: str,
    score: float,
    certificate_path: Path | None,
    phone: str | None = None,
) -> str:
    """Envia notificaciones por los canales configurados y deja evidencia local si faltan credenciales."""
    results: list[str] = []
    for channel in settings.notification_channels:
        if channel == "email":
            results.append(_send_email(registration_id, recipient, name, summary, status, score, certificate_path))
        elif channel == "slack":
            results.append(_send_slack(registration_id, name, summary, status, score, certificate_path))
        elif channel == "whatsapp":
            results.append(_send_whatsapp(registration_id, name, phone, summary, status, score, certificate_path))
        else:
            log_notification(registration_id, channel, "", "omitido", "Canal no soportado")
            results.append(f"{channel}:omitido")
    return "; ".join(results)
