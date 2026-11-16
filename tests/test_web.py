import importlib.util
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

script = Path(__file__).resolve().parents[1] / "scripts" / "serve-web.py"
spec = importlib.util.spec_from_file_location("serve_web", script)
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)


class FakeResponse:
    status = 200

    def read(self, limit):
        return json.dumps({"sessionId": "web-test", "category": "orcamento", "priority": "media", "response": "Resposta de teste", "status": "success"}).encode()


class FakeConnection:
    request_data = None

    def __init__(self, host, port, timeout):
        assert (host, port, timeout) == ("127.0.0.1", 5678, 57)

    def request(self, method, path, body, headers):
        self.request_data = (method, path, json.loads(body), headers)
        FakeConnection.request_data = self.request_data

    def getresponse(self):
        return FakeResponse()

    def close(self):
        pass


class WebTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)
        web.PORT = cls.server.server_port
        cls.url = f"http://127.0.0.1:{web.PORT}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_forwards_json_to_existing_webhook(self):
        body = {"sessionId": "web-test", "message": "Quero um orçamento"}
        request = urllib.request.Request(self.url + "/api/message", json.dumps(body).encode(), {"Content-Type": "application/json"})
        with patch.object(web, "HTTPConnection", FakeConnection):
            with urllib.request.urlopen(request) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.load(response)["category"], "orcamento")
        self.assertEqual(FakeConnection.request_data[0:3], ("POST", web.WEBHOOK, body))

    def test_rejects_cross_origin(self):
        request = urllib.request.Request(self.url + "/api/message", b"{}", {"Content-Type": "application/json", "Origin": "https://example.com"})
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        self.assertEqual(error.exception.code, 403)
        error.exception.close()

    def test_rejects_invalid_json(self):
        request = urllib.request.Request(self.url + "/api/message", b"{", {"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        self.assertEqual(error.exception.code, 400)
        error.exception.close()


if __name__ == "__main__":
    unittest.main()
