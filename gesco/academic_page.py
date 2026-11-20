"""Interface de gestion des cycles, évaluations et bulletins."""
import json
import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QFileDialog, QInputDialog
)

from .academic import (
    CYCLES, MONTHS, LYCEE_SERIES, create_academic_class, create_academic_year,
    create_assessment, list_academic_classes, list_academic_years,
    list_assessments, finalize_assessment, save_assessment_grade,
    list_report_cards, export_report_card_pdf,
)
from .services import list_students, list_subjects, get_school_settings


class AcademicClassDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Créer une classe")
        form = QFormLayout(self)
        self.name = QLineEdit()
        self.cycle = QComboBox()
        self.cycle.addItem("Primaire", "primaire")
        self.cycle.addItem("Collège", "college")
        self.cycle.addItem("Lycée", "lycee")
        self.series = QComboBox()
        self.series.addItems(LYCEE_SERIES)
        self.cycle.currentIndexChanged.connect(
            lambda: self.series.setEnabled(self.cycle.currentData() == "lycee")
        )
        self.series.setEnabled(False)
        form.addRow("Nom de la classe", self.name)
        form.addRow("Cycle", self.cycle)
        form.addRow("Série (lycée)", self.series)
        buttons = QHBoxLayout()
        ok, cancel = QPushButton("Créer"), QPushButton("Annuler")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        form.addRow(buttons)


class AcademicPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Cycles, évaluations et bulletins")
        title.setObjectName("contentTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(
            "Primaire : 3 trimestres. Collège et lycée : 2 trimestres. "
            "Les bulletins sont archivés après validation."
        ))

        toolbar = QHBoxLayout()
        self.cycle = QComboBox()
        self.cycle.addItem("Tous les cycles", "")
        self.cycle.addItem("Primaire", "primaire")
        self.cycle.addItem("Collège", "college")
        self.cycle.addItem("Lycée", "lycee")
        self.cycle.currentIndexChanged.connect(self.refresh)
        self.year = QComboBox()
        self.class_box = QComboBox()
        self.add_year = QPushButton("＋ Année scolaire")
        self.add_class = QPushButton("＋ Classe")
        self.add_session = QPushButton("＋ Évaluation")
        self.add_year.clicked.connect(self.create_year)
        self.add_class.clicked.connect(self.create_class)
        self.add_session.clicked.connect(self.create_session)
        for widget in (QLabel("Cycle"), self.cycle, QLabel("Année"), self.year,
                       QLabel("Classe"), self.class_box, self.add_year,
                       self.add_class, self.add_session):
            toolbar.addWidget(widget)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Classe", "Cycle / série", "Type", "Période", "Année scolaire", "État"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.grade_button = QPushButton("Saisir / modifier les notes")
        self.finalize_button = QPushButton("Valider et générer les bulletins")
        self.export_class_button = QPushButton("Exporter le récapitulatif PDF")
        self.export_student_button = QPushButton("Exporter un bulletin individuel")
        self.grade_button.clicked.connect(self.enter_grade)
        self.finalize_button.clicked.connect(self.finalize)
        self.export_class_button.clicked.connect(self.export_class)
        self.export_student_button.clicked.connect(self.export_student)
        for button in (self.grade_button, self.finalize_button,
                       self.export_class_button, self.export_student_button):
            actions.addWidget(button)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self, *_):
        current_year = self.year.currentData()
        self.year.blockSignals(True)
        self.year.clear()
        for row in list_academic_years():
            self.year.addItem(row["label"] + (" (active)" if row["active"] else ""), row["id"])
        if current_year is not None:
            idx = self.year.findData(current_year)
            if idx >= 0:
                self.year.setCurrentIndex(idx)
        self.year.blockSignals(False)

        current_class = self.class_box.currentData()
        self.class_box.blockSignals(True)
        self.class_box.clear()
        for row in list_academic_classes(self.cycle.currentData()):
            label = row["name"]
            if row["series_name"]:
                label += " — " + row["series_name"]
            self.class_box.addItem(label, row["id"])
        if current_class is not None:
            idx = self.class_box.findData(current_class)
            if idx >= 0:
                self.class_box.setCurrentIndex(idx)
        self.class_box.blockSignals(False)

        sessions = list_assessments()
        if self.cycle.currentData():
            sessions = [s for s in sessions if s["cycle_code"] == self.cycle.currentData()]
        self.table.setRowCount(len(sessions))
        self.sessions = sessions
        for i, row in enumerate(sessions):
            cycle_label = CYCLES.get(row["cycle_code"], {}).get("label", "À classer")
            if row["series_name"]:
                cycle_label += " — " + row["series_name"]
            values = [row["class_name"], cycle_label,
                      "Évaluation mensuelle" if row["kind"] == "monthly" else "Composition",
                      row["period_key"], row["year_label"],
                      "Finalisée" if row["status"] == "finalized" else "Brouillon"]
            for j, value in enumerate(values):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

    def selected_session(self):
        index = self.table.currentRow()
        if index < 0 or index >= len(self.sessions):
            QMessageBox.information(self, "Sélection", "Sélectionnez une évaluation dans le tableau.")
            return None
        return self.sessions[index]

    def create_year(self):
        label, ok = QInputDialog.getText(self, "Année scolaire", "Intitulé (ex. 2026-2027) :")
        if not ok:
            return
        try:
            create_academic_year(label, active=True)
            self.refresh()
        except (ValueError, sqlite3.IntegrityError) as exc:
            QMessageBox.warning(self, "Année scolaire", str(exc))

    def create_class(self):
        dialog = AcademicClassDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            create_academic_class(dialog.name.text(), dialog.cycle.currentData(),
                                  dialog.series.currentText())
            self.refresh()
        except (ValueError, sqlite3.IntegrityError) as exc:
            QMessageBox.warning(self, "Classe", str(exc))

    def create_session(self):
        class_id, year_id = self.class_box.currentData(), self.year.currentData()
        if class_id is None:
            QMessageBox.information(self, "Classe", "Créez ou sélectionnez une classe du cycle choisi.")
            return
        if year_id is None:
            QMessageBox.information(self, "Année scolaire", "Créez d'abord une année scolaire.")
            return
        cls = next((c for c in list_academic_classes() if c["id"] == class_id), None)
        if cls is None:
            return
        kind, ok = QInputDialog.getItem(self, "Type", "Type d'évaluation :",
                                        ["Évaluation mensuelle", "Composition trimestrielle"], 0, False)
        if not ok:
            return
        if kind == "Évaluation mensuelle":
            period, ok = QInputDialog.getItem(self, "Mois", "Mois :", MONTHS, 0, False)
        else:
            term_count = CYCLES[cls["cycle_code"]]["terms"]
            periods = [f"T{i}" for i in range(1, term_count + 1)]
            period, ok = QInputDialog.getItem(self, "Trimestre", "Période :", periods, 0, False)
        if not ok:
            return
        settings = get_school_settings()
        try:
            create_assessment(class_id, year_id,
                              "monthly" if kind == "Évaluation mensuelle" else "composition",
                              period, float(settings["grading_scale"]))
            self.refresh()
        except (ValueError, sqlite3.IntegrityError) as exc:
            QMessageBox.warning(self, "Évaluation", str(exc))

    def enter_grade(self):
        session = self.selected_session()
        if session is None:
            return
        if session["status"] != "draft":
            QMessageBox.information(self, "Évaluation finalisée",
                                    "Cette évaluation est verrouillée après publication.")
            return
        students = [s for s in list_students() if s["class_id"] == session["class_id"]]
        subjects = list_subjects()
        if not students or not subjects:
            QMessageBox.information(self, "Données manquantes",
                                    "Ajoutez les élèves et les matières avant la saisie.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Saisie d'une note")
        form = QFormLayout(dialog)
        student_box, subject_box, status_box = QComboBox(), QComboBox(), QComboBox()
        for s in students:
            student_box.addItem(f'{s["last_name"]} {s["first_name"]} — {s["matricule"]}', s["id"])
        for s in subjects:
            subject_box.addItem(f'{s["name"]} (coef. {s["coefficient"]:g})', s["id"])
        status_box.addItem("Note saisie", "graded")
        status_box.addItem("Absent", "absent")
        status_box.addItem("Non renseigné", "missing")
        score = QDoubleSpinBox()
        score.setRange(0, float(session["grading_scale"]))
        score.setDecimals(2)
        comment = QLineEdit()
        form.addRow("Élève", student_box)
        form.addRow("Matière", subject_box)
        form.addRow("Statut", status_box)
        form.addRow("Note", score)
        form.addRow("Appréciation", comment)
        status_box.currentIndexChanged.connect(lambda: score.setEnabled(status_box.currentData() == "graded"))
        buttons = QHBoxLayout()
        save, cancel = QPushButton("Enregistrer"), QPushButton("Annuler")
        save.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            save_assessment_grade(session["id"], student_box.currentData(),
                                  subject_box.currentData(), score.value(),
                                  status_box.currentData(), comment.text())
            QMessageBox.information(self, "Notes", "La note a été enregistrée.")
        except (ValueError, sqlite3.IntegrityError) as exc:
            QMessageBox.warning(self, "Saisie impossible", str(exc))

    def finalize(self):
        session = self.selected_session()
        if session is None:
            return
        answer = QMessageBox.question(
            self, "Validation définitive",
            "Valider cette évaluation ? GESCO calculera les moyennes et archivera "
            "un bulletin individuel par élève ainsi qu'un récapitulatif de classe."
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            summary = finalize_assessment(session["id"])
            QMessageBox.information(
                self, "Bulletins générés",
                f'{len(summary["students"])} bulletins individuels et un récapitulatif de classe ont été archivés.'
            )
            self.refresh()
        except (ValueError, sqlite3.IntegrityError) as exc:
            QMessageBox.warning(self, "Validation impossible", str(exc))

    def export_class(self):
        session = self.selected_session()
        if session is None:
            return
        reports = list_report_cards(session["id"], "class")
        if not reports:
            QMessageBox.information(self, "Aucun bulletin", "Validez d'abord l'évaluation.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exporter le récapitulatif",
                                               "recapitulatif_classe.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            settings = get_school_settings()
            export_report_card_pdf(json.loads(reports[-1]["snapshot_json"]), path,
                                   settings["school_name"])
            QMessageBox.information(self, "Export PDF", "Le récapitulatif PDF a été créé.")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur PDF", str(exc))

    def export_student(self):
        session = self.selected_session()
        if session is None:
            return
        reports = list_report_cards(session["id"], "student")
        if not reports:
            QMessageBox.information(self, "Aucun bulletin", "Validez d'abord l'évaluation.")
            return
        choices = []
        by_label = {}
        for row in reports:
            snapshot = json.loads(row["snapshot_json"])
            label = f'{snapshot["student"]["name"]} — {snapshot["student"]["matricule"]}'
            choices.append(label)
            by_label[label] = snapshot
        selected, ok = QInputDialog.getItem(self, "Bulletin individuel", "Élève :", choices, 0, False)
        if not ok:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exporter le bulletin",
                                               "bulletin_eleve.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            settings = get_school_settings()
            export_report_card_pdf(by_label[selected], path, settings["school_name"])
            QMessageBox.information(self, "Export PDF", "Le bulletin individuel a été créé.")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur PDF", str(exc))
