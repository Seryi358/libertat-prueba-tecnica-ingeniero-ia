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
    gmail_client_id: str
    gmail_client_secret: str
    gmail_refresh_token: str
    gmail_from: str
    notification_channels: tuple[str, ...]
    slack_webhook_url: str
    whatsapp_webhook_url: str
    evolution_api_url: str
    evolution_api_key: str
    evolution_instance: str
    whatsapp_graph_api_version: str
    whatsapp_phone_number_id: str
    whatsapp_access_token: str
    whatsapp_default_to: str
    supabase_sync_enabled: bool = False
    supabase_url: str = ""
    supabase_service_key: str = ""
    model_api_enabled: bool = False
    model_api_url: str = ""
    model_api_key: str = ""
    model_api_model: str = ""

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
            gmail_client_id=os.getenv("GMAIL_CLIENT_ID", ""),
            gmail_client_secret=os.getenv("GMAIL_CLIENT_SECRET", ""),
            gmail_refresh_token=os.getenv("GMAIL_REFRESH_TOKEN", ""),
            gmail_from=os.getenv("GMAIL_FROM", os.getenv("SMTP_FROM", "educacion@libertat.local")),
            notification_channels=_as_list(os.getenv("NOTIFICATION_CHANNELS"), ("email",)),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
            whatsapp_webhook_url=os.getenv("WHATSAPP_WEBHOOK_URL", ""),
            evolution_api_url=os.getenv("EVOLUTION_API_URL", "").rstrip("/"),
            evolution_api_key=os.getenv("EVOLUTION_API_KEY", ""),
            evolution_instance=os.getenv("EVOLUTION_INSTANCE", ""),
            whatsapp_graph_api_version=os.getenv("WHATSAPP_GRAPH_API_VERSION", "v23.0"),
            whatsapp_phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
            whatsapp_access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
            whatsapp_default_to=os.getenv("WHATSAPP_DEFAULT_TO", ""),
            supabase_sync_enabled=_as_bool(os.getenv("SUPABASE_SYNC_ENABLED"), False),
            supabase_url=os.getenv("SUPABASE_URL", "").rstrip("/"),
            supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
            model_api_enabled=_as_bool(os.getenv("MODEL_API_ENABLED"), False),
            model_api_url=os.getenv("MODEL_API_URL", "").rstrip("/"),
            model_api_key=os.getenv("MODEL_API_KEY", ""),
            model_api_model=os.getenv("MODEL_API_MODEL", ""),
        )


settings = Settings.from_env()
