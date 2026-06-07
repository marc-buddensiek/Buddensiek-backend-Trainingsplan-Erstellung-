"""
Typeform Webhook Payload → KlientenInput

Typeform sendet choice-Antworten mit unterschiedlichen ref-Typen:
  - Felder mit custom ref (hauptziel, equipment, trainingsjahre) → choice.ref verwenden
  - Numerische Choices (tage_pro_woche, session_dauer_min, schlaf_stunden) → choice.label → int/float
"""

from __future__ import annotations
from typing import Optional
from models import KlientenInput


def parse_typeform_payload(payload: dict) -> KlientenInput:
    """
    Wandelt Typeform-Webhook-Payload in KlientenInput um.
    Raises pydantic.ValidationError wenn Pflichtfelder fehlen oder ungültig sind.
    """
    answers_raw = payload["form_response"]["answers"]
    by_ref: dict[str, dict] = {a["field"]["ref"]: a for a in answers_raw}

    def _text(ref: str) -> Optional[str]:
        a = by_ref.get(ref)
        if not a or a.get("type") != "text":
            return None
        val = a.get("text", "").strip()
        return val or None

    def _number(ref: str) -> Optional[float]:
        a = by_ref.get(ref)
        return a["number"] if a and a.get("type") == "number" else None

    def _boolean(ref: str) -> Optional[bool]:
        a = by_ref.get(ref)
        return a["boolean"] if a and a.get("type") == "boolean" else None

    def _choice_ref(ref: str) -> Optional[str]:
        a = by_ref.get(ref)
        return a["choice"]["ref"] if a and a.get("type") == "choice" else None

    def _choice_label(ref: str) -> Optional[str]:
        a = by_ref.get(ref)
        return a["choice"]["label"] if a and a.get("type") == "choice" else None

    def _choices_labels(ref: str) -> list[str]:
        a = by_ref.get(ref)
        if a and a.get("type") == "choices":
            return a["choices"]["labels"]
        return []

    # Equipment-Details aus den vier möglichen Follow-Up-Feldern zusammenführen
    equipment_items: list[str] = []
    for _ref in ("home_gym_items", "travel_items", "kettlebell_items", "hybrid_items"):
        equipment_items.extend(_choices_labels(_ref))

    return KlientenInput(
        client_id=payload["form_response"]["hidden"]["client_id"],
        vorname=_text("vorname"),
        alter=_number("alter"),
        hauptziel=_choice_ref("hauptziel"),
        schwachstelle=_choice_ref("schwachstelle"),
        tage_pro_woche=int(_choice_label("tage_pro_woche")),
        session_dauer_min=int(_choice_label("session_dauer_min")),
        equipment=_choice_ref("equipment"),
        trainingsjahre=_choice_ref("trainingsjahre"),
        stress_level=_number("stress_level"),
        schlaf_stunden=float(_choice_label("schlaf_stunden")),
        verletzungen=[v for v in _choices_labels("verletzungen") if v != "keine"],
        medizinische_diagnosen=_text("medizinische_diagnosen"),
        motivation=_text("motivation"),
        aktuelles_training=_text("aktuelles_training"),
        equipment_items=equipment_items,
        kniebeugen_wdh=_number("kniebeugen_wdh"),
        pushups_wdh=_number("pushups_wdh"),
        situps_wdh=_number("situps_wdh"),
        burpees_wdh=_number("burpees_wdh"),
        plank_sek=_number("plank_sek"),
    )
