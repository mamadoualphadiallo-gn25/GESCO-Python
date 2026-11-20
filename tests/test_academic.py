"""Tests des cycles, évaluations, compositions et bulletins automatiques."""
import pytest

from gesco.academic import (
    create_academic_class, create_academic_year, create_assessment,
    save_assessment_grade, finalize_assessment, list_report_cards,
)
from gesco.annual import generate_annual_report_cards, list_annual_report_cards
from gesco.services import add_student, add_subject


def setup_class(cycle="primaire"):
    class_id = create_academic_class(
        "Classe test " + cycle, cycle,
        "Sciences sociales" if cycle == "lycee" else ""
    )
    year_id = create_academic_year("2026-2027")
    student_id = add_student("MAT-001", "Diallo", "Aminata", class_id=class_id)
    subject_id = add_subject("Mathématiques", 2)
    return class_id, year_id, student_id, subject_id


def test_primary_accepts_three_terms():
    class_id, year_id, _, _ = setup_class("primaire")
    assert create_assessment(class_id, year_id, "composition", "T3") > 0


def test_college_rejects_third_term():
    class_id, year_id, _, _ = setup_class("college")
    with pytest.raises(ValueError, match="2 trimestre"):
        create_assessment(class_id, year_id, "composition", "T3")


def test_finalizing_assessment_archives_student_and_class_reports():
    class_id, year_id, student_id, subject_id = setup_class()
    session_id = create_assessment(class_id, year_id, "monthly", "Octobre")
    save_assessment_grade(session_id, student_id, subject_id, 15)
    summary = finalize_assessment(session_id)
    assert summary["students"][0]["average"] == 15
    assert len(list_report_cards(session_id, "student")) == 1
    assert len(list_report_cards(session_id, "class")) == 1


def test_annual_report_is_generated_from_finalized_assessments():
    class_id, year_id, student_id, subject_id = setup_class()
    for kind, period, score in [
        ("monthly", "Octobre", 12),
        ("composition", "T1", 16),
    ]:
        session_id = create_assessment(class_id, year_id, kind, period)
        save_assessment_grade(session_id, student_id, subject_id, score)
        finalize_assessment(session_id)
    summary = generate_annual_report_cards(class_id, year_id)
    assert summary["students"][0]["average"] == 14
    assert len(list_annual_report_cards(class_id, year_id, "annual")) == 1
    assert len(list_annual_report_cards(class_id, year_id, "class")) == 1
