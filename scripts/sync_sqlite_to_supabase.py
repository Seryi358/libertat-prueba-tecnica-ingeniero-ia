from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def _post_json(url: str, key: str, payload: list[dict], *, on_conflict: str | None = None) -> None:
    target = url if on_conflict is None else f"{url}?on_conflict={urllib.parse.quote(on_conflict)}"
    request = urllib.request.Request(
        target,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30):
        return


def _rows(connection: sqlite3.Connection, table: str) -> list[dict]:
    connection.row_factory = sqlite3.Row
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table}").fetchall()]


def sync(database_path: Path, supabase_url: str, supabase_key: str) -> tuple[int, int]:
    with sqlite3.connect(database_path) as connection:
        registros = _rows(connection, "registros")
        notificaciones = _rows(connection, "notificaciones")

    for row in registros:
        row["quiz_json"] = json.loads(row["quiz_json"])

    base = supabase_url.rstrip("/")
    if registros:
        _post_json(f"{base}/rest/v1/registros", supabase_key, registros, on_conflict="id")
    if notificaciones:
        for row in notificaciones:
            row.pop("id", None)
        _post_json(f"{base}/rest/v1/notificaciones", supabase_key, notificaciones)
    return len(registros), len(notificaciones)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza SQLite local hacia Supabase.")
    parser.add_argument("--database", default=os.getenv("DATABASE_PATH", "data/libertat_webinar.sqlite3"))
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not supabase_url or not supabase_key:
        print("Faltan SUPABASE_URL y SUPABASE_SERVICE_KEY.", file=sys.stderr)
        return 2

    try:
        registros, notificaciones = sync(Path(args.database), supabase_url, supabase_key)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"Error HTTP de Supabase {exc.code}: {detail}", file=sys.stderr)
        return 1

    print(f"Sincronizados {registros} registros y {notificaciones} notificaciones.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
