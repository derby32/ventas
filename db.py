import sqlite3
from pathlib import Path

DB_PATH = Path("ventas.db")


def init_db():
    """Initialize the database and insert default admin if empty."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create tables if they don't exist
    cur.execute(
        """CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role_id INTEGER,
                FOREIGN KEY(role_id) REFERENCES roles(id)
            )"""
    )
    conn.commit()

    # Check if any user exists
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        # Insert default admin role and user
        cur.execute("INSERT INTO roles (name) VALUES (?)", ("admin",))
        role_id = cur.lastrowid
        cur.execute(
            "INSERT INTO users (username, password, role_id) VALUES (?,?,?)",
            ("admin", "admin", role_id),
        )
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
