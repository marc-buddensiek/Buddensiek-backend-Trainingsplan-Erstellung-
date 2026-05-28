"""
exercises.json filtern nach Equipment + Level + Verletzungs-Substitutionen

Gibt ein Dict zurück: {"pattern_name": [übungs_dict, ...]}
Verletzungs-Warnungen werden als "substitutions_b"-Flags übergeben (englisch).

Mapping VerletzungsBereich (Deutsch) → exercises.json substitutions_b key (Englisch):
  knie        → knee
  schulter    → shoulder
  wirbelsäule → spine
  hüfte       → hip
  ellenbogen  → elbow
  handgelenk  → wrist
  hals        → neck
  knöchel     → ankle
"""

from __future__ import annotations
import json
import pathlib

from models import KlientenInput, Equipment, VerletzungsBereich


_EXERCISES_PATH = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"

_VERLETZUNG_MAP: dict[str, str] = {
    "knie":         "knee",
    "schulter":     "shoulder",
    "wirbelsäule":  "spine",
    "hüfte":        "hip",
    "ellenbogen":   "elbow",
    "handgelenk":   "wrist",
    "hals":         "neck",
    "knöchel":      "ankle",
}

# Equipment-Pfade die sich gegenseitig einschließen
_EQUIPMENT_INCLUDES: dict[str, list[str]] = {
    "gym":        ["gym"],
    "home_gym":   ["home_gym", "bodyweight"],
    "kettlebell": ["kettlebell", "bodyweight"],
    "bodyweight": ["bodyweight"],
    "travel":     ["travel", "bodyweight"],
    "hybrid":     ["hybrid", "kettlebell", "bodyweight"],
}


def _lade_exercises() -> list[dict]:
    return json.loads(_EXERCISES_PATH.read_text())["exercises"]


def filtere_uebungen(klient: KlientenInput, level: int) -> dict[str, list[dict]]:
    """
    Returns dict by pattern with filtered exercises.
    Each exercise in list has an extra field 'verletzungs_flag' (list of affected body parts).
    """
    alle = _lade_exercises()
    erlaubte_equipment = _EQUIPMENT_INCLUDES.get(klient.equipment.value, [klient.equipment.value])

    verletzungs_keys = {
        _VERLETZUNG_MAP[v.value]
        for v in klient.verletzungen
        if v.value in _VERLETZUNG_MAP
    }

    result: dict[str, list[dict]] = {}

    for ex in alle:
        # Equipment-Check
        if not any(eq in erlaubte_equipment for eq in ex["equipment"]):
            continue
        # Level-Check — zeige nur Übungen die für dieses Level geeignet sind
        if ex["level_min"] > level:
            continue

        # Verletzungs-Flag aufbauen
        sub_b = ex.get("substitutions_b", {})
        betroffene = [key for key in verletzungs_keys if key in sub_b]

        ex_copy = dict(ex)
        ex_copy["verletzungs_flag"] = betroffene

        pattern = ex["pattern"]
        result.setdefault(pattern, []).append(ex_copy)

    return result
