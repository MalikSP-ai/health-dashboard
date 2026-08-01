"""
One-time Strava OAuth setup.

Opens the Strava authorization page in your browser, listens on
http://localhost:8721/callback for the redirect, exchanges the returned
code for a refresh token, and prints the values to put in your .env file.

Prerequisites:
1. Create an API app at https://www.strava.com/settings/api
   - Set "Authorization Callback Domain" to: localhost
2. Put STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in your .env file first.

Usage:
    python strava_auth.py
"""

import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
REDIRECT_PORT = 8721
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
SCOPE = "activity:read_all"

_auth_code: dict = {}


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        qs = parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        error = qs.get("error", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if error:
            _auth_code["error"] = error
            self.wfile.write(f"<h1>Fejl: {error}</h1>Du kan lukke dette vindue.".encode("utf-8"))
        else:
            _auth_code["code"] = code
            self.wfile.write("<h1>Godkendt!</h1>Du kan lukke dette vindue og gå tilbage til terminalen.".encode("utf-8"))

    def log_message(self, format, *args):
        pass  # silence default request logging


def main() -> None:
    if not CLIENT_ID or not CLIENT_SECRET:
        raise SystemExit(
            "Mangler STRAVA_CLIENT_ID / STRAVA_CLIENT_SECRET i .env.\n"
            "Opret en app på https://www.strava.com/settings/api og tilføj værdierne først."
        )

    auth_url = (
        "https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        f"&scope={SCOPE}"
        "&approval_prompt=auto"
    )

    print(f"Åbner browser til Strava-godkendelse:\n{auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", REDIRECT_PORT), _CallbackHandler)
    print(f"Venter på godkendelse på {REDIRECT_URI} ...")
    while "code" not in _auth_code and "error" not in _auth_code:
        server.handle_request()

    if "error" in _auth_code:
        raise SystemExit(f"Strava-godkendelse fejlede: {_auth_code['error']}")

    token_resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": _auth_code["code"],
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    token_resp.raise_for_status()
    tokens = token_resp.json()

    print("\nGodkendelse gennemført! Tilføj denne linje til din .env fil:\n")
    print(f"STRAVA_REFRESH_TOKEN={tokens['refresh_token']}")


if __name__ == "__main__":
    main()
