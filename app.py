
import os
import time
from functools import wraps

import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get(
    "BARANGAYASSIST_SECRET_KEY",
    "dev-only-change-this-secret-key"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "barangayassist"),
    "cursorclass": pymysql.cursors.DictCursor,
    "charset": "utf8mb4",
    "connect_timeout": 5
}


def get_db():
    return pymysql.connect(**DB_CONFIG)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
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

            cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE users
                    ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'resident'
                """)

            cursor.execute("SHOW COLUMNS FROM concerns LIKE 'resident_id'")
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE concerns
                    ADD COLUMN resident_id INT NULL
                """)

            cursor.execute("SHOW COLUMNS FROM concerns LIKE 'assigned_staff_id'")
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE concerns
                    ADD COLUMN assigned_staff_id INT NULL
                """)

            cursor.execute("""
                SHOW INDEX FROM concerns
                WHERE Key_name = 'idx_concerns_resident'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE concerns
                    ADD INDEX idx_concerns_resident (resident_id)
                """)

            cursor.execute("""
                SHOW INDEX FROM concerns
                WHERE Key_name = 'idx_concerns_staff'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE concerns
                    ADD INDEX idx_concerns_staff (assigned_staff_id)
                """)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ============================================================
# DEFAULT ADMIN AND STAFF ACCOUNTS
# ============================================================

def create_default_accounts():
    connection = get_db()

    default_accounts = [
        {
            "name": "Barangay Administrator",
            "email": "admin.barangayassist@gmail.com",
            "password": os.environ.get(
                "BARANGAYASSIST_ADMIN_PASSWORD", "Admin@12345"
            ),
            "role": "admin"
        },
        {
            "name": "Barangay Staff",
            "email": "staff.barangayassist@gmail.com",
            "password": os.environ.get(
                "BARANGAYASSIST_STAFF_PASSWORD", "Staff@12345"
            ),
            "role": "staff"
        }
    ]

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM users
                WHERE email = %s
            """, ("admin@barangayassist.local",))
            old_admin = cursor.fetchone()

            cursor.execute("""
                SELECT id FROM users
                WHERE email = %s
            """, ("admin.barangayassist@gmail.com",))
            new_admin = cursor.fetchone()

            if old_admin and not new_admin:
                cursor.execute("""
                    UPDATE users
                    SET email = %s, role = %s
                    WHERE id = %s
                """, (
                    "admin.barangayassist@gmail.com",
                    "admin",
                    old_admin["id"]
                ))

            for account in default_accounts:
                cursor.execute("""
                    SELECT id FROM users
                    WHERE email = %s
                """, (account["email"],))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE users
                        SET role = %s
                        WHERE id = %s
                    """, (account["role"], existing["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO users
                        (name, email, password, purok, contact, role)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        account["name"],
                        account["email"],
                        generate_password_hash(account["password"]),
                        "",
                        "",
                        account["role"]
                    ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    print("BarangayAssist default account initialization complete.")
    print("Local development admin: admin.barangayassist@gmail.com / Admin@12345")
    print("Local development staff: staff.barangayassist@gmail.com / Staff@12345")
    print("Change these credentials before deployment.")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_clean_name(name):
    if name and "@" not in name:
        return name.title()

    if name:
        return name.split("@")[0].replace(".", " ").replace("_", " ").title()

    return "User"


def admin_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("index"))

        if session.get("role") != "admin":
            return "403 - Access Denied", 403

        return function(*args, **kwargs)

    return decorated_function


def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("index"))

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# LOGIN RATE LIMITING
# ============================================================

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
LOGIN_ATTEMPTS = {}


def is_locked(identifier):
    record = LOGIN_ATTEMPTS.get(identifier)

    if not record:
        return False, 0

    locked_until = record.get("locked_until")

    if locked_until and time.time() < locked_until:
        remaining = max(1, int(locked_until - time.time() + 0.99))
        return True, remaining

    if locked_until and time.time() >= locked_until:
        LOGIN_ATTEMPTS.pop(identifier, None)

    return False, 0


def register_failed_attempt(identifier):
    record = LOGIN_ATTEMPTS.setdefault(
        identifier,
        {"failed": 0, "locked_until": None}
    )

    record["failed"] += 1

    if record["failed"] >= MAX_FAILED_ATTEMPTS:
        record["locked_until"] = time.time() + LOCKOUT_SECONDS


def clear_attempts(identifier):
    LOGIN_ATTEMPTS.pop(identifier, None)


# ============================================================
# JINJA FILTERS
# ============================================================

@app.template_filter("truncatewords")
def truncatewords_filter(value, count):
    if not value:
        return ""

    words = value.split()
    count = max(0, int(count))

    if len(words) <= count:
        return value

    return " ".join(words[:count]) + "..."


@app.template_filter("slugify")
def slugify_filter(value):
    if not value:
        return ""

    return value.lower().replace(" ", "-")


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():
    if "user_id" in session:
        role = session.get("role")

        if role == "admin":
            return redirect(url_for("admin_dashboard"))

        if role == "staff":
            return redirect(url_for("staff_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("index.html", error=request.args.get("error"))


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    purok = request.form.get("purok", "").strip()
    contact = request.form.get("contact", "").strip()

    if not name or not email or not password:
        return redirect(url_for("index", error="missing_fields"))

    if len(name) > 150 or len(email) > 150 or len(password) < 8:
        return redirect(url_for("index", error="invalid_input"))

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return redirect(url_for("index", error="invalid_email"))

    if len(purok) > 100 or len(contact) > 20:
        return redirect(url_for("index", error="invalid_input"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM users
                WHERE LOWER(email) = %s
            """, (email,))

            if cursor.fetchone():
                return redirect(url_for("index", error="email_exists"))

            cursor.execute("""
                INSERT INTO users
                (name, email, password, purok, contact, role)
                VALUES (%s, %s, %s, %s, %s, 'resident')
            """, (
                name,
                email,
                generate_password_hash(password),
                purok,
                contact
            ))

        connection.commit()

    except pymysql.err.IntegrityError:
        connection.rollback()
        return redirect(url_for("index", error="email_exists"))

    except Exception:
        connection.rollback()
        app.logger.exception("Registration failed")
        return "Registration failed. Please try again.", 500

    finally:
        connection.close()

    # Do NOT sign the resident in automatically. Send them back to the
    # landing page so they see the "account created" confirmation and
    # log in with their new credentials.
    return redirect(url_for("index", registered="1"))


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()

    if not email:
        email = request.form.get("username", "").strip().lower()

    password = request.form.get("password", "")
    identifier = email

    if not identifier or not password:
        return redirect(url_for("index", error="missing_fields_login"))

    locked, remaining = is_locked(identifier)

    if locked:
        return f"Too many failed attempts. Try again in {remaining} seconds.", 429

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM users
                WHERE LOWER(email) = %s
            """, (email,))
            user = cursor.fetchone()

    except Exception:
        app.logger.exception("Login database query failed")
        return "Login is temporarily unavailable. Please try again.", 500

    finally:
        connection.close()

    if user and check_password_hash(user["password"], password):
        clear_attempts(identifier)

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))

        if user["role"] == "staff":
            return redirect(url_for("staff_dashboard"))

        return redirect(url_for("dashboard"))

    register_failed_attempt(identifier)
    locked_now, remaining_now = is_locked(identifier)

    if locked_now:
        return f"Too many failed attempts. Try again in {remaining_now} seconds.", 429

    return redirect(url_for("index", error="invalid_login"))


# ============================================================
# RESIDENT DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") == "staff":
        return redirect(url_for("staff_dashboard"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM concerns
                WHERE resident_id = %s
                ORDER BY created_at DESC
            """, (session["user_id"],))
            concerns = cursor.fetchall()

            cursor.execute("""
                SELECT
                    SUM(status = 'Pending') AS pending_count,
                    SUM(status = 'In Progress') AS in_progress_count,
                    SUM(status = 'Resolved') AS resolved_count
                FROM concerns
                WHERE resident_id = %s
            """, (session["user_id"],))
            counts = cursor.fetchone()

    except Exception:
        app.logger.exception("Resident dashboard query failed")
        return "Unable to load the dashboard. Please try again.", 500

    finally:
        connection.close()

    return render_template(
        "dashboard.html",
        concerns=concerns,
        pending_count=counts["pending_count"] or 0,
        in_progress_count=counts["in_progress_count"] or 0,
        resolved_count=counts["resolved_count"] or 0,
        clean_name=get_clean_name(session.get("user_name", ""))
    )


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route("/staff/dashboard")
@login_required
def staff_dashboard():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") != "staff":
        return redirect(url_for("dashboard"))

    connection = get_db()

    try:
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
                SELECT
                    COUNT(*) AS total_count,
                    SUM(status = 'Pending') AS pending_count,
                    SUM(status = 'In Progress') AS in_progress_count,
                    SUM(status = 'Resolved') AS resolved_count
                FROM concerns
                WHERE assigned_staff_id = %s
            """, (session["user_id"],))
            counts = cursor.fetchone()

    except Exception:
        app.logger.exception("Staff dashboard query failed")
        return "Unable to load the staff dashboard. Please try again.", 500

    finally:
        connection.close()

    return render_template(
        "staff_dashboard.html",
        concerns=concerns,
        total_count=counts["total_count"] or 0,
        pending_count=counts["pending_count"] or 0,
        in_progress_count=counts["in_progress_count"] or 0,
        resolved_count=counts["resolved_count"] or 0,
        clean_name=get_clean_name(session.get("user_name", ""))
    )


# ============================================================
# STAFF ASSIGNED CONCERNS
# ============================================================

@app.route("/staff/concerns")
@login_required
def staff_concerns():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") != "staff":
        return redirect(url_for("dashboard"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.*, r.name AS resident_name
                FROM concerns c
                LEFT JOIN users r ON r.id = c.resident_id
                WHERE c.assigned_staff_id = %s
                ORDER BY c.created_at DESC
            """, (session["user_id"],))
            concerns = cursor.fetchall()

    except Exception:
        app.logger.exception("Staff concerns query failed")
        return "Unable to load your assigned concerns. Please try again.", 500

    finally:
        connection.close()

    return render_template(
        "staff_concerns.html",
        concerns=concerns,
        clean_name=get_clean_name(session.get("user_name", ""))
    )


