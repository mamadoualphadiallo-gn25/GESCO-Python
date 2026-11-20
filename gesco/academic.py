"""Gestion des cycles, évaluations, compositions et bulletins GESCO.

Ce module ajoute une couche académique versionnée au-dessus des tables historiques.
Les notes et classes déjà présentes sont conservées.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .database import get_connection, fetch_all, fetch_one

CYCLES = {
    "primaire": {"label": "Primaire", "terms": 3},
    "college": {"label": "Collège", "terms": 2},
    "lycee": {"label": "Lycée", "terms": 2},
}
PRIMARY_LEVELS = [f"{n}ème année" for n in range(1, 7)]
COLLEGE_LEVELS = [f"{n}ème année" for n in range(7, 11)]
LYCEE_LEVELS = ["11ème année", "12ème année", "Terminale"]
LYCEE_SERIES = ["Sciences sociales", "Sciences expérimentales", "Sciences mathématiques"]
MONTHS = ["Septembre", "Octobre", "Novembre", "Décembre", "Janvier",
          "Février", "Mars", "Avril", "Mai", "Juin"]


def _columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}


def initialize_academic_schema() -> None:
    """Migration additive et non destructive de la base locale."""
    with get_connection() as db:
        class_columns = _columns(db, "classes")
        if "cycle_code" not in class_columns:
            db.execute("ALTER TABLE classes ADD COLUMN cycle_code TEXT NOT NULL DEFAULT 'non_classe'")
        if "series_name" not in class_columns:
            db.execute("ALTER TABLE classes ADD COLUMN series_name TEXT NOT NULL DEFAULT ''")
        if "archived" not in class_columns:
            db.execute("ALTER TABLE classes ADD COLUMN archived INTEGER NOT NULL DEFAULT 0")

        db.executescript("""
        CREATE TABLE IF NOT EXISTS academic_cycles (
            code TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            term_count INTEGER NOT NULL CHECK(term_count IN (2,3))
        );
        CREATE TABLE IF NOT EXISTS lycee_series (
            name TEXT PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS academic_years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL UNIQUE,
            start_date TEXT NOT NULL DEFAULT '',
            end_date TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 0 CHECK(active IN (0,1))
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_academic_year
            ON academic_years(active) WHERE active=1;
        CREATE TABLE IF NOT EXISTS assessment_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
            academic_year_id INTEGER NOT NULL REFERENCES academic_years(id) ON DELETE RESTRICT,
            kind TEXT NOT NULL CHECK(kind IN ('monthly','composition')),
            period_key TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','finalized')),
            grading_scale REAL NOT NULL DEFAULT 20 CHECK(grading_scale > 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finalized_at TEXT,
            UNIQUE(class_id, academic_year_id, kind, period_key)
        );
        CREATE TABLE IF NOT EXISTS assessment_grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
            subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
            score REAL,
            status TEXT NOT NULL DEFAULT 'graded' CHECK(status IN ('graded','absent','missing')),
            comment TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, student_id, subject_id),
            CHECK(score IS NULL OR score >= 0)
        );
        CREATE TABLE IF NOT EXISTS report_card_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_code TEXT NOT NULL,
            name TEXT NOT NULL,
            config_json TEXT NOT NULL DEFAULT '{}',
            is_default INTEGER NOT NULL DEFAULT 0,
            UNIQUE(cycle_code, name)
        );
        CREATE TABLE IF NOT EXISTS report_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES assessment_sessions(id) ON DELETE RESTRICT,
            student_id INTEGER REFERENCES students(id) ON DELETE RESTRICT,
            report_type TEXT NOT NULL CHECK(report_type IN ('student','class','annual')),
            version INTEGER NOT NULL DEFAULT 1,
            snapshot_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_assessment_class_year
            ON assessment_sessions(class_id, academic_year_id, status);
        CREATE INDEX IF NOT EXISTS idx_assessment_grades_session
            ON assessment_grades(session_id, student_id);
        CREATE INDEX IF NOT EXISTS idx_report_cards_session
            ON report_cards(session_id, report_type, student_id);
        """)
        report_columns = _columns(db, "report_cards")
        if "class_id" not in report_columns:
            db.execute("ALTER TABLE report_cards ADD COLUMN class_id INTEGER REFERENCES classes(id)")
        if "academic_year_id" not in report_columns:
            db.execute("ALTER TABLE report_cards ADD COLUMN academic_year_id INTEGER REFERENCES academic_years(id)")
        for code, data in CYCLES.items():
            db.execute(
                "INSERT INTO academic_cycles(code,label,term_count) VALUES(?,?,?) "
                "ON CONFLICT(code) DO UPDATE SET label=excluded.label, term_count=excluded.term_count",
                (code, data["label"], data["terms"]),
            )
        for series in LYCEE_SERIES:
            db.execute("INSERT OR IGNORE INTO lycee_series(name) VALUES(?)", (series,))


def list_cycles():
    return fetch_all("SELECT code,label,term_count FROM academic_cycles ORDER BY CASE code WHEN 'primaire' THEN 1 WHEN 'college' THEN 2 ELSE 3 END")


def list_series():
    return [row["name"] for row in fetch_all("SELECT name FROM lycee_series ORDER BY name")]


def create_academic_class(name: str, cycle_code: str, series_name: str = "") -> int:
    name = name.strip()
    if not name or cycle_code not in CYCLES:
        raise ValueError("Le nom et le cycle de la classe sont obligatoires.")
    if cycle_code == "lycee" and series_name not in LYCEE_SERIES:
        raise ValueError("Choisissez une série valide pour une classe du lycée.")
    if cycle_code != "lycee":
        series_name = ""
    with get_connection() as db:
        cur = db.execute(
            "INSERT INTO classes(name,level,cycle_code,series_name) VALUES(?,?,?,?)",
            (name, name, cycle_code, series_name),
        )
        return int(cur.lastrowid)


def update_academic_class(class_id: int, name: str, cycle_code: str, series_name: str = "") -> None:
    name = name.strip()
    if not name or cycle_code not in CYCLES:
        raise ValueError("Le nom et le cycle de la classe sont obligatoires.")
    if cycle_code == "lycee" and series_name not in LYCEE_SERIES:
        raise ValueError("Choisissez une série valide pour le lycée.")
    if cycle_code != "lycee":
        series_name = ""
    with get_connection() as db:
        db.execute("UPDATE classes SET name=?,level=?,cycle_code=?,series_name=? WHERE id=?",
                   (name, name, cycle_code, series_name, class_id))


def list_academic_classes(cycle_code: str = ""):
    if cycle_code:
        return fetch_all(
            "SELECT id,name,level,cycle_code,series_name FROM classes WHERE archived=0 AND cycle_code=? ORDER BY name",
            (cycle_code,),
        )
    return fetch_all(
        "SELECT id,name,level,cycle_code,series_name FROM classes WHERE archived=0 ORDER BY cycle_code,name"
    )


def archive_academic_class(class_id: int) -> None:
    with get_connection() as db:
        db.execute("UPDATE classes SET archived=1 WHERE id=?", (class_id,))


def create_academic_year(label: str, start_date: str = "", end_date: str = "", active: bool = True) -> int:
    label = label.strip()
    if not label:
        raise ValueError("L'intitulé de l'année scolaire est obligatoire.")
    with get_connection() as db:
        if active:
            db.execute("UPDATE academic_years SET active=0")
        cur = db.execute(
            "INSERT INTO academic_years(label,start_date,end_date,active) VALUES(?,?,?,?)",
            (label, start_date, end_date, int(active)),
        )
        return int(cur.lastrowid)


def list_academic_years():
    return fetch_all("SELECT * FROM academic_years ORDER BY start_date DESC,id DESC")


def set_active_academic_year(year_id: int) -> None:
    with get_connection() as db:
        db.execute("UPDATE academic_years SET active=0")
        changed = db.execute("UPDATE academic_years SET active=1 WHERE id=?", (year_id,)).rowcount
        if not changed:
            raise ValueError("Année scolaire introuvable.")


def _class_cycle(db: sqlite3.Connection, class_id: int):
    row = db.execute("SELECT id,name,cycle_code,series_name FROM classes WHERE id=? AND archived=0",
                     (class_id,)).fetchone()
    if row is None:
        raise ValueError("Classe introuvable ou archivée.")
    if row["cycle_code"] not in CYCLES:
        raise ValueError("Cette ancienne classe doit être affectée à un cycle avant de créer une évaluation.")
    return row


def create_assessment(class_id: int, academic_year_id: int, kind: str,
                      period_key: str, grading_scale: float = 20) -> int:
    if kind not in ("monthly", "composition"):
        raise ValueError("Type d'évaluation invalide.")
    period_key = period_key.strip()
    if grading_scale <= 0 or not period_key:
        raise ValueError("Période et barème valides obligatoires.")
    with get_connection() as db:
        cls = _class_cycle(db, class_id)
        year = db.execute("SELECT id FROM academic_years WHERE id=?", (academic_year_id,)).fetchone()
        if year is None:
            raise ValueError("Année scolaire introuvable.")
        if kind == "monthly" and period_key not in MONTHS:
            raise ValueError("Choisissez un mois scolaire valide.")
        if kind == "composition":
            allowed = [f"T{i}" for i in range(1, CYCLES[cls["cycle_code"]]["terms"] + 1)]
            if period_key not in allowed:
                raise ValueError(f"Ce cycle comporte {len(allowed)} trimestre(s) : {', '.join(allowed)}.")
        cur = db.execute(
            "INSERT INTO assessment_sessions(class_id,academic_year_id,kind,period_key,grading_scale) VALUES(?,?,?,?,?)",
            (class_id, academic_year_id, kind, period_key, grading_scale),
        )
        return int(cur.lastrowid)


def list_assessments(class_id: int | None = None):
    sql = """SELECT a.*, c.name AS class_name, c.cycle_code, c.series_name, y.label AS year_label
             FROM assessment_sessions a JOIN classes c ON c.id=a.class_id
             JOIN academic_years y ON y.id=a.academic_year_id"""
    if class_id is not None:
        return fetch_all(sql + " WHERE a.class_id=? ORDER BY a.created_at DESC", (class_id,))
    return fetch_all(sql + " ORDER BY a.created_at DESC")


def save_assessment_grade(session_id: int, student_id: int, subject_id: int,
                          score: float | None, status: str = "graded", comment: str = "") -> int:
    if status not in ("graded", "absent", "missing"):
        raise ValueError("Statut de note invalide.")
    with get_connection() as db:
        session = db.execute("SELECT * FROM assessment_sessions WHERE id=?", (session_id,)).fetchone()
        if session is None:
            raise ValueError("Évaluation introuvable.")
        if session["status"] != "draft":
            raise ValueError("Cette évaluation est finalisée ; rouvrez-la avec une action administrative dédiée.")
        student = db.execute("SELECT class_id,active FROM students WHERE id=?", (student_id,)).fetchone()
        if student is None or not student["active"] or student["class_id"] != session["class_id"]:
            raise ValueError("L'élève ne fait pas partie de cette classe.")
        subject = db.execute("SELECT id FROM subjects WHERE id=?", (subject_id,)).fetchone()
        if subject is None:
            raise ValueError("Matière introuvable.")
        if status == "graded":
            if score is None or score < 0 or score > session["grading_scale"]:
                raise ValueError(f"La note doit être comprise entre 0 et {session['grading_scale']:g}.")
        else:
            score = None
        db.execute(
            """INSERT INTO assessment_grades(session_id,student_id,subject_id,score,status,comment,updated_at)
               VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(session_id,student_id,subject_id) DO UPDATE SET
               score=excluded.score,status=excluded.status,comment=excluded.comment,updated_at=CURRENT_TIMESTAMP""",
            (session_id, student_id, subject_id, score, status, comment.strip()),
        )
        row = db.execute(
            "SELECT id FROM assessment_grades WHERE session_id=? AND student_id=? AND subject_id=?",
            (session_id, student_id, subject_id),
        ).fetchone()
        return int(row["id"])


def _build_student_snapshot(db: sqlite3.Connection, session, student) -> dict[str, Any]:
    grades = db.execute(
        """SELECT ag.score,ag.status,ag.comment,sub.name AS subject_name,sub.coefficient
           FROM assessment_grades ag JOIN subjects sub ON sub.id=ag.subject_id
           WHERE ag.session_id=? AND ag.student_id=? ORDER BY sub.name""",
        (session["id"], student["id"]),
    ).fetchall()
    valid = [g for g in grades if g["status"] == "graded" and g["score"] is not None]
    total_coef = sum(float(g["coefficient"]) for g in valid)
    average = (sum(float(g["score"]) / session["grading_scale"] * 20 * float(g["coefficient"])
                   for g in valid) / total_coef) if total_coef else None
    return {
        "student": {"id": student["id"], "matricule": student["matricule"],
                    "name": f'{student["last_name"]} {student["first_name"]}'},
        "class": session["class_name"], "cycle": CYCLES[session["cycle_code"]]["label"],
        "series": session["series_name"] or "", "school_year": session["year_label"],
        "period": session["period_key"], "kind": session["kind"],
        "grading_scale": session["grading_scale"],
        "subjects": [{"name": g["subject_name"], "score": g["score"],
                      "status": g["status"], "coefficient": g["coefficient"],
                      "comment": g["comment"]} for g in grades],
        "average": round(average, 2) if average is not None else None,
    }


def finalize_assessment(session_id: int) -> dict[str, Any]:
    """Verrouille une évaluation et archive les bulletins individuels + classe."""
    with get_connection() as db:
        session = db.execute(
            """SELECT a.*,c.name AS class_name,c.cycle_code,c.series_name,y.label AS year_label
               FROM assessment_sessions a JOIN classes c ON c.id=a.class_id
               JOIN academic_years y ON y.id=a.academic_year_id WHERE a.id=?""",
            (session_id,),
        ).fetchone()
        if session is None:
            raise ValueError("Évaluation introuvable.")
        if session["status"] == "finalized":
            raise ValueError("Cette évaluation est déjà finalisée.")
        students = db.execute(
            "SELECT id,matricule,last_name,first_name FROM students WHERE class_id=? AND active=1 ORDER BY last_name,first_name",
            (session["class_id"],),
        ).fetchall()
        if not students:
            raise ValueError("Impossible de finaliser une classe sans élève actif.")
        snapshots = [_build_student_snapshot(db, session, s) for s in students]
        ranked = sorted([s for s in snapshots if s["average"] is not None],
                        key=lambda s: (-s["average"], s["student"]["name"].casefold()))
        rank_by_id = {}
        previous = object()
        rank = 0
        for pos, item in enumerate(ranked, 1):
            avg = item["average"]
            if avg != previous:
                rank = pos
                previous = avg
            rank_by_id[item["student"]["id"]] = rank
        for item in snapshots:
            item["rank"] = rank_by_id.get(item["student"]["id"])
            item["class_size"] = len(students)
        averages = [s["average"] for s in snapshots if s["average"] is not None]
        summary = {
            "class": session["class_name"], "cycle": CYCLES[session["cycle_code"]]["label"],
            "series": session["series_name"] or "", "school_year": session["year_label"],
            "period": session["period_key"], "kind": session["kind"],
            "student_count": len(students), "graded_count": len(averages),
            "class_average": round(sum(averages) / len(averages), 2) if averages else None,
            "highest_average": max(averages) if averages else None,
            "lowest_average": min(averages) if averages else None,
            "students": snapshots,
        }
        db.execute("UPDATE assessment_sessions SET status='finalized',finalized_at=CURRENT_TIMESTAMP WHERE id=?",
                   (session_id,))
        for item in snapshots:
            existing = db.execute(
                "SELECT COALESCE(MAX(version),0) AS v FROM report_cards WHERE session_id=? AND student_id=? AND report_type='student'",
                (session_id, item["student"]["id"]),
            ).fetchone()["v"]
            db.execute(
                "INSERT INTO report_cards(session_id,student_id,report_type,version,snapshot_json,class_id,academic_year_id) VALUES(?,?,'student',?,?,?,?)",
                (session_id, item["student"]["id"], int(existing) + 1,
                 json.dumps(item, ensure_ascii=False), session["class_id"], session["academic_year_id"]),
            )
        existing = db.execute(
            "SELECT COALESCE(MAX(version),0) AS v FROM report_cards WHERE session_id=? AND report_type='class'",
            (session_id,),
        ).fetchone()["v"]
        db.execute(
            "INSERT INTO report_cards(session_id,student_id,report_type,version,snapshot_json,class_id,academic_year_id) VALUES(?,NULL,'class',?,?,?,?)",
            (session_id, int(existing) + 1, json.dumps(summary, ensure_ascii=False),
             session["class_id"], session["academic_year_id"]),
        )
        return summary


def list_report_cards(session_id: int, report_type: str = ""):
    sql = "SELECT * FROM report_cards WHERE session_id=?"
    params: tuple = (session_id,)
    if report_type:
        sql += " AND report_type=?"
        params += (report_type,)
    return fetch_all(sql + " ORDER BY report_type,student_id,version DESC", params)


def export_report_card_pdf(snapshot: dict[str, Any], destination: str | Path,
                           school_name: str = "Mon établissement") -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=36, leftMargin=36,
                            topMargin=32, bottomMargin=32)
    student = snapshot.get("student", {})
    title = "Bulletin scolaire" if snapshot.get("report_type") != "class" else "Récapitulatif de classe"
    story = [Paragraph(escape(school_name), styles["Title"]),
             Paragraph(title, styles["Heading1"]),
             Paragraph(f'Année : {escape(str(snapshot.get("school_year","")))} | '
                       f'Classe : {escape(str(snapshot.get("class","")))}', styles["Normal"]),
             Paragraph(f'Période : {escape(str(snapshot.get("period","")))}', styles["Normal"]),
             Spacer(1, 12)]
    if student:
        story.append(Paragraph(f'Élève : {escape(str(student.get("name","")))} '
                               f'({escape(str(student.get("matricule","")))})', styles["Heading2"]))
    data = [["Matière", "Note", "Coefficient", "Statut", "Appréciation"]]
    for row in snapshot.get("subjects", []):
        score = "—" if row["score"] is None else f'{row["score"]:.2f}/{snapshot.get("grading_scale",20):g}'
        data.append([row["name"], score, str(row["coefficient"]), row["status"], row.get("comment","")])
    table = Table(data, repeatRows=1, colWidths=[145, 65, 65, 65, 155])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#20365f")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),.4,colors.HexColor("#d8deea")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f2f5fa")]),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story.append(table)
    if student:
        story += [Spacer(1, 12),
                  Paragraph(f'Moyenne générale : {snapshot.get("average") if snapshot.get("average") is not None else "Non calculable"} / 20',
                            styles["Heading2"]),
                  Paragraph(f'Rang : {snapshot.get("rank") or "Non classé"} / {snapshot.get("class_size","—")}',
                            styles["Normal"])]
    else:
        story += [Spacer(1, 12),
                  Paragraph(f'Effectif : {snapshot.get("student_count",0)} | '
                            f'Moyenne de classe : {snapshot.get("class_average") or "—"}',
                            styles["Heading2"])]
    doc.build(story)
    return Path(destination)
