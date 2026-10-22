import sqlite3
import time
import os
from pathlib import Path
from config import Config

DEFAULT_SOS_MESSAGE = (
    "🚨 [CỨU HỘ KHẨN CẤP - SOS ALERT] 🚨\n"
    "Tôi đang gặp sự cố/nguy hiểm và không thể xác nhận an toàn đúng hạn!\n"
    "Hệ thống Dead Man's Switch đã tự động kích hoạt gửi tin nhắn này.\n"
    "Xin vui lòng liên hệ ngay với tôi hoặc gọi lực lượng cứu hộ hỗ trợ khẩn cấp!\n"
    "Thời gian kích hoạt: {time}"
)

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DB_PATH
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Config Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sos_config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # 2. Emergency Contacts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emergency_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zalo_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    phone TEXT,
                    note TEXT,
                    is_active INTEGER DEFAULT 1,
                    added_at REAL
                )
            """)

            # 3. SOS Sessions (Dead Man's Switch state)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sos_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL, -- ARMED, CANCELLED_SAFE, TRIGGERED
                    started_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    sos_message TEXT NOT NULL,
                    warning_5m_sent INTEGER DEFAULT 0,
                    warning_1m_sent INTEGER DEFAULT 0,
                    cancelled_at REAL,
                    triggered_at REAL
                )
            """)

            # 4. Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sos_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    event_type TEXT NOT NULL,
                    target_id TEXT,
                    status TEXT,
                    details TEXT,
                    created_at REAL
                )
            """)

            conn.commit()

        # Seed default SOS message if not present
        if not self.get_config("sos_message"):
            self.set_config("sos_message", DEFAULT_SOS_MESSAGE)
        if not self.get_config("default_timeout_minutes"):
            self.set_config("default_timeout_minutes", str(Config.DEFAULT_TIMEOUT_MINUTES))

    # --- Config helpers ---
    def get_config(self, key, default=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM sos_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_config(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sos_config (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, str(value)))
            conn.commit()

    def get_sos_message(self):
        return self.get_config("sos_message", DEFAULT_SOS_MESSAGE)

    def set_sos_message(self, message):
        self.set_config("sos_message", message)

    # --- Emergency Contacts helpers ---
    def add_contact(self, zalo_id, name="Bạn bè", phone="", note=""):
        zalo_id = str(zalo_id).strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO emergency_contacts (zalo_id, name, phone, note, is_active, added_at)
                VALUES (?, ?, ?, ?, 1, ?)
                ON CONFLICT(zalo_id) DO UPDATE SET
                    name = excluded.name,
                    phone = excluded.phone,
                    note = excluded.note,
                    is_active = 1
            """, (zalo_id, name, phone, note, time.time()))
            conn.commit()

    def remove_contact(self, zalo_id):
        zalo_id = str(zalo_id).strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM emergency_contacts WHERE zalo_id = ?", (zalo_id,))
            affected = cursor.rowcount
            conn.commit()
            return affected > 0

    def list_contacts(self, active_only=True):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM emergency_contacts WHERE is_active = 1 ORDER BY id ASC")
            else:
                cursor.execute("SELECT * FROM emergency_contacts ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    # --- Session & Dead Man's Switch helpers ---
    def create_session(self, user_id, duration_seconds, custom_msg=None):
        """Cancels any existing active session and creates a new ARMED session."""
        now = time.time()
        expires_at = now + duration_seconds
        sos_msg = custom_msg or self.get_sos_message()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Cancel active sessions first
            cursor.execute("""
                UPDATE sos_sessions
                SET status = 'CANCELLED_SAFE', cancelled_at = ?
                WHERE status = 'ARMED'
            """, (now,))

            cursor.execute("""
                INSERT INTO sos_sessions (user_id, status, started_at, expires_at, sos_message)
                VALUES (?, 'ARMED', ?, ?, ?)
            """, (str(user_id), now, expires_at, sos_msg))
            session_id = cursor.lastrowid
            conn.commit()

        self.log_event(session_id, "ARM", str(user_id), "SUCCESS", f"Kích hoạt đếm ngược {duration_seconds} giây")
        return session_id, expires_at

    def get_active_session(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sos_sessions WHERE status = 'ARMED' ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def cancel_active_session(self, user_id):
        now = time.time()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM sos_sessions WHERE status = 'ARMED' ORDER BY id DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if not row:
                return None

            session_id = row["id"]
            cursor.execute("""
                UPDATE sos_sessions
                SET status = 'CANCELLED_SAFE', cancelled_at = ?
                WHERE id = ?
            """, (now, session_id))
            conn.commit()

        self.log_event(session_id, "SAFE", str(user_id), "SUCCESS", "Người dùng đã tắt lệnh an toàn")
        return session_id

    def extend_active_session(self, user_id, additional_seconds):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, expires_at FROM sos_sessions WHERE status = 'ARMED' ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return None, None

            session_id = row["id"]
            new_expires = row["expires_at"] + additional_seconds
            cursor.execute("""
                UPDATE sos_sessions
                SET expires_at = ?, warning_5m_sent = 0, warning_1m_sent = 0
                WHERE id = ?
            """, (new_expires, session_id))
            conn.commit()

        self.log_event(session_id, "EXTEND", str(user_id), "SUCCESS", f"Gia hạn thêm {additional_seconds} giây")
        return session_id, new_expires

    def mark_warning_sent(self, session_id, warning_level):
        """warning_level: '5m' or '1m'"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            col = "warning_5m_sent" if warning_level == "5m" else "warning_1m_sent"
            cursor.execute(f"UPDATE sos_sessions SET {col} = 1 WHERE id = ?", (session_id,))
            conn.commit()

    def mark_session_triggered(self, session_id):
        now = time.time()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sos_sessions
                SET status = 'TRIGGERED', triggered_at = ?
                WHERE id = ?
            """, (now, session_id))
            conn.commit()
        self.log_event(session_id, "TRIGGER", "SYSTEM", "SUCCESS", "Đã quá hạn mà không phản hồi -> Kích hoạt gửi SOS")

    # --- Logs helpers ---
    def log_event(self, session_id, event_type, target_id, status, details):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sos_logs (session_id, event_type, target_id, status, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, event_type, str(target_id), status, details, time.time()))
            conn.commit()

    def get_recent_logs(self, limit=10):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sos_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