# ============================================================
# STAFF PROFILE
# ============================================================

@app.route("/staff/profile")
@login_required
def staff_profile():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") != "staff":
        return redirect(url_for("dashboard"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name, email, purok, contact, role
                FROM users
                WHERE id = %s
            """, (session["user_id"],))
            account = cursor.fetchone()

            cursor.execute("""
                SELECT
                    COUNT(*) AS total_concerns,
                    SUM(status = 'Pending') AS pending_count,
                    SUM(status = 'In Progress') AS in_progress_count,
                    SUM(status = 'Resolved') AS resolved_count
                FROM concerns
                WHERE assigned_staff_id = %s
            """, (session["user_id"],))
            stats = cursor.fetchone()

    except Exception:
        app.logger.exception("Staff profile query failed")
        return "Unable to load your profile. Please try again.", 500

    finally:
        connection.close()

    if not account:
        return redirect(url_for("logout"))

    return render_template(
        "staff_profile.html",
        account=account,
        total_concerns=stats["total_concerns"] or 0,
        pending_count=stats["pending_count"] or 0,
        in_progress_count=stats["in_progress_count"] or 0,
        resolved_count=stats["resolved_count"] or 0,
        clean_name=get_clean_name(session.get("user_name", ""))
    )


# ============================================================
# STAFF UPDATE CONCERN
# ============================================================

@app.route("/staff/update-concern/<int:concern_id>", methods=["POST"])
@login_required
def staff_update_concern(concern_id):
    if session.get("role") != "staff":
        return "403 - Access Denied", 403

    status = request.form.get("status", "").strip()
    allowed_statuses = {"Pending", "In Progress", "Resolved"}

    if status not in allowed_statuses:
        return redirect(url_for("staff_dashboard"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE concerns
                SET status = %s
                WHERE id = %s AND assigned_staff_id = %s
            """, (status, concern_id, session["user_id"]))

        connection.commit()

    except Exception:
        connection.rollback()
        app.logger.exception("Staff concern update failed")
        return "Unable to update the concern. Please try again.", 500

    finally:
        connection.close()

    flash("Concern status updated to " + status + ".", "success")

    return redirect(url_for("staff_dashboard"))


# ============================================================
# SUBMIT CONCERN
# ============================================================

@app.route("/submit_concern", methods=["GET", "POST"])
@login_required
def submit_concern():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") == "staff":
        return redirect(url_for("staff_dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "General").strip()

        allowed_categories = {
            "General",
            "Street Lights",
            "Waste Collection",
            "Water Supply",
            "Roads & Drainage",
            "Community Services"
        }

        if not title or not description:
            return redirect(url_for("submit_concern", error="missing_fields"))

        if len(title) > 200 or category not in allowed_categories:
            return redirect(url_for("submit_concern", error="invalid_input"))

        connection = get_db()

        try:
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

        except Exception:
            connection.rollback()
            app.logger.exception("Concern submission failed")
            return "Unable to submit your concern. Please try again.", 500

        finally:
            connection.close()

        return redirect(url_for("dashboard"))

    return render_template(
        "submit_concern.html",
        clean_name=get_clean_name(session.get("user_name", "")),
        error=request.args.get("error")
    )


# ============================================================
# MY CONCERNS
# ============================================================

@app.route("/my_concerns")
@login_required
def my_concerns():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") == "staff":
        return redirect(url_for("staff_dashboard"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM concerns
                WHERE resident_id = %s
                ORDER BY created_at DESC
            """, (session["user_id"],))
            concerns = cursor.fetchall()

            cursor.execute("""
                SELECT
                    SUM(status = 'Pending') AS pending_count,
                    SUM(status = 'In Progress') AS in_progress_count,
                    SUM(status = 'Resolved') AS resolved_count
                FROM concerns
                WHERE resident_id = %s
            """, (session["user_id"],))
            counts = cursor.fetchone()

    except Exception:
        app.logger.exception("My concerns query failed")
        return "Unable to load your concerns. Please try again.", 500

    finally:
        connection.close()

    return render_template(
        "my_concerns.html",
        concerns=concerns,
        pending_count=counts["pending_count"] or 0,
        in_progress_count=counts["in_progress_count"] or 0,
        resolved_count=counts["resolved_count"] or 0,
        clean_name=get_clean_name(session.get("user_name", ""))
    )


# ============================================================
# PROFILE
# ============================================================

@app.route("/profile")
@login_required
def profile():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if session.get("role") == "staff":
        return redirect(url_for("staff_dashboard"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name, email, purok, contact, role
                FROM users
                WHERE id = %s
            """, (session["user_id"],))
            account = cursor.fetchone()

            cursor.execute("""
                SELECT
                    COUNT(*) AS total_concerns,
                    SUM(status = 'Pending') AS pending_count,
                    SUM(status = 'In Progress') AS in_progress_count,
                    SUM(status = 'Resolved') AS resolved_count
                FROM concerns
                WHERE resident_id = %s
            """, (session["user_id"],))
            stats = cursor.fetchone()

    except Exception:
        app.logger.exception("Profile query failed")
        return "Unable to load your profile. Please try again.", 500

    finally:
        connection.close()

    if not account:
        return redirect(url_for("logout"))

    return render_template(
        "profile.html",
        account=account,
        total_concerns=stats["total_concerns"] or 0,
        pending_count=stats["pending_count"] or 0,
        in_progress_count=stats["in_progress_count"] or 0,
        resolved_count=stats["resolved_count"] or 0,
        clean_name=get_clean_name(session.get("user_name", ""))
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_concerns,
                    SUM(CASE WHEN LOWER(status) = 'pending'
                        THEN 1 ELSE 0 END) AS pending_count,
                    SUM(CASE WHEN LOWER(status) IN
                        ('in progress', 'in_progress')
                        THEN 1 ELSE 0 END) AS in_progress_count,
                    SUM(CASE WHEN LOWER(status) = 'resolved'
                        THEN 1 ELSE 0 END) AS resolved_count
                FROM concerns
            """)
            stats = cursor.fetchone() or {}

            cursor.execute("""
                SELECT COUNT(*) AS total_residents
                FROM users
                WHERE LOWER(role) = 'resident'
            """)
            total_residents = cursor.fetchone()["total_residents"]

            cursor.execute("""
                SELECT COUNT(*) AS total_staff
                FROM users
                WHERE LOWER(role) = 'staff'
            """)
            total_staff = cursor.fetchone()["total_staff"]

            cursor.execute("""
                SELECT c.*, u.name AS assigned_staff_name
                FROM concerns c
                LEFT JOIN users u ON u.id = c.assigned_staff_id
                ORDER BY c.created_at DESC
                LIMIT 10
            """)
            recent_concerns = cursor.fetchall()

            cursor.execute("""
                SELECT id, name
                FROM users
                WHERE LOWER(role) = 'staff'
                ORDER BY name ASC
            """)
            staff_users = cursor.fetchall()

        return render_template(
            "admin_dashboard.html",
            total_concerns=stats.get("total_concerns") or 0,
            pending_count=stats.get("pending_count") or 0,
            in_progress_count=stats.get("in_progress_count") or 0,
            resolved_count=stats.get("resolved_count") or 0,
            total_residents=total_residents or 0,
            total_staff=total_staff or 0,
            recent_concerns=recent_concerns,
            staff_users=staff_users,
            clean_name=get_clean_name(
                session.get("user_name", "Administrator")
            )
        )

    except Exception:
        app.logger.exception("Admin dashboard failed")
        return "Unable to load the admin dashboard.", 500

    finally:
        connection.close()


# ============================================================
# ADMIN ALL CONCERNS — ONLY ONE ROUTE
# ============================================================

@app.route("/admin/concerns")
@admin_required
def admin_concerns():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    c.*,
                    r.name AS resident_name,
                    r.email AS resident_email,
                    s.name AS assigned_staff_name
                FROM concerns c
                LEFT JOIN users r ON r.id = c.resident_id
                LEFT JOIN users s ON s.id = c.assigned_staff_id
                ORDER BY c.created_at DESC
            """)
            concerns = cursor.fetchall()

            cursor.execute("""
                SELECT id, name, email
                FROM users
                WHERE LOWER(role) = 'staff'
                ORDER BY name ASC
            """)
            staff_users = cursor.fetchall()

        return render_template(
            "admin_concerns.html",
            concerns=concerns,
            staff_users=staff_users,
            clean_name=get_clean_name(
                session.get("user_name", "Administrator")
            )
        )

    except Exception:
        app.logger.exception("Admin concerns page failed")
        return "Unable to load concerns. Please try again.", 500

    finally:
        connection.close()


# ============================================================
# ADMIN ASSIGN CONCERN
# ============================================================

@app.route("/admin/concerns/<int:concern_id>/assign", methods=["POST"])
@admin_required
def admin_assign_concern(concern_id):
    staff_id = request.form.get("assigned_staff_id", "").strip()

    # Return the admin to the page they submitted the form from.
    return_to = request.form.get("next", "").strip()
    if return_to in ("admin_dashboard", "admin_concerns"):
        destination = return_to
    else:
        destination = "admin_concerns"

    if not staff_id.isdigit():
        flash("Please select a valid staff member.", "error")
        return redirect(url_for(destination))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id
                FROM users
                WHERE id = %s AND LOWER(role) = 'staff'
            """, (int(staff_id),))
            staff = cursor.fetchone()

            if not staff:
                flash("Selected staff account was not found.", "error")
                return redirect(url_for(destination))

            cursor.execute("""
                UPDATE concerns
                SET assigned_staff_id = %s
                WHERE id = %s
            """, (int(staff_id), concern_id))

        connection.commit()
        flash("Concern assigned successfully.", "success")

    except Exception:
        connection.rollback()
        app.logger.exception("Concern assignment failed")
        flash("Unable to assign the concern.", "error")

    finally:
        connection.close()

    return redirect(url_for(destination))


# ============================================================
# ADMIN — USERS
# ============================================================

@app.route("/admin/users")
@admin_required
def admin_users():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    u.id,
                    u.name,
                    u.email,
                    u.purok,
                    u.contact,
                    u.role,
                    COUNT(c.id) AS concern_count,
                    SUM(CASE WHEN LOWER(c.status) = 'resolved'
                        THEN 1 ELSE 0 END) AS resolved_count
                FROM users u
                LEFT JOIN concerns c ON c.resident_id = u.id
                GROUP BY u.id
                ORDER BY
                    CASE WHEN LOWER(u.role) = 'admin' THEN 0
                         WHEN LOWER(u.role) = 'staff' THEN 1
                         ELSE 2 END,
                    u.name ASC
            """)
            users = cursor.fetchall()

        return render_template(
            "admin_users.html",
            users=users,
            resident_count=sum(
                1 for u in users if (u.get("role") or "").lower() == "resident"
            ),
            staff_count=sum(
                1 for u in users if (u.get("role") or "").lower() == "staff"
            ),
            clean_name=get_clean_name(session.get("user_name", "Administrator"))
        )

    except Exception:
        app.logger.exception("Admin users page failed")
        return "Unable to load users. Please try again.", 500

    finally:
        connection.close()


# ============================================================
# ADMIN — BARANGAY STAFF
# ============================================================

@app.route("/admin/staff")
@admin_required
def admin_staff():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    u.id,
                    u.name,
                    u.email,
                    u.purok,
                    u.contact,
                    COUNT(c.id) AS assigned_count,
                    SUM(CASE WHEN LOWER(c.status) = 'pending'
                        THEN 1 ELSE 0 END) AS pending_count,
                    SUM(CASE WHEN LOWER(c.status) IN
                        ('in progress', 'in_progress')
                        THEN 1 ELSE 0 END) AS in_progress_count,
                    SUM(CASE WHEN LOWER(c.status) = 'resolved'
                        THEN 1 ELSE 0 END) AS resolved_count
                FROM users u
                LEFT JOIN concerns c ON c.assigned_staff_id = u.id
                WHERE LOWER(u.role) = 'staff'
                GROUP BY u.id
                ORDER BY u.name ASC
            """)
            staff_users = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) AS total_concerns FROM concerns
            """)
            total_concerns = cursor.fetchone()["total_concerns"] or 0

        return render_template(
            "admin_staff.html",
            staff_users=staff_users,
            total_concerns=total_concerns,
            clean_name=get_clean_name(session.get("user_name", "Administrator"))
        )

    except Exception:
        app.logger.exception("Admin staff page failed")
        return "Unable to load staff. Please try again.", 500

    finally:
        connection.close()


# ============================================================
# ADMIN — SERVICE ROUTING
# ============================================================

@app.route("/admin/routing")
@admin_required
def admin_routing():
    allowed_categories = [
        "General",
        "Street Lights",
        "Waste Collection",
        "Water Supply",
        "Roads & Drainage",
        "Community Services"
    ]

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            # Per-category workload and current assignment spread.
            cursor.execute("""
                SELECT
                    c.category,
                    COUNT(c.id) AS total_count,
                    SUM(CASE WHEN LOWER(c.status) = 'pending'
                        THEN 1 ELSE 0 END) AS pending_count,
                    SUM(CASE WHEN LOWER(c.status) IN
                        ('in progress', 'in_progress')
                        THEN 1 ELSE 0 END) AS in_progress_count,
                    SUM(CASE WHEN LOWER(c.status) = 'resolved'
                        THEN 1 ELSE 0 END) AS resolved_count,
                    SUM(CASE WHEN c.assigned_staff_id IS NULL
                        THEN 1 ELSE 0 END) AS unassigned_count
                FROM concerns c
                GROUP BY c.category
            """)
            category_stats = {row["category"]: row for row in cursor.fetchall()}

            # Staff workload, used to suggest the least busy handler.
            cursor.execute("""
                SELECT
                    u.id,
                    u.name,
                    COUNT(c.id) AS assigned_count
                FROM users u
                LEFT JOIN concerns c ON c.assigned_staff_id = u.id
                WHERE LOWER(u.role) = 'staff'
                GROUP BY u.id
                ORDER BY u.name ASC
            """)
            staff_users = cursor.fetchall()

            # Concerns still waiting for an owner.
            cursor.execute("""
                SELECT
                    c.id,
                    c.title,
                    c.category,
                    c.status,
                    c.created_at,
                    r.name AS resident_name
                FROM concerns c
                LEFT JOIN users r ON r.id = c.resident_id
                WHERE c.assigned_staff_id IS NULL
                ORDER BY c.created_at ASC
            """)
            unassigned = cursor.fetchall()

        # Merge categories that have no concerns yet so every route
        # in the allow-list is always visible.
        categories = []
        for name in allowed_categories:
            stats = category_stats.get(name)
            categories.append(stats or {
                "category": name,
                "total_count": 0,
                "pending_count": 0,
                "in_progress_count": 0,
                "resolved_count": 0,
                "unassigned_count": 0
            })

        # Categories present in the DB but outside the default list.
        for name, stats in category_stats.items():
            if name not in allowed_categories:
                categories.append(stats)

        total_concerns = sum(row["total_count"] or 0 for row in categories)

        return render_template(
            "admin_routing.html",
            categories=categories,
            staff_users=staff_users,
            unassigned=unassigned,
            total_concerns=total_concerns,
            clean_name=get_clean_name(session.get("user_name", "Administrator"))
        )

    except Exception:
        app.logger.exception("Admin routing page failed")
        return "Unable to load routing. Please try again.", 500

    finally:
        connection.close()


# ============================================================
# ADMIN — REPORTS
# ============================================================

@app.route("/admin/reports")
@admin_required
def admin_reports():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN LOWER(status) = 'pending'
                        THEN 1 ELSE 0 END) AS pending_count,
                    SUM(CASE WHEN LOWER(status) IN
                        ('in progress', 'in_progress')
                        THEN 1 ELSE 0 END) AS in_progress_count,
                    SUM(CASE WHEN LOWER(status) = 'resolved'
                        THEN 1 ELSE 0 END) AS resolved_count
                FROM concerns
            """)
            overall = cursor.fetchone() or {}

            cursor.execute("""
                SELECT
                    COALESCE(NULLIF(category, ''), 'General') AS category,
                    COUNT(*) AS total_count,
                    SUM(CASE WHEN LOWER(status) = 'resolved'
                        THEN 1 ELSE 0 END) AS resolved_count
                FROM concerns
                GROUP BY COALESCE(NULLIF(category, ''), 'General')
                ORDER BY total_count DESC
            """)
            by_category = cursor.fetchall()

            cursor.execute("""
                SELECT
                    COALESCE(NULLIF(u.purok, ''), 'Unspecified') AS purok,
                    COUNT(*) AS total_count
                FROM concerns c
                LEFT JOIN users u ON u.id = c.resident_id
                GROUP BY COALESCE(NULLIF(u.purok, ''), 'Unspecified')
                ORDER BY total_count DESC
            """)
            by_purok = cursor.fetchall()

            # YEAR()/MONTH() avoid % placeholders, which pymysql only
            # interpolates when query arguments are supplied.
            cursor.execute("""
                SELECT
                    YEAR(created_at) AS year_num,
                    MONTH(created_at) AS month_num,
                    COUNT(*) AS total_count,
                    SUM(CASE WHEN LOWER(status) = 'resolved'
                        THEN 1 ELSE 0 END) AS resolved_count
                FROM concerns
                GROUP BY YEAR(created_at), MONTH(created_at)
                ORDER BY year_num DESC, month_num DESC
                LIMIT 6
            """)
            raw_months = cursor.fetchall()

            cursor.execute("""
                SELECT
                    r.name AS resident_name,
                    COALESCE(NULLIF(r.purok, ''), 'Unspecified') AS purok,
                    COUNT(*) AS concern_count
                FROM concerns c
                JOIN users r ON r.id = c.resident_id
                GROUP BY r.id
                ORDER BY concern_count DESC
                LIMIT 5
            """)
            top_reporters = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) AS total_residents FROM users
                WHERE LOWER(role) = 'resident'
            """)
            total_residents = cursor.fetchone()["total_residents"] or 0

            cursor.execute("""
                SELECT COUNT(*) AS total_staff FROM users
                WHERE LOWER(role) = 'staff'
            """)
            total_staff = cursor.fetchone()["total_staff"] or 0

        total = overall.get("total") or 0
        resolved = overall.get("resolved_count") or 0
        resolution_rate = round((resolved / total) * 100) if total else 0

        # MySQL returns month numbers; format the label in Python so the
        # template never has to touch strftime on a possibly-null date.
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]

        by_month = []
        for row in raw_months:
            month_num = int(row.get("month_num") or 1)
            year_num = int(row.get("year_num") or 0)
            label = (
                f"{month_names[month_num - 1]} {year_num}"
                if 1 <= month_num <= 12 and year_num
                else "Unknown"
            )
            by_month.append({
                "month_label": label,
                "total_count": row.get("total_count") or 0,
                "resolved_count": row.get("resolved_count") or 0
            })

        # Highest value in each series so bars scale proportionally.
        max_category = max(
            (row["total_count"] for row in by_category), default=0
        ) or 1
        max_purok = max(
            (row["total_count"] for row in by_purok), default=0
        ) or 1
        max_month = max(
            (row["total_count"] for row in by_month), default=0
        ) or 1

        return render_template(
            "admin_reports.html",
            total_concerns=total,
            pending_count=overall.get("pending_count") or 0,
            in_progress_count=overall.get("in_progress_count") or 0,
            resolved_count=resolved,
            resolution_rate=resolution_rate,
            by_category=by_category,
            by_purok=by_purok,
            by_month=by_month,
            top_reporters=top_reporters,
            total_residents=total_residents,
            total_staff=total_staff,
            max_category=max_category,
            max_purok=max_purok,
            max_month=max_month,
            clean_name=get_clean_name(session.get("user_name", "Administrator"))
        )

    except Exception:
        app.logger.exception("Admin reports page failed")
        return "Unable to load reports. Please try again.", 500

    finally:
        connection.close()


