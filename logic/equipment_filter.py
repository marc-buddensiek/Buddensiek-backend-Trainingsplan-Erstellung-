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

# Übungen werden Python-seitig gefiltert BEVOR Claude sie sieht
_VERLETZUNG_BLOCKED: dict[str, set[str]] = {
    "knie":         {"deep_squat", "lunge", "jump", "plyo"},
    "schulter":     {"overhead_press", "bench_heavy", "dip"},
    "wirbelsäule":  {"heavy_hinge", "loaded_flexion"},
    "hüfte":        {"deep_squat", "wide_lunge"},
    "ellenbogen":   {"curl_pronation", "skull_crusher"},
    "handgelenk":   {"front_squat", "push_up_floor"},
    "hals":         {"heavy_shrug", "behind_neck"},
    "knöchel":      {"deep_squat", "jumping", "sprinting"},
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

    # Geblockte pattern_tags aus allen Verletzungen zusammenstellen
    blocked_patterns: set[str] = set()
    for v in klient.verletzungen:
        blocked_patterns |= _VERLETZUNG_BLOCKED.get(v.value, set())

    result: dict[str, list[dict]] = {}

    for ex in alle:
        # Equipment-Check
        if not any(eq in erlaubte_equipment for eq in ex["equipment"]):
            continue
        # Level-Check
        if ex["level_min"] > level:
            continue
        # Equipment-Detail-Check: Übung braucht spezifisches Gerät das der Klient hat?
        required = ex.get("equipment_requires", [])
        if required and klient.equipment_items and not any(item in klient.equipment_items for item in required):
            continue
        # Verletzungs-Blocking via pattern_tags (Python-seitig, vor Claude)
        if blocked_patterns and set(ex.get("pattern_tags", [])) & blocked_patterns:
            continue

        # Verletzungs-Flag für Substitutions-Hinweise aufbauen
        sub_b = ex.get("substitutions_b", {})
        betroffene = [key for key in verletzungs_keys if key in sub_b]

        ex_copy = dict(ex)
        ex_copy["verletzungs_flag"] = betroffene

        pattern = ex["pattern"]
        result.setdefault(pattern, []).append(ex_copy)

    return result
