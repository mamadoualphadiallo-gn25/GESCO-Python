from gesco.results import class_results

def test_class_results_orders_and_ranks(monkeypatch):
    from gesco import results
    monkeypatch.setattr(results, "list_students", lambda: [
        {"id": 1, "class_id": 7, "matricule": "A", "last_name": "Alpha", "first_name": "A"},
        {"id": 2, "class_id": 7, "matricule": "B", "last_name": "Beta", "first_name": "B"},
        {"id": 3, "class_id": 7, "matricule": "C", "last_name": "Gamma", "first_name": "C"},
    ])
    monkeypatch.setattr(results, "calculate_average", lambda student_id, period:
                        {1: 14.5, 2: 14.5, 3: 9.0}[student_id])
    data = class_results(7, "1er trimestre")
    assert [row["rank"] for row in data] == [1, 1, 3]
    assert [row["matricule"] for row in data] == ["A", "B", "C"]
