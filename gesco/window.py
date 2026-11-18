"""Fenêtre principale de GESCO."""
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QFrame
from .database import fetch_one
from .management import ManagementPage
from .subjects import SubjectsPage
from .grades import GradesPage
from .settings import SettingsPage
from .results_page import ResultsPage

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
            QPushButton { background: #ffffff; border: 1px solid #dce2ec; border-radius: 8px; padding: 10px 14px; font-size: 13px; }
            QPushButton:hover { background: #eaf0ff; }
            #contentTitle { font-size: 25px; font-weight: 700; }
            #statCard { background: white; border: 1px solid #e4e9f1; border-radius: 12px; padding: 18px; }
            #statValue { font-size: 28px; font-weight: 700; color: #3157c8; }
            QTableWidget { background:white; border:1px solid #e4e9f1; border-radius:10px; gridline-color:#edf0f5; selection-background-color:#dce7ff; }
            QHeaderView::section { background:#edf1f8; padding:9px; border:0; font-weight:600; }
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox { background:white; border:1px solid #dce2ec; border-radius:7px; padding:8px; }
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
        self.pages = QStackedWidget()
        self.dashboard = self._dashboard()
        self.students = ManagementPage("students")
        self.classes = ManagementPage("classes")
        self.subjects = SubjectsPage()
        self.grades = GradesPage()
        self.results = ResultsPage()
        self.settings = SettingsPage()
        for page in [self.dashboard, self.students, self.classes, self.subjects, self.grades, self.results, self.settings]:
            self.pages.addWidget(page)
        for label, index in [("Tableau de bord", 0), ("Élèves", 1), ("Classes", 2),
                             ("Matières", 3), ("Notes", 4), ("Résultats", 5), ("Paramètres", 6)]:
            button = QPushButton(label)
            button.setStyleSheet("color:white; background:transparent; border:0; text-align:left; margin:3px 8px;")
            button.clicked.connect(lambda checked=False, i=index: self.pages.setCurrentIndex(i))
            side_layout.addWidget(button)
        side_layout.addStretch()
        version = QLabel("Version 1.1.0 • Hors ligne")
        version.setStyleSheet("color:#aab7cc; padding:14px;")
        side_layout.addWidget(version)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)

    def _dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        heading = QLabel("Tableau de bord")
        heading.setObjectName("contentTitle")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Vue générale de votre établissement"))
        cards = QHBoxLayout()
        for label, query in [("Élèves inscrits", "SELECT COUNT(*) FROM students WHERE active=1"),
                             ("Classes", "SELECT COUNT(*) FROM classes"),
                             ("Matières", "SELECT COUNT(*) FROM subjects")]:
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
