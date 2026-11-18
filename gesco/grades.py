"""Saisie et consultation des notes."""
import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QDoubleSpinBox, QLineEdit, QMessageBox,
    QHeaderView, QFormLayout, QDialog
)
from .services import list_students, list_subjects, list_grades, add_grade, get_school_settings


class GradeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Saisir une note")
        form = QFormLayout(self)
        self.student = QComboBox()
        for s in list_students():
            self.student.addItem(f'{s["matricule"]} — {s["last_name"]} {s["first_name"]} ({s["class_name"]})', s["id"])
        self.subject = QComboBox()
        for s in list_subjects():
            self.subject.addItem(f'{s["name"]} (coef. {s["coefficient"]:g})', s["id"])
        self.period = QComboBox()
        self.period.setEditable(True)
        self.period.addItems(["Octobre", "Novembre", "Décembre", "Janvier", "Février",
                              "Mars", "Avril", "Mai", "Juin", "1er trimestre",
                              "2e trimestre", "3e trimestre", "Annuel"])
        self.score = QDoubleSpinBox()
        self.score.setDecimals(2)
        self.score.setRange(0, 1000)
        self.score.setMaximum(float(get_school_settings()["grading_scale"]))
        self.comment = QLineEdit()
        self.comment.setPlaceholderText("Commentaire facultatif")
        form.addRow("Élève", self.student)
        form.addRow("Matière", self.subject)
        form.addRow("Période", self.period)
        form.addRow("Note", self.score)
        form.addRow("Commentaire", self.comment)
        buttons = QHBoxLayout()
        save, cancel = QPushButton("Enregistrer"), QPushButton("Annuler")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        form.addRow(buttons)


class GradesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        heading = QLabel("Gestion des notes")
        heading.setObjectName("contentTitle")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Saisissez et consultez les évaluations par période."))
        bar = QHBoxLayout()
        self.period = QComboBox()
        self.period.setEditable(True)
        self.period.addItem("Toutes les périodes")
        self.period.addItems(["Octobre", "Novembre", "Décembre", "Janvier", "Février",
                              "Mars", "Avril", "Mai", "Juin", "1er trimestre",
                              "2e trimestre", "3e trimestre", "Annuel"])
        self.period.currentTextChanged.connect(self.refresh)
        add = QPushButton("＋ Saisir une note")
        add.clicked.connect(self.add_item)
        bar.addWidget(QLabel("Période :"))
        bar.addWidget(self.period, 1)
        bar.addWidget(add)
        layout.addLayout(bar)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Matricule", "Élève", "Classe", "Matière",
                                              "Période", "Note", "Coefficient"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        self.refresh()

    def refresh(self, *_):
        period = self.period.currentText().strip()
        rows = list_grades("" if period == "Toutes les périodes" else period)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            values = [row["matricule"], f'{row["last_name"]} {row["first_name"]}',
                      row["class_name"] or "Non affecté", row["subject_name"],
                      row["period"], f'{row["score"]:g}/{row["max_score"]:g}',
                      f'{row["coefficient"]:g}']
            for j, value in enumerate(values):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

    def add_item(self):
        if not list_students():
            QMessageBox.information(self, "Aucun élève", "Inscrivez d'abord au moins un élève.")
            return
        if not list_subjects():
            QMessageBox.information(self, "Aucune matière", "Créez d'abord au moins une matière.")
            return
        dialog = GradeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                add_grade(dialog.student.currentData(), dialog.subject.currentData(),
                          dialog.period.currentText(), dialog.score.value(),
                          comment=dialog.comment.text())
                self.refresh()
            except (ValueError, sqlite3.IntegrityError) as exc:
                QMessageBox.warning(self, "Enregistrement impossible", str(exc))
