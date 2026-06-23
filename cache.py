import sqlite3
import os
from datetime import datetime

DB_FILE = "jobs_cache.db"

def get_db_path() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, DB_FILE)

def init_db():
    """Initializes SQLite tables if they do not exist."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        
        # Salary cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salary_cache (
                url TEXT PRIMARY KEY,
                has_salary INTEGER,
                min_salary_usd REAL,
                max_salary_usd REAL,
                explanation TEXT,
                evaluated_at TEXT
            )
        """)
        
        # ATS evaluation cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ats_cache (
                url TEXT,
                resume_hash TEXT,
                match_score INTEGER,
                explanation TEXT,
                evaluated_at TEXT,
                PRIMARY KEY (url, resume_hash)
            )
        """)
        conn.commit()
    finally:
        conn.close()

def get_cached_salary(url: str) -> dict | None:
    """Retrieves cached salary evaluation details for a URL."""
    if not url:
        return None
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT has_salary, min_salary_usd, max_salary_usd, explanation FROM salary_cache WHERE url = ?",
            (url,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "has_salary": bool(row[0]),
                "min_salary_usd": row[1],
                "max_salary_usd": row[2],
                "explanation": row[3]
            }
        return None
    finally:
        conn.close()

def set_cached_salary(url: str, has_salary: bool, min_salary: float, max_salary: float, explanation: str):
    """Saves salary evaluation details in cache."""
    if not url:
        return
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO salary_cache (url, has_salary, min_salary_usd, max_salary_usd, explanation, evaluated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (url, 1 if has_salary else 0, min_salary, max_salary, explanation, datetime.utcnow().isoformat())
        )
        conn.commit()
    finally:
        conn.close()

def get_cached_ats(url: str, resume_hash: str) -> dict | None:
    """Retrieves cached ATS evaluation details for a URL and resume hash."""
    if not url or not resume_hash:
        return None
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT match_score, explanation FROM ats_cache WHERE url = ? AND resume_hash = ?",
            (url, resume_hash)
        )
        row = cursor.fetchone()
        if row:
            return {
                "match_score": row[0],
                "explanation": row[1]
            }
        return None
    finally:
        conn.close()

def set_cached_ats(url: str, resume_hash: str, match_score: int, explanation: str):
    """Saves ATS evaluation details in cache."""
    if not url or not resume_hash:
        return
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO ats_cache (url, resume_hash, match_score, explanation, evaluated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (url, resume_hash, match_score, explanation, datetime.utcnow().isoformat())
        )
        conn.commit()
    finally:
        conn.close()