# ============================================================
# ADMIN — SETTINGS
# ============================================================

@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_password or not new_password or not confirm_password:
            flash("Please fill in all password fields.", "error")
            return redirect(url_for("admin_settings"))

        if len(new_password) < 8:
            flash("New password must be at least 8 characters.", "error")
            return redirect(url_for("admin_settings"))

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect(url_for("admin_settings"))

        if new_password == current_password:
            flash("New password must differ from the current one.", "error")
            return redirect(url_for("admin_settings"))

        connection = get_db()

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, password FROM users
                    WHERE id = %s
                """, (session["user_id"],))
                user = cursor.fetchone()

                if not user or not check_password_hash(
                    user["password"], current_password
                ):
                    flash("Current password is incorrect.", "error")
                    return redirect(url_for("admin_settings"))

                cursor.execute("""
                    UPDATE users
                    SET password = %s
                    WHERE id = %s
                """, (generate_password_hash(new_password), session["user_id"]))

            connection.commit()
            flash("Password updated successfully.", "success")

        except Exception:
            connection.rollback()
            app.logger.exception("Admin password change failed")
            flash("Unable to update the password.", "error")

        finally:
            connection.close()

        return redirect(url_for("admin_settings"))

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT email FROM users
                WHERE id = %s
            """, (session["user_id"],))
            row = cursor.fetchone()
            admin_email = (row or {}).get("email", "")
    except Exception:
        app.logger.exception("Failed to load admin settings")
        admin_email = ""
    finally:
        connection.close()

    return render_template(
        "admin_settings.html",
        admin_email=admin_email,
        clean_name=get_clean_name(session.get("user_name", "Administrator"))
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
    try:
        init_db()
        create_default_accounts()

    except Exception:
        app.logger.exception(
            "Startup failed. Check that MySQL is running and the "
            "'barangayassist' database exists."
        )
        raise

    app.run(debug=True)
