import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "employee.db")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")


def get_connection():
    # Use WAL mode + busy timeout to reduce "database is locked" errors
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # These PRAGMAs are cheap and safe to run on each new connection
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")  # wait up to 5s if DB is busy
    return conn


def init_db():
    """Create tables and seed data if they don't exist."""
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    # Ensure same WAL + busy_timeout settings for the initializer connection
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emp_id TEXT UNIQUE,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            salary TEXT,
            join_date TEXT,
            username TEXT UNIQUE,
            profile_image TEXT,
            qualification TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            type TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            applied_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'absent',
            login_time TEXT,
            logout_time TEXT,
            UNIQUE(emp_id, date)
        )
    """)

    # Add new columns if they don't exist (for existing DBs)
    try:
        cursor.execute("ALTER TABLE employees ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE employees ADD COLUMN profile_image TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE employees ADD COLUMN qualification TEXT")
    except sqlite3.OperationalError:
        pass

    # Seed users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            [
                ("admin", "admin123", "ADMIN"),
                ("john", "pass123", "EMPLOYEE"),
                ("priya", "pass123", "EMPLOYEE"),
                ("rahul", "pass123", "EMPLOYEE"),
            ],
        )

    # Seed employees if empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """INSERT INTO employees (name, emp_id, email, department, salary, join_date, username, qualification)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                ("Hari Priya", "ADMIN001", "admin@company.com", "HR", "", "2020-01-01", "admin", ""),
                ("John Doe", "EMP001", "john@company.com", "Development", "75000", "2023-01-10", "john", "B.Tech"),
                ("Priya Sharma", "EMP002", "priya@company.com", "HR", "65000", "2022-03-15", "priya", "MBA"),
                ("Rahul Kumar", "EMP003", "rahul@company.com", "Finance", "70000", "2023-06-01", "rahul", "B.Com"),
            ],
        )

    # Seed leaves if empty
    cursor.execute("SELECT COUNT(*) FROM leaves")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """INSERT INTO leaves (emp_id, from_date, to_date, type, reason, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                ("EMP001", "2026-01-28", "2026-01-29", "casual", "Family event", "pending"),
                ("EMP002", "2026-01-27", "2026-01-27", "sick", "Fever", "pending"),
                ("EMP001", "2026-02-10", "2026-02-12", "sick", "Flu", "pending"),
            ],
        )

    # Seed attendance if empty
    cursor.execute("SELECT COUNT(*) FROM attendance")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """INSERT INTO attendance (emp_id, date, status, login_time)
               VALUES (?, ?, ?, ?)""",
            [
                ("EMP001", "2026-02-02", "present", "09:00:00"),
                ("EMP002", "2026-02-02", "present", "09:15:00"),
            ],
        )

    conn.commit()
    conn.close()

    # Ensure uploads directory exists
    os.makedirs(UPLOADS_DIR, exist_ok=True)
