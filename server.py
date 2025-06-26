import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlparse
import secrets

import db

HOST = '0.0.0.0'
PORT = 8000

SESSIONS = {}


def random_hex(n=8):
    return secrets.token_hex(n)


class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content='html'):
        self.send_response(status)
        if content == 'json':
            self.send_header('Content-Type', 'application/json')
        else:
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

    def _read_user(self):
        cookie = SimpleCookie(self.headers.get('Cookie'))
        session = cookie.get('session')
        if session:
            return SESSIONS.get(session.value)
        return None

    def do_GET(self):
        if self.path == '/health':
            self._set_headers(200, 'json')
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            return
        if self.path == '/init':
            db.init_db()
            self._set_headers(200, 'json')
            self.wfile.write(json.dumps({'db': 'initialized'}).encode())
            return

        user = self._read_user()
        if self.path == '/login':
            self._set_headers()
            self.wfile.write(
                b"<form method='POST' action='/login'>"
                b"Usuario: <input name='username'><br>"
                b"Clave: <input type='password' name='password'><br>"
                b"<input type='submit' value='Login'>"
                b"</form>"
            )
        elif self.path == '/logout':
            if user:
                for key, val in list(SESSIONS.items()):
                    if val == user:
                        del SESSIONS[key]
                        break
            self._set_headers()
            self.send_header('Set-Cookie', 'session=; Path=/; Max-Age=0')
            self.end_headers()
            self.wfile.write(b"Logged out")
        elif self.path == '/users':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            users = db.list_users()
            user_list = ''.join(f'<li>{u}</li>' for u in users)
            form = (
                "<form method='POST' action='/users'>"
                "Usuario:<input name='username'>"
                "Clave:<input type='password' name='password'>"
                "Rol:<input name='role'>"
                "<input type='submit' value='Add'>"
                "</form>"
            )
            self.wfile.write(f"<ul>{user_list}</ul>{form}".encode())
        else:
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            self.wfile.write(f"Hola {user}".encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        content_type = self.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            try:
                payload = json.loads(data.decode())
            except json.JSONDecodeError:
                payload = {}
        else:
            payload = parse_qs(data.decode())

        if self.path == '/login':
            username = payload.get('username')
            password = payload.get('password')
            if isinstance(username, list):
                username = username[0]
            if isinstance(password, list):
                password = password[0]
            if username and password and db.authenticate(username, password):
                token = random_hex(16)
                SESSIONS[token] = username
                self._set_headers()
                self.send_header('Set-Cookie', f'session={token}; Path=/')
                self.end_headers()
                self.wfile.write(b'Logged in')
            else:
                self._set_headers(403)
                self.wfile.write(b'Forbidden')
        elif self.path == '/users':
            user = self._read_user()
            if not user:
                self._set_headers(403)
                self.wfile.write(b'Forbidden')
                return
            username = payload.get('username')
            password = payload.get('password')
            role = payload.get('role', 'cajero')
            if isinstance(username, list):
                username = username[0]
            if isinstance(password, list):
                password = password[0]
            if isinstance(role, list):
                role = role[0]
            if username and password:
                try:
                    db.add_user(username, role, password)
                    self._set_headers()
                    self.wfile.write(b'added')
                except ValueError:
                    self._set_headers(400)
                    self.wfile.write(b'error')
            else:
                self._set_headers(400)
                self.wfile.write(b'error')
        elif self.path == '/sale':
            product = payload.get('product')
            store = payload.get('store')
            if isinstance(product, list):
                product = product[0]
            if isinstance(store, list):
                store = store[0]
            if not product or not store:
                self._set_headers(400, 'json')
                self.wfile.write(json.dumps({'error': 'product and store required'}).encode())
                return
            code = random_hex(4)
            db.create_sale(product, store, code)
            self._set_headers(200, 'json')
            self.wfile.write(json.dumps({'code': code}).encode())
        elif self.path == '/delivery':
            code = payload.get('code')
            if isinstance(code, list):
                code = code[0]
            if not code:
                self._set_headers(400, 'json')
                self.wfile.write(json.dumps({'error': 'code required'}).encode())
                return
            try:
                delivered = db.mark_delivered(code)
                self._set_headers(200, 'json')
                self.wfile.write(json.dumps({'delivered': delivered}).encode())
            except ValueError:
                self._set_headers(404, 'json')
                self.wfile.write(json.dumps({'error': 'sale not found'}).encode())
        else:
            self._set_headers(404, 'json')
            self.wfile.write(json.dumps({'error': 'not found'}).encode())


def run():
    server = HTTPServer((HOST, PORT), Handler)
    print(f'Serving on http://{HOST}:{PORT}')
    server.serve_forever()


if __name__ == '__main__':
    run()
