"""
Typeform Webhook Payload → KlientenInput

Typeform sendet choice-Antworten mit unterschiedlichen ref-Typen:
  - Felder mit custom ref (hauptziel, equipment, trainingsjahre) → choice.ref verwenden
  - nebenziel hat jetzt saubere choice refs → choice.ref verwenden
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

    return KlientenInput(
        client_id=payload["form_response"]["hidden"]["client_id"],
        vorname=_text("vorname"),
        alter=_number("alter"),
        hauptziel=_choice_ref("hauptziel"),                    # ref: "muskelaufbau" | "fettabbau" | ...
        nebenziel=_choice_ref("nebenziel"),                    # nur gesetzt wenn Typeform Q7=Ja, sonst None
        tage_pro_woche=int(_choice_label("tage_pro_woche")),
        session_dauer_min=int(_choice_label("session_dauer_min")),
        equipment=_choice_ref("equipment"),                    # ref: "gym" | "home_gym" | ...
        trainingsjahre=_choice_ref("trainingsjahre"),          # ref: "keine" | "unter_1" | ...
        stress_level=_number("stress_level"),
        schlaf_stunden=float(_choice_label("schlaf_stunden")),
        verletzungen=[v for v in _choices_labels("verletzungen") if v != "keine"],
        schmerzen_akut=_boolean("schmerzen_akut") or False,
        medizinische_diagnosen=_text("medizinische_diagnosen"),
        motivation=_text("motivation"),
        aktuelles_training=_text("aktuelles_training"),
        kniebeugen_wdh=_number("kniebeugen_wdh"),
        pushups_wdh=_number("pushups_wdh"),
        situps_wdh=_number("situps_wdh"),
        burpees_wdh=_number("burpees_wdh"),
        plank_sek=_number("plank_sek"),
    )
