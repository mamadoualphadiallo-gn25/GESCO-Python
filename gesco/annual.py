"""Calcul et archivage des bulletins annuels GESCO."""
import json
from .database import get_connection, fetch_all
from .academic import CYCLES, _class_cycle


def generate_annual_report_cards(class_id: int, academic_year_id: int):
    """Moyenne annuelle pondérée par matière à partir des évaluations finalisées."""
    with get_connection() as db:
        cls = _class_cycle(db, class_id)
        year = db.execute("SELECT * FROM academic_years WHERE id=?", (academic_year_id,)).fetchone()
        if year is None:
            raise ValueError("Année scolaire introuvable.")
        sessions = db.execute(
            """SELECT id FROM assessment_sessions
               WHERE class_id=? AND academic_year_id=? AND status='finalized'
               ORDER BY finalized_at,id""", (class_id, academic_year_id)
        ).fetchall()
        if not sessions:
            raise ValueError("Aucune évaluation finalisée pour cette classe et cette année.")
        session_ids = [r["id"] for r in sessions]
        marks = ",".join("?" for _ in session_ids)
        students = db.execute(
            """SELECT id,matricule,last_name,first_name FROM students
               WHERE class_id=? AND active=1 ORDER BY last_name,first_name""", (class_id,)
        ).fetchall()
        if not students:
            raise ValueError("Aucun élève actif dans cette classe.")
        snapshots = []
        for student in students:
            rows = db.execute(
                f"""SELECT sub.name,sub.coefficient,
                           AVG(ag.score / a.grading_scale * 20.0) AS annual_score,
                           COUNT(*) AS assessment_count
                    FROM assessment_grades ag
                    JOIN assessment_sessions a ON a.id=ag.session_id
                    JOIN subjects sub ON sub.id=ag.subject_id
                    WHERE ag.student_id=? AND ag.status='graded' AND ag.score IS NOT NULL
                      AND a.id IN ({marks})
                    GROUP BY sub.id,sub.name,sub.coefficient ORDER BY sub.name""",
                (student["id"], *session_ids)
            ).fetchall()
            coef_total = sum(float(r["coefficient"]) for r in rows)
            average = (sum(float(r["annual_score"]) * float(r["coefficient"]) for r in rows)
                       / coef_total) if coef_total else None
            snapshots.append({
                "student": {"id": student["id"], "matricule": student["matricule"],
                            "name": f'{student["last_name"]} {student["first_name"]}'},
                "class": cls["name"], "cycle": CYCLES[cls["cycle_code"]]["label"],
                "series": cls["series_name"], "school_year": year["label"],
                "period": "Annuel", "kind": "annual", "grading_scale": 20,
                "subjects": [{"name": r["name"], "score": round(r["annual_score"], 2),
                              "status": "graded", "coefficient": r["coefficient"],
                              "comment": f'{r["assessment_count"]} résultat(s) pris en compte'}
                             for r in rows],
                "average": round(average, 2) if average is not None else None,
            })
        ranked = sorted((s for s in snapshots if s["average"] is not None),
                        key=lambda s: (-s["average"], s["student"]["name"].casefold()))
        previous, rank = object(), 0
        rank_map = {}
        for position, item in enumerate(ranked, 1):
            if item["average"] != previous:
                rank, previous = position, item["average"]
            rank_map[item["student"]["id"]] = rank
        for item in snapshots:
            item["rank"] = rank_map.get(item["student"]["id"])
            item["class_size"] = len(students)
        averages = [s["average"] for s in snapshots if s["average"] is not None]
        summary = {
            "report_type": "class", "class": cls["name"],
            "cycle": CYCLES[cls["cycle_code"]]["label"], "series": cls["series_name"],
            "school_year": year["label"], "period": "Annuel", "kind": "annual",
            "student_count": len(students), "graded_count": len(averages),
            "class_average": round(sum(averages) / len(averages), 2) if averages else None,
            "highest_average": max(averages) if averages else None,
            "lowest_average": min(averages) if averages else None, "students": snapshots,
        }
        for item in snapshots:
            old = db.execute(
                """SELECT COALESCE(MAX(version),0) AS v FROM report_cards
                   WHERE class_id=? AND academic_year_id=? AND student_id=? AND report_type='annual'""",
                (class_id, academic_year_id, item["student"]["id"])
            ).fetchone()["v"]
            db.execute(
                """INSERT INTO report_cards(session_id,student_id,report_type,version,snapshot_json,class_id,academic_year_id)
                   VALUES(NULL,?,'annual',?,?,?,?)""",
                (item["student"]["id"], int(old)+1, json.dumps(item, ensure_ascii=False),
                 class_id, academic_year_id)
            )
        old = db.execute(
            """SELECT COALESCE(MAX(version),0) AS v FROM report_cards
               WHERE class_id=? AND academic_year_id=? AND report_type='class' AND session_id IS NULL""",
            (class_id, academic_year_id)
        ).fetchone()["v"]
        db.execute(
            """INSERT INTO report_cards(session_id,student_id,report_type,version,snapshot_json,class_id,academic_year_id)
               VALUES(NULL,NULL,'class',?,?,?,?)""",
            (int(old)+1, json.dumps(summary, ensure_ascii=False), class_id, academic_year_id)
        )
        return summary


def list_annual_report_cards(class_id: int, academic_year_id: int, report_type: str = ""):
    sql = """SELECT * FROM report_cards WHERE class_id=? AND academic_year_id=?
             AND session_id IS NULL AND report_type IN ('annual','class')"""
    params = (class_id, academic_year_id)
    if report_type:
        sql += " AND report_type=?"
        params += (report_type,)
    return fetch_all(sql + " ORDER BY report_type,student_id,version DESC", params)
