import sqlite3
from datetime import datetime
import hashlib

DB_PATH = 'ventas.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Roles
    cur.execute(
        """CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )"""
    )
    # Users
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role_id INTEGER,
        FOREIGN KEY(role_id) REFERENCES roles(id)
    )"""
    )
    # Stores (general deposit or bar stock)
    cur.execute(
        """CREATE TABLE IF NOT EXISTS stores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )"""
    )
    # Items (insumos)
    cur.execute(
        """CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        unit TEXT NOT NULL
    )"""
    )
    # Inventory per store
    cur.execute(
        """CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER,
        item_id INTEGER,
        quantity REAL DEFAULT 0,
        FOREIGN KEY(store_id) REFERENCES stores(id),
        FOREIGN KEY(item_id) REFERENCES items(id),
        UNIQUE(store_id, item_id)
    )"""
    )
    # Products sold
    cur.execute(
        """CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        price REAL NOT NULL
    )"""
    )
    # Recipe linking products with items and amounts used
    cur.execute(
        """CREATE TABLE IF NOT EXISTS recipes (
        product_id INTEGER,
        item_id INTEGER,
        amount REAL NOT NULL,
        PRIMARY KEY(product_id, item_id),
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(item_id) REFERENCES items(id)
    )"""
    )
    # Sales tickets
    cur.execute(
        """CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        store_id INTEGER NOT NULL,
        code_hex TEXT UNIQUE NOT NULL,
        delivered INTEGER DEFAULT 0,
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(store_id) REFERENCES stores(id)
    )"""
    )
    conn.commit()
    conn.close()


def add_role(name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO roles(name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def add_user(username: str, role_name: str, password: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM roles WHERE name=?", (role_name,))
    role = cur.fetchone()
    if not role:
        raise ValueError("Role not found")
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cur.execute(
        "INSERT OR IGNORE INTO users(username, password_hash, role_id) VALUES (?,?,?)",
        (username, password_hash, role[0]),
    )
    conn.commit()
    conn.close()


def authenticate(username: str, password: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT password_hash FROM users WHERE username=?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == row[0]


def list_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users ORDER BY username")
    users = [r[0] for r in cur.fetchall()]
    conn.close()
    return users


def add_store(name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO stores(name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def add_item(name: str, unit: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO items(name, unit) VALUES (?,?)", (name, unit))
    conn.commit()
    conn.close()


def set_inventory(store: str, item: str, quantity: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM stores WHERE name=?", (store,))
    store_row = cur.fetchone()
    cur.execute("SELECT id FROM items WHERE name=?", (item,))
    item_row = cur.fetchone()
    if not store_row or not item_row:
        raise ValueError("store or item not found")
    store_id, item_id = store_row[0], item_row[0]
    cur.execute(
        "INSERT INTO inventory(store_id, item_id, quantity) VALUES (?,?,?) "
        "ON CONFLICT(store_id, item_id) DO UPDATE SET quantity=excluded.quantity",
        (store_id, item_id, quantity),
    )
    conn.commit()
    conn.close()


def add_product(name: str, price: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO products(name, price) VALUES (?,?)", (name, price))
    conn.commit()
    conn.close()


def add_recipe(product: str, item: str, amount: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM products WHERE name=?", (product,))
    prod = cur.fetchone()
    cur.execute("SELECT id FROM items WHERE name=?", (item,))
    item_row = cur.fetchone()
    if not prod or not item_row:
        raise ValueError("product or item not found")
    cur.execute(
        "INSERT OR REPLACE INTO recipes(product_id, item_id, amount) VALUES (?,?,?)",
        (prod[0], item_row[0], amount),
    )
    conn.commit()
    conn.close()


def create_sale(product: str, store: str, code_hex: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM products WHERE name=?", (product,))
    prod = cur.fetchone()
    cur.execute("SELECT id FROM stores WHERE name=?", (store,))
    store_row = cur.fetchone()
    if not prod or not store_row:
        raise ValueError("product or store not found")
    cur.execute(
        "INSERT INTO sales(created_at, product_id, store_id, code_hex, delivered) "
        "VALUES (?,?,?,?,0)",
        (datetime.utcnow().isoformat(), prod[0], store_row[0], code_hex),
    )
    sale_id = cur.lastrowid
    conn.commit()
    conn.close()
    return sale_id


def mark_delivered(code_hex: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, product_id, store_id, delivered FROM sales WHERE code_hex=?", (code_hex,))
    row = cur.fetchone()
    if not row:
        raise ValueError("sale not found")
    if row[3]:
        conn.close()
        return False
    sale_id, product_id, store_id, _ = row
    # reduce inventory based on recipe
    for item_id, amount in cur.execute(
        "SELECT item_id, amount FROM recipes WHERE product_id=?", (product_id,)
    ):
        # check current quantity
        cur.execute(
            "SELECT quantity FROM inventory WHERE store_id=? AND item_id=?",
            (store_id, item_id),
        )
        q = cur.fetchone()
        current = q[0] if q else 0
        cur.execute(
            "INSERT INTO inventory(store_id, item_id, quantity) VALUES (?,?,?) "
            "ON CONFLICT(store_id, item_id) DO UPDATE SET quantity=quantity-?",
            (store_id, item_id, current - amount, amount),
        )
    cur.execute("UPDATE sales SET delivered=1 WHERE id=?", (sale_id,))
    conn.commit()
    conn.close()
    return True

