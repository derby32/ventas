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
            roles = db.list_roles()
            role_opts = ''.join(f'<option>{r}</option>' for r in roles)
            form = (
                "<form method='POST' action='/users'>"
                "Usuario:<input name='username'>"
                "Clave:<input type='password' name='password'>"
                "Rol:<select name='role'>" + role_opts + "</select>"
                "<input type='submit' value='Add'>"
                "</form>"
            )
            self.wfile.write(f"<h1>Usuarios</h1><ul>{user_list}</ul>{form}".encode())
        elif self.path == '/roles':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            roles = db.list_roles()
            role_list = ''.join(f'<li>{r}</li>' for r in roles)
            form = (
                "<form method='POST' action='/roles'>"
                "Rol:<input name='name'>"
                "<input type='submit' value='Add'>"
                "</form>"
            )
            self.wfile.write(f"<h1>Roles</h1><ul>{role_list}</ul>{form}".encode())
        elif self.path == '/stores':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            stores = db.list_stores()
            store_list = ''.join(f'<li>{s}</li>' for s in stores)
            form = (
                "<form method='POST' action='/stores'>"
                "Deposito:<input name='name'>"
                "<input type='submit' value='Add'>"
                "</form>"
            )
            self.wfile.write(f"<h1>Depositos</h1><ul>{store_list}</ul>{form}".encode())
        elif self.path == '/items':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            items = db.list_items()
            item_list = ''.join(f'<li>{i}</li>' for i in items)
            form = (
                "<form method='POST' action='/items'>"
                "Insumo:<input name='name'>"
                "Unidad:<input name='unit'>"
                "<input type='submit' value='Add'>"
                "</form>"
            )
            self.wfile.write(f"<h1>Insumos</h1><ul>{item_list}</ul>{form}".encode())
        elif self.path == '/inventory':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            stores = db.list_stores()
            items = db.list_items()
            store_opts = ''.join(f'<option>{s}</option>' for s in stores)
            item_opts = ''.join(f'<option>{i}</option>' for i in items)
            form = (
                "<form method='POST' action='/inventory'>"
                "Deposito:<select name='store'>" + store_opts + "</select>"
                "Insumo:<select name='item'>" + item_opts + "</select>"
                "Cantidad:<input name='quantity'>"
                "<input type='submit' value='Set'>"
                "</form>"
            )
            self.wfile.write(form.encode())
        elif self.path == '/products':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            products = db.list_products()
            product_list = ''.join(f'<li>{p}</li>' for p in products)
            form = (
                "<form method='POST' action='/products'>"
                "Producto:<input name='name'>"
                "Precio:<input name='price'>"
                "<input type='submit' value='Add'>"
                "</form>"
            )
            self.wfile.write(f"<h1>Productos</h1><ul>{product_list}</ul>{form}".encode())
        elif self.path == '/recipes':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            products = db.list_products()
            items = db.list_items()
            prod_opts = ''.join(f'<option>{p}</option>' for p in products)
            item_opts = ''.join(f'<option>{i}</option>' for i in items)
            form = (
                "<form method='POST' action='/recipes'>"
                "Producto:<select name='product'>" + prod_opts + "</select>"
                "Insumo:<select name='item'>" + item_opts + "</select>"
                "Cantidad:<input name='amount'>"
                "<input type='submit' value='Add'>"
                "</form>"
            )
            self.wfile.write(form.encode())
        elif self.path == '/sale':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            products = db.list_products()
            stores = db.list_stores()
            prod_opts = ''.join(f'<option>{p}</option>' for p in products)
            store_opts = ''.join(f'<option>{s}</option>' for s in stores)
            form = (
                "<form method='POST' action='/sale'>"
                "Producto:<select name='product'>" + prod_opts + "</select>"
                "Deposito:<select name='store'>" + store_opts + "</select>"
                "<input type='submit' value='Vender'>"
                "</form>"
            )
            self.wfile.write(form.encode())
        elif self.path == '/delivery':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            form = (
                "<form method='POST' action='/delivery'>"
                "Codigo:<input name='code'>"
                "<input type='submit' value='Entregar'>"
                "</form>"
            )
            self.wfile.write(form.encode())
        elif self.path == '/':
            if not user:
                self._set_headers(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self._set_headers()
            links = (
                "<ul>"
                "<li><a href='/users'>Usuarios</a></li>"
                "<li><a href='/roles'>Roles</a></li>"
                "<li><a href='/stores'>Depositos</a></li>"
                "<li><a href='/items'>Insumos</a></li>"
                "<li><a href='/inventory'>Inventario</a></li>"
                "<li><a href='/products'>Productos</a></li>"
                "<li><a href='/recipes'>Recetas</a></li>"
                "<li><a href='/sale'>Venta</a></li>"
                "<li><a href='/delivery'>Entrega</a></li>"
                "<li><a href='/logout'>Logout</a></li>"
                "</ul>"
            )
            self.wfile.write(links.encode())
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
        elif self.path == '/roles':
            user = self._read_user()
            if not user:
                self._set_headers(403)
                self.wfile.write(b'Forbidden')
                return
            name = payload.get('name')
            if isinstance(name, list):
                name = name[0]
            if name:
                db.add_role(name)
                self._set_headers()
                self.wfile.write(b'added')
            else:
                self._set_headers(400)
                self.wfile.write(b'error')
        elif self.path == '/stores':
            user = self._read_user()
            if not user:
                self._set_headers(403)
                self.wfile.write(b'Forbidden')
                return
            name = payload.get('name')
            if isinstance(name, list):
                name = name[0]
            if name:
                db.add_store(name)
                self._set_headers()
                self.wfile.write(b'added')
            else:
                self._set_headers(400)
                self.wfile.write(b'error')
        elif self.path == '/items':
            user = self._read_user()
            if not user:
                self._set_headers(403)
                self.wfile.write(b'Forbidden')
                return
            name = payload.get('name')
            unit = payload.get('unit')
            if isinstance(name, list):
                name = name[0]
            if isinstance(unit, list):
                unit = unit[0]
            if name and unit:
                db.add_item(name, unit)
                self._set_headers()
                self.wfile.write(b'added')
            else:
                self._set_headers(400)
                self.wfile.write(b'error')
        elif self.path == '/inventory':
            user = self._read_user()
            if not user:
                self._set_headers(403)
                self.wfile.write(b'Forbidden')
                return
            store = payload.get('store')
            item = payload.get('item')
            quantity = payload.get('quantity')
            if isinstance(store, list):
                store = store[0]
            if isinstance(item, list):
                item = item[0]
            if isinstance(quantity, list):
                quantity = quantity[0]
            if store and item and quantity is not None:
                try:
                    db.set_inventory(store, item, float(quantity))
                    self._set_headers()
                    self.wfile.write(b'set')
                except ValueError:
                    self._set_headers(400)
                    self.wfile.write(b'error')
            else:
                self._set_headers(400)
                self.wfile.write(b'error')
        elif self.path == '/products':
            user = self._read_user()
            if not user:
                self._set_headers(403)
                self.wfile.write(b'Forbidden')
                return
            name = payload.get('name')
            price = payload.get('price')
            if isinstance(name, list):
                name = name[0]
            if isinstance(price, list):
                price = price[0]
            if name and price:
                try:
                    db.add_product(name, float(price))
                    self._set_headers()
                    self.wfile.write(b'added')
                except ValueError:
                    self._set_headers(400)
                    self.wfile.write(b'error')
            else:
                self._set_headers(400)
                self.wfile.write(b'error')
        elif self.path == '/recipes':
            user = self._read_user()
            if not user:
                self._set_headers(403)
                self.wfile.write(b'Forbidden')
                return
            product = payload.get('product')
            item = payload.get('item')
            amount = payload.get('amount')
            if isinstance(product, list):
                product = product[0]
            if isinstance(item, list):
                item = item[0]
            if isinstance(amount, list):
                amount = amount[0]
            if product and item and amount:
                try:
                    db.add_recipe(product, item, float(amount))
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
