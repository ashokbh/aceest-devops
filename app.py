"""
ACEest Fitness & Gym - Flask Web Application
Converted from Tkinter (ver 3.2.4) to Flask web service.
"""

from flask import Flask, request, jsonify, session
import sqlite3
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aceest-secret-2025")

DB_NAME = os.environ.get("DB_NAME", "aceest_fitness.db")

# ---------- PROGRAM DEFINITIONS ----------
PROGRAMS = {
    "Fat Loss": {
        "workout": "Full Body HIIT / Circuit Training / Cardio + Weights",
        "diet": "Egg Whites, Chicken, Fish Curry - Target ~2000 kcal",
        "calorie_factor": 22
    },
    "Muscle Gain": {
        "workout": "Push/Pull/Legs / Upper-Lower Split / Full Body Strength",
        "diet": "Eggs, Biryani, Mutton Curry - Target ~3200 kcal",
        "calorie_factor": 35
    },
    "Beginner": {
        "workout": "Full Body 3x/week - Air Squats, Ring Rows, Push-ups",
        "diet": "Balanced Tamil Meals - Protein Target 120g/day",
        "calorie_factor": 26
    }
}


# ---------- DATABASE HELPERS ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            age INTEGER,
            height REAL,
            weight REAL,
            program TEXT,
            calories INTEGER,
            target_weight REAL,
            target_adherence INTEGER,
            membership_status TEXT DEFAULT 'Active',
            membership_end TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            week TEXT,
            adherence INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            date TEXT,
            workout_type TEXT,
            duration_min INTEGER,
            notes TEXT
        )
    """)

    cur.execute("SELECT username FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES ('admin','admin123','Admin')")

    conn.commit()
    conn.close()


# ---------- UTILITY ----------
def calculate_calories(weight: float, program: str) -> int:
    if program not in PROGRAMS:
        return 0
    return int(weight * PROGRAMS[program]["calorie_factor"])


def validate_client_data(data: dict) -> tuple[bool, str]:
    """Returns (is_valid, error_message)."""
    if not data.get("name", "").strip():
        return False, "Name is required"
    if not data.get("program", "").strip():
        return False, "Program is required"
    if data.get("program") not in PROGRAMS:
        return False, f"Invalid program. Choose from: {list(PROGRAMS.keys())}"
    weight = data.get("weight", 0)
    if weight is not None:
        try:
            weight = float(weight)
            if weight < 0:
                return False, "Weight must be a positive number"
        except (TypeError, ValueError):
            return False, "Weight must be a number"
    return True, ""


# ---------- AUTH ROUTES ----------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    row = cur.fetchone()
    conn.close()

    if row:
        session["user"] = username
        session["role"] = row["role"]
        return jsonify({"status": "ok", "role": row["role"], "username": username})

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "ok"})


# ---------- CLIENT ROUTES ----------
@app.route("/api/clients", methods=["GET"])
def list_clients():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, age, weight, program, calories, membership_status FROM clients ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/clients", methods=["POST"])
def create_client():
    data = request.get_json() or {}

    is_valid, error = validate_client_data(data)
    if not is_valid:
        return jsonify({"status": "error", "message": error}), 400

    weight = float(data.get("weight", 0))
    calories = calculate_calories(weight, data["program"])

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO clients (name, age, height, weight, program, calories,
                                 target_weight, target_adherence, membership_status, membership_end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["name"].strip(),
            data.get("age"),
            data.get("height"),
            weight,
            data["program"],
            calories,
            data.get("target_weight"),
            data.get("target_adherence"),
            data.get("membership_status", "Active"),
            data.get("membership_end")
        ))
        conn.commit()
        client_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"status": "error", "message": "Client name already exists"}), 409
    finally:
        conn.close()

    return jsonify({"status": "ok", "id": client_id, "calories": calories}), 201


@app.route("/api/clients/<name>", methods=["GET"])
def get_client(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE name=?", (name,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "error", "message": "Client not found"}), 404

    return jsonify(dict(row))


@app.route("/api/clients/<name>", methods=["PUT"])
def update_client(name):
    data = request.get_json() or {}

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM clients WHERE name=?", (name,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"status": "error", "message": "Client not found"}), 404

    weight = float(data.get("weight", 0))
    program = data.get("program")
    calories = calculate_calories(weight, program) if program in PROGRAMS else 0

    cur.execute("""
        UPDATE clients SET age=?, height=?, weight=?, program=?, calories=?,
               target_weight=?, target_adherence=?, membership_status=?, membership_end=?
        WHERE name=?
    """, (
        data.get("age"), data.get("height"), weight, program, calories,
        data.get("target_weight"), data.get("target_adherence"),
        data.get("membership_status", "Active"), data.get("membership_end"), name
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "calories": calories})


@app.route("/api/clients/<name>", methods=["DELETE"])
def delete_client(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM clients WHERE name=?", (name,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"status": "error", "message": "Client not found"}), 404

    return jsonify({"status": "ok"})


# ---------- PROGRAM ROUTES ----------
@app.route("/api/programs", methods=["GET"])
def get_programs():
    return jsonify(list(PROGRAMS.keys()))


@app.route("/api/programs/<name>", methods=["GET"])
def get_program_detail(name):
    if name not in PROGRAMS:
        return jsonify({"status": "error", "message": "Program not found"}), 404
    return jsonify(PROGRAMS[name])


# ---------- PROGRESS ROUTES ----------
@app.route("/api/clients/<name>/progress", methods=["GET"])
def get_progress(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/clients/<name>/progress", methods=["POST"])
def log_progress(name):
    data = request.get_json() or {}
    adherence = data.get("adherence", 0)

    if not isinstance(adherence, (int, float)) or not (0 <= adherence <= 100):
        return jsonify({"status": "error", "message": "Adherence must be between 0 and 100"}), 400

    week = data.get("week") or datetime.now().strftime("Week %U - %Y")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
                (name, week, int(adherence)))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "week": week}), 201


# ---------- WORKOUT ROUTES ----------
@app.route("/api/clients/<name>/workouts", methods=["GET"])
def get_workouts(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, date, workout_type, duration_min, notes
        FROM workouts WHERE client_name=? ORDER BY date DESC
    """, (name,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/clients/<name>/workouts", methods=["POST"])
def log_workout(name):
    data = request.get_json() or {}
    workout_type = data.get("workout_type", "").strip()

    if not workout_type:
        return jsonify({"status": "error", "message": "workout_type is required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        data.get("date") or date.today().isoformat(),
        workout_type,
        data.get("duration_min", 60),
        data.get("notes", "")
    ))
    conn.commit()
    workout_id = cur.lastrowid
    conn.close()
    return jsonify({"status": "ok", "id": workout_id}), 201


# ---------- MEMBERSHIP ROUTE ----------
@app.route("/api/clients/<name>/membership", methods=["GET"])
def check_membership(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT membership_status, membership_end FROM clients WHERE name=?", (name,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "error", "message": "Client not found"}), 404

    return jsonify({"membership_status": row["membership_status"], "membership_end": row["membership_end"]})


# ---------- HEALTH CHECK ----------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "app": "ACEest Fitness & Gym"})


if __name__ == "__main__":
    init_db()
    app.run(debug=False, host="0.0.0.0", port=5000)
