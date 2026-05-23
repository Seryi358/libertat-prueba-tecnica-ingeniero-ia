from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
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


def listen_for_code(client_id: str, client_secret: str, redirect_uri: str) -> None:
    parsed_redirect = urllib.parse.urlparse(redirect_uri)
    if parsed_redirect.hostname not in {"127.0.0.1", "localhost"}:
        raise SystemExit("La accion listen requiere un redirect URI local.")

    class OAuthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            code = query.get("code", [""])[0]
            if not code:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"No se recibio codigo OAuth.")
                return
            try:
                token = exchange_code(client_id, client_secret, redirect_uri, code)
                refresh_token = token.get("refresh_token", "")
                if not refresh_token:
                    raise RuntimeError("Google no devolvio refresh_token.")
                print("GMAIL_REFRESH_TOKEN=" + refresh_token)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Autorizacion completada. Puedes cerrar esta pestana.")
            except Exception as exc:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(exc).encode("utf-8"))

        def log_message(self, format: str, *args) -> None:
            return

    port = parsed_redirect.port or 80
    server = HTTPServer((parsed_redirect.hostname or "127.0.0.1", port), OAuthHandler)
    print(build_auth_url(client_id, redirect_uri))
    print("Esperando autorizacion OAuth...")
    server.handle_request()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara OAuth de Gmail API para envio de correos.")
    parser.add_argument("action", choices=["url", "exchange", "listen"])
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
    if args.action == "listen":
        listen_for_code(args.client_id, args.client_secret, args.redirect_uri)
        return
    if not args.code:
        raise SystemExit("Falta GMAIL_AUTH_CODE o --code.")

    token = exchange_code(args.client_id, args.client_secret, args.redirect_uri, args.code)
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise SystemExit("Google no devolvio refresh_token. Repite con prompt=consent y access_type=offline.")
    print("GMAIL_REFRESH_TOKEN=" + refresh_token)


if __name__ == "__main__":
    main()
