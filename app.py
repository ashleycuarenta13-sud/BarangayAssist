from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

app.secret_key = "barangayassist-secret-key"


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "barangayassist",
    "cursorclass": pymysql.cursors.DictCursor
}


def get_db():
    return pymysql.connect(**DB_CONFIG)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    connection = get_db()

    with connection.cursor() as cursor:

        # USERS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                purok VARCHAR(100) DEFAULT '',
                contact VARCHAR(20) DEFAULT '',
                role VARCHAR(20) NOT NULL DEFAULT 'resident'
            )
        """)

        # CONCERNS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concerns (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                category VARCHAR(100) DEFAULT 'General',
                status VARCHAR(30) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Make sure existing users table has role column
        cursor.execute("""
            SHOW COLUMNS FROM users LIKE 'role'
        """)

        role_column = cursor.fetchone()

        if not role_column:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'resident'
            """)

    connection.commit()
    connection.close()


# ============================================================
# CREATE DEFAULT ADMIN
# ============================================================

def create_default_admin():

    connection = get_db()

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT id
            FROM users
            WHERE email = %s
        """, ("admin@barangayassist.local",))

        admin = cursor.fetchone()

        if not admin:

            password_hash = generate_password_hash("Admin@12345")

            cursor.execute("""
                INSERT INTO users
                (name, email, password, purok, contact, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                "Barangay Administrator",
                "admin@barangayassist.local",
                password_hash,
                "",
                "",
                "admin"
            ))

            connection.commit()

            print("----------------------------------------")
            print("DEFAULT ADMIN ACCOUNT CREATED")
            print("Email: admin@barangayassist.local")
            print("Password: Admin@12345")
            print("----------------------------------------")

    connection.close()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_clean_name(name):

    if name and '@' not in name:
        return name.title()

    if name:
        return name.split('@')[0].replace('.', ' ').replace('_', ' ').title()

    return "User"


def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("index"))

        if session.get("role") != "admin":
            return "403 - Access Denied", 403

        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# JINJA FILTERS
# ============================================================

@app.template_filter("truncatewords")
def truncatewords_filter(s, count):

    if not s:
        return ""

    words = s.split()

    if len(words) <= int(count):
        return s

    return " ".join(words[:int(count)]) + "..."


@app.template_filter("slugify")
def slugify_filter(s):

    if not s:
        return ""

    return s.lower().replace(" ", "-")


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    if "user_id" in session:

        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["POST"])
def register():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    purok = request.form.get("purok", "").strip()
    contact = request.form.get("contact", "").strip()

    if not name or not email or not password:
        return redirect(url_for("index"))

    connection = get_db()

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT id
            FROM users
            WHERE email = %s
        """, (email,))

        existing_user = cursor.fetchone()

        if existing_user:
            connection.close()
            return redirect(url_for("index"))

        password_hash = generate_password_hash(password)

        # IMPORTANT:
        # Every public registration is automatically a RESIDENT.
        cursor.execute("""
            INSERT INTO users
            (name, email, password, purok, contact, role)
            VALUES (%s, %s, %s, %s, %s, 'resident')
        """, (
            name,
            email,
            password_hash,
            purok,
            contact
        ))

        connection.commit()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

    connection.close()

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["role"] = user["role"]

    return redirect(url_for("dashboard"))


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["POST"])
def login():

    email = request.form.get("email", "").strip()

    if not email:
        email = request.form.get("username", "").strip()

    password = request.form.get("password", "")

    connection = get_db()

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

    connection.close()

    if user and check_password_hash(user["password"], password):

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["role"] = user["role"]

        # ADMIN
        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))

        # RESIDENT
        return redirect(url_for("dashboard"))

    return redirect(url_for("index", error=1))


# ============================================================
# RESIDENT DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("index"))

    # Prevent admin from entering resident dashboard
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    connection = get_db()

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT *
            FROM concerns
            ORDER BY created_at DESC
        """)

        concerns = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE status = 'Pending'
        """)

        pending_count = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE status = 'In Progress'
        """)

        in_progress_count = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE status = 'Resolved'
        """)

        resolved_count = cursor.fetchone()["c"]

    connection.close()

    return render_template(
        "dashboard.html",
        concerns=concerns,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        clean_name=get_clean_name(
            session.get("user_name", "")
        )
    )


# ============================================================
# SUBMIT CONCERN
# ============================================================

@app.route("/submit_concern", methods=["GET", "POST"])
def submit_concern():

    if "user_id" not in session:
        return redirect(url_for("index"))

    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        title = request.form.get("title", "").strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            "General"
        ).strip()

        if not title or not description:
            return redirect(
                url_for("submit_concern")
            )

        connection = get_db()

        with connection.cursor() as cursor:

            cursor.execute("""
                INSERT INTO concerns
                (title, description, category, status)
                VALUES (%s, %s, %s, 'Pending')
            """, (
                title,
                description,
                category
            ))

        connection.commit()
        connection.close()

        return redirect(url_for("dashboard"))

    return render_template(
        "submit_concern.html",
        clean_name=get_clean_name(
            session.get("user_name", "")
        )
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    connection = get_db()

    with connection.cursor() as cursor:

        # --------------------------------------------
        # TOTAL USERS
        # --------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
        """)

        total_users = cursor.fetchone()["total"]


        # --------------------------------------------
        # TOTAL RESIDENTS
        # --------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'resident'
        """)

        total_residents = cursor.fetchone()["total"]


        # --------------------------------------------
        # TOTAL STAFF
        # --------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'staff'
        """)

        total_staff = cursor.fetchone()["total"]


        # --------------------------------------------
        # TOTAL CONCERNS
        # --------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM concerns
        """)

        total_concerns = cursor.fetchone()["total"]


        # --------------------------------------------
        # PENDING
        # --------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM concerns
            WHERE status = 'Pending'
        """)

        pending_count = cursor.fetchone()["total"]


        # --------------------------------------------
        # IN PROGRESS
        # --------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM concerns
            WHERE status = 'In Progress'
        """)

        in_progress_count = cursor.fetchone()["total"]


        # --------------------------------------------
        # RESOLVED
        # --------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM concerns
            WHERE status = 'Resolved'
        """)

        resolved_count = cursor.fetchone()["total"]


        # --------------------------------------------
        # RECENT CONCERNS
        # --------------------------------------------

        cursor.execute("""
            SELECT *
            FROM concerns
            ORDER BY created_at DESC
            LIMIT 8
        """)

        recent_concerns = cursor.fetchall()

    connection.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_residents=total_residents,
        total_staff=total_staff,
        total_concerns=total_concerns,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        recent_concerns=recent_concerns,
        clean_name=get_clean_name(
            session.get(
                "user_name",
                "Administrator"
            )
        )
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    init_db()

    create_default_admin()

    app.run(debug=True)