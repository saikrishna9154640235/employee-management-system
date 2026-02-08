from flask import Flask, render_template, request, redirect, session, jsonify, flash
from db import get_connection, init_db, UPLOADS_DIR
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import sqlite3

app = Flask(__name__)
init_db()
app.secret_key = "secretkey"
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2MB max for uploads
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_emp_id():
    """Get emp_id for current session user. Admin -> ADMIN001, employees -> lookup by username."""
    username = session.get("user")
    if not username:
        return None
    if username == "admin":
        return "ADMIN001"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id FROM employees WHERE username=? OR emp_id=?", (username, username))
    row = cursor.fetchone()
    conn.close()
    return row["emp_id"] if row else None


def get_current_employee():
    """Get full employee record for current user."""
    emp_id = get_emp_id()
    if not emp_id:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password),
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            if user[0] == "ADMIN":
                return redirect("/admin")
            else:
                return redirect("/employee")
        else:
            return "Invalid Credentials"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# FORGOT PASSWORD
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        username = request.form["username"]
        new_password = request.form["password"]
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
        conn.commit()
        conn.close()
        return redirect("/")
    return render_template("forgot_password.html")


# ADMIN DASHBOARD
@app.route("/admin")
def admin_dashboard():
    if "user" not in session:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees ORDER BY emp_id")
    employees = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """SELECT l.*, e.name FROM leaves l
           JOIN employees e ON l.emp_id = e.emp_id
           WHERE l.status = 'pending' ORDER BY l.applied_at DESC"""
    )
    pending_leaves = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM employees")
    total_employees = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leaves WHERE status = 'pending'")
    pending_leaves_count = cursor.fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=? AND status='present'",
        (today,),
    )
    today_attendance = cursor.fetchone()[0]

    admin_emp_id = get_emp_id()
    cursor.execute(
        "SELECT * FROM attendance WHERE emp_id=? AND date=?",
        (admin_emp_id, today),
    )
    admin_att_row = cursor.fetchone()

    # Auto-cap admin's daily work duration to 9 hours if needed
    if admin_att_row and admin_att_row["login_time"] and not admin_att_row["logout_time"]:
        try:
            login_dt = datetime.strptime(f"{today} {admin_att_row['login_time']}", "%Y-%m-%d %H:%M:%S")
            cutoff_dt = login_dt + timedelta(hours=9)
            now_dt = datetime.now()
            if now_dt >= cutoff_dt:
                cutoff_time = cutoff_dt.strftime("%H:%M:%S")
                cursor.execute(
                    "UPDATE attendance SET logout_time=? WHERE emp_id=? AND date=?",
                    (cutoff_time, admin_emp_id, today),
                )
                conn.commit()
                cursor.execute(
                    "SELECT * FROM attendance WHERE emp_id=? AND date=?",
                    (admin_emp_id, today),
                )
                admin_att_row = cursor.fetchone()
        except ValueError:
            pass

    admin_attendance_status = dict(admin_att_row) if admin_att_row else None

    # Recent activity: last 5 leaves (any status) + today's attendance
    cursor.execute(
        """SELECT l.emp_id, e.name, l.type, l.from_date, l.to_date, l.status, l.applied_at
           FROM leaves l JOIN employees e ON l.emp_id = e.emp_id
           ORDER BY l.applied_at DESC LIMIT 5"""
    )
    recent_leaves = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """SELECT a.emp_id, e.name, a.login_time
           FROM attendance a JOIN employees e ON a.emp_id = e.emp_id
           WHERE a.date = ? AND a.status = 'present' AND a.login_time IS NOT NULL
           ORDER BY a.login_time DESC""",
        (today,),
    )
    today_attendance_list = [dict(row) for row in cursor.fetchall()]

    # Build combined recent_activity list (leaves + today's check-ins, newest first)
    recent_activity = []
    for leave in recent_leaves:
        applied_at = leave.get("applied_at") or ""
        status_label = "applied for" if leave["status"] == "pending" else leave["status"]
        recent_activity.append({
            "type": "leave",
            "message": f"{leave['name']} {status_label} {leave['type']} leave ({leave['from_date']} – {leave['to_date']})",
            "time": applied_at[:16] if len(applied_at) >= 16 else applied_at,
            "sort_key": applied_at,
        })
    for att in today_attendance_list:
        login_time = att.get("login_time") or ""
        recent_activity.append({
            "type": "attendance",
            "message": f"{att['name']} marked attendance",
            "time": login_time[:5] if len(login_time) >= 5 else login_time,
            "sort_key": f"{today} {login_time}",
        })
    recent_activity.sort(key=lambda x: x["sort_key"], reverse=True)
    recent_activity = recent_activity[:8]

    conn.close()

    current_user = get_current_employee()
    if not current_user:
        current_user = {"name": "Admin", "emp_id": "ADMIN001", "department": "HR", "email": "admin@company.com", "join_date": "2020-01-01", "profile_image": None, "qualification": ""}

    return render_template(
        "admin_dashboard.html",
        employees=employees,
        pending_leaves=pending_leaves,
        total_employees=total_employees,
        pending_leaves_count=pending_leaves_count,
        today_attendance=today_attendance,
        current_user=current_user,
        admin_attendance_status=admin_attendance_status,
        recent_activity=recent_activity,
    )


