"""Gestion des modèles personnalisables de bulletins."""
import json
import re
from .academic import CYCLES
from .database import get_connection, fetch_all, fetch_one


def save_template(cycle_code: str, name: str, header_color: str = "#20365f",
                  show_coefficients: bool = True, show_comments: bool = True,
                  show_rank: bool = True, make_default: bool = False) -> int:
    if cycle_code not in CYCLES or not name.strip():
        raise ValueError("Cycle et nom du modèle obligatoires.")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", header_color):
        raise ValueError("La couleur doit être au format hexadécimal #RRGGBB.")
    config = {
        "header_color": header_color,
        "show_coefficients": bool(show_coefficients),
        "show_comments": bool(show_comments),
        "show_rank": bool(show_rank),
    }
    with get_connection() as db:
        if make_default:
            db.execute("UPDATE report_card_templates SET is_default=0 WHERE cycle_code=?",
                       (cycle_code,))
        db.execute(
            """INSERT INTO report_card_templates(cycle_code,name,config_json,is_default)
               VALUES(?,?,?,?) ON CONFLICT(cycle_code,name) DO UPDATE SET
               config_json=excluded.config_json,is_default=excluded.is_default""",
            (cycle_code, name.strip(), json.dumps(config, ensure_ascii=False), int(make_default))
        )
        row = db.execute(
            "SELECT id FROM report_card_templates WHERE cycle_code=? AND name=?",
            (cycle_code, name.strip())
        ).fetchone()
        return int(row["id"])


def list_templates(cycle_code: str = ""):
    if cycle_code:
        return fetch_all(
            "SELECT * FROM report_card_templates WHERE cycle_code=? ORDER BY is_default DESC,name",
            (cycle_code,)
        )
    return fetch_all("SELECT * FROM report_card_templates ORDER BY cycle_code,is_default DESC,name")


def get_default_template(cycle_code: str) -> dict:
    row = fetch_one(
        "SELECT config_json FROM report_card_templates WHERE cycle_code=? ORDER BY is_default DESC,id LIMIT 1",
        (cycle_code,)
    )
    if not row:
        return {}
    try:
        return json.loads(row["config_json"])
    except (TypeError, json.JSONDecodeError):
        return {}
