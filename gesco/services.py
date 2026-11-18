"""Règles métier et opérations de gestion scolaire."""
from .database import get_connection, fetch_all, fetch_one


def list_classes():
    return fetch_all("SELECT id, name, level FROM classes ORDER BY name")


def add_class(name: str, level: str = "") -> int:
    name = name.strip()
    if not name:
        raise ValueError("Le nom de la classe est obligatoire.")
    with get_connection() as db:
        cursor = db.execute("INSERT INTO classes(name, level) VALUES (?, ?)", (name, level.strip()))
        return int(cursor.lastrowid)


def update_class(class_id: int, name: str, level: str = "") -> None:
    name = name.strip()
    if not name:
        raise ValueError("Le nom de la classe est obligatoire.")
    with get_connection() as db:
        db.execute("UPDATE classes SET name=?, level=? WHERE id=?", (name, level.strip(), class_id))


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
                gender: str = "", class_id: int | None = None, birth_date: str = "") -> int:
    values = [matricule.strip(), last_name.strip(), first_name.strip()]
    if not all(values):
        raise ValueError("Le matricule, le nom et le prénom sont obligatoires.")
    with get_connection() as db:
        cursor = db.execute(
            """INSERT INTO students(matricule, last_name, first_name, gender, birth_date, class_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (*values, gender, birth_date, class_id),
        )
        return int(cursor.lastrowid)


def update_student(student_id: int, matricule: str, last_name: str, first_name: str,
                   gender: str = "", class_id: int | None = None, birth_date: str = "") -> None:
    values = [matricule.strip(), last_name.strip(), first_name.strip()]
    if not all(values):
        raise ValueError("Le matricule, le nom et le prénom sont obligatoires.")
    with get_connection() as db:
        db.execute(
            """UPDATE students SET matricule=?, last_name=?, first_name=?, gender=?,
                   birth_date=?, class_id=? WHERE id=?""",
            (*values, gender, birth_date, class_id, student_id),
        )


def delete_student(student_id: int) -> None:
    with get_connection() as db:
        db.execute("UPDATE students SET active=0 WHERE id=?", (student_id,))


def list_subjects():
    return fetch_all("SELECT id, name, coefficient FROM subjects ORDER BY name")


def add_subject(name: str, coefficient: float = 1) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Le nom de la matière est obligatoire.")
    if coefficient <= 0:
        raise ValueError("Le coefficient doit être supérieur à zéro.")
    with get_connection() as db:
        cursor = db.execute("INSERT INTO subjects(name, coefficient) VALUES (?, ?)",
                            (name, coefficient))
        return int(cursor.lastrowid)


def update_subject(subject_id: int, name: str, coefficient: float) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Le nom de la matière est obligatoire.")
    if coefficient <= 0:
        raise ValueError("Le coefficient doit être supérieur à zéro.")
    with get_connection() as db:
        db.execute("UPDATE subjects SET name=?, coefficient=? WHERE id=?",
                   (name, coefficient, subject_id))


def delete_subject(subject_id: int) -> None:
    with get_connection() as db:
        db.execute("DELETE FROM subjects WHERE id=?", (subject_id,))


def get_school_settings():
    return fetch_one("SELECT school_name, school_year, grading_scale, absence_as_zero FROM school_settings WHERE id=1")


def update_school_settings(school_name: str, school_year: str, grading_scale: float,
                           absence_as_zero: bool = False) -> None:
    if not school_name.strip():
        raise ValueError("Le nom de l'établissement est obligatoire.")
    if grading_scale <= 0:
        raise ValueError("Le barème doit être supérieur à zéro.")
    with get_connection() as db:
        db.execute(
            """UPDATE school_settings SET school_name=?, school_year=?,
                   grading_scale=?, absence_as_zero=? WHERE id=1""",
            (school_name.strip(), school_year.strip(), grading_scale, int(absence_as_zero)),
        )


def add_grade(student_id: int, subject_id: int, period: str,
              score: float, max_score: float | None = None, comment: str = "") -> int:
    if not period.strip():
        raise ValueError("La période est obligatoire.")
    settings = get_school_settings()
    maximum = float(max_score if max_score is not None else settings["grading_scale"])
    if maximum <= 0 or score < 0 or score > maximum:
        raise ValueError(f"La note doit être comprise entre 0 et {maximum:g}.")
    with get_connection() as db:
        cursor = db.execute(
            """INSERT INTO grades(student_id, subject_id, period, score, max_score, comment)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (student_id, subject_id, period.strip(), score, maximum, comment.strip()),
        )
        return int(cursor.lastrowid)


def list_grades(period: str = ""):
    if period.strip():
        return fetch_all(
            """SELECT g.id, g.period, g.score, g.max_score, g.comment,
                      s.matricule, s.last_name, s.first_name, c.name AS class_name,
                      sub.name AS subject_name, sub.coefficient
               FROM grades g JOIN students s ON s.id=g.student_id
               LEFT JOIN classes c ON c.id=s.class_id
               JOIN subjects sub ON sub.id=g.subject_id
               WHERE g.period=? ORDER BY c.name, s.last_name, sub.name""",
            (period.strip(),),
        )
    return fetch_all(
        """SELECT g.id, g.period, g.score, g.max_score, g.comment,
                  s.matricule, s.last_name, s.first_name, c.name AS class_name,
                  sub.name AS subject_name, sub.coefficient
           FROM grades g JOIN students s ON s.id=g.student_id
           LEFT JOIN classes c ON c.id=s.class_id
           JOIN subjects sub ON sub.id=g.subject_id
           ORDER BY g.period, c.name, s.last_name, sub.name"""
    )


def calculate_average(student_id: int, period: str) -> float | None:
    with get_connection() as db:
        rows = db.execute(
            """SELECT g.score, g.max_score, sub.coefficient
               FROM grades g JOIN subjects sub ON sub.id=g.subject_id
               WHERE g.student_id=? AND g.period=?""",
            (student_id, period),
        ).fetchall()
    if not rows:
        return None
    weighted = sum((r["score"] / r["max_score"]) * 20 * r["coefficient"] for r in rows)
    coefficients = sum(r["coefficient"] for r in rows)
    return round(weighted / coefficients, 2) if coefficients else None
