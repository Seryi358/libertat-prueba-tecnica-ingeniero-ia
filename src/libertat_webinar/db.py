from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .config import settings
from .schemas import GeneratedContent, RegistrationInput


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO registros (
                id, nombre, email, tema_webinar, fecha_asistencia, resumen, quiz_json,
                estado, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', ?, ?)
            """,
            (
                registration_id,
                data.nombre,
                data.email,
                data.tema_webinar,
                data.fecha_asistencia.isoformat(),
                content.resumen,
                content.model_dump_json(),
                _now_iso(),
                _now_iso(),
            ),
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
                _now_iso(),
                registration_id,
            ),
        )


def log_notification(
    registration_id: str,
    channel: str,
    destination: str,
    status: str,
    detail: str | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO notificaciones (registro_id, canal, destino, estado, detalle, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (registration_id, channel, destination, status, detail, _now_iso()),
        )
