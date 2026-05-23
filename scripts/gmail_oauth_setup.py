from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request


AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/gmail.send"


def build_auth_url(client_id: str, redirect_uri: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code(client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
    payload = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara OAuth de Gmail API para envio de correos.")
    parser.add_argument("action", choices=["url", "exchange"])
    parser.add_argument("--client-id", default=os.getenv("GMAIL_CLIENT_ID", ""))
    parser.add_argument("--client-secret", default=os.getenv("GMAIL_CLIENT_SECRET", ""))
    parser.add_argument("--redirect-uri", default=os.getenv("GMAIL_REDIRECT_URI", "http://127.0.0.1:8765/oauth2callback"))
    parser.add_argument("--code", default=os.getenv("GMAIL_AUTH_CODE", ""))
    args = parser.parse_args()

    if not args.client_id:
        raise SystemExit("Falta GMAIL_CLIENT_ID o --client-id.")

    if args.action == "url":
        print(build_auth_url(args.client_id, args.redirect_uri))
        return

    if not args.client_secret:
        raise SystemExit("Falta GMAIL_CLIENT_SECRET o --client-secret.")
    if not args.code:
        raise SystemExit("Falta GMAIL_AUTH_CODE o --code.")

    token = exchange_code(args.client_id, args.client_secret, args.redirect_uri, args.code)
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise SystemExit("Google no devolvio refresh_token. Repite con prompt=consent y access_type=offline.")
    print("GMAIL_REFRESH_TOKEN=" + refresh_token)


if __name__ == "__main__":
    main()
