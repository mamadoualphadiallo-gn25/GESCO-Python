"""Règles métier et calculs scolaires."""
from .database import get_connection


def add_class(name: str, level: str = "") -> int:
    name = name.strip()
    if not name:
        raise ValueError("Le nom de la classe est obligatoire.")
    with get_connection() as db:
        cursor = db.execute(
            "INSERT INTO classes(name, level) VALUES (?, ?)", (name, level.strip())
        )
        return int(cursor.lastrowid)


def add_student(matricule: str, last_name: str, first_name: str,
                gender: str = "", class_id: int | None = None) -> int:
    values = [matricule.strip(), last_name.strip(), first_name.strip()]
    if not all(values):
        raise ValueError("Le matricule, le nom et le prénom sont obligatoires.")
    with get_connection() as db:
        cursor = db.execute(
            """INSERT INTO students(matricule, last_name, first_name, gender, class_id)
               VALUES (?, ?, ?, ?, ?)""",
            (*values, gender, class_id),
        )
        return int(cursor.lastrowid)


def add_grade(student_id: int, subject_id: int, period: str,
              score: float, max_score: float = 20) -> int:
    if max_score <= 0 or score < 0 or score > max_score:
        raise ValueError("La note doit être comprise entre 0 et le barème.")
    with get_connection() as db:
        cursor = db.execute(
            """INSERT INTO grades(student_id, subject_id, period, score, max_score)
               VALUES (?, ?, ?, ?, ?)""",
            (student_id, subject_id, period.strip(), score, max_score),
        )
        return int(cursor.lastrowid)


def calculate_average(student_id: int, period: str) -> float | None:
    rows = []
    with get_connection() as db:
        rows = db.execute(
            """SELECT g.score, g.max_score, s.coefficient
               FROM grades g JOIN subjects s ON s.id = g.subject_id
               WHERE g.student_id = ? AND g.period = ?""",
            (student_id, period),
        ).fetchall()
    if not rows:
        return None
    weighted_total = sum((r["score"] / r["max_score"]) * 20 * r["coefficient"] for r in rows)
    coefficients = sum(r["coefficient"] for r in rows)
    return round(weighted_total / coefficients, 2) if coefficients else None
