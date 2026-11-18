"""Vérifie que les modules de l'interface peuvent être importés."""
def test_all_interface_modules_import():
    from gesco.window import MainWindow
    from gesco.management import ManagementPage
    from gesco.subjects import SubjectsPage
    from gesco.grades import GradesPage
    from gesco.settings import SettingsPage
    from gesco.results_page import ResultsPage

    assert all((MainWindow, ManagementPage, SubjectsPage, GradesPage,
                SettingsPage, ResultsPage))
