"""Behavior tests for parity.py. Two local HTTP servers stand in for PHP and Go.

    python3 tests/test_parity.py
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".agents", "scripts"))
import parity  # noqa: E402

PHP_ORDERS = {"data": [{"id": "1", "total": 10.5, "tags": []}], "meta": {"request_id": "php-abc"}}


def serve(routes):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, body = routes[self.path]
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def stop(server):
    server.shutdown()
    server.server_close()


class ParityTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cases = os.path.join(self.dir, "cases.jsonl")
        self.baseline = os.path.join(self.dir, "baseline.jsonl")
        self.config = os.path.join(self.dir, "parity.json")
        with open(self.cases, "w") as f:
            f.write(json.dumps({"id": "orders", "method": "GET", "path": "/orders"}) + "\n")
            f.write(json.dumps({"id": "missing", "method": "GET", "path": "/orders/404"}) + "\n")
        with open(self.config, "w") as f:
            json.dump({"ignore_paths": ["$.meta.request_id"]}, f)
        php, self.php_url = serve({"/orders": (200, PHP_ORDERS), "/orders/404": (404, {"error": "not found"})})
        self.addCleanup(stop, php)
        self.run_cli("record", "--base-url", self.php_url, "--cases", self.cases, "--out", self.baseline)

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = parity.main(list(argv))
        return code, out.getvalue()

    def check(self, go_routes):
        go, url = serve(go_routes)
        self.addCleanup(stop, go)
        return self.run_cli("check", "--base-url", url, "--baseline", self.baseline,
                            "--config", self.config, "--json")

    def test_identical_responses_pass_even_when_an_ignored_field_differs(self):
        go_orders = json.loads(json.dumps(PHP_ORDERS))
        go_orders["meta"]["request_id"] = "go-xyz"
        code, out = self.check({"/orders": (200, go_orders), "/orders/404": (404, {"error": "not found"})})
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads(out)["counts"]["MATCH"], 2)

    def test_go_number_id_and_null_slice_are_reported_as_type_changes(self):
        go_orders = {"data": [{"id": 1, "total": 10.5, "tags": None}], "meta": {"request_id": "go"}}
        code, out = self.check({"/orders": (200, go_orders), "/orders/404": (404, {"error": "not found"})})
        self.assertEqual(code, 1, out)
        diffs = {d["path"]: d["detail"] for d in json.loads(out)["results"][0]["diffs"]}
        self.assertEqual(diffs["$.data[0].id"], 'type string -> number ("1" -> 1)')
        self.assertEqual(diffs["$.data[0].tags"], "type array -> null ([] -> null)")

    def test_status_code_difference_fails(self):
        code, out = self.check({"/orders": (200, PHP_ORDERS), "/orders/404": (500, {"error": "not found"})})
        self.assertEqual(code, 1, out)
        self.assertEqual(json.loads(out)["results"][1]["diffs"][0], {"path": "status", "detail": "404 -> 500"})

    def test_missing_key_in_go_fails(self):
        go_orders = {"data": [{"id": "1", "total": 10.5}], "meta": {"request_id": "go"}}
        code, out = self.check({"/orders": (200, go_orders), "/orders/404": (404, {"error": "not found"})})
        self.assertEqual(code, 1, out)
        self.assertIn({"path": "$.data[0].tags", "detail": "missing in Go"}, json.loads(out)["results"][0]["diffs"])

    def test_unreachable_server_is_inconclusive_not_a_pass(self):
        code, out = self.run_cli("check", "--base-url", "http://127.0.0.1:9", "--baseline", self.baseline, "--json")
        self.assertEqual(code, 3, out)
        self.assertEqual(json.loads(out)["counts"]["UNREACHABLE"], 2)

    def test_auth_headers_are_not_written_to_the_baseline(self):
        with open(self.baseline) as f:
            for row in map(json.loads, f):
                self.assertNotIn("authorization", row["headers"])
                self.assertNotIn("date", row["headers"])

    def test_duplicate_case_ids_are_an_input_error(self):
        with open(self.cases, "a") as f:
            f.write(json.dumps({"id": "orders", "path": "/orders"}) + "\n")
        code, _ = self.run_cli("record", "--base-url", self.php_url, "--cases", self.cases, "--out", self.baseline)
        self.assertEqual(code, 2)

    def test_wildcard_ignore_path_covers_every_array_item(self):
        matcher = parity.ignore_matcher(["$.data[*].updated_at"])
        self.assertTrue(matcher("$.data[3].updated_at"))
        self.assertFalse(matcher("$.data[3].updated_by"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
