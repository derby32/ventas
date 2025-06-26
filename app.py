import argparse
import sqlite3
import os
from datetime import datetime
import json

DB_FILE = 'ventas.db'

# Database initialization

def get_connection():
    return sqlite3.connect(DB_FILE)


def setup_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role_id INTEGER REFERENCES roles(id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS bars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        unit TEXT NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        price REAL NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS recipes (
        product_id INTEGER REFERENCES products(id),
        ingredient_id INTEGER REFERENCES ingredients(id),
        amount REAL NOT NULL,
        PRIMARY KEY (product_id, ingredient_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS general_stock (
        ingredient_id INTEGER PRIMARY KEY REFERENCES ingredients(id),
        quantity REAL NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS bar_stock (
        bar_id INTEGER REFERENCES bars(id),
        ingredient_id INTEGER REFERENCES ingredients(id),
        quantity REAL NOT NULL,
        PRIMARY KEY (bar_id, ingredient_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER REFERENCES products(id),
        bar_id INTEGER REFERENCES bars(id),
        user_id INTEGER REFERENCES users(id),
        price REAL NOT NULL,
        code TEXT UNIQUE NOT NULL,
        delivered INTEGER DEFAULT 0,
        timestamp TEXT NOT NULL
    )''')

    conn.commit()
    conn.close()


def add_role(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO roles(name) VALUES (?)', (name,))
    conn.commit()
    conn.close()


def add_user(username, password, role):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM roles WHERE name=?', (role,))
    role_row = cur.fetchone()
    if not role_row:
        raise ValueError(f'Role {role} not found')
    role_id = role_row[0]
    cur.execute('INSERT INTO users(username, password, role_id) VALUES (?,?,?)',
                (username, password, role_id))
    conn.commit()
    conn.close()


def add_bar(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO bars(name) VALUES (?)', (name,))
    conn.commit()
    conn.close()


def add_ingredient(name, unit):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO ingredients(name, unit) VALUES (?,?)', (name, unit))
    conn.commit()
    conn.close()


def add_product(name, price):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO products(name, price) VALUES (?,?)', (name, price))
    conn.commit()
    conn.close()


def add_recipe(product_name, ingredient_name, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM products WHERE name=?', (product_name,))
    p = cur.fetchone()
    if not p:
        raise ValueError('Product not found')
    product_id = p[0]
    cur.execute('SELECT id FROM ingredients WHERE name=?', (ingredient_name,))
    i = cur.fetchone()
    if not i:
        raise ValueError('Ingredient not found')
    ingredient_id = i[0]
    cur.execute('''INSERT OR REPLACE INTO recipes(product_id, ingredient_id, amount)
                   VALUES (?,?,?)''', (product_id, ingredient_id, amount))
    conn.commit()
    conn.close()


def stock_in_general(ingredient_name, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM ingredients WHERE name=?', (ingredient_name,))
    row = cur.fetchone()
    if not row:
        raise ValueError('Ingredient not found')
    ing_id = row[0]
    cur.execute(
        'INSERT INTO general_stock(ingredient_id, quantity) '
        'VALUES(?, ?) '
        'ON CONFLICT(ingredient_id) DO UPDATE SET quantity=quantity+excluded.quantity',
        (ing_id, amount))
    conn.commit()
    conn.close()


def transfer_stock(bar_name, ingredient_name, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM bars WHERE name=?', (bar_name,))
    row = cur.fetchone()
    if not row:
        raise ValueError('Bar not found')
    bar_id = row[0]
    cur.execute('SELECT id FROM ingredients WHERE name=?', (ingredient_name,))
    row = cur.fetchone()
    if not row:
        raise ValueError('Ingredient not found')
    ing_id = row[0]
    cur.execute('SELECT quantity FROM general_stock WHERE ingredient_id=?', (ing_id,))
    row = cur.fetchone()
    if not row or row[0] < amount:
        raise ValueError('Not enough stock in general store')
    cur.execute('UPDATE general_stock SET quantity=quantity-? WHERE ingredient_id=?', (amount, ing_id))
    cur.execute(
        'INSERT INTO bar_stock(bar_id, ingredient_id, quantity) '
        'VALUES(?,?,?) '
        'ON CONFLICT(bar_id, ingredient_id) DO UPDATE SET quantity=quantity+excluded.quantity',
        (bar_id, ing_id, amount))
    conn.commit()
    conn.close()


def make_sale(product_name, bar_name, user_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM products WHERE name=?', (product_name,))
    p = cur.fetchone()
    if not p:
        raise ValueError('Product not found')
    product_id = p[0]
    cur.execute('SELECT price FROM products WHERE id=?', (product_id,))
    price = cur.fetchone()[0]
    cur.execute('SELECT id FROM bars WHERE name=?', (bar_name,))
    b = cur.fetchone()
    if not b:
        raise ValueError('Bar not found')
    bar_id = b[0]
    cur.execute('SELECT id FROM users WHERE username=?', (user_name,))
    u = cur.fetchone()
    if not u:
        raise ValueError('User not found')
    user_id = u[0]

    # check recipe and bar stock
    cur.execute('SELECT ingredient_id, amount FROM recipes WHERE product_id=?', (product_id,))
    recipe_items = cur.fetchall()
    for ing_id, amt in recipe_items:
        cur.execute('SELECT quantity FROM bar_stock WHERE bar_id=? AND ingredient_id=?', (bar_id, ing_id))
        row = cur.fetchone()
        if not row or row[0] < amt:
            raise ValueError('Not enough stock in bar')

    # deduct stock
    for ing_id, amt in recipe_items:
        cur.execute('UPDATE bar_stock SET quantity=quantity-? WHERE bar_id=? AND ingredient_id=?',
                    (amt, bar_id, ing_id))

    sale_code = os.urandom(3).hex()
    timestamp = datetime.utcnow().isoformat()

    cur.execute('''INSERT INTO sales(product_id, bar_id, user_id, price, code, timestamp)
                   VALUES (?,?,?,?,?,?)''',
                (product_id, bar_id, user_id, price, sale_code, timestamp))
    sale_id = cur.lastrowid
    conn.commit()
    conn.close()
    print(json.dumps({'sale_id': sale_id, 'code': sale_code}, indent=2))


def scan_sale(code, bar_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM bars WHERE name=?', (bar_name,))
    row = cur.fetchone()
    if not row:
        raise ValueError('Bar not found')
    bar_id = row[0]
    cur.execute('SELECT id, delivered FROM sales WHERE code=? AND bar_id=?', (code, bar_id))
    sale = cur.fetchone()
    if not sale:
        raise ValueError('Sale not found')
    if sale[1]:
        print('Sale already delivered')
    else:
        cur.execute('UPDATE sales SET delivered=1 WHERE id=?', (sale[0],))
        conn.commit()
        print('Sale marked as delivered')
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Sistema de ventas para boliche')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('setup')

    pr = sub.add_parser('add-role')
    pr.add_argument('name')

    pu = sub.add_parser('add-user')
    pu.add_argument('username')
    pu.add_argument('password')
    pu.add_argument('role')

    pb = sub.add_parser('add-bar')
    pb.add_argument('name')

    pi = sub.add_parser('add-ingredient')
    pi.add_argument('name')
    pi.add_argument('unit')

    pp = sub.add_parser('add-product')
    pp.add_argument('name')
    pp.add_argument('price', type=float)

    prc = sub.add_parser('add-recipe')
    prc.add_argument('product')
    prc.add_argument('ingredient')
    prc.add_argument('amount', type=float)

    sg = sub.add_parser('stock-in')
    sg.add_argument('ingredient')
    sg.add_argument('amount', type=float)

    ts = sub.add_parser('transfer-stock')
    ts.add_argument('bar')
    ts.add_argument('ingredient')
    ts.add_argument('amount', type=float)

    mk = sub.add_parser('sale')
    mk.add_argument('product')
    mk.add_argument('bar')
    mk.add_argument('user')

    sc = sub.add_parser('scan')
    sc.add_argument('code')
    sc.add_argument('bar')

    args = parser.parse_args()

    if args.cmd == 'setup':
        setup_db()
        print('DB ready')
    elif args.cmd == 'add-role':
        add_role(args.name)
    elif args.cmd == 'add-user':
        add_user(args.username, args.password, args.role)
    elif args.cmd == 'add-bar':
        add_bar(args.name)
    elif args.cmd == 'add-ingredient':
        add_ingredient(args.name, args.unit)
    elif args.cmd == 'add-product':
        add_product(args.name, args.price)
    elif args.cmd == 'add-recipe':
        add_recipe(args.product, args.ingredient, args.amount)
    elif args.cmd == 'stock-in':
        stock_in_general(args.ingredient, args.amount)
    elif args.cmd == 'transfer-stock':
        transfer_stock(args.bar, args.ingredient, args.amount)
    elif args.cmd == 'sale':
        make_sale(args.product, args.bar, args.user)
    elif args.cmd == 'scan':
        scan_sale(args.code, args.bar)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