# EMPLOYEE DASHBOARD
@app.route("/employee")
def employee():
    if "user" not in session:
        return redirect("/")

    emp_id = get_emp_id()
    if not emp_id:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,))
    row = cursor.fetchone()
    current_user = dict(row) if row else {}

    cursor.execute(
        "SELECT COUNT(*) FROM leaves WHERE emp_id=?",
        (emp_id,),
    )
    my_leaves_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM leaves WHERE emp_id=? AND status='pending'",
        (emp_id,),
    )
    my_pending_leaves = cursor.fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT * FROM attendance WHERE emp_id=? AND date=?",
        (emp_id, today),
    )
    att_row = cursor.fetchone()

    # Auto-cap employee's daily work duration to 9 hours if needed
    if att_row and att_row["login_time"] and not att_row["logout_time"]:
        try:
            login_dt = datetime.strptime(f"{today} {att_row['login_time']}", "%Y-%m-%d %H:%M:%S")
            cutoff_dt = login_dt + timedelta(hours=9)
            now_dt = datetime.now()
            if now_dt >= cutoff_dt:
                cutoff_time = cutoff_dt.strftime("%H:%M:%S")
                cursor.execute(
                    "UPDATE attendance SET logout_time=? WHERE emp_id=? AND date=?",
                    (cutoff_time, emp_id, today),
                )
                conn.commit()
                cursor.execute(
                    "SELECT * FROM attendance WHERE emp_id=? AND date=?",
                    (emp_id, today),
                )
                att_row = cursor.fetchone()
        except ValueError:
            pass

    attendance_status = dict(att_row) if att_row else None

    cursor.execute(
        "SELECT * FROM leaves WHERE emp_id=? ORDER BY applied_at DESC",
        (emp_id,),
    )
    my_leaves = [dict(row) for row in cursor.fetchall()]

    conn.close()

    if not current_user:
        return redirect("/")

    return render_template(
        "employee_dashboard.html",
        current_user=current_user,
        my_leaves_count=my_leaves_count,
        my_pending_leaves=my_pending_leaves,
        attendance_status=attendance_status,
        my_leaves=my_leaves,
    )


# ADD EMPLOYEE
@app.route("/add_employee", methods=["POST"])
def add_employee():
    if "user" not in session:
        return redirect("/")

    name = request.form.get("name")
    emp_id = request.form.get("emp_id", "").strip()
    email = request.form.get("email")
    dept = request.form.get("department")
    salary = request.form.get("salary", "")
    join_date = request.form.get("join_date", "")
    password = request.form.get("password", "")

    if not emp_id or not name or not email or not dept:
        return redirect("/admin#create-employee")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO employees (name, emp_id, email, department, salary, join_date, username) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, emp_id, email, dept, salary, join_date, emp_id),
        )
        if emp_id and password:
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                (emp_id, password, "EMPLOYEE"),
            )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        flash("Employee ID already exists. Please use a different ID.")
    finally:
        conn.close()
    return redirect("/admin")


