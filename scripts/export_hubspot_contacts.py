from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


HUBSPOT_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"
PROPERTIES = ["firstname", "lastname", "email", "createdate"]


class HubSpotError(RuntimeError):
    """Error controlado al consumir HubSpot."""


def _request_contacts(token: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        HUBSPOT_SEARCH_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            retry_after = int(exc.headers.get("Retry-After", "5"))
            time.sleep(retry_after)
            return _request_contacts(token, payload)
        if exc.code in {400, 401, 500}:
            detail = exc.read().decode("utf-8", errors="replace")
            raise HubSpotError(f"HubSpot respondio {exc.code}: {detail}") from exc
        raise


def fetch_recent_contacts(token: str, days: int = 30) -> list[dict[str, str]]:
    """Obtiene contactos creados en los ultimos `days` dias con paginacion."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    after: str | None = None
    contacts: list[dict[str, str]] = []

    while True:
        payload: dict[str, Any] = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "createdate",
                            "operator": "GTE",
                            "value": since.isoformat(timespec="milliseconds"),
                        }
                    ]
                }
            ],
            "properties": PROPERTIES,
            "limit": 100,
        }
        if after:
            payload["after"] = after

        data = _request_contacts(token, payload)
        for item in data.get("results", []):
            props = item.get("properties", {})
            contacts.append({key: props.get(key, "") for key in PROPERTIES})

        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break

    return contacts


def export_csv(contacts: list[dict[str, str]], output: Path) -> None:
    """Escribe los contactos en CSV."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PROPERTIES)
        writer.writeheader()
        writer.writerows(contacts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="contactos_hubspot.csv")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    token = os.getenv("HUBSPOT_TOKEN")
    if not token:
        raise SystemExit("Define HUBSPOT_TOKEN antes de ejecutar el script.")

    contacts = fetch_recent_contacts(token=token, days=args.days)
    export_csv(contacts, Path(args.output))
    print(f"Contactos exportados: {len(contacts)}")


if __name__ == "__main__":
    main()
