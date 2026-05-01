from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- DB CONNECTION ----------------
def get_db():
    return sqlite3.connect("database.db")


# ---------------- INIT DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        weight REAL,
        bodyfat REAL,
        calories INTEGER,
        workout TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    if request.method == "POST":
        weight = float(request.form["weight"])
        bodyfat = float(request.form["bodyfat"])
        calories = int(request.form["calories"])
        workout = request.form["workout"]

        date = datetime.now().strftime("%d-%m")

        conn.execute(
            "INSERT INTO progress (user_id, weight, bodyfat, calories, workout, date) VALUES (?, ?, ?, ?, ?, ?)",
            (session["user_id"], weight, bodyfat, calories, workout, date)
        )
        conn.commit()

    data = conn.execute(
        "SELECT weight, bodyfat, date FROM progress WHERE user_id=? ORDER BY id",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    weights = [row[0] for row in data]
    bodyfats = [row[1] for row in data]
    dates = [row[2] for row in data]

    return render_template(
        "dashboard.html",
        weights=json.dumps(weights),
        bodyfats=json.dumps(bodyfats),
        dates=json.dumps(dates)
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
