"""Paramètres généraux de l'établissement et du barème."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QDoubleSpinBox, QCheckBox, QPushButton, QMessageBox
from .services import get_school_settings, update_school_settings


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Paramètres de l'établissement")
        title.setObjectName("contentTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Ces paramètres sont enregistrés localement sur cet ordinateur."))
        form = QFormLayout()
        self.school_name = QLineEdit()
        self.school_year = QLineEdit()
        self.scale = QDoubleSpinBox()
        self.scale.setRange(1, 1000)
        self.scale.setDecimals(2)
        self.absence_zero = QCheckBox("Considérer une absence à une évaluation comme une note zéro")
        form.addRow("Nom de l'établissement", self.school_name)
        form.addRow("Année scolaire", self.school_year)
        form.addRow("Barème maximal", self.scale)
        form.addRow("", self.absence_zero)
        layout.addLayout(form)
        save = QPushButton("Enregistrer les paramètres")
        save.clicked.connect(self.save)
        layout.addWidget(save)
        layout.addStretch()
        self.load()

    def load(self):
        settings = get_school_settings()
        if settings:
            self.school_name.setText(settings["school_name"])
            self.school_year.setText(settings["school_year"])
            self.scale.setValue(float(settings["grading_scale"]))
            self.absence_zero.setChecked(bool(settings["absence_as_zero"]))

    def save(self):
        try:
            update_school_settings(self.school_name.text(), self.school_year.text(),
                                   self.scale.value(), self.absence_zero.isChecked())
            QMessageBox.information(self, "Paramètres", "Les paramètres ont été enregistrés.")
        except ValueError as exc:
            QMessageBox.warning(self, "Paramètres invalides", str(exc))
