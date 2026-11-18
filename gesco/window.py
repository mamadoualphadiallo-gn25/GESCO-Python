"""Interface principale de GESCO."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame
)
from .database import fetch_one


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GESCO — Gestion scolaire")
        self.resize(1180, 760)
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f4f6fb; color: #182235; font-family: Segoe UI; }
            #sidebar { background: #17243a; }
            #brand { color: white; font-size: 23px; font-weight: 700; padding: 20px; }
            QPushButton { background: #ffffff; border: 1px solid #dce2ec; border-radius: 8px;
                          padding: 11px 15px; text-align: left; font-size: 14px; }
            QPushButton:hover { background: #eaf0ff; }
            #contentTitle { font-size: 25px; font-weight: 700; }
            #statCard { background: white; border: 1px solid #e4e9f1; border-radius: 12px; padding: 18px; }
            #statValue { font-size: 28px; font-weight: 700; color: #3157c8; }
        """)
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        brand = QLabel("GESCO")
        brand.setObjectName("brand")
        side_layout.addWidget(brand)
        side_layout.addWidget(self._nav_button("Tableau de bord", 0))
        side_layout.addWidget(self._nav_button("Élèves", 1))
        side_layout.addWidget(self._nav_button("Classes", 2))
        side_layout.addWidget(self._nav_button("Notes", 3))
        side_layout.addWidget(self._nav_button("Paramètres", 4))
        side_layout.addStretch()
        version = QLabel("Version 1.0.0 • Hors ligne")
        version.setStyleSheet("color:#aab7cc; padding:14px;")
        side_layout.addWidget(version)
        self.pages = QStackedWidget()
        for title, description in [
            ("Tableau de bord", "Vue générale de votre établissement"),
            ("Gestion des élèves", "Inscription et suivi des élèves"),
            ("Gestion des classes", "Organisation des classes et niveaux"),
            ("Gestion des notes", "Saisie et suivi des évaluations"),
            ("Paramètres", "Configuration de l'établissement et du barème"),
        ]:
            self.pages.addWidget(self._page(title, description))
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)

    def _nav_button(self, text: str, index: int):
        button = QPushButton(text)
        button.setStyleSheet("color:#17243a; margin:4px 12px;")
        button.clicked.connect(lambda: self.pages.setCurrentIndex(index))
        return button

    def _page(self, title: str, description: str):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        heading = QLabel(title)
        heading.setObjectName("contentTitle")
        subtitle = QLabel(description)
        subtitle.setStyleSheet("color:#68758a; font-size:14px;")
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        if title == "Tableau de bord":
            cards = QHBoxLayout()
            for label, query in [
                ("Élèves inscrits", "SELECT COUNT(*) FROM students WHERE active=1"),
                ("Classes", "SELECT COUNT(*) FROM classes"),
                ("Matières", "SELECT COUNT(*) FROM subjects"),
            ]:
                card = QFrame()
                card.setObjectName("statCard")
                card_layout = QVBoxLayout(card)
                caption = QLabel(label)
                value = QLabel(str(fetch_one(query)[0]))
                value.setObjectName("statValue")
                card_layout.addWidget(caption)
                card_layout.addWidget(value)
                cards.addWidget(card)
            layout.addLayout(cards)
        layout.addStretch()
        return page
