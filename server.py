from flask import Flask
from db import init_db

app = Flask(__name__)


@app.route("/init")
def init_route():
    init_db()
    return "Database initialized", 200


if __name__ == "__main__":
    app.run(debug=True)
