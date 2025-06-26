# Ventas

This repository provides a minimal prototype for a bar stock and sales system. It
uses a small HTTP server implemented with Python's standard library and a
SQLite database. The code is intended as a starting point for a larger system.

## Features

* Initialize the database with `/init`.
* Register a sale using `/sale` with JSON payload `{"product": "name", "store": "bar"}`.
  A random hexadecimal code is generated for the ticket.
* Mark a sale as delivered using `/delivery` with JSON payload `{"code": "hex"}`.
  When a sale is delivered, inventory is reduced according to the configured
  recipe.
* Check server health with `/health`.
* Access an HTML interface for all management tasks at `/login`, `/users`,
  `/roles`, `/stores`, `/items`, `/inventory`, `/products`, `/recipes`, `/sale`
  and `/delivery`.

## Running the server

```bash
python3 server.py
```

The server listens on `0.0.0.0:8000`.

## Database helpers

The `db.py` module provides helper functions to create roles, users, stores,
items, products and recipes. See the code for details.

The server now includes a basic HTML interface for the entire prototype. Use
`/login` to authenticate and then navigate to the pages listed above to manage
roles, users, inventory, products, recipes and sales. Session tokens are stored
in the database so authentication survives server restarts, though security
remains minimal.
