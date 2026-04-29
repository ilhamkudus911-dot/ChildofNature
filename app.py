import sqlite3
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.secret_key = "CON_9x7A!mK2#pQ8$vL1@Nature_2026"

# HOME
@app.route("/")
def home():

    photo = "default.png"

    if "user" in session:

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT photo FROM users WHERE username=?",
            (session["user"],)
        )

        user = cur.fetchone()
        conn.close()

        if user:
            photo = user[0]

    return render_template(
        "home.html",
        session_photo=photo
    )
# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    pesan = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if len(username) < 3:
            pesan = "Username minimal 3 karakter"
            return render_template("register.html", pesan=pesan)

        if len(password) < 6:
            pesan = "Password minimal 6 karakter"
            return render_template("register.html", pesan=pesan)

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            photo TEXT,
            fullname TEXT,
            bio TEXT
        )
        """)

        try:
            cur.execute(
                """
                INSERT INTO users (username, password, photo, fullname, bio) VALUES (?, ?, ?, ?, ?)
                """,
                (username, hashed_password, "default.png", "", "")
            )   

            conn.commit()
            pesan = "Akun berhasil dibuat"
        except:
            pesan = "Username sudah dipakai"

        conn.close()

        flash("Akun berhasil dibuat!")
        return redirect("/")

    return render_template("register.html", pesan=pesan)

# LOGIN
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
            db_username = user[0]
            db_password = user[1]
            db_role = user[2]

            if check_password_hash(db_password, password):
                session["user"] = db_username
                session["role"] = db_role
                return redirect("/dashboard")
            else:
                pesan = "Password salah"
        else:
            pesan = "Username tidak ditemukan"

    return render_template("login.html", pesan=pesan)

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", nama=session["user"])
    return redirect("/login")

# PROFILE
@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        """
        SELECT username, photo, fullname, bio
        FROM users
        WHERE username=?
        """,
        (session["user"],)
    )

    user = cur.fetchone()
    conn.close()

    return render_template("profile.html", user=user)

# GANTI PASSWORD
@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user" not in session:
        return redirect("/login")

    pesan = ""

    if request.method == "POST":

        new_password = request.form["password"]
        hashed_password = generate_password_hash(new_password)

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET password=? WHERE username=?",
            (hashed_password, session["user"])
        )

        conn.commit()
        conn.close()

        pesan = "Password berhasil diubah"

    return render_template("change_password.html", pesan=pesan)

# EDIT PROFILE
@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":

        fullname = request.form["fullname"]
        bio = request.form["bio"]
        new_password = request.form["password"]

        if "photo" in request.files:
            file = request.files["photo"]

            if file and file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

                cur.execute(
                    "UPDATE users SET photo=? WHERE username=?",
                    (filename, username)
                )

        cur.execute(
            "UPDATE users SET fullname=?, bio=? WHERE username=?",
            (fullname, bio, username)
        )

        if new_password != "":
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

# PAKET TRIP DETAIL
@app.route("/packages")
def packages():
    return render_template("packages.html")

# BOOKING FORM
@app.route("/booking/<trip_name>", methods=["GET", "POST"])
def booking(trip_name):

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        full_name = request.form["full_name"]
        phone = request.form["phone"]
        people = request.form["people"]
        trip_date = request.form["trip_date"]
        note = request.form["note"]

        if len(full_name) < 3:
            return "Nama terlalu pendek"

        if not phone.isdigit():
            return "Nomor WhatsApp harus angka"

        if len(phone) < 10:
            return "Nomor WhatsApp tidak valid"

        if int(people) < 1:
            return "Jumlah peserta minimal 1"

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO bookings
        (username, trip_name, full_name, phone, people, trip_date, note, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user"],
            trip_name,
            full_name,
            phone,
            people,
            trip_date,
            note,
            "Pending"
        ))

        conn.commit()
        conn.close()

        return redirect("/my-bookings")

    return render_template("booking.html", trip_name=trip_name)

# LIHAT BOOKING
@app.route("/my-bookings")
def my_bookings():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT trip_name, full_name, trip_date, status
    FROM bookings
    WHERE username=?
    ORDER BY id DESC
    """, (session["user"],))

    data = cur.fetchall()
    conn.close()

    return render_template("my_bookings.html", data=data)

# ABOUT US
@app.route("/about")
def about():
    return render_template("about.html")

# CONTACT US
@app.route("/contact")
def contact():
    return render_template("contact.html")

# LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ADMIN PANEL
@app.route("/admin")
def admin():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT role FROM users WHERE username=?",
        (session["user"],)
    )

    user = cur.fetchone()

    if not user:
        conn.close()
        return redirect("/login")

    role = user[0]

    if role != "admin":
        conn.close()
        flash("Akses ditolak.")
        return redirect("/dashboard")

    # Statistik
    cur.execute("SELECT COUNT(*) FROM bookings")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM bookings WHERE status='Pending'")
    pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM bookings WHERE status='Confirmed'")
    confirmed = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM bookings WHERE status='Cancelled'")
    cancelled = cur.fetchone()[0]

# Data booking
    cur.execute("""
    SELECT id, username, trip_name, full_name, phone, people, trip_date, status
    FROM bookings
    ORDER BY id DESC
    """)

    data = cur.fetchall()
    conn.close()

    return render_template(
        "admin.html",
        data=data,
        total=total,
        pending=pending,
        confirmed=confirmed,
        cancelled=cancelled
)

# UPDATE STATUS BOOKING
@app.route("/update-booking/<int:id>/<status>")
def update_booking(id, status):

    if "user" not in session:
        return redirect("/login")

    # opsional: batasi admin tertentu
    if session["user"] != "admin":
        return redirect("/dashboard")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "UPDATE bookings SET status=? WHERE id=?",
        (status, id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

if __name__ == "__main__":
    app.run()