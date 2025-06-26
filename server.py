import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import secrets

import db

HOST = '0.0.0.0'
PORT = 8000


def random_hex(n=8):
    return secrets.token_hex(n)


class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self._set_headers(200)
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        elif self.path == '/init':
            db.init_db()
            self._set_headers(200)
            self.wfile.write(json.dumps({'db': 'initialized'}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'not found'}).encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        try:
            payload = json.loads(data.decode())
        except json.JSONDecodeError:
            payload = {}
        if self.path == '/sale':
            product = payload.get('product')
            store = payload.get('store')
            if not product or not store:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'product and store required'}).encode())
                return
            code = random_hex(4)
            db.create_sale(product, store, code)
            self._set_headers(200)
            self.wfile.write(json.dumps({'code': code}).encode())
        elif self.path == '/delivery':
            code = payload.get('code')
            if not code:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'code required'}).encode())
                return
            try:
                delivered = db.mark_delivered(code)
                self._set_headers(200)
                self.wfile.write(json.dumps({'delivered': delivered}).encode())
            except ValueError:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'sale not found'}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'not found'}).encode())


def run():
    server = HTTPServer((HOST, PORT), Handler)
    print(f'Serving on http://{HOST}:{PORT}')
    server.serve_forever()


if __name__ == '__main__':
    run()
