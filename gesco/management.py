"""Écrans de gestion des classes et des élèves."""
import sqlite3
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QHeaderView
)
from PySide6.QtCore import QDate
from .database import fetch_all
from .services import (
    list_classes, list_students, add_class, update_class, delete_class,
    add_student, update_student, delete_student
)


class ClassDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Classe")
        form = QFormLayout(self)
        self.name = QLineEdit(data["name"] if data else "")
        self.level = QLineEdit(data["level"] if data else "")
        form.addRow("Nom de la classe *", self.name)
        form.addRow("Niveau", self.level)
        buttons = QHBoxLayout()
        save = QPushButton("Enregistrer")
        cancel = QPushButton("Annuler")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        form.addRow(buttons)


class StudentDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Fiche élève")
        form = QFormLayout(self)
        self.matricule = QLineEdit(data["matricule"] if data else "")
        self.last_name = QLineEdit(data["last_name"] if data else "")
        self.first_name = QLineEdit(data["first_name"] if data else "")
        self.gender = QComboBox()
        self.gender.addItems(["Non précisé", "Masculin", "Féminin"])
        if data and data["gender"] in ["Masculin", "Féminin"]:
            self.gender.setCurrentText(data["gender"])
        self.birth = QDateEdit()
        self.birth.setCalendarPopup(True)
        self.birth.setDisplayFormat("dd/MM/yyyy")
        self.birth.setDate(QDate.currentDate())
        if data and data["birth_date"]:
            parsed = QDate.fromString(data["birth_date"], "yyyy-MM-dd")
            if parsed.isValid():
                self.birth.setDate(parsed)
        self.class_box = QComboBox()
        self.class_box.addItem("Non affecté", None)
        classes = list_classes()
        for item in classes:
            self.class_box.addItem(item["name"], item["id"])
        if data and data["class_id"] is not None:
            index = self.class_box.findData(data["class_id"])
            if index >= 0:
                self.class_box.setCurrentIndex(index)
        form.addRow("Matricule *", self.matricule)
        form.addRow("Nom *", self.last_name)
        form.addRow("Prénom *", self.first_name)
        form.addRow("Sexe", self.gender)
        form.addRow("Date de naissance", self.birth)
        form.addRow("Classe", self.class_box)
        buttons = QHBoxLayout()
        save = QPushButton("Enregistrer")
        cancel = QPushButton("Annuler")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        form.addRow(buttons)


class ManagementPage(QWidget):
    def __init__(self, kind: str):
        super().__init__()
        self.kind = kind
        self.rows = []
        layout = QVBoxLayout(self)
        title = "Gestion des élèves" if kind == "students" else "Gestion des classes"
        subtitle = "Inscrire, rechercher et suivre les élèves." if kind == "students" else "Créer et organiser les classes de l'établissement."
        heading = QLabel(title)
        heading.setObjectName("contentTitle")
        hint = QLabel(subtitle)
        hint.setStyleSheet("color:#68758a;")
        layout.addWidget(heading)
        layout.addWidget(hint)
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un élève..." if kind == "students" else "Rechercher une classe...")
        self.search.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search, 1)
        add = QPushButton("＋ Ajouter")
        edit = QPushButton("Modifier")
        remove = QPushButton("Archiver" if kind == "students" else "Supprimer")
        add.clicked.connect(self.add_item)
        edit.clicked.connect(self.edit_item)
        remove.clicked.connect(self.remove_item)
        toolbar.addWidget(add)
        toolbar.addWidget(edit)
        toolbar.addWidget(remove)
        layout.addLayout(toolbar)
        self.table = QTableWidget()
        headers = (["Matricule", "Nom", "Prénom", "Sexe", "Date de naissance", "Classe"]
                   if kind == "students" else ["Nom de la classe", "Niveau", "Effectif"])
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        self.refresh()

    def refresh(self, *_):
        self.rows = (list_students(self.search.text()) if self.kind == "students"
                     else [r for r in list_classes()
                           if self.search.text().lower() in r["name"].lower()
                           or self.search.text().lower() in r["level"].lower()])
        self.table.setRowCount(len(self.rows))
        for row_index, row in enumerate(self.rows):
            if self.kind == "students":
                values = [row["matricule"], row["last_name"], row["first_name"],
                          row["gender"], row["birth_date"], row["class_name"]]
            else:
                count = fetch_all("SELECT id FROM students WHERE active=1 AND class_id=?", (row["id"],))
                values = [row["name"], row["level"], str(len(count))]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value or ""))
                item.setData(Qt.ItemDataRole.UserRole, row["id"])
                self.table.setItem(row_index, col, item)

    def selected(self):
        index = self.table.currentRow()
        if index < 0 or index >= len(self.rows):
            QMessageBox.information(self, "Sélection", "Sélectionnez d'abord une ligne.")
            return None
        return self.rows[index]

    def add_item(self):
        dialog = StudentDialog(self) if self.kind == "students" else ClassDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            if self.kind == "students":
                add_student(dialog.matricule.text(), dialog.last_name.text(),
                            dialog.first_name.text(), dialog.gender.currentText(),
                            dialog.class_box.currentData(),
                            dialog.birth.date().toString("yyyy-MM-dd"))
            else:
                add_class(dialog.name.text(), dialog.level.text())
            self.refresh()
        except (ValueError, sqlite3.IntegrityError) as exc:
            QMessageBox.warning(self, "Impossible d'enregistrer", str(exc))

    def edit_item(self):
        row = self.selected()
        if row is None:
            return
        dialog = StudentDialog(self, row) if self.kind == "students" else ClassDialog(self, row)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            if self.kind == "students":
                update_student(row["id"], dialog.matricule.text(), dialog.last_name.text(),
                               dialog.first_name.text(), dialog.gender.currentText(),
                               dialog.class_box.currentData(),
                               dialog.birth.date().toString("yyyy-MM-dd"))
            else:
                update_class(row["id"], dialog.name.text(), dialog.level.text())
            self.refresh()
        except (ValueError, sqlite3.IntegrityError) as exc:
            QMessageBox.warning(self, "Impossible de modifier", str(exc))

    def remove_item(self):
        row = self.selected()
        if row is None:
            return
        label = row["matricule"] if self.kind == "students" else row["name"]
        action = "archiver" if self.kind == "students" else "supprimer"
        answer = QMessageBox.question(self, "Confirmation", f"Voulez-vous vraiment {action} « {label} » ?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        if self.kind == "students":
            delete_student(row["id"])
        else:
            delete_class(row["id"])
        self.refresh()
