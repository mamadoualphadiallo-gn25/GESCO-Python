"""Fenêtre principale et tableau de bord de GESCO."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame
)
from .database import fetch_one
from .management import ManagementPage
from .subjects import SubjectsPage
from .grades import GradesPage
from .settings import SettingsPage
from .results_page import ResultsPage


APP_STYLE = """
QMainWindow, QWidget { background:#f5f7fb; color:#172033; font-family:"Segoe UI"; font-size:10pt; }
#sidebar { background:#111c35; border:0; }
#brand { color:white; font-size:25pt; font-weight:800; padding:8px 8px 0; }
#brandSub { color:#9eacc7; font-size:9pt; padding:0 8px 18px; }
QPushButton { background:white; color:#26344d; border:1px solid #e2e8f2; border-radius:9px; padding:10px 15px; font-weight:600; }
QPushButton:hover { background:#edf3ff; border-color:#c8d8fa; }
QPushButton:pressed { background:#dfe9ff; }
QPushButton#navButton { color:#c4cee0; background:transparent; border:0; text-align:left; padding:12px 14px; margin:2px 8px; border-radius:9px; font-weight:600; }
QPushButton#navButton:hover { background:#202e4d; color:white; }
QPushButton#navButton:checked { background:#315fce; color:white; }
QPushButton#primaryButton { color:white; background:#315fce; border:1px solid #315fce; }
QPushButton#primaryButton:hover { background:#244eaf; }
#topbar { background:white; border-bottom:1px solid #e6ebf3; }
#topTitle { color:#18243a; font-size:11pt; font-weight:700; }
#topHint, #pageSubtitle { color:#7b879b; font-size:9pt; }
#contentTitle { color:#17243a; font-size:23pt; font-weight:750; padding-top:5px; }
#statCard { background:white; border:1px solid #e6ebf3; border-radius:14px; padding:16px; }
#statLabel { color:#758198; font-size:9pt; font-weight:600; }
#statValue { color:#1d2b45; font-size:27pt; font-weight:800; }
#statAccent { color:#315fce; font-size:9pt; font-weight:700; }
#panel { background:white; border:1px solid #e6ebf3; border-radius:14px; }
QTableWidget { background:white; alternate-background-color:#f8faff; border:1px solid #e5eaf2; border-radius:10px; gridline-color:#edf1f6; selection-background-color:#e2ebff; selection-color:#17243a; padding:4px; }
QTableWidget::item { padding:7px; border:0; }
QHeaderView::section { background:#f0f3f8; color:#52617a; padding:10px; border:0; border-bottom:1px solid #e2e8f0; font-weight:700; }
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox { background:white; color:#17243a; border:1px solid #dce3ee; border-radius:8px; padding:9px; min-height:20px; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus { border:1px solid #4778df; }
QCheckBox { spacing:8px; }
QScrollBar:vertical { background:transparent; width:10px; margin:2px; }
QScrollBar::handle:vertical { background:#cbd4e2; border-radius:5px; min-height:25px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GESCO — Gestion scolaire")
        self.resize(1360, 850)
        self.setMinimumSize(1050, 680)
        self.setStyleSheet(APP_STYLE)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(238)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12, 22, 12, 18)
        side.setSpacing(4)
        brand = QLabel("GESCO")
        brand.setObjectName("brand")
        brand_sub = QLabel("GESTION SCOLAIRE")
        brand_sub.setObjectName("brandSub")
        side.addWidget(brand)
        side.addWidget(brand_sub)
        section = QLabel("ESPACE DE TRAVAIL")
        section.setStyleSheet("color:#8190ad; font-size:8pt; font-weight:700; padding:16px 12px 5px;")
        side.addWidget(section)

        self.pages = QStackedWidget()
        self.dashboard = self._dashboard()
        self.students = ManagementPage("students")
        self.classes = ManagementPage("classes")
        self.subjects = SubjectsPage()
        self.grades = GradesPage()
        self.results = ResultsPage()
        self.settings = SettingsPage()
        self.page_widgets = [self.dashboard, self.students, self.classes,
                             self.subjects, self.grades, self.results, self.settings]
        for page in self.page_widgets:
            self.pages.addWidget(page)

        self.nav_buttons = []
        nav_items = [
            ("▦   Tableau de bord", 0), ("♙   Élèves", 1), ("▤   Classes", 2),
            ("▧   Matières", 3), ("✎   Notes", 4), ("▥   Résultats", 5),
            ("⚙   Paramètres", 6)
        ]
        for label, index in nav_items:
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setMinimumHeight(44)
            button.clicked.connect(lambda checked=False, i=index: self.navigate(i))
            side.addWidget(button)
            self.nav_buttons.append(button)
        side.addStretch()
        offline = QLabel("●  APPLICATION HORS LIGNE")
        offline.setStyleSheet("color:#8fa0bf; padding:10px 8px; font-size:8pt;")
        side.addWidget(offline)
        version = QLabel("GESCO  •  Édition Windows")
        version.setStyleSheet("color:#71809e; padding:0 8px; font-size:8pt;")
        side.addWidget(version)

        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        topbar = QFrame()
        topbar.setObjectName("topbar")
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(28, 14, 28, 14)
        top_title = QLabel("Espace d'administration")
        top_title.setObjectName("topTitle")
        top_hint = QLabel("Suivi des élèves, des notes et des résultats")
        top_hint.setObjectName("topHint")
        top_layout.addWidget(top_title)
        top_layout.addStretch()
        top_layout.addWidget(top_hint)
        main_layout.addWidget(topbar)
        main_layout.addWidget(self.pages, 1)
        root_layout.addWidget(sidebar)
        root_layout.addWidget(main_area, 1)
        self.setCentralWidget(root)
        self.navigate(0)

    def navigate(self, index: int):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        if index == 0:
            self.refresh_dashboard()
        else:
            refresh = getattr(self.page_widgets[index], "refresh", None)
            if callable(refresh):
                refresh()

    def _dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)
        heading = QLabel("Tableau de bord")
        heading.setObjectName("contentTitle")
        subtitle = QLabel("Vue d'ensemble de votre établissement et de l'activité scolaire.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        self.stat_values = []
        stats = [
            ("ÉLÈVES INSCRITS", "SELECT COUNT(*) FROM students WHERE active=1", "Effectif actif"),
            ("CLASSES", "SELECT COUNT(*) FROM classes", "Groupes pédagogiques"),
            ("MATIÈRES", "SELECT COUNT(*) FROM subjects", "Disciplines enregistrées"),
            ("NOTES SAISIES", "SELECT COUNT(*) FROM grades", "Évaluations enregistrées"),
        ]
        for label, query, detail in stats:
            card = QFrame()
            card.setObjectName("statCard")
            card.setMinimumHeight(132)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 16, 18, 16)
            caption = QLabel(label)
            caption.setObjectName("statLabel")
            value = QLabel("0")
            value.setObjectName("statValue")
            foot = QLabel(detail)
            foot.setObjectName("statAccent")
            card_layout.addWidget(caption)
            card_layout.addWidget(value)
            card_layout.addStretch()
            card_layout.addWidget(foot)
            cards.addWidget(card)
            self.stat_values.append((value, query))
        layout.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(22, 20, 22, 20)
        panel_layout.setSpacing(12)
        panel_title = QLabel("Accès rapide")
        panel_title.setStyleSheet("font-size:15pt; font-weight:700; color:#1c2a43;")
        panel_desc = QLabel("Choisissez une action pour commencer votre travail.")
        panel_desc.setObjectName("pageSubtitle")
        panel_layout.addWidget(panel_title)
        panel_layout.addWidget(panel_desc)
        actions = QHBoxLayout()
        for label, index in [
            ("＋  Inscrire un élève", 1), ("▤  Gérer les classes", 2),
            ("✎  Saisir des notes", 4), ("▥  Voir les résultats", 5)
        ]:
            button = QPushButton(label)
            button.setMinimumHeight(48)
            if index == 1:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, i=index: self.navigate(i))
            actions.addWidget(button)
        panel_layout.addLayout(actions)
        layout.addWidget(panel)
        layout.addStretch()
        return page

    def refresh_dashboard(self):
        for value_label, query in self.stat_values:
            result = fetch_one(query)
            value_label.setText(str(result[0] if result else 0))
