#!/usr/bin/env python3
"""
Local proxy server for the USCF Rating Estimator HTML page.

Author: Sudhakar Gandhi

Run this locally (python3 app/uscf-lookup-server.py) then open
web/uscf-rating-estimator.html in a browser. The page will call
http://localhost:8765/lookup?id=<USCF_ID> to fetch the player's
prior rated games count from the public US Chess MSA page,
sidestepping the browser's CORS restriction (uschess.org does not
send Access-Control-Allow-Origin headers, so the page's own fetch()
to uschess.org would otherwise be blocked).
"""

import json
import re
import ssl
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8765
MSA_URL = "https://www.uschess.org/msa/MbrDtlMain.php?{}"


def _ssl_context():
    # macOS python.org builds often lack a working default cert store; prefer certifi's bundle.
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def lookup_prior_games(uscf_id):
    """Fetch the 'Regular' rating games-played count from the public US Chess MSA page.

    Returns a dict: {"found": bool, "games": int|None}.
    'found' is False only when the USCF ID doesn't resolve to a player page.
    'games' is None when the player is established (MSA shows no games count,
    meaning enough games have been played that the cap doesn't apply).
    """
    url = MSA_URL.format(uscf_id)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=10, context=_ssl_context()) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    if "Could not retrieve data" in html:
        return {"found": False, "games": None}

    match = re.search(r"Regular Rating[^(]*\(Based on (\d+) games\)", html)
    games = int(match.group(1)) if match else None
    return {"found": True, "games": games}


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/lookup":
            self._send_json(404, {"error": "not found"})
            return

        uscf_id = parse_qs(parsed.query).get("id", [""])[0].strip()
        if not uscf_id.isdigit():
            self._send_json(400, {"error": "invalid or missing 'id' parameter"})
            return

        try:
            result = lookup_prior_games(uscf_id)
        except OSError as exc:
            self._send_json(502, {"error": f"lookup failed: {exc}"})
            return

        if not result["found"]:
            self._send_json(404, {"error": "USCF ID not found"})
            return

        self._send_json(200, {"games": result["games"], "established": result["games"] is None})

    def log_message(self, format, *args):
        pass  # keep the console quiet


if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"USCF lookup proxy running at http://localhost:{PORT}/lookup?id=<USCF_ID>")
    print("Leave this running, then open uscf-rating-estimator.html in your browser.")
    server.serve_forever()
