import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bot.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS professors (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                full_name   TEXT NOT NULL,
                national_id TEXT NOT NULL,
                phone       TEXT NOT NULL,
                degree      TEXT NOT NULL DEFAULT '',
                retired     TEXT NOT NULL DEFAULT '',
                department  TEXT NOT NULL,
                days        TEXT NOT NULL,
                hours       TEXT NOT NULL,
                courses     TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS admins (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                label   TEXT NOT NULL
            );
        """)
        # ── مهاجرت برای دیتابیس‌های قدیمی (ستون‌های جدید) ────────────────────
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(professors)")}
        if "degree" not in existing_cols:
            conn.execute("ALTER TABLE professors ADD COLUMN degree TEXT NOT NULL DEFAULT ''")
        if "retired" not in existing_cols:
            conn.execute("ALTER TABLE professors ADD COLUMN retired TEXT NOT NULL DEFAULT ''")


def save_professor(data: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO professors
              (user_id, full_name, national_id, phone, degree, retired, department,
               days, hours, courses, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["user_id"],
            data["full_name"],
            data["national_id"],
            data["phone"],
            data["degree"],
            data["retired"],
            data["department"],
            "، ".join(data["days"]),
            "، ".join(data["hours"]),
            "، ".join(data["courses"]),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))


def get_all_professors():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM professors ORDER BY id DESC").fetchall()


def delete_professor(record_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM professors WHERE id=?", (record_id,))
        return cur.rowcount > 0


def delete_all_professors() -> int:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM professors")
        return cur.rowcount


def add_admin(user_id: int, label: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admins (user_id, label) VALUES (?,?)",
            (user_id, label),
        )


def remove_admin(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM admins WHERE user_id=?", (user_id,))


def list_admins():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM admins").fetchall()


def is_admin(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM admins WHERE user_id=?", (user_id,)
        ).fetchone()
        return row is not None
