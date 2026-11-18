"""Tests unitaires des règles métier."""
import pytest
from gesco.services import add_class, add_student, add_grade


def test_add_class_rejects_empty_name():
    with pytest.raises(ValueError):
        add_class("   ")


def test_add_student_rejects_missing_identity():
    with pytest.raises(ValueError):
        add_student("", "Diallo", "Mamadou")


def test_add_grade_rejects_out_of_range():
    with pytest.raises(ValueError):
        add_grade(1, 1, "Octobre", 25, 20)