# APPLY LEAVE
@app.route("/apply_leave", methods=["POST"])
def apply_leave():
    if "user" not in session:
        return redirect("/")

    emp_id = get_emp_id()
    if not emp_id:
        return jsonify({"error": "Not logged in"}), 401

    from_date = request.form.get("fromDate")
    to_date = request.form.get("toDate")
    leave_type = request.form.get("leaveType", "casual").replace(" Leave", "").lower()
    reason = request.form.get("reason", "")

    if not from_date or not to_date:
        return jsonify({"error": "From and To dates required"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leaves (emp_id, from_date, to_date, type, reason) VALUES (?, ?, ?, ?, ?)",
        (emp_id, from_date, to_date, leave_type, reason),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# APPROVE / REJECT LEAVE
@app.route("/leave/<int:leave_id>/approve", methods=["POST"])
def approve_leave(leave_id):
    if "user" not in session:
        return redirect("/")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE leaves SET status='approved' WHERE id=?", (leave_id,))
    conn.commit()
    conn.close()
    return redirect("/admin#leave-requests")


@app.route("/leave/<int:leave_id>/reject", methods=["POST"])
def reject_leave(leave_id):
    if "user" not in session:
        return redirect("/")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE leaves SET status='rejected' WHERE id=?", (leave_id,))
    conn.commit()
    conn.close()
    return redirect("/admin#leave-requests")


# ATTENDANCE
@app.route("/attendance", methods=["POST"])
def mark_attendance():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    emp_id = get_emp_id()
    if not emp_id:
        return jsonify({"error": "Invalid user"}), 401

    action = request.form.get("action", "login")  # login or logout
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance WHERE emp_id=? AND date=?", (emp_id, today))
    row = cursor.fetchone()

    # Auto-cap daily work duration to 9 hours.
    # If someone stayed logged in and 9 hours have passed since login,
    # automatically set logout_time to login_time + 9 hours.
    if row and row["login_time"] and not row["logout_time"]:
        try:
            login_dt = datetime.strptime(f"{today} {row['login_time']}", "%Y-%m-%d %H:%M:%S")
            cutoff_dt = login_dt + timedelta(hours=9)
            now_dt = datetime.now()
            if now_dt >= cutoff_dt:
                cutoff_time = cutoff_dt.strftime("%H:%M:%S")
                cursor.execute(
                    "UPDATE attendance SET logout_time=? WHERE emp_id=? AND date=?",
                    (cutoff_time, emp_id, today),
                )
                conn.commit()
                cursor.execute("SELECT * FROM attendance WHERE emp_id=? AND date=?", (emp_id, today))
                row = cursor.fetchone()
        except ValueError:
            # If time format is unexpected, skip auto logout rather than failing.
            pass

    if action == "login":
        # If the employee has already completed 9 hours and has a logout_time,
        # prevent another login for the same day.
        if row and row["logout_time"]:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Today's 9 working hours are already completed.",
            }), 400

        if row:
            cursor.execute(
                "UPDATE attendance SET status='present', login_time=? WHERE emp_id=? AND date=?",
                (now_time, emp_id, today),
            )
        else:
            cursor.execute(
                "INSERT INTO attendance (emp_id, date, status, login_time) VALUES (?, ?, 'present', ?)",
                (emp_id, today, now_time),
            )
    else:  # logout
        if row:
            cursor.execute(
                "UPDATE attendance SET logout_time=? WHERE emp_id=? AND date=?",
                (now_time, emp_id, today),
            )

    conn.commit()

    # Re-fetch to return authoritative times (after any auto-cap logic above)
    cursor.execute("SELECT * FROM attendance WHERE emp_id=? AND date=?", (emp_id, today))
    saved_row = cursor.fetchone()
    conn.close()

    login_t = saved_row["login_time"] if saved_row else None
    logout_t = saved_row["logout_time"] if saved_row else None

    return jsonify({
        "success": True,
        "action": action,
        "login_time": login_t,
        "logout_time": logout_t,
    })


# API: Get attendance for calendar (month/year)
@app.route("/api/attendance/<int:month>/<int:year>")
def api_attendance(month, year):
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    emp_id = get_emp_id()
    if not emp_id:
        return jsonify({"error": "Invalid user"}), 401

    # month is 1-12 from URL
    from datetime import date
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, status, login_time, logout_time FROM attendance WHERE emp_id=? AND date>=? AND date<?",
        (emp_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
    )
    rows = cursor.fetchall()
    conn.close()

    attendance = {}
    for row in rows:
        attendance[row["date"]] = {
            "status": row["status"],
            "login_time": row["login_time"],
            "logout_time": row["logout_time"],
        }

    return jsonify({"attendance": attendance})


# UPDATE PROFILE
@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user" not in session:
        return redirect("/")

    emp_id = get_emp_id()
    if not emp_id:
        return redirect("/")

    name = request.form.get("name")
    email = request.form.get("email")
    department = request.form.get("department")
    qualification = request.form.get("qualification", "")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE employees SET name=?, email=?, department=?, qualification=? WHERE emp_id=?",
        (name, email, department, qualification, emp_id),
    )
    conn.commit()
    conn.close()

    if session.get("user") == "admin":
        return redirect("/admin#update-profile")
    return redirect("/employee#update-profile")


# CHANGE PASSWORD
@app.route("/change_password", methods=["POST"])
def change_password():
    if "user" not in session:
        return redirect("/")

    username = session["user"]
    current_pwd = request.form.get("currentPwd")
    new_pwd = request.form.get("newPwd")
    confirm_pwd = request.form.get("confirmPwd")

    if new_pwd != confirm_pwd:
        return "Passwords do not match", 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, current_pwd))
    if not cursor.fetchone():
        conn.close()
        return "Current password is incorrect", 400

    cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pwd, username))
    conn.commit()
    conn.close()

    if username == "admin":
        return redirect("/admin#change-password")
    return redirect("/employee#change-password")


# PROFILE IMAGE UPLOAD
@app.route("/upload_profile_image", methods=["POST"])
def upload_profile_image():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    emp_id = get_emp_id()
    if not emp_id:
        return jsonify({"error": "Invalid user"}), 401

    if "file" not in request.files and "profilePic" not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files.get("file") or request.files.get("profilePic")
    if not file or file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{emp_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    filename = secure_filename(filename)
    filepath = os.path.join(UPLOADS_DIR, filename)
    file.save(filepath)

    rel_path = f"uploads/{filename}"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET profile_image=? WHERE emp_id=?", (rel_path, emp_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "url": f"/static/{rel_path}"})


if __name__ == "__main__":
    app.run(debug=True, port=5004)
