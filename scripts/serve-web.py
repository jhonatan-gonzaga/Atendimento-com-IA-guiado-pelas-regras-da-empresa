#!/usr/bin/env python3
"""Serve a local chat page and forward its messages to the existing n8n webhook."""
import json
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
WEBHOOK = "/webhook/atendimento-empresarial"
PAGE = (Path(__file__).resolve().parents[1] / "web" / "index.html").read_bytes()


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if content_type.startswith("text/html"):
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status, message):
        self._send(status, json.dumps({"response": message, "status": "error"}).encode())

    def _local_request(self):
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        return host in (f"127.0.0.1:{PORT}", f"localhost:{PORT}") and (origin is None or origin == f"http://{host}")

    def do_GET(self):
        if not self._local_request():
            return self._error(403, "Acesso local necessário.")
        if self.path == "/":
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if self.path == "/favicon.ico":
            return self._send(204, b"")
        self._error(404, "Página não encontrada.")

    def do_POST(self):
        if not self._local_request():
            return self._error(403, "Acesso local necessário.")
        if self.path != "/api/message":
            return self._error(404, "Rota não encontrada.")
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self._error(415, "Envie JSON.")
        try:
            size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._error(400, "Tamanho da mensagem inválido.")
        if size < 1 or size > 32768:
            return self._error(413, "Mensagem muito longa.")
        body = self.rfile.read(size)
        try:
            if not isinstance(json.loads(body), dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            return self._error(400, "JSON inválido.")

        connection = HTTPConnection(HOST, 5678, timeout=57)
        try:
            connection.request("POST", WEBHOOK, body=body, headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            result = response.read(16385)
            if len(result) > 16384 or not isinstance(json.loads(result), dict):
                raise ValueError
            self._send(response.status, result)
        except (OSError, ValueError):
            self._error(502, "Não foi possível consultar o n8n. Verifique se ele está ativo.")
        finally:
            connection.close()


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Interface local: http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
