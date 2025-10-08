from __future__ import annotations

import hashlib
import secrets
import sqlite3
import string
import time
from pathlib import Path

from utils import normalize_phone_number


CODE_TTL_SECONDS = 300
SESSION_TTL_HOURS = 12


class AuthManager:
    """Simple authentication manager that handles login codes and session tokens."""

    def __init__(self, db_path: str = "data/auth.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _initialize_database(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS login_codes (
                    phone TEXT PRIMARY KEY,
                    code_hash TEXT NOT NULL,
                    expires_at INTEGER NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    phone TEXT NOT NULL,
                    expires_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def _hash_code(self, phone: str, code: str) -> str:
        digest = hashlib.sha256(f"{phone}:{code}".encode("utf-8")).hexdigest()
        return digest

    def _generate_code(self) -> str:
        alphabet = string.digits
        return "".join(secrets.choice(alphabet) for _ in range(6))

    def _store_code(self, phone: str, code: str) -> None:
        expires_at = int(time.time()) + CODE_TTL_SECONDS
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO login_codes (phone, code_hash, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(phone) DO UPDATE SET code_hash=excluded.code_hash, expires_at=excluded.expires_at
                """,
                (phone, self._hash_code(phone, code), expires_at),
            )
            conn.commit()

    def request_code(self, phone_number: str) -> str:
        normalized = normalize_phone_number(phone_number)
        if not normalized:
            raise ValueError("Geçerli bir telefon numarası giriniz.")

        code = self._generate_code()
        self._store_code(normalized, code)
        return code

    def verify_code(self, phone_number: str, code: str) -> str:
        normalized = normalize_phone_number(phone_number)
        if not normalized:
            raise ValueError("Geçerli bir telefon numarası giriniz.")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT code_hash, expires_at FROM login_codes WHERE phone = ?", (normalized,))
            row = cursor.fetchone()

        if not row:
            raise ValueError("Bu numara için aktif bir doğrulama kodu bulunamadı.")

        code_hash, expires_at = row
        if expires_at < int(time.time()):
            self._delete_code(normalized)
            raise ValueError("Doğrulama kodunun süresi dolmuş. Lütfen yeni bir kod isteyin.")

        if self._hash_code(normalized, code) != code_hash:
            raise ValueError("Doğrulama kodu geçersiz.")

        token = secrets.token_urlsafe(32)
        session_expiry = int(time.time() + SESSION_TTL_HOURS * 3600)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (token, phone, expires_at) VALUES (?, ?, ?)",
                (token, normalized, session_expiry),
            )
            conn.commit()

        self._delete_code(normalized)
        return token

    def _delete_code(self, phone: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM login_codes WHERE phone = ?", (phone,))
            conn.commit()

    def validate_session(self, token: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT phone, expires_at FROM sessions WHERE token = ?", (token,))
            row = cursor.fetchone()

        if not row:
            raise ValueError("Oturum bulunamadı veya süresi doldu.")

        phone, expires_at = row
        current_time = int(time.time())
        if expires_at < current_time:
            self.invalidate_session(token)
            raise ValueError("Oturum süresi dolmuş. Lütfen tekrar giriş yapın.")

        return phone

    def invalidate_session(self, token: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

    def cleanup_expired_sessions(self) -> None:
        current_time = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE expires_at < ?", (current_time,))
            cursor.execute("DELETE FROM login_codes WHERE expires_at < ?", (current_time,))
            conn.commit()


__all__ = ["AuthManager"]
