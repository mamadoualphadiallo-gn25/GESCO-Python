"""Initialisation et accès à la base SQLite locale de GESCO."""
from pathlib import Path
import sqlite3

APP_DIR = Path.home() / "Documents" / "GESCO"
DB_PATH = APP_DIR / "gesco.db"


def get_connection() -> sqlite3.Connection:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS school_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            school_name TEXT NOT NULL DEFAULT 'Mon établissement',
            school_year TEXT NOT NULL DEFAULT '',
            grading_scale REAL NOT NULL DEFAULT 20,
            absence_as_zero INTEGER NOT NULL DEFAULT 0
        );
        INSERT OR IGNORE INTO school_settings (id) VALUES (1);

        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            level TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT NOT NULL UNIQUE,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            gender TEXT NOT NULL DEFAULT '',
            birth_date TEXT NOT NULL DEFAULT '',
            class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            coefficient REAL NOT NULL DEFAULT 1 CHECK (coefficient > 0)
        );
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            period TEXT NOT NULL,
            score REAL NOT NULL,
            max_score REAL NOT NULL DEFAULT 20,
            comment TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (score >= 0 AND max_score > 0 AND score <= max_score)
        );
        CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_id);
        CREATE INDEX IF NOT EXISTS idx_grades_student_period ON grades(student_id, period);
        """)
    # Migration additive : aucune table ni donnée historique n'est supprimée.
    from .academic import initialize_academic_schema
    initialize_academic_schema()


def fetch_one(query: str, params: tuple = ()):
    with get_connection() as db:
        return db.execute(query, params).fetchone()


def fetch_all(query: str, params: tuple = ()):
    with get_connection() as db:
        return db.execute(query, params).fetchall()
