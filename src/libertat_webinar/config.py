from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "si", "sí"}


def _as_list(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    channels = tuple(item.strip().lower() for item in value.split(",") if item.strip())
    return channels or default


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_base_url: str
    database_path: Path
    ollama_url: str
    ollama_model: str
    ollama_enabled: bool
    smtp_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    notification_channels: tuple[str, ...]
    slack_webhook_url: str
    whatsapp_webhook_url: str
    whatsapp_graph_api_version: str
    whatsapp_phone_number_id: str
    whatsapp_access_token: str
    whatsapp_default_to: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_env=os.getenv("APP_ENV", "local"),
            app_base_url=os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
            database_path=Path(os.getenv("DATABASE_PATH", "data/libertat_webinar.sqlite3")),
            ollama_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            ollama_enabled=_as_bool(os.getenv("OLLAMA_ENABLED"), False),
            smtp_enabled=_as_bool(os.getenv("SMTP_ENABLED"), False),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from=os.getenv("SMTP_FROM", "educacion@libertat.local"),
            notification_channels=_as_list(os.getenv("NOTIFICATION_CHANNELS"), ("email",)),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
            whatsapp_webhook_url=os.getenv("WHATSAPP_WEBHOOK_URL", ""),
            whatsapp_graph_api_version=os.getenv("WHATSAPP_GRAPH_API_VERSION", "v23.0"),
            whatsapp_phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
            whatsapp_access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
            whatsapp_default_to=os.getenv("WHATSAPP_DEFAULT_TO", ""),
        )


settings = Settings.from_env()
