from __future__ import annotations

import json
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .config import settings
from .schemas import GeneratedContent, RegistrationInput


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _supabase_headers(prefer: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _supabase_enabled() -> bool:
    return bool(
        settings.supabase_sync_enabled
        and settings.supabase_url
        and settings.supabase_service_key
    )


def _post_supabase(table: str, payload: dict, *, on_conflict: str | None = None) -> None:
    if not _supabase_enabled():
        return

    query = f"?on_conflict={urllib.parse.quote(on_conflict)}" if on_conflict else ""
    request = urllib.request.Request(
        f"{settings.supabase_url}/rest/v1/{table}{query}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=_supabase_headers("resolution=merge-duplicates,return=minimal"),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15):
            return
    except (OSError, urllib.error.URLError, urllib.error.HTTPError):
        return


def _patch_supabase(table: str, filters: dict[str, str], payload: dict) -> None:
    if not _supabase_enabled():
        return

    query = "&".join(
        f"{urllib.parse.quote(key)}=eq.{urllib.parse.quote(value)}"
        for key, value in filters.items()
    )
    request = urllib.request.Request(
        f"{settings.supabase_url}/rest/v1/{table}?{query}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=_supabase_headers("return=minimal"),
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(request, timeout=15):
            return
    except (OSError, urllib.error.URLError, urllib.error.HTTPError):
        return


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registros (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL,
                telefono TEXT,
                tema_webinar TEXT NOT NULL,
                fecha_asistencia TEXT NOT NULL,
                resumen TEXT NOT NULL,
                quiz_json TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                puntaje REAL,
                constancia_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(registros)").fetchall()
        }
        if "telefono" not in columns:
            conn.execute("ALTER TABLE registros ADD COLUMN telefono TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registro_id TEXT NOT NULL,
                canal TEXT NOT NULL,
                destino TEXT NOT NULL,
                estado TEXT NOT NULL,
                detalle TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(registro_id) REFERENCES registros(id)
            )
            """
        )


def create_registration(registration_id: str, data: RegistrationInput, content: GeneratedContent) -> None:
    created_at = _now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO registros (
                id, nombre, email, telefono, tema_webinar, fecha_asistencia, resumen, quiz_json,
                estado, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pendiente', ?, ?)
            """,
            (
                registration_id,
                data.nombre,
                data.email,
                data.telefono,
                data.tema_webinar,
                data.fecha_asistencia.isoformat(),
                content.resumen,
                content.model_dump_json(),
                created_at,
                created_at,
            ),
        )
    _post_supabase(
        "registros",
        {
            "id": registration_id,
            "nombre": data.nombre,
            "email": str(data.email),
            "telefono": data.telefono,
            "tema_webinar": data.tema_webinar,
            "fecha_asistencia": data.fecha_asistencia.isoformat(),
            "resumen": content.resumen,
            "quiz_json": content.model_dump(mode="json"),
            "estado": "pendiente",
            "puntaje": None,
            "constancia_path": None,
            "created_at": created_at,
            "updated_at": created_at,
        },
        on_conflict="id",
    )


def get_registration(registration_id: str) -> sqlite3.Row | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM registros WHERE id = ?", (registration_id,)).fetchone()
    return row


def list_registrations() -> list[sqlite3.Row]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM registros ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    return rows


def content_from_row(row: sqlite3.Row) -> GeneratedContent:
    return GeneratedContent.model_validate(json.loads(row["quiz_json"]))


def update_result(registration_id: str, status: str, score: float, certificate_path: Path | None) -> None:
    updated_at = _now_iso()
    with connect() as conn:
        conn.execute(
            """
            UPDATE registros
            SET estado = ?, puntaje = ?, constancia_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                score,
                str(certificate_path) if certificate_path else None,
                updated_at,
                registration_id,
            ),
        )
    _patch_supabase(
        "registros",
        {"id": registration_id},
        {
            "estado": status,
            "puntaje": score,
            "constancia_path": str(certificate_path) if certificate_path else None,
            "updated_at": updated_at,
        },
    )


def log_notification(
    registration_id: str,
    channel: str,
    destination: str,
    status: str,
    detail: str | None = None,
) -> None:
    created_at = _now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO notificaciones (registro_id, canal, destino, estado, detalle, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (registration_id, channel, destination, status, detail, created_at),
        )
    _post_supabase(
        "notificaciones",
        {
            "registro_id": registration_id,
            "canal": channel,
            "destino": destination,
            "estado": status,
            "detalle": detail,
            "created_at": created_at,
        },
    )
