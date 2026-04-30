import sqlite3
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.secret_key = "CON_9x7A!mK2#pQ8$vL1@Nature_2026"

# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect("database_new.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        photo TEXT DEFAULT 'default.png',
        fullname TEXT,
        bio TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================
@app.route("/")
def home():
    photo = "default.png"

    if "user" in session:
        conn = sqlite3.connect("database_new.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT photo FROM users WHERE username=?",
            (session["user"],)
        )

        user = cur.fetchone()
        conn.close()

        if user and user[0]:
            photo = user[0]

    return render_template("home.html", session_photo=photo)

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    pesan = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if len(username) < 3:
            return render_template("register.html", pesan="Username minimal 3 karakter")

        if len(password) < 6:
            return render_template("register.html", pesan="Password minimal 6 karakter")

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("database_new.db")
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO users (username, password, role, photo, fullname, bio)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, hashed_password, "user", "default.png", "", ""))

            conn.commit()
            flash("Akun berhasil dibuat!")
            return redirect("/login")

        except sqlite3.IntegrityError:
            pesan = "Username sudah dipakai"

        conn.close()

    return render_template("register.html", pesan=pesan)

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    pesan = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT username, password, role FROM users WHERE username=?",
            (username,)
        )

        user = cur.fetchone()
        conn.close()

        if user:
            db_username, db_password, db_role = user

            if check_password_hash(db_password, password):
                session["user"] = db_username
                session["role"] = db_role if db_role else "user"
                return redirect("/dashboard")
            else:
                pesan = "Password salah"
        else:
            pesan = "Username tidak ditemukan"

    return render_template("login.html", pesan=pesan)

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", nama=session["user"])
    return redirect("/login")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)