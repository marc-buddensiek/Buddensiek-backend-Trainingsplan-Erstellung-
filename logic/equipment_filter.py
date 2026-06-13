"""
exercises.json filtern nach Equipment + Level + 2-Stufen-Verletzungsfilter
(Stufe 1: joint_stress ∩ Verletzungen · Stufe 2: impact_level high — Spec Thema 8,
pattern_tags-Blocker gestrichen 2026-06-12, Tags sind dormant).

Gibt ein Dict zurück: {"pattern_name": [übungs_dict, ...]}

Mapping VerletzungsBereich (Deutsch) → joint_stress-Vokabel (Englisch):
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
    Returns dict by pattern with filtered exercises (verletzungssicher per Konstruktion).
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
        # Level-Check
        if ex["skill_level"] > level:
            continue
        # Equipment-Detail-Check: Übung braucht spezifisches Gerät das der Klient hat?
        required = ex.get("equipment_requires", [])
        if required and klient.equipment_items and not any(item in klient.equipment_items for item in required):
            continue
        # Verletzungs-Filter Stufe 1: Übung belastet eine verletzte Region → raus
        # (Vereinigung über alle Verletzungen — Mehrfach-Verletzungen automatisch abgedeckt)
        if verletzungs_keys and any(r in ex.get("joint_stress", []) for r in verletzungs_keys):
            continue
        # Verletzungs-Filter Stufe 2: bei jeder Verletzung kein high-Impact (Spec Thema 8)
        if verletzungs_keys and ex.get("impact_level") == "high":
            continue

        # Kein verletzungs_flag mehr: nach dem 2-Stufen-Filter ist die Liste
        # per Konstruktion verletzungssicher (substitutions_b abgelöst, MVP-5 Naht 3)
        result.setdefault(ex["pattern"], []).append(ex)

    return result
