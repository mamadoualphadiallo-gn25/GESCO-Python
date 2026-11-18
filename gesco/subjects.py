"""Écrans de gestion des matières et des coefficients."""
import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QMessageBox, QHeaderView
)
from .services import list_subjects, add_subject, update_subject, delete_subject


class SubjectDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Matière et coefficient")
        form = QFormLayout(self)
        self.name = QLineEdit(data["name"] if data else "")
        self.coefficient = QDoubleSpinBox()
        self.coefficient.setRange(0.01, 100)
        self.coefficient.setDecimals(2)
        self.coefficient.setValue(float(data["coefficient"]) if data else 1)
        form.addRow("Nom de la matière *", self.name)
        form.addRow("Coefficient", self.coefficient)
        actions = QHBoxLayout()
        save, cancel = QPushButton("Enregistrer"), QPushButton("Annuler")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        actions.addWidget(save)
        actions.addWidget(cancel)
        form.addRow(actions)


class SubjectsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.rows = []
        layout = QVBoxLayout(self)
        title = QLabel("Gestion des matières")
        title.setObjectName("contentTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Définissez les matières enseignées et leurs coefficients."))
        actions = QHBoxLayout()
        add, edit, remove = QPushButton("＋ Ajouter"), QPushButton("Modifier"), QPushButton("Supprimer")
        add.clicked.connect(self.add_item)
        edit.clicked.connect(self.edit_item)
        remove.clicked.connect(self.remove_item)
        actions.addWidget(add)
        actions.addWidget(edit)
        actions.addWidget(remove)
        actions.addStretch()
        layout.addLayout(actions)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Matière", "Coefficient"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self):
        self.rows = list_subjects()
        self.table.setRowCount(len(self.rows))
        for i, row in enumerate(self.rows):
            self.table.setItem(i, 0, QTableWidgetItem(row["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(f'{row["coefficient"]:g}'))

    def selected(self):
        index = self.table.currentRow()
        if index < 0 or index >= len(self.rows):
            QMessageBox.information(self, "Sélection", "Sélectionnez une matière.")
            return None
        return self.rows[index]

    def add_item(self):
        dialog = SubjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                add_subject(dialog.name.text(), dialog.coefficient.value())
                self.refresh()
            except (ValueError, sqlite3.IntegrityError) as exc:
                QMessageBox.warning(self, "Enregistrement impossible", str(exc))

    def edit_item(self):
        row = self.selected()
        if row is None:
            return
        dialog = SubjectDialog(self, row)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                update_subject(row["id"], dialog.name.text(), dialog.coefficient.value())
                self.refresh()
            except (ValueError, sqlite3.IntegrityError) as exc:
                QMessageBox.warning(self, "Modification impossible", str(exc))

    def remove_item(self):
        row = self.selected()
        if row is None:
            return
        answer = QMessageBox.question(self, "Confirmation",
                                      f'Supprimer la matière « {row["name"]} » et ses notes associées ?')
        if answer == QMessageBox.StandardButton.Yes:
            delete_subject(row["id"])
            self.refresh()
