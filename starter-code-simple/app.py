# app_secure.py — secure rewrite of the classroom starter app
# EDUCATIONAL: This is an improved example for students. Still review before production use.

import os
import sqlite3
import logging
import secrets
from flask import Flask, request, jsonify, abort
import bcrypt
from dotenv import load_dotenv

# Load .env if present (optional for local dev)
load_dotenv()

# Basic configuration from environment
DATABASE_PATH = os.getenv("DATABASE_PATH", "users.db")
SECRET_KEY = os.getenv("SECRET_KEY", None)
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")

if SECRET_KEY is None:
    # Generate a non-persistent secret key for local runs if none provided.
    # In production, require a real SECRET_KEY via environment/secret manager.
    SECRET_KEY = secrets.token_urlsafe(32)

# Configure logging (do NOT log sensitive contents)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY


def get_db_connection():
    """Return a sqlite3 connection. Use row factory for convenience."""
    conn = sqlite3.connect(DATABASE_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create users table if it doesn't exist (password column stores bcrypt hashes)."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """
    with get_db_connection() as conn:
        conn.execute(create_sql)


def validate_username_password(username: str, password: str):
    """Basic validation rules — expand as needed for your assignment."""
    if not username or not isinstance(username, str) or len(username.strip()) < 3:
        return "Username must be at least 3 characters."
    if not password or not isinstance(password, str) or len(password) < 8:
        return "Password must be at least 8 characters."
    return None


@app.route("/health", methods=["GET"])
def health_check():
    # Don't return secrets — return the DB filename only for local debugging.
    return jsonify({"status": "healthy", "database": os.path.basename(DATABASE_PATH)})


@app.route("/users", methods=["GET"])
def get_users():
    """Return list of users (do NOT return password hashes)."""
    with get_db_connection() as conn:
        rows = conn.execute("SELECT id, username FROM users").fetchall()
        users = [{"id": r["id"], "username": r["username"]} for r in rows]
    return jsonify({"users": users})


@app.route("/users", methods=["POST"])
def create_user():
    """Create a new user with bcrypt-hashed password. Uses parameterized SQL."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    # Input validation
    error = validate_username_password(username, password)
    if error:
        return jsonify({"error": error}), 400

    # Hash the password with bcrypt (store the utf-8 string)
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    hashed_str = hashed.decode("utf-8")

    insert_sql = "INSERT INTO users (username, password) VALUES (?, ?)"
    try:
        with get_db_connection() as conn:
            conn.execute(insert_sql, (username, hashed_str))
    except sqlite3.IntegrityError as e:
        # Likely UNIQUE constraint violation for username
        logger.info("Attempt to create duplicate user: %s", username)
        return jsonify({"error": "Username already exists"}), 409
    except Exception:
        logger.exception("Unexpected error when creating user")
        return jsonify({"error": "Internal server error"}), 500

    # Safe log: do NOT include password or password hash
    logger.info("Created user: %s", username)
    return jsonify({"message": "User created", "username": username}), 201


@app.route("/login", methods=["POST"])
def login():
    """Authenticate user by comparing bcrypt hashes from DB."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    select_sql = "SELECT id, username, password FROM users WHERE username = ?"
    try:
        with get_db_connection() as conn:
            row = conn.execute(select_sql, (username,)).fetchone()
    except Exception:
        logger.exception("DB error during login")
        return jsonify({"error": "Internal server error"}), 500

    if row is None:
        # Avoid leaking whether username exists
        logger.info("Failed login attempt for username: %s", username)
        return jsonify({"message": "Invalid credentials"}), 401

    stored_hash = row["password"].encode("utf-8")
    if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        # Authentication successful — in production you'd issue a JWT or session
        logger.info("Successful login for user id=%s username=%s", row["id"], row["username"])
        return jsonify({"message": "Login successful", "user_id": row["id"]})
    else:
        logger.info("Failed login attempt for username: %s", username)
        return jsonify({"message": "Invalid credentials"}), 401


if __name__ == "__main__":
    init_db()
    # Do not enable debug mode by default in production. Controlled by environment.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
