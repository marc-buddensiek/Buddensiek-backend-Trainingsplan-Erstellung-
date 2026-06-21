"""
Level + Ziel + Wochen-Typ + Recovery → per-Tier Sätze + RPE

Volumen = Modell A v2 (Befund 3) — additive Satz-Regel pro Slot, ziel- + level- + wochen-abhängig:
  saetze = clamp(BASIS[ziel][tier] + LEVEL_OFFSET[level] (nur acc/iso) + RAMPE[ziel][woche],
                 BODEN[tier], DECKE[ziel][tier]).
  Mike-Rampe: muskelaufbau/recomp steigern über W1→W3 und deloaden in W4 über das Volumen;
  fettabbau/longevity bleiben flach (Deload dort nur über die RPE). RPE-Welle separat (s.u.).

Session-Budget (Kraft): (Dauer − Warmup 10 − Finisher) ÷ 2 Min/Satz;
  Finisher = 8 Min bei Recomp, sonst 0. Conditioning läuft separat über _METABOLIC_CONFIG.

RPE-Welle (ziel-abhängig, level-gedeckelt — float, 0.5-Raster):
  base = clamp(ZIEL_RPE_WELLE[ziel][woche], FLOOR=4, LEVEL_CAP[level])
  W1 Akku · W2 Prog · W3 Int · W4 Deload — Deload-RPE kommt aus der W4-Spalte der Tabelle.
  Tier-Offset: compound 0 · accessory −1 · isolation −2 · core 0 (Fallback auf ziel_rpe).
  Stress/Schlaf wirken NICHT mehr auf RPE (entkoppelt) — nur noch informativ (recovery_modifier).
"""

from __future__ import annotations
from typing import Literal
from models import KlientenInput, Hauptziel


WocheTyp = Literal["akkumulation", "progression", "intensivierung", "deload"]

# Volumen-Korridore (Modell A v2, Befund 3): additive Satz-Regel pro Slot —
# saetze = clamp(BASIS[ziel][tier] + LEVEL_OFFSET[level](nur acc/iso) + RAMPE[ziel][woche], BODEN, DECKE)
_BASIS: dict[str, dict[str, int]] = {
    "muskelaufbau": {"compound": 3, "accessory": 3, "isolation": 3, "core": 2},
    "fettabbau":    {"compound": 3, "accessory": 2, "isolation": 2, "core": 2},
    "recomp":       {"compound": 3, "accessory": 3, "isolation": 2, "core": 2},
    "longevity":    {"compound": 2, "accessory": 2, "isolation": 2, "core": 2},
}
_LEVEL_OFFSET: dict[int, int] = {1: -1, 2: 0, 3: 0, 4: 1}   # nur accessory + isolation
_RAMPE: dict[str, list[int]] = {   # W1 Akku · W2 Prog · W3 Int · W4 Deload
    "muskelaufbau": [0, 1, 2, -2],
    "recomp":       [0, 0, 1, -1],
    "fettabbau":    [0, 0, 0, 0],
    "longevity":    [0, 0, 0, 0],
}
_BODEN: dict[str, int] = {"compound": 2, "accessory": 2, "isolation": 2, "core": 1}
_WOCHE_IDX = {"akkumulation": 0, "progression": 1, "intensivierung": 2, "deload": 3}


def _decke(ziel: str, tier: str) -> int:
    if tier == "compound": return 4
    if tier == "core":     return 3
    return 5 if ziel == "muskelaufbau" else 4   # accessory/isolation

# Kapazitäts-Konstanten (Spec Thema 3, Zeit-Parameter) — Single Source of Truth,
# auch von plan_assembler konsumiert (Naht 2).
WARMUP_MIN          = 10
FINISHER_MIN_RECOMP = 8
ZEIT_PRO_SATZ_KRAFT = 2.0


def finisher_min(ziel: Hauptziel) -> int:
    return FINISHER_MIN_RECOMP if ziel == Hauptziel.recomp else 0


def tier_floor(tier: str) -> int:
    return _BODEN[tier]   # Korridor-Boden je Tier — Trim-Floor (Modell A v2)

