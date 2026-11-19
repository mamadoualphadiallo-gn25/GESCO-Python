"""Écran de consultation des résultats et export du classement PDF."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView)
from .services import list_classes
from .results import class_results, export_ranking_pdf

class ResultsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Résultats et classement")
        title.setObjectName("contentTitle")
        layout.addWidget(title)
        bar = QHBoxLayout()
        self.class_box = QComboBox()
        self.period_box = QComboBox()
        self.period_box.setEditable(True)
        self.period_box.addItems(["Octobre", "Novembre", "Décembre", "1er trimestre",
                                  "2e trimestre", "3e trimestre", "Annuel"])
        refresh = QPushButton("Actualiser")
        refresh.clicked.connect(self.refresh)
        export = QPushButton("Exporter le classement PDF")
        export.clicked.connect(self.export_pdf)
        bar.addWidget(QLabel("Classe")); bar.addWidget(self.class_box, 1)
        bar.addWidget(QLabel("Période")); bar.addWidget(self.period_box, 1)
        bar.addWidget(refresh); bar.addWidget(export)
        layout.addLayout(bar)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Rang", "Matricule", "Élève", "Moyenne / 20", "Mention"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        for cls in list_classes():
            self.class_box.addItem(cls["name"], cls["id"])
        self.class_box.currentIndexChanged.connect(self.refresh)
        self.period_box.currentTextChanged.connect(self.refresh)
        self.refresh()

    def refresh(self, *_):
        class_id = self.class_box.currentData()
        if class_id is None:
            self.table.setRowCount(0); return
        rows = class_results(class_id, self.period_box.currentText())
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            avg = row["average"]
            values = [row["rank"] or "—", row["matricule"], row["name"],
                      "—" if avg is None else f"{avg:.2f}",
                      "Non classé" if avg is None else "Très bien" if avg >= 16 else
                      "Bien" if avg >= 14 else "Assez bien" if avg >= 12 else
                      "Passable" if avg >= 10 else "Insuffisant"]
            for j, value in enumerate(values):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

    def export_pdf(self):
        class_id = self.class_box.currentData()
        if class_id is None:
            QMessageBox.information(self, "Classe requise", "Créez ou sélectionnez une classe.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le classement",
            "classement.pdf", "PDF (*.pdf)")
        if not path: return
        try:
            export_ranking_pdf(class_id, self.period_box.currentText(), path)
            QMessageBox.information(self, "Export terminé", "Le classement PDF a été créé.")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur PDF", str(exc))
