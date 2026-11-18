"""Calcul des résultats de classe et génération des classements PDF."""
from pathlib import Path
from .services import list_students, list_classes, calculate_average

def class_results(class_id: int, period: str):
    rows = [s for s in list_students() if s["class_id"] == class_id]
    results = []
    for student in rows:
        average = calculate_average(student["id"], period)
        results.append({"id": student["id"], "matricule": student["matricule"],
                        "name": f'{student["last_name"]} {student["first_name"]}',
                        "average": average})
    results.sort(key=lambda item: (item["average"] is None,
                                   -(item["average"] or 0), item["name"].casefold()))
    previous = object()
    rank = 0
    for position, item in enumerate(results, 1):
        value = item["average"]
        if value is None:
            item["rank"] = None
        else:
            if value != previous:
                rank = position
                previous = value
            item["rank"] = rank
    return results

def export_ranking_pdf(class_id: int, period: str, destination: str | Path):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    classes = {c["id"]: c for c in list_classes()}
    cls = classes.get(class_id)
    if cls is None:
        raise ValueError("Classe introuvable.")
    rows = class_results(class_id, period)
    doc = SimpleDocTemplate(str(destination), pagesize=landscape(A4),
                            rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32)
    styles = getSampleStyleSheet()
    story = [Paragraph("GESCO — Classement par mérite", styles["Title"]),
             Paragraph(f'Classe : {cls["name"]} | Période : {period}', styles["Heading2"]),
             Spacer(1, 14)]
    data = [["Rang", "Matricule", "Nom et prénom", "Moyenne / 20", "Mention"]]
    for item in rows:
        avg = item["average"]
        mention = ("Non classé" if avg is None else "Très bien" if avg >= 16 else
                   "Bien" if avg >= 14 else "Assez bien" if avg >= 12 else
                   "Passable" if avg >= 10 else "Insuffisant")
        data.append([item["rank"] or "—", item["matricule"], item["name"],
                     "—" if avg is None else f"{avg:.2f}", mention])
    table = Table(data, repeatRows=1, colWidths=[55, 110, 260, 110, 130])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20365f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#d8deea")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5fa")]),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 1), (3, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    doc.build(story)
    return Path(destination)
