"""Règles métier et opérations de gestion scolaire."""
import sqlite3
from .database import get_connection, fetch_all


def list_classes():
    return fetch_all("SELECT id, name, level FROM classes ORDER BY name")


def add_class(name: str, level: str = "") -> int:
    name = name.strip()
    if not name:
        raise ValueError("Le nom de la classe est obligatoire.")
    with get_connection() as db:
        cursor = db.execute("INSERT INTO classes(name, level) VALUES (?, ?)",
                            (name, level.strip()))
        return int(cursor.lastrowid)


def update_class(class_id: int, name: str, level: str = "") -> None:
    name = name.strip()
    if not name:
        raise ValueError("Le nom de la classe est obligatoire.")
    with get_connection() as db:
        db.execute("UPDATE classes SET name=?, level=? WHERE id=?",
                   (name, level.strip(), class_id))


def delete_class(class_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM classes WHERE id=?", (class_id,))


def list_students(search: str = ""):
    pattern = f"%{search.strip()}%"
    return fetch_all(
        """SELECT s.id, s.matricule, s.last_name, s.first_name, s.gender,
                  s.birth_date, s.class_id, COALESCE(c.name, 'Non affecté') AS class_name
           FROM students s LEFT JOIN classes c ON c.id=s.class_id
           WHERE s.active=1 AND (s.matricule LIKE ? OR s.last_name LIKE ?
             OR s.first_name LIKE ? OR c.name LIKE ?)
           ORDER BY s.last_name, s.first_name""",
        (pattern, pattern, pattern, pattern),
    )


def add_student(matricule: str, last_name: str, first_name: str,
                gender: str = "", class_id: int | None = None,
                birth_date: str = "") -> int:
    values = [matricule.strip(), last_name.strip(), first_name.strip()]
    if not all(values):
        raise ValueError("Le matricule, le nom et le prénom sont obligatoires.")
    with get_connection() as db:
        cursor = db.execute(
            """INSERT INTO students(matricule, last_name, first_name, gender,
                                    birth_date, class_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (*values, gender, birth_date, class_id),
        )
        return int(cursor.lastrowid)


def update_student(student_id: int, matricule: str, last_name: str,
                   first_name: str, gender: str = "",
                   class_id: int | None = None, birth_date: str = "") -> None:
    values = [matricule.strip(), last_name.strip(), first_name.strip()]
    if not all(values):
        raise ValueError("Le matricule, le nom et le prénom sont obligatoires.")
    with get_connection() as db:
        db.execute(
            """UPDATE students SET matricule=?, last_name=?, first_name=?,
                   gender=?, birth_date=?, class_id=? WHERE id=?""",
            (*values, gender, birth_date, class_id, student_id),
        )


def delete_student(student_id: int) -> None:
    # Archivage logique : l'historique des notes est conservé.
    with get_connection() as db:
        db.execute("UPDATE students SET active=0 WHERE id=?", (student_id,))


def add_grade(student_id: int, subject_id: int, period: str,
              score: float, max_score: float = 20) -> int:
    if not period.strip():
        raise ValueError("La période est obligatoire.")
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
    with get_connection() as db:
        rows = db.execute(
            """SELECT g.score, g.max_score, s.coefficient
               FROM grades g JOIN subjects s ON s.id=g.subject_id
               WHERE g.student_id=? AND g.period=?""",
            (student_id, period),
        ).fetchall()
    if not rows:
        return None
    weighted = sum((r["score"] / r["max_score"]) * 20 * r["coefficient"] for r in rows)
    coefficients = sum(r["coefficient"] for r in rows)
    return round(weighted / coefficients, 2) if coefficients else None