# RPE-Welle pro Ziel (W1 Akku · W2 Prog · W3 Int · W4 Deload) — Intensität vor Volumen.
_ZIEL_RPE_WELLE: dict[str, list[int]] = {
    "muskelaufbau": [7, 8, 9, 6],
    "recomp":       [7, 8, 8, 6],
    "fettabbau":    [7, 7, 8, 6],
    "longevity":    [6, 7, 7, 5],
}
_LEVEL_CAP: dict[int, int] = {1: 7, 2: 8, 3: 9, 4: 9}   # max RPE je Level
_RPE_FLOOR = 4


def _recovery_lage(klient: KlientenInput) -> str:
    # Schlechtester zutreffender Fall gewinnt → schwerste Lage ZUERST:
    if klient.stress_level >= 9 or klient.schlaf_stunden <= 4:
        return "sehr_hoch"
    if klient.stress_level >= 8 or klient.schlaf_stunden <= 5:
        return "hoch"
    if klient.stress_level < 5 and klient.schlaf_stunden >= 7:
        return "gut"
    return "normal"


def _ziel_rpe_base(ziel: str, level: int, woche_typ: WocheTyp) -> float:
    # Welle aus der Ziel-Tabelle, gedeckelt durch den Level-Cap, Boden 4.
    welle = _ZIEL_RPE_WELLE[ziel][_WOCHE_IDX[woche_typ]]
    return float(max(_RPE_FLOOR, min(_LEVEL_CAP[level], welle)))


def _tier_saetze(ziel: str, level: int, tier: str, woche_typ: WocheTyp) -> int:
    # additive Korridor-Regel: Basis(ziel) + Level-Offset(nur acc/iso) + Rampe(ziel,woche),
    # geklemmt in [Boden, Decke]. Mike-Rampe steigert muskel/recomp, deloadet via −Rampe.
    offset = _LEVEL_OFFSET[level] if tier in ("accessory", "isolation") else 0
    rampe  = _RAMPE[ziel][_WOCHE_IDX[woche_typ]]
    return max(_BODEN[tier], min(_decke(ziel, tier), _BASIS[ziel][tier] + offset + rampe))


def berechne_volumen(
    klient: KlientenInput,
    level: int,
    woche_typ: WocheTyp,
) -> dict:
    """
    Returns dict with:
      compound_saetze, accessory_saetze, isolation_saetze, core_saetze: int (Tier-Caps 2–4)
      ziel_saetze: int (= compound_saetze, Haupt-Compound der Session)
      ziel_rpe, compound_rpe, accessory_rpe, isolation_rpe: float (0.5-Raster)
      volumen_stufe: str
      recovery_modifier: str
    """
    lage = _recovery_lage(klient)

    # ── Volumen: Modell A v2 — additive Korridor-Regel (ziel × level × woche), Befund 3 ──
    ziel = klient.hauptziel.value
    compound_saetze  = _tier_saetze(ziel, level, "compound", woche_typ)
    accessory_saetze = _tier_saetze(ziel, level, "accessory", woche_typ)
    isolation_saetze = _tier_saetze(ziel, level, "isolation", woche_typ)
    core_saetze      = _tier_saetze(ziel, level, "core", woche_typ)

    # ── RPE: ziel-abhängige Welle, level-gedeckelt; Recovery wirkt NICHT mehr (entkoppelt) ──
    raw_rpe  = _ziel_rpe_base(ziel, level, woche_typ)   # Deload = W4-Spalte der Tabelle
    ziel_rpe = max(4.0, min(10.0, round(raw_rpe * 2) / 2))   # 0.5-Raster, float in [4,10]

    # ── Volumen-Stufe (Wellen-Label, unverändert) ──
    if woche_typ == "deload":
        stufe = "sehr_niedrig"
    elif woche_typ == "akkumulation":
        stufe = "niedrig"
    elif woche_typ == "progression":
        stufe = "mittel"
    else:
        stufe = "hoch"

    return {
        "compound_saetze":  compound_saetze,
        "accessory_saetze": accessory_saetze,
        "isolation_saetze": isolation_saetze,
        "core_saetze":      core_saetze,
        "ziel_saetze":      compound_saetze,
        "ziel_rpe":         ziel_rpe,
        "compound_rpe":     ziel_rpe,
        "accessory_rpe":    max(4.0, ziel_rpe - 1),
        "isolation_rpe":    max(4.0, ziel_rpe - 2),
        "volumen_stufe":    stufe,
        "recovery_modifier": lage,
    }
