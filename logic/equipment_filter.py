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

# Stufe-2-Gating (Verletzungsfilter): High-Impact nur bei Bein-/Achs-/Hals-Verletzung meiden.
# Backstop, bis joint_stress lückenlos getaggt ist — dann kann Stufe 2 ganz entfallen (BACKLOG).
_HIGH_IMPACT_GATED = {"knee", "ankle", "hip", "spine", "neck"}

# Verletzungs-Intensitäts-Deckel (PRIO 2, Safety): der Filter wählt die verletzungssicherste
# Übung, deckelt aber NICHT, wie hart sie geladen wird — diese zweite Schicht tut das.
# joint (aus _VERLETZUNG_MAP) → (betroffene Patterns, RPE-Ceiling). Erweiterbar (knie/schulter …).
# SINGLE SOURCE: Assembler-Emission UND plan_checker Regel 4 nutzen denselben Helper (keine Doppel-Logik).
_VERLETZUNG_RPE_CEILING: dict[str, tuple[set[str], float]] = {
    "spine": ({"hinge", "squat"}, 7.0),   # Wirbelsäule: axiale Hinge/Squat-Last → RIR ≥ 3
}


def verletzungs_rpe_cap(verletzungen, pattern: str, rpe: float | None) -> float | None:
    """Deckelt die RPE einer Übung, wenn eine Verletzung das Pattern axial/risikobehaftet macht.
    rpe is None (Conditioning) → unverändert. Mehrfach-Verletzungen: striktester Ceiling gewinnt."""
    if rpe is None:
        return rpe
    for v in verletzungen:
        joint = _VERLETZUNG_MAP.get(getattr(v, "value", v))
        regel = _VERLETZUNG_RPE_CEILING.get(joint)
        if regel and pattern in regel[0]:
            rpe = min(rpe, regel[1])
    return rpe

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
        # Verletzungs-Filter Stufe 2: High-Impact nur bei Bein-/Achs-/Hals-Verletzung meiden
        # (joint-gegated, Spec Thema 8) — Oberkörper-Verletzte behalten Fuß-Sprünge.
        if (verletzungs_keys & _HIGH_IMPACT_GATED) and ex.get("impact_level") == "high":
            continue

        # Kein verletzungs_flag mehr: nach dem 2-Stufen-Filter ist die Liste
        # per Konstruktion verletzungssicher (substitutions_b abgelöst, MVP-5 Naht 3)
        result.setdefault(ex["pattern"], []).append(ex)

    _apply_pattern_fallback(result)
    return result


# Ersatz-Pattern bei leerem Pool (MVP-5 Naht 4): biomechanisch nächstes Pattern.
# Sicherheitsstufen werden NIE gelockert — bei leerem Pool springt das verwandte
# Pattern ein (markiert), greift auch das nicht, entfällt der Slot ersatzlos.
_FALLBACK_PATTERN: dict[str, str] = {
    "push_vertical":   "push_horizontal",  # beide Druck
    "push_horizontal": "push_vertical",
    "pull_vertical":   "pull_horizontal",  # beide Zug
    "pull_horizontal": "pull_vertical",
    "squat":           "single_leg",       # beide kniedominant
    "single_leg":      "squat",
    "hinge":           "single_leg",       # SL-RDL = hüftdominant, echter Hinge-Ersatz
    "carry":           "core",             # beide Rumpf-Stabilität
}


def _apply_pattern_fallback(pools: dict[str, list[dict]]) -> None:
    """Füllt leere Pattern-Pools aus dem verwandten Pattern (in-place, markiert
    via 'ersatz_fuer'). Liest nur aus original befüllten Pools → kein Chaining."""
    vorhanden = {p for p, exs in pools.items() if exs}
    for pattern, ersatz in _FALLBACK_PATTERN.items():
        if pattern in vorhanden or ersatz not in vorhanden:
            continue  # Pool hat Übungen ODER Ersatz auch leer → Slot entfällt downstream
        pools[pattern] = [{**ex, "ersatz_fuer": pattern} for ex in pools[ersatz]]
