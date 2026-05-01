from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = "secret"


def get_db():
    return sqlite3.connect("database.db")


# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]

        db = get_db()
        db.execute("INSERT INTO users (name, password) VALUES (?, ?)", (name, password))
        db.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE name=? AND password=?",
            (name, password),
        ).fetchone()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()

    if request.method == "POST":
        weight = request.form["weight"]
        bodyfat = request.form["bodyfat"]
        calories = request.form["calories"]
        workout = request.form["workout"]

        # CLEAN INPUT (IMPORTANT)
        bodyfat = bodyfat.replace("%", "")

        date = datetime.now().strftime("%d-%m")

        db.execute(
            "INSERT INTO progress (user_id, weight, bodyfat, calories, workout, date) VALUES (?, ?, ?, ?, ?, ?)",
            (session["user_id"], weight, bodyfat, calories, workout, date),
        )
        db.commit()

    data = db.execute(
        "SELECT weight, bodyfat, calories, date FROM progress WHERE user_id=? ORDER BY id",
        (session["user_id"],),
    ).fetchall()

    # SAFE CONVERSION
    weights = [float(row[0]) for row in data]
    bodyfats = [float(str(row[1]).replace('%', '')) for row in data]
    calories = [float(row[2]) for row in data]
    dates = [row[3] for row in data]

    # ---------------- STATS ----------------
    current_weight = weights[-1] if weights else 0
    start_weight = weights[0] if weights else 0
    change = current_weight - start_weight

    goal = 55  # you can change
    progress = 0

    if weights and start_weight != goal:
        progress = int(((start_weight - current_weight) / (start_weight - goal)) * 100)

    # ---------------- PREDICTIONS ----------------
    rate = (start_weight - current_weight) / len(weights) if weights else 0
    exp3 = current_weight - (rate * 12)
    exp5 = current_weight - (rate * 20)

    return render_template(
        "dashboard.html",
        weights=json.dumps(weights),
        bodyfats=json.dumps(bodyfats),
        calories=json.dumps(calories),
        dates=json.dumps(dates),
        current_weight=current_weight,
        change=round(change, 2),
        progress=progress,
        exp3=round(exp3, 1),
        exp5=round(exp5, 1),
    )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
