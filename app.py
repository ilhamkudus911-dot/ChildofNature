import sqlite3
import os
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "CON_secure_key_2026"
app.config["UPLOAD_FOLDER"] = "static/uploads"


# =========================
# INIT DATABASE
# =========================
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        photo TEXT DEFAULT 'default.png',
        fullname TEXT,
        bio TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        trip_name TEXT,
        full_name TEXT,
        phone TEXT,
        people TEXT,
        trip_date TEXT,
        note TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("home.html")


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    pesan = ""

    if request.method == "POST":
        username = request.form["username"]
        raw_password = request.form["password"]

        # VALIDASI PASSWORD
        if not re.match("^[a-zA-Z0-9]{6,}$", raw_password):
            flash("Password minimal 6 karakter dan hanya huruf & angka")
            return redirect(request.url)

        hashed_password = generate_password_hash(raw_password)

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        try:
            cur.execute("""
            INSERT INTO users (username, password)
            VALUES (?, ?)
            """, (username, hashed_password))

            conn.commit()
            flash("Akun berhasil dibuat")
            return redirect("/login")

        except:
            pesan = "Username sudah dipakai"

        conn.close()

    return render_template("register.html", pesan=pesan)


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    pesan = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("SELECT username, password FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user"] = user[0]
            return redirect("/dashboard")
        else:
            pesan = "Login gagal"

    return render_template("login.html", pesan=pesan)


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", nama=session["user"])


# =========================
# PROFILE
# =========================
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT username, photo, fullname, bio
    FROM users WHERE username=?
    """, (session["user"],))

    user = cur.fetchone()
    conn.close()

    return render_template("profile.html", user=user)


# =========================
# EDIT PROFILE
# =========================
@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":

        fullname = request.form.get("fullname", "")
        bio = request.form.get("bio", "")
        new_password = request.form.get("password", "")

        # Upload foto
        if "photo" in request.files:
            file = request.files["photo"]

            if file and file.filename != "":
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                file.save(filepath)

                cur.execute(
                    "UPDATE users SET photo=? WHERE username=?",
                    (filename, username)
                )

        # Update data
        cur.execute(
            "UPDATE users SET fullname=?, bio=? WHERE username=?",
            (fullname, bio, username)
        )

        # Update password
        if new_password:
            if not re.match("^[a-zA-Z0-9]{6,}$", new_password):
                flash("Password hanya huruf & angka (min 6)")
                return redirect(request.url)

            hashed = generate_password_hash(new_password)
            cur.execute(
                "UPDATE users SET password=? WHERE username=?",
                (hashed, username)
            )

        conn.commit()

    cur.execute(
        "SELECT username, photo, fullname, bio FROM users WHERE username=?",
        (username,)
    )

    user = cur.fetchone()
    conn.close()

    return render_template("edit_profile.html", user=user)


# =========================
# PACKAGES
# =========================
@app.route("/packages")
def packages():
    return render_template("packages.html")


# =========================
# BOOKING
# =========================
@app.route("/booking/<trip_name>", methods=["GET", "POST"])
def booking(trip_name):

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        phone = request.form["phone"]

        # VALIDASI WA
        if not phone.isdigit() or not phone.startswith("08") or len(phone) < 10:
            flash("Nomor WA tidak valid")
            return redirect(request.url)

        trip_date = request.form["trip_date"]

        today = datetime.now().date()
        input_date = datetime.strptime(trip_date, "%Y-%m-%d").date()

        if input_date < today:
            flash("Tanggal tidak boleh di masa lalu")
            return redirect(request.url)

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO bookings
        (username, trip_name, full_name, phone, people, trip_date, note, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user"],
            trip_name,
            request.form["full_name"],
            phone,
            request.form["people"],
            trip_date,
            request.form["note"],
            "Pending"
        ))

        conn.commit()
        conn.close()

        return redirect("/my-bookings")

    return render_template(
        "booking.html",
        trip_name=trip_name,
        today=datetime.now().date()
    )


# =========================
# MY BOOKINGS
# =========================
@app.route("/my-bookings")
def my_bookings():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT trip_name, full_name, trip_date, status
    FROM bookings WHERE username=?
    ORDER BY id DESC
    """, (session["user"],))

    data = cur.fetchall()
    conn.close()

    return render_template("my_bookings.html", data=data)


# =========================
# ABOUT & CONTACT
# =========================
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))