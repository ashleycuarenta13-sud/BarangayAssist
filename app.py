from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import time

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

        # Ownership and assignment fields for existing databases.
        cursor.execute("SHOW COLUMNS FROM concerns LIKE 'resident_id'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE concerns
                ADD COLUMN resident_id INT NULL AFTER status
            """)

        cursor.execute("SHOW COLUMNS FROM concerns LIKE 'assigned_staff_id'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE concerns
                ADD COLUMN assigned_staff_id INT NULL AFTER resident_id
            """)

        cursor.execute("SHOW INDEX FROM concerns WHERE Key_name = 'idx_concerns_resident'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE concerns
                ADD INDEX idx_concerns_resident (resident_id)
            """)

        cursor.execute("SHOW INDEX FROM concerns WHERE Key_name = 'idx_concerns_staff'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE concerns
                ADD INDEX idx_concerns_staff (assigned_staff_id)
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

            password_hash = generate_password_hash("Admin123")

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
# LOGIN RATE-LIMITING / LOCKOUT
# ============================================================
# Simple in-memory tracker keyed by the submitted email/username.
# After MAX_FAILED_ATTEMPTS consecutive failures, the account is
# temporarily locked for LOCKOUT_SECONDS. A successful login clears
# the counter. This is in-memory only (resets if the server restarts) —
# fine for this lab; a production app would use Redis/DB instead.

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60

# { "email": {"failed": int, "locked_until": float|None} }
LOGIN_ATTEMPTS = {}


def is_locked(identifier):
    record = LOGIN_ATTEMPTS.get(identifier)
    if not record:
        return False, 0

    locked_until = record.get("locked_until")
    if locked_until and time.time() < locked_until:
        remaining = int(locked_until - time.time())
        return True, remaining

    # Lockout period has expired — reset the record.
    if locked_until and time.time() >= locked_until:
        LOGIN_ATTEMPTS.pop(identifier, None)

    return False, 0


def register_failed_attempt(identifier):
    record = LOGIN_ATTEMPTS.setdefault(identifier, {"failed": 0, "locked_until": None})
    record["failed"] += 1

    if record["failed"] >= MAX_FAILED_ATTEMPTS:
        record["locked_until"] = time.time() + LOCKOUT_SECONDS


def clear_attempts(identifier):
    LOGIN_ATTEMPTS.pop(identifier, None)


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

        if session.get("role") == "staff":
            return redirect(url_for("staff_dashboard"))

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

    identifier = email.lower()

    # --------------------------------------------------
    # Check lockout BEFORE touching the database.
    # --------------------------------------------------
    locked, remaining = is_locked(identifier)

    if locked:
        return (
            f"Account temporarily locked. Too many failed attempts. "
            f"Please try again in {remaining} seconds.",
            429
        )

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

        # Successful login clears any failed-attempt history.
        clear_attempts(identifier)

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["role"] = user["role"]

        # ADMIN
        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))

        # BARANGAY STAFF
        if user["role"] == "staff":
            return redirect(url_for("staff_dashboard"))

        # RESIDENT
        return redirect(url_for("dashboard"))

    # --------------------------------------------------
    # Failed login: record the attempt. If this failure just
    # crossed the threshold, respond with a lockout message
    # (instead of the normal redirect) so the lockout takes
    # effect immediately on the attempt that triggers it.
    # --------------------------------------------------
    register_failed_attempt(identifier)

    locked_now, remaining_now = is_locked(identifier)

    if locked_now:
        return (
            f"Account temporarily locked. Too many failed attempts. "
            f"Please try again in {remaining_now} seconds.",
            429
        )

    return redirect(url_for("index.html", error=1)), 200


# ============================================================
# RESIDENT DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("index"))

    # Keep role-specific dashboards separate.
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") == "staff":
        return redirect(url_for("staff_dashboard"))

    connection = get_db()

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT *
            FROM concerns
            WHERE resident_id = %s
            ORDER BY created_at DESC
        """, (session["user_id"],))

        concerns = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE status = 'Pending' AND resident_id = %s
        """, (session["user_id"],))

        pending_count = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE status = 'In Progress' AND resident_id = %s
        """, (session["user_id"],))

        in_progress_count = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE status = 'Resolved' AND resident_id = %s
        """, (session["user_id"],))

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
# STAFF DASHBOARD
# ============================================================

@app.route("/staff/dashboard")
def staff_dashboard():

    if "user_id" not in session:
        return redirect(url_for("index"))

    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") != "staff":
        return redirect(url_for("dashboard"))

    connection = get_db()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.*, r.name AS resident_name
            FROM concerns c
            LEFT JOIN users r ON r.id = c.resident_id
            WHERE c.assigned_staff_id = %s
            ORDER BY c.created_at DESC
        """, (session["user_id"],))
        concerns = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE assigned_staff_id = %s
        """, (session["user_id"],))
        total_count = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE status = 'Pending' AND assigned_staff_id = %s
        """, (session["user_id"],))
        pending_count = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE status = 'In Progress' AND assigned_staff_id = %s
        """, (session["user_id"],))
        in_progress_count = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) AS c
            FROM concerns
            WHERE status = 'Resolved' AND assigned_staff_id = %s
        """, (session["user_id"],))
        resolved_count = cursor.fetchone()["c"]

    connection.close()

    return render_template(
        "staff_dashboard.html",
        concerns=concerns,
        total_count=total_count,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        clean_name=get_clean_name(session.get("user_name", ""))
    )


@app.route("/staff/update-concern/<int:concern_id>", methods=["POST"])
def staff_update_concern(concern_id):

    if "user_id" not in session:
        return redirect(url_for("index"))

    if session.get("role") != "staff":
        return redirect(url_for("dashboard"))

    status = request.form.get("status", "Pending").strip()
    allowed_statuses = {"Pending", "In Progress", "Resolved"}

    if status not in allowed_statuses:
        status = "Pending"

    connection = get_db()
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE concerns
            SET status = %s
            WHERE id = %s
        """, (status, concern_id))
    connection.commit()
    connection.close()

    return redirect(url_for("staff_dashboard"))


# ============================================================
# SUBMIT CONCERN
# ============================================================

@app.route("/submit_concern", methods=["GET", "POST"])
def submit_concern():

    if "user_id" not in session:
        return redirect(url_for("index"))

    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") == "staff":
        return redirect(url_for("staff_dashboard"))

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
                (title, description, category, status, resident_id)
                VALUES (%s, %s, %s, 'Pending', %s)
            """, (
                title,
                description,
                category,
                session["user_id"]
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
            SELECT c.*, r.name AS resident_name, s.name AS assigned_staff_name
            FROM concerns c
            LEFT JOIN users r ON r.id = c.resident_id
            LEFT JOIN users s ON s.id = c.assigned_staff_id
            ORDER BY c.created_at DESC
            LIMIT 8
        """)

        recent_concerns = cursor.fetchall()

        cursor.execute("""
            SELECT id, name, email
            FROM users
            WHERE role = 'staff'
            ORDER BY name ASC
        """)

        staff_users = cursor.fetchall()

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
        staff_users=staff_users,
        clean_name=get_clean_name(
            session.get(
                "user_name",
                "Administrator"
            )
        )
    )


@app.route("/admin/assign-concern/<int:concern_id>", methods=["POST"])
@admin_required
def admin_assign_concern(concern_id):

    assigned_staff_id = request.form.get("assigned_staff_id", "").strip()

    if assigned_staff_id:
        try:
            assigned_staff_id = int(assigned_staff_id)
        except ValueError:
            assigned_staff_id = None

    connection = get_db()

    with connection.cursor() as cursor:
        if assigned_staff_id:
            cursor.execute("""
                SELECT id
                FROM users
                WHERE id = %s AND role = 'staff'
            """, (assigned_staff_id,))

            valid_staff = cursor.fetchone()
            if not valid_staff:
                assigned_staff_id = None

        cursor.execute("""
            UPDATE concerns
            SET assigned_staff_id = %s
            WHERE id = %s
        """, (assigned_staff_id, concern_id))

    connection.commit()
    connection.close()

    return redirect(url_for("admin_dashboard"))


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
